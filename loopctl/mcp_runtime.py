#!/usr/bin/env python3
"""Default-deny stateless MCP runtime for loopctl.

Every call resolves one immutable Git subject, validates the policy and selected
module at that subject, checks out a disposable worktree, removes tracked files
outside the selected module's transitive capability closure, executes only the
contract-derived argv/carrier, bounds output, and removes the worktree.

Transport: line-delimited JSON-RPC 2.0 over stdio. Supported methods are
initialize, tools/list, and tools/call.
"""

from __future__ import annotations

import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterator

HERE = Path(__file__).resolve().parent
PROTOCOL = "2024-11-05"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
TAG = re.compile(r"^v[0-9][0-9A-Za-z._-]*$")
SAFE_ARTIFACT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
SECRET_NAMES = {
    "ANTHROPIC_API_KEY",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "CODEX_ACCESS_TOKEN",
    "CODEX_API_KEY",
    "E2B_API_KEY",
    "FORGEJO_PASSWORD",
    "FORGEJO_TOKEN",
    "GEMINI_API_KEY",
    "GITHUB_TOKEN",
    "OPENAI_API_KEY",
}


class McpError(ValueError):
    """An MCP policy, request, or immutable execution contract is invalid."""


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def repo_root() -> Path:
    process = subprocess.run(
        ["git", "-C", str(HERE), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise McpError(process.stderr.strip() or "not inside a Git worktree")
    return Path(process.stdout.strip())


def git(root: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise McpError(process.stderr.strip() or f"git {' '.join(args)} failed")
    return process.stdout.strip()


def resolve_ref(root: Path, ref: str) -> tuple[str, str]:
    if ref in {"HEAD", "main", "master", "trunk"}:
        raise McpError(f"mutable ref is refused: {ref}")
    if not (SHA40.fullmatch(ref) or TAG.fullmatch(ref)):
        raise McpError("ref must be an exact 40-hex commit or immutable v* tag")
    commit = git(root, "rev-parse", f"{ref}^{{commit}}")
    tree = git(root, "rev-parse", f"{commit}^{{tree}}")
    if not SHA40.fullmatch(commit) or not SHA40.fullmatch(tree):
        raise McpError("ref did not resolve to immutable Git ids")
    return commit, tree


def json_at_ref(root: Path, ref: str, path: str) -> dict[str, Any]:
    process = subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise McpError(f"{ref} has no {path}")
    try:
        value = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise McpError(f"{ref}:{path} is not JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise McpError(f"{ref}:{path} must be an object")
    return value


def tool_name(command: dict[str, Any]) -> str:
    return f"loopctl_{command['loop']}_{command['mode']}"


def selected_modules(lock: dict[str, Any]) -> set[str]:
    modules = lock.get("modules")
    if not isinstance(modules, list):
        raise McpError("composition lock modules are malformed")
    return {item["id"] for item in modules if isinstance(item, dict) and isinstance(item.get("id"), str)}


def load_modules_at_ref(root: Path, ref: str, selected: set[str]) -> dict[str, dict[str, Any]]:
    modules: dict[str, dict[str, Any]] = {}
    for module_id in sorted(selected):
        modules[module_id] = json_at_ref(
            root, ref, f".arena/modules/{module_id}/module.json"
        )
    return modules


def validate_external_policy(
    contract: dict[str, Any],
    policy: dict[str, Any],
    lock: dict[str, Any],
    modules: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    sys.path.insert(0, str(HERE))
    import mcp_tools  # noqa: PLC0415

    tools = mcp_tools.build(contract, policy)
    selected = selected_modules(lock)
    for tool in tools:
        entry = tool["_policy"]
        module_id = entry["module"]
        if module_id not in selected:
            raise McpError(f"MCP policy module is not selected: {module_id}")
        module = modules.get(module_id)
        if module is None:
            raise McpError(f"MCP policy module manifest is absent: {module_id}")
        external = module.get("external_policy") or {}
        if external.get("exposed") is not True:
            raise McpError(f"module does not permit external exposure: {module_id}")
        loop_id = tool["_argv"]["loop"]
        loop_matches = [
            loop
            for loop in module.get("loops", [])
            if isinstance(loop, dict) and loop.get("id") == loop_id
        ]
        if len(loop_matches) != 1 or loop_matches[0].get("external_policy") != "allowlisted":
            raise McpError(
                f"tool {tool['name']} is not an allowlisted loop of module {module_id}"
            )
        if entry["mutation"] != external.get("mutation") and not (
            entry["mutation"] == "none" and external.get("mutation") == "disposable-worktree"
        ):
            raise McpError(f"tool mutation exceeds module policy: {tool['name']}")
        if entry["secrets"] != "none":
            raise McpError(
                f"broker-only secret delivery is not implemented for external tool {tool['name']}"
            )
    return tools


def module_closure(
    module_id: str,
    modules: dict[str, dict[str, Any]],
) -> list[str]:
    providers: dict[str, str] = {}
    for candidate, module in modules.items():
        for capability in module.get("provides", []):
            if capability in providers and providers[capability] != candidate:
                raise McpError(f"duplicate capability provider: {capability}")
            providers[capability] = candidate
    selected: set[str] = set()
    queue = [module_id]
    while queue:
        current = queue.pop(0)
        if current in selected:
            continue
        selected.add(current)
        for capability in modules[current].get("requires", []):
            if capability.startswith("external:"):
                continue
            provider = providers.get(capability)
            if provider is None:
                raise McpError(f"{current} has no provider for {capability}")
            queue.append(provider)
    return sorted(selected)


def normalize_prefix(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise McpError(f"module path is not portable: {value}")
    return path.as_posix().rstrip("/")


def closure_prefixes(
    closure: list[str],
    modules: dict[str, dict[str, Any]],
) -> list[str]:
    prefixes: set[str] = set()
    for module_id in closure:
        module = modules[module_id]
        for value in module.get("roots", []):
            prefixes.add(normalize_prefix(value))
        for component in (module.get("components") or {}).values():
            for value in component.get("paths", []):
                prefixes.add(normalize_prefix(value))
        prefixes.add(f".arena/modules/{module_id}/module.json")
    # These are immutable generated inputs, not host secrets.  They are needed
    # only when a selected module explicitly refers to them.
    prefixes.update(
        {
            ".arena/mcp-policy.json",
            ".arena/locks/bettor-arena.lock.json",
            ".arena/contexts.lock.json",
            "data/module-proof/subjects.lock.json",
            "data/context-capsules/driver-parity.json",
        }
    )
    return sorted(prefix for prefix in prefixes if prefix and prefix != ".")


def path_matches(path: str, prefix: str) -> bool:
    return path == prefix or path.startswith(prefix + "/")


def prune_worktree(worktree: Path, prefixes: list[str]) -> tuple[int, int]:
    process = subprocess.run(
        ["git", "-C", str(worktree), "ls-files", "-z"],
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise McpError("cannot list disposable worktree files")
    kept = removed = 0
    for raw in process.stdout.split(b"\0"):
        if not raw:
            continue
        path = raw.decode("utf-8", errors="strict")
        if any(path_matches(path, prefix) for prefix in prefixes):
            kept += 1
            continue
        target = worktree / path
        if target.is_symlink() or target.is_file():
            target.unlink()
        removed += 1
    for directory in sorted(
        (path for path in worktree.rglob("*") if path.is_dir()),
        key=lambda item: len(item.parts),
        reverse=True,
    ):
        if directory.name == ".git":
            continue
        try:
            directory.rmdir()
        except OSError:
            pass
    return kept, removed


@contextmanager
def disposable_worktree(root: Path, commit: str) -> Iterator[tuple[Path, Path]]:
    base = Path(tempfile.mkdtemp(prefix="loopctl-mcp-"))
    worktree = base / "repo"
    try:
        process = subprocess.run(
            ["git", "-C", str(root), "worktree", "add", "--detach", str(worktree), commit],
            capture_output=True,
            text=True,
            check=False,
        )
        if process.returncode != 0:
            raise McpError(process.stderr.strip() or "git worktree add failed")
        yield base, worktree
    finally:
        if worktree.exists():
            subprocess.run(
                ["git", "-C", str(root), "worktree", "remove", "--force", str(worktree)],
                capture_output=True,
                check=False,
            )
        shutil.rmtree(base, ignore_errors=True)


def to_argv(tool: dict[str, Any], arguments: dict[str, Any]) -> list[str]:
    spec = tool["_argv"]
    allowed = {
        flag.lstrip("-").replace("-", "_"): flag for flag in spec["flags"]
    }
    unknown = sorted(set(arguments) - set(allowed))
    if unknown:
        raise McpError(f"undeclared argument(s): {unknown}")
    argv = [spec["loop"], spec["mode"]]
    for key, value in sorted(arguments.items()):
        flag = allowed[key]
        if isinstance(value, bool):
            if value:
                argv.append(flag)
            continue
        if not isinstance(value, str):
            raise McpError(f"argument {key} must be a string or boolean")
        candidate = Path(value)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise McpError(f"server-host path is forbidden: {key}")
        argv.extend([flag, value])
    if "--json" not in argv:
        argv.append("--json")
    return argv


def safe_artifact_ref(value: object) -> str:
    if not isinstance(value, str) or not SAFE_ARTIFACT.fullmatch(value):
        raise McpError(f"unsafe artifact_ref: {value!r}")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise McpError(f"artifact_ref escapes bundle: {value!r}")
    return value


def materialize_inline_bundle(
    base: Path,
    arguments: dict[str, Any],
    max_bytes: int,
) -> Path:
    if set(arguments) != {"bundle"} or not isinstance(arguments["bundle"], dict):
        raise McpError("typed inline carrier accepts exactly one bundle object")
    bundle = arguments["bundle"]
    if set(bundle) != {"packet_ref", "files"} or not isinstance(bundle["files"], list):
        raise McpError("bundle must contain packet_ref and files")
    if not bundle["files"]:
        raise McpError("bundle.files must be non-empty")
    packet_ref = safe_artifact_ref(bundle["packet_ref"])
    target = base / "input"
    seen: set[str] = set()
    total = 0
    for index, item in enumerate(bundle["files"]):
        if not isinstance(item, dict) or set(item) != {
            "artifact_ref",
            "sha256",
            "content_base64",
        }:
            raise McpError(f"bundle.files[{index}] is not closed")
        artifact_ref = safe_artifact_ref(item["artifact_ref"])
        if artifact_ref in seen:
            raise McpError(f"duplicate artifact_ref: {artifact_ref}")
        seen.add(artifact_ref)
        try:
            content = base64.b64decode(item["content_base64"], validate=True)
        except (TypeError, ValueError) as exc:
            raise McpError(f"bundle.files[{index}] has invalid base64") from exc
        total += len(content)
        if total > max_bytes:
            raise McpError("decoded inline request exceeds policy limit")
        if hashlib.sha256(content).hexdigest() != item["sha256"]:
            raise McpError(f"inline artifact digest mismatch: {artifact_ref}")
        destination = target / artifact_ref
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
    if packet_ref not in seen:
        raise McpError("packet_ref is not present in files")
    return target / packet_ref


def bounded_payload(process: subprocess.CompletedProcess[str], limit: int) -> dict[str, Any]:
    total = len(process.stdout.encode()) + len(process.stderr.encode())
    if total > limit:
        raise McpError("loopctl output exceeds policy limit")
    try:
        value = json.loads(process.stdout)
    except json.JSONDecodeError:
        return {
            "error": "loopctl produced no JSON result",
            "exit": process.returncode,
            "stdout": process.stdout[-4000:],
            "stderr": process.stderr[-4000:],
        }
    if not isinstance(value, dict):
        raise McpError("loopctl JSON result must be an object")
    return value


def execute_tool(
    root: Path,
    commit: str,
    tree: str,
    tool: dict[str, Any],
    modules: dict[str, dict[str, Any]],
    policy_digest: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    policy = tool["_policy"]
    closure = module_closure(policy["module"], modules)
    prefixes = closure_prefixes(closure, modules)
    payload: dict[str, Any]
    cleanup = "FAIL"
    with disposable_worktree(root, commit) as (base, worktree):
        kept, removed = prune_worktree(worktree, prefixes)
        if not (worktree / "loopctl" / "loopctl.sh").is_file():
            raise McpError("selected module closure omitted loopctl")
        carrier = tool.get("_carrier")
        if carrier:
            if carrier.get("kind") != "ctg-inline-bundle@1.0.0":
                raise McpError(f"unsupported carrier: {carrier.get('kind')}")
            packet = materialize_inline_bundle(
                base, arguments, policy["max_request_bytes"]
            )
            output = base / "output"
            argv = [
                "ctg",
                "run",
                "--packet",
                str(packet),
                "--output",
                str(output),
                "--json",
            ]
        else:
            request_size = len(canonical(arguments))
            if request_size > policy["max_request_bytes"]:
                raise McpError("request exceeds policy limit")
            argv = to_argv(tool, arguments)
        environment = dict(os.environ)
        if policy["secrets"] == "none":
            for name in SECRET_NAMES:
                environment.pop(name, None)
        try:
            process = subprocess.run(
                ["sh", "loopctl/loopctl.sh", *argv],
                cwd=worktree,
                env=environment,
                capture_output=True,
                text=True,
                timeout=policy["max_seconds"],
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise McpError(f"tool timed out after {policy['max_seconds']} seconds") from exc
        payload = bounded_payload(process, policy["max_output_bytes"])
        payload["mcp_subject"] = {
            "module": policy["module"],
            "module_closure": closure,
            "commit": commit,
            "tree": tree,
            "policy_sha256": policy_digest,
            "kept_tracked_files": kept,
            "removed_tracked_files": removed,
            "owner_dependency_borrowing": False,
        }
    cleanup = "PASS"
    payload["mcp_subject"]["cleanup"] = cleanup
    return payload


def public_tool(tool: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in tool.items() if not key.startswith("_")}


def error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def result(request_id: Any, value: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": value}


def load_surface(root: Path, commit: str) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], str]:
    contract = json_at_ref(root, commit, "loopctl/contract.json")
    policy = json_at_ref(root, commit, ".arena/mcp-policy.json")
    lock = json_at_ref(root, commit, ".arena/locks/bettor-arena.lock.json")
    selected = selected_modules(lock)
    modules = load_modules_at_ref(root, commit, selected)
    tools = validate_external_policy(contract, policy, lock, modules)
    return tools, modules, digest_value(policy)


def handle(
    request: dict[str, Any],
    root: Path,
    commit: str,
    tree: str,
    tools: list[dict[str, Any]],
    modules: dict[str, dict[str, Any]],
    policy_digest: str,
) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    if method == "initialize":
        return result(
            request_id,
            {
                "protocolVersion": PROTOCOL,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "loopctl", "version": commit},
            },
        )
    if method == "tools/list":
        return result(request_id, {"tools": [public_tool(tool) for tool in tools]})
    if method == "tools/call":
        params = request.get("params") or {}
        tool = next((item for item in tools if item["name"] == params.get("name")), None)
        if tool is None:
            return error(request_id, -32602, f"unknown or unexposed tool {params.get('name')!r}")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            return error(request_id, -32602, "tool arguments must be an object")
        try:
            payload = execute_tool(
                root, commit, tree, tool, modules, policy_digest, arguments
            )
        except (McpError, OSError, subprocess.SubprocessError) as exc:
            payload = {"error": str(exc), "exit": 64}
        return result(
            request_id,
            {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(payload, indent=2, ensure_ascii=False),
                    }
                ],
                "isError": payload.get("exit", 0) != 0,
            },
        )
    if method == "notifications/initialized":
        return None
    return error(request_id, -32601, f"unsupported method: {method}")


def parse_args(argv: list[str], environment: dict[str, str] | None = None) -> str:
    environment = os.environ if environment is None else environment
    ref = environment.get("LOOPCTL_REF", "")
    rest = list(argv)
    while rest:
        flag = rest.pop(0)
        if flag != "--ref" or not rest:
            raise McpError("usage: mcp_server.py --ref <40-hex|v-tag>")
        ref = rest.pop(0)
    if not ref:
        raise McpError("an immutable --ref or LOOPCTL_REF is required")
    return ref


def serve(ref: str) -> int:
    root = repo_root()
    commit, tree = resolve_ref(root, ref)
    tools, modules, policy_digest = load_surface(root, commit)
    for line in sys.stdin:
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise json.JSONDecodeError("request is not an object", line, 0)
        except json.JSONDecodeError as exc:
            print(json.dumps(error(None, -32700, f"parse error: {exc}")), flush=True)
            continue
        response = handle(request, root, commit, tree, tools, modules, policy_digest)
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)
    return 0


def _selftest() -> int:
    red = 0

    def case(name: str, got: Any, want: Any) -> None:
        nonlocal red
        if got != want:
            print(f"SELFTEST case failed — {name}: got {got!r}, want {want!r}", file=sys.stderr)
            red = 1

    root = repo_root()
    commit = git(root, "rev-parse", "HEAD")
    tree = git(root, "rev-parse", f"{commit}^{{tree}}")
    tools, modules, policy_digest = load_surface(root, commit)
    case("policy-exposes-a-bounded-set", 0 < len(tools) < 20, True)
    case("policy-digest-is-stable", len(policy_digest), 64)
    case("all-tools-name-a-module", all(tool["_policy"]["module"] in modules for tool in tools), True)
    try:
        parse_args(["--ref", "HEAD"], {})
        case("mutable-head-is-refused", "accepted", "McpError")
    except McpError:
        pass
    try:
        to_argv(tools[0], {"force_receipt": "/tmp/escape"})
        case("absolute-server-path-is-refused", "accepted", "McpError")
    except McpError:
        pass
    response = handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        root,
        commit,
        tree,
        tools,
        modules,
        policy_digest,
    )
    case("tools-list-hides-policy", all("_policy" not in tool for tool in response["result"]["tools"]), True)
    response = handle(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "loopctl_macro_run"}},
        root,
        commit,
        tree,
        tools,
        modules,
        policy_digest,
    )
    case("unexposed-tool-is-unknown", "error" in response, True)
    source = Path(__file__).read_text(encoding="utf-8")
    case("no-owner-node-modules-borrowing", "symlink_to(root / factory)" in source, False)

    parent: Path | None = None
    with disposable_worktree(root, commit) as (_, worktree):
        parent = worktree.parent
        closure = module_closure(tools[0]["_policy"]["module"], modules)
        prune_worktree(worktree, closure_prefixes(closure, modules))
        case("unselected-notebooklm-is-absent", (worktree / "notebooklm").exists(), tools[0]["_policy"]["module"] == "notebooklm")
    case("disposable-worktree-is-cleaned", parent is not None and not parent.exists(), True)

    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--selftest"]:
        return _selftest()
    try:
        ref = parse_args(argv)
        return serve(ref)
    except McpError as exc:
        print(f"mcp-server FATAL: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
