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
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROTOCOL = "2024-11-05"


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


def run_isolated(root: Path, ref: str, argv: list[str]) -> dict:
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
        proc = subprocess.run(
            ["sh", "loopctl/loopctl.sh", *argv],
            cwd=str(worktree),
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            return json.loads(proc.stdout)
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
        try:
            argv = to_argv(tool, params.get("arguments") or {})
        except ValueError as exc:
            return error(rid, -32602, str(exc))
        payload = run_isolated(root, ref, argv)
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
    blob = subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:loopctl/contract.json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if blob.returncode != 0:
        raise SystemExit(
            f"mcp FATAL: {ref!r} has no loopctl/contract.json — that ref predates the CLI, "
            "so there is no surface to serve."
        )
    contract = json.loads(blob.stdout)
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


def serve(ref: str) -> int:
    root = repo_root()
    assert_ref_serves_json(root, ref)
    tools = load_tools(HERE / "contract.json")
    for line in sys.stdin:
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

    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv[:1] == ["--selftest"]:
        raise SystemExit(_selftest())
    ref = "HEAD"
    if argv[:1] == ["--ref"] and len(argv) > 1:
        ref = argv[1]
    elif os.environ.get("LOOPCTL_REF"):
        ref = os.environ["LOOPCTL_REF"]
    raise SystemExit(serve(ref))
