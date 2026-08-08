#!/usr/bin/env python3
"""Stateless MCP server over loopctl, one disposable worktree per call.

    mcp_server.py [--ref <commit|tag>]      serve on stdio
    mcp_server.py --selftest

Isolation is the whole design. Every tool call checks the pinned ref out into a
fresh detached worktree, runs THAT version's loopctl inside it, returns the JSON
result, and destroys the worktree. An external caller therefore cannot reach the
tree anyone is working in, cannot leave anything behind between calls, and cannot
be affected by an edit in flight. Stateless is structural here, not a promise.

--ref pins which workflow answers. A tag is the point: `--ref v1.0` means every
external call is served by the version that tag names, no matter what HEAD is
doing, so customer traffic and internal iteration stop sharing a fate. Without
it the server serves HEAD, which is fine for a dev box and wrong for a service.

The tool list is GENERATED from contract.json (see mcp_tools.py), so the MCP
surface cannot drift from the CLI surface and surface.lock guards both.

Deliberately not solved here, because pretending otherwise would be worse:
  * Driver authentication. `claude -p` and `codex exec` need a live subscription
    session inside the container. container_preflight.sh checks it by spending a
    real turn, because a present-but-unauthenticated binary fails later looking
    like a model refusal.
  * Prompt cache. A fresh process per call reuses nothing. Keep this server
    long-lived — the isolation comes from the per-call worktree, not from
    restarting the process.

Transport is line-delimited JSON-RPC 2.0 over stdio, implemented directly: the
protocol surface used here is initialize / tools/list / tools/call, and a
dependency for three methods would have to be installed in every container that
runs this.
"""

from __future__ import annotations

import json
import base64
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL = "2024-11-05"
MAX_REQUEST_BYTES = 1024 * 1024
MAX_INLINE_OUTPUT_BYTES = 1024 * 1024
SAFE_REF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")

# Tools an external caller may not reach, each with the reason it is refused.
# A denial that cannot say why is indistinguishable from a bug to whoever hits it.
DENIED_TOOLS = {
    "loopctl_openwiki_run": "it can spend real model turns and rewrite openwiki/ "
    "in place; the CLI makes that opt-in behind --full, and an authorization layer "
    "that cannot see flags must refuse the whole tool rather than trust the caller",
    "loopctl_macro_run": "it registers git hooks and mutates git config in whatever "
    "tree it runs in",
    "loopctl_mcp_serve": "a caller able to start another server, unpinned, can "
    "escape the pin it was given",
    "loopctl_container_build": "it drives the host's container runtime",
    "loopctl_container_preflight": "it spends a real model turn per driver to test "
    "credentials, which is a host-operator action rather than a caller's",
}


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "-C", str(HERE), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return Path(out)


def load_tools(contract: Path) -> list[dict]:
    sys.path.insert(0, str(HERE))
    import mcp_tools  # noqa: PLC0415 - resolved from this file's own directory

    return mcp_tools.build(json.loads(contract.read_text(encoding="utf-8")))


def contract_at_ref(root: Path, ref: str) -> dict:
    blob = subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:loopctl/contract.json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if blob.returncode != 0:
        raise ValueError(f"{ref!r} has no loopctl/contract.json")
    value = json.loads(blob.stdout)
    if not isinstance(value, dict):
        raise ValueError(f"{ref!r} contract is not an object")
    return value


def load_tools_at_ref(root: Path, ref: str) -> list[dict]:
    sys.path.insert(0, str(HERE))
    import mcp_tools  # noqa: PLC0415

    return mcp_tools.build(contract_at_ref(root, ref))


def to_argv(tool: dict, arguments: dict) -> list[str]:
    """Arguments to a loopctl argv, refusing anything the tool did not declare.

    An undeclared argument is dropped loudly rather than forwarded: forwarding is
    how a caller starts depending on a target's private switches, which is the
    thing the CLI exists to prevent, and an MCP wrapper is exactly where that
    would creep back in.
    """
    spec = tool["_argv"]
    argv = [spec["loop"], spec["mode"]]
    allowed = {f.lstrip("-").replace("-", "_"): f for f in spec["flags"]}
    unknown = sorted(set(arguments) - set(allowed))
    if unknown:
        raise ValueError(
            f"argument(s) {unknown} are not on the surface for "
            f"{spec['loop']} {spec['mode']}; declared: {sorted(allowed)}"
        )
    for key, value in sorted(arguments.items()):
        flag = allowed[key]
        if isinstance(value, bool):
            if value:
                argv.append(flag)
        else:
            argv += [flag, str(value)]
    if "--json" not in argv:
        argv.append("--json")
    return argv


def safe_artifact_ref(value: object) -> str:
    if not isinstance(value, str) or not SAFE_REF.fullmatch(value):
        raise ValueError(f"unsafe artifact_ref: {value!r}")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"artifact_ref escapes the inline bundle: {value!r}")
    return value


def materialize_inline_bundle(base: Path, arguments: dict) -> Path:
    if set(arguments) != {"bundle"} or not isinstance(arguments["bundle"], dict):
        raise ValueError(
            "CTG MCP accepts exactly one bundle object; local packet/output paths are forbidden"
        )
    bundle = arguments["bundle"]
    if set(bundle) != {"packet_ref", "files"} or not isinstance(bundle["files"], list):
        raise ValueError("bundle must be closed: packet_ref + non-empty files")
    if not bundle["files"]:
        raise ValueError("bundle.files must be non-empty")
    packet_ref = safe_artifact_ref(bundle["packet_ref"])
    target = base / "input"
    seen: set[str] = set()
    decoded_total = 0
    for index, item in enumerate(bundle["files"]):
        if not isinstance(item, dict) or set(item) != {
            "artifact_ref",
            "sha256",
            "content_base64",
        }:
            raise ValueError(f"bundle.files[{index}] is not closed")
        artifact_ref = safe_artifact_ref(item["artifact_ref"])
        if artifact_ref in seen:
            raise ValueError(f"duplicate inline artifact_ref: {artifact_ref}")
        seen.add(artifact_ref)
        try:
            content = base64.b64decode(item["content_base64"], validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"bundle.files[{index}] has invalid base64") from exc
        decoded_total += len(content)
        if decoded_total > MAX_REQUEST_BYTES:
            raise ValueError("decoded CTG inline bundle exceeds 1 MiB")
        actual = hashlib.sha256(content).hexdigest()
        if item["sha256"] != actual:
            raise ValueError(f"inline artifact digest mismatch: {artifact_ref}")
        destination = target / artifact_ref
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    if packet_ref not in seen:
        raise ValueError(f"packet_ref is not present in bundle.files: {packet_ref}")
    return target / packet_ref


def inline_ctg_delivery(output: Path, payload: dict) -> dict:
    result_path = output / "ctg-route-result.json"
    if not result_path.is_file():
        payload["stdout"] = "[CTG MCP streams redacted]"
        payload["stderr"] = "[CTG MCP streams redacted]"
        payload["artifacts"] = []
        return payload
    result = json.loads(result_path.read_text(encoding="utf-8"))
    delivered = []
    total = len(result_path.read_bytes())
    for item in result.get("artifacts", []):
        artifact_ref = safe_artifact_ref(item.get("artifact_ref"))
        artifact = (output / artifact_ref).resolve()
        try:
            artifact.relative_to(output.resolve())
        except ValueError as exc:
            raise ValueError(f"result artifact escapes output: {artifact_ref}") from exc
        content = artifact.read_bytes()
        if hashlib.sha256(content).hexdigest() != item.get("sha256"):
            raise ValueError(f"result artifact digest mismatch: {artifact_ref}")
        total += len(content)
        if total > MAX_INLINE_OUTPUT_BYTES:
            raise ValueError("CTG output exceeds bounded 1 MiB inline delivery")
        delivered.append(
            {
                "kind": item.get("kind"),
                "sha256": item.get("sha256"),
                "content_base64": base64.b64encode(content).decode("ascii"),
            }
        )
    payload["artifacts"] = []
    payload["stdout"] = "[CTG MCP streams redacted; typed artifacts delivered inline]"
    payload["stderr"] = ""
    payload["ctg_delivery"] = {"route_result": result, "artifacts": delivered}
    return payload


def run_isolated(
    root: Path,
    ref: str,
    argv: list[str] | None = None,
    *,
    carrier: dict | None = None,
    arguments: dict | None = None,
) -> dict:
    base = Path(tempfile.mkdtemp(prefix="loopctl-mcp-"))
    worktree = base / "repo"
    try:
        add = subprocess.run(
            ["git", "-C", str(root), "worktree", "add", "--detach", str(worktree), ref],
            capture_output=True,
            text=True,
            check=False,
        )
        if add.returncode != 0:
            return {
                "error": f"could not check {ref} out into a worktree: {add.stderr.strip()[:400]}",
                "exit": 64,
            }
        # The factory's dependencies are gitignored, so no checkout carries them.
        # Borrowing is bounded and stated: whether a clean install suffices is
        # portability.sh's claim, not this server's.
        factory = "loop_wiki/evolve-perfect-seed-repo-factory/node_modules"
        if (root / factory).is_dir() and not (worktree / factory).exists():
            (worktree / factory).parent.mkdir(parents=True, exist_ok=True)
            (worktree / factory).symlink_to(root / factory)
        ctg_output = None
        if carrier and carrier.get("kind") == "ctg-inline-bundle@1.0.0":
            packet = materialize_inline_bundle(base, arguments or {})
            ctg_output = base / "output"
            argv = [
                "ctg",
                "run",
                "--packet",
                str(packet),
                "--output",
                str(ctg_output),
                "--json",
            ]
        if argv is None:
            raise ValueError("isolated call has neither argv nor a supported carrier")
        proc = subprocess.run(
            ["sh", "loopctl/loopctl.sh", *argv],
            cwd=str(worktree),
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            payload = json.loads(proc.stdout)
            return inline_ctg_delivery(ctg_output, payload) if ctg_output else payload
        except json.JSONDecodeError:
            # --json failed to produce a result: report the raw streams rather
            # than a parse error, or the caller sees the wrapper's problem
            # instead of the run's.
            return {
                "error": "loopctl produced no JSON result",
                "exit": proc.returncode,
                "stdout": proc.stdout[-4000:],
                "stderr": proc.stderr[-4000:],
            }
    finally:
        subprocess.run(
            ["git", "-C", str(root), "worktree", "remove", "--force", str(worktree)],
            capture_output=True,
            check=False,
        )
        shutil.rmtree(base, ignore_errors=True)


def handle(request: dict, root: Path, ref: str, tools: list[dict]) -> dict | None:
    method, rid = request.get("method"), request.get("id")
    if method == "initialize":
        result = {
            "protocolVersion": PROTOCOL,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "loopctl", "version": ref},
        }
    elif method == "tools/list":
        result = {
            "tools": [
                {k: v for k, v in t.items() if not k.startswith("_")} for t in tools
            ]
        }
    elif method == "tools/call":
        params = request.get("params") or {}
        tool = next((t for t in tools if t["name"] == params.get("name")), None)
        if tool is None:
            return error(rid, -32602, f"unknown tool {params.get('name')!r}")
        if tool["name"] in DENIED_TOOLS:
            # Authorization lives here, not only in the proxy. The installed
            # OpenShell (0.0.59) matches MCP by method and has no per-TOOL
            # matcher — its policy parser rejects `tool:` outright — so a policy
            # can only allow or deny tools/call as a whole. Depending on a
            # capability the running version lacks would mean exposing every
            # declared tool while a comment claimed otherwise. When the proxy
            # gains per-tool rules they become defence in depth over this, not a
            # replacement for it.
            return error(
                rid,
                -32602,
                f"{tool['name']} is not available to external callers: "
                f"{DENIED_TOOLS[tool['name']]}",
            )
        try:
            arguments = params.get("arguments") or {}
            if tool.get("_carrier"):
                argv = None
            else:
                argv = to_argv(tool, arguments)
        except ValueError as exc:
            return error(rid, -32602, str(exc))
        try:
            payload = run_isolated(
                root,
                ref,
                argv,
                carrier=tool.get("_carrier"),
                arguments=arguments,
            )
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            payload = {"error": str(exc), "exit": 64}
        # isError follows the run's own exit code, so a red gate reaches the
        # caller as a failure rather than as a success carrying bad news.
        result = {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(payload, indent=2, ensure_ascii=False),
                }
            ],
            "isError": payload.get("exit", 1) != 0,
        }
    elif method and method.startswith("notifications/"):
        return None  # notifications take no reply
    else:
        return error(rid, -32601, f"method {method!r} is not implemented")
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def error(rid, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


def assert_ref_serves_json(root: Path, ref: str) -> None:
    """The pinned ref must have the surface this wrapper depends on.

    The wrapper's contract with its caller is structured output, so it forces
    --json onto every call. A ref whose surface predates that flag refuses it as
    undeclared — correctly — and the caller sees exit 64 on every single request
    with no hint that the REF is what is wrong. Checked once, at startup, naming
    the fix, instead of being rediscovered per call.
    """
    try:
        contract = contract_at_ref(root, ref)
    except (ValueError, json.JSONDecodeError):
        raise SystemExit(
            f"mcp FATAL: {ref!r} has no loopctl/contract.json — that ref predates the CLI, "
            "so there is no surface to serve."
        )
    missing = [
        f"{c['loop']} {c['mode']}"
        for c in contract["commands"]
        if "--json" not in c.get("optional", [])
    ]
    if missing:
        raise SystemExit(
            f"mcp FATAL: the surface at {ref!r} (surface_version "
            f"{contract.get('surface_version', 'unknown')}) does not declare --json for "
            f"{missing[:3]}{'…' if len(missing) > 3 else ''}. This server forces --json so its "
            "caller gets structured output, and that ref would refuse it as undeclared on every "
            "call. Pin a ref whose surface carries --json, or serve HEAD."
        )


def serve_http(ref: str, port: int) -> int:
    """The same handler over HTTP POST /mcp, so a policy can see the traffic.

    stdio is unreachable from a sandbox and, more importantly, ungovernable: an
    OpenShell policy inspects MCP over HTTP and can allow or deny per method and
    per tool. A stdio server hands every declared tool to whoever spawns it,
    because there is nothing in between to judge the call. This transport exists
    so the authorization surface can be the policy rather than the client's good
    manners.

    Deliberately minimal and deliberately local: one path, POST only, JSON in and
    JSON out. It binds to 127.0.0.1 — a sandbox reaches it through the runtime's
    host alias, and anything wider would expose the loops to the network at large,
    which is the opposite of the point.
    """
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    root = repo_root()
    assert_ref_serves_json(root, ref)
    tools = load_tools_at_ref(root, ref)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802 - stdlib naming
            if self.path.rstrip("/") != "/mcp":
                self.send_error(404, "only /mcp is served")
                return
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_REQUEST_BYTES:
                self._json(error(None, -32602, "request exceeds 1 MiB"))
                return
            try:
                request = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError as exc:
                self._json(error(None, -32700, f"parse error: {exc}"))
                return
            response = handle(request, root, ref, tools)
            # A notification has no reply; 202 says "accepted, nothing to read"
            # rather than returning an empty body a client would try to parse.
            if response is None:
                self.send_response(202)
                self.end_headers()
                return
            self._json(response)

        def _json(self, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args) -> None:  # noqa: ANN002 - stdlib signature
            return  # the trace that matters is the proxy's, not this one's

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"mcp: serving ref={ref} on http://127.0.0.1:{port}/mcp", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def serve(ref: str) -> int:
    root = repo_root()
    assert_ref_serves_json(root, ref)
    tools = load_tools_at_ref(root, ref)
    for line in sys.stdin:
        if len(line.encode("utf-8")) > MAX_REQUEST_BYTES:
            print(json.dumps(error(None, -32602, "request exceeds 1 MiB")), flush=True)
            continue
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            print(json.dumps(error(None, -32700, f"parse error: {exc}")), flush=True)
            continue
        response = handle(request, root, ref, tools)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


# ---------------------------------------------------------------- selftest


def _selftest() -> int:
    red = 0

    def case(name: str, got, want) -> None:
        nonlocal red
        if got != want:
            print(
                f"SELFTEST case failed — {name}: got {got!r}, want {want!r}",
                file=sys.stderr,
            )
            red = 1

    tools = load_tools(HERE / "contract.json")
    case("tools-generated-from-the-contract", len(tools) > 0, True)

    micro = next(t for t in tools if t["name"] == "loopctl_micro_run")
    case(
        "string-arg-becomes-flag-and-value",
        to_argv(micro, {"packet": "/p.json", "output": "/o"}),
        ["micro", "run", "--output", "/o", "--packet", "/p.json", "--json"],
    )
    # A false boolean must not appear at all: `--full false` would be parsed as
    # --full with a positional, which is a different request than the caller made.
    ow = next(t for t in tools if t["name"] == "loopctl_openwiki_run")
    ctg = next(t for t in tools if t["name"] == "loopctl_ctg_run")
    case("ctg-mcp-requires-inline-bundle", ctg["inputSchema"]["required"], ["bundle"])
    case(
        "ctg-mcp-hides-local-packet-path",
        "packet" in ctg["inputSchema"]["properties"],
        False,
    )
    try:
        with tempfile.TemporaryDirectory() as temp:
            materialize_inline_bundle(Path(temp), {"packet": "/tmp/packet.json"})
        case("ctg-local-path-carrier-is-refused", "returned", "ValueError")
    except ValueError:
        case("ctg-local-path-carrier-is-refused", "ValueError", "ValueError")
    case(
        "false-boolean-is-omitted",
        "--full" in to_argv(ow, {"request": "/r", "full": False}),
        False,
    )
    case(
        "true-boolean-is-a-bare-flag",
        "--full" in to_argv(ow, {"request": "/r", "full": True}),
        True,
    )
    # --json is forced on: the wrapper's contract with its caller is structured
    # output, and a call that forgot the flag would return prose.
    case("json-is-always-requested", to_argv(micro, {"packet": "/p"})[-1], "--json")
    try:
        to_argv(micro, {"sneaky": "x"})
        case("undeclared-argument-is-refused", "returned", "ValueError")
    except ValueError:
        case("undeclared-argument-is-refused", "ValueError", "ValueError")

    root = repo_root()
    case(
        "initialize-answers",
        handle(
            {"jsonrpc": "2.0", "id": 1, "method": "initialize"}, root, "HEAD", tools
        )["result"]["protocolVersion"],
        PROTOCOL,
    )
    case(
        "tools-list-hides-internal-fields",
        all(
            "_argv" not in t
            for t in handle(
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, root, "HEAD", tools
            )["result"]["tools"]
        ),
        True,
    )
    case(
        "unknown-tool-is-an-error",
        "error"
        in handle(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "nope"},
            },
            root,
            "HEAD",
            tools,
        ),
        True,
    )
    case(
        "notification-gets-no-reply",
        handle(
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            root,
            "HEAD",
            tools,
        ),
        None,
    )
    case(
        "unknown-method-is-an-error",
        "error"
        in handle(
            {"jsonrpc": "2.0", "id": 4, "method": "resources/list"}, root, "HEAD", tools
        ),
        True,
    )

    # Server-side authorization, because the proxy on the installed version
    # cannot do it. Both directions: a denied tool is refused WITH ITS REASON,
    # and an allowed one is not caught by the same check — a deny list that
    # catches everything is indistinguishable from a broken server.
    denied = handle(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {"name": "loopctl_openwiki_run", "arguments": {"request": "/r"}},
        },
        root,
        "HEAD",
        tools,
    )
    case("denied-tool-is-refused", "error" in denied, True)
    case(
        "denial-carries-its-reason",
        "model turns" in denied.get("error", {}).get("message", ""),
        True,
    )
    case("every-denial-has-a-reason", all(bool(v) for v in DENIED_TOOLS.values()), True)
    case("allowed-tool-is-not-denied", "loopctl_micro_run" in DENIED_TOOLS, False)
    case("ctg-inline-tool-is-not-denied", "loopctl_ctg_run" in DENIED_TOOLS, False)

    parser_cases = (
        ("missing-ref-is-fatal", [], {}, True),
        ("mutable-head-is-fatal", ["--ref", "HEAD"], {}, True),
        ("unknown-flag-is-fatal", ["--ref", "abc123", "--reff"], {}, True),
        ("missing-ref-value-is-fatal", ["--ref"], {}, True),
        (
            "exact-ref-and-http-parse",
            ["--ref", "abc123", "--http", "8765"],
            {},
            False,
        ),
    )
    for name, arguments, environment, want_error in parser_cases:
        try:
            parsed = parse_server_args(arguments, environment)
        except (TypeError, ValueError):
            got_error = True
            parsed = None
        else:
            got_error = False
        case(name, got_error, want_error)
        if name == "exact-ref-and-http-parse":
            case("exact-ref-and-http-values", parsed, ("abc123", 8765))

    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


def parse_server_args(
    argv: list[str], environment: dict[str, str] | None = None
) -> tuple[str, int | None]:
    environment = os.environ if environment is None else environment
    ref = environment.get("LOOPCTL_REF", "")
    port = None
    rest = list(argv)
    while rest:
        flag = rest.pop(0)
        if flag == "--ref":
            if not rest:
                raise ValueError("--ref requires an exact commit or immutable tag")
            ref = rest.pop(0)
        elif flag == "--http":
            if not rest:
                raise ValueError("--http requires a port")
            port = int(rest.pop(0))
        else:
            raise ValueError(f"unknown argument: {flag}")
    if not ref or ref == "HEAD":
        raise ValueError("an exact --ref or LOOPCTL_REF is required; HEAD is mutable")
    return ref, port


if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv[:1] == ["--selftest"]:
        raise SystemExit(_selftest())
    try:
        ref, port = parse_server_args(argv)
    except (TypeError, ValueError) as exc:
        print(f"mcp-server FATAL: {exc}", file=sys.stderr)
        raise SystemExit(64) from exc
    raise SystemExit(serve_http(ref, port) if port else serve(ref))
