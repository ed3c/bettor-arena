#!/usr/bin/env python3
"""Zero-network gate for the default-deny MCP exposure and runtime contract."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys


def root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_selftest(repo: Path) -> int:
    tools_test = subprocess.run(
        [sys.executable, str(repo / "loopctl" / "mcp_tools.py"), "--selftest"],
        cwd=repo,
        check=False,
    )
    if tools_test.returncode != 0:
        return tools_test.returncode

    sys.path.insert(0, str(repo / "loopctl"))
    import mcp_runtime  # noqa: PLC0415

    red = 0

    def case(name: str, got, want) -> None:
        nonlocal red
        if got != want:
            print(f"SELFTEST case failed — {name}: got {got!r}, want {want!r}", file=sys.stderr)
            red = 1

    commit = mcp_runtime.git(repo, "rev-parse", "HEAD")
    tree = mcp_runtime.git(repo, "rev-parse", f"{commit}^{{tree}}")
    tools, modules, policy_digest = mcp_runtime.load_surface(repo, commit)
    case("bounded-policy-tool-count", 0 < len(tools) < 20, True)
    case("policy-digest-length", len(policy_digest), 64)
    case("every-tool-module-is-selected", all(tool["_policy"]["module"] in modules for tool in tools), True)
    try:
        mcp_runtime.resolve_ref(repo, "HEAD")
    except mcp_runtime.McpError:
        pass
    else:
        case("mutable-head-is-refused", "accepted", "McpError")
    try:
        mcp_runtime.to_argv(tools[0], {"force_receipt": "/tmp/escape"})
    except mcp_runtime.McpError:
        pass
    else:
        case("absolute-server-path-is-refused", "accepted", "McpError")

    response = mcp_runtime.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        repo,
        commit,
        tree,
        tools,
        modules,
        policy_digest,
    )
    case("tools-list-hides-policy", all("_policy" not in tool for tool in response["result"]["tools"]), True)
    response = mcp_runtime.handle(
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "loopctl_macro_run"}},
        repo,
        commit,
        tree,
        tools,
        modules,
        policy_digest,
    )
    case("unexposed-tool-is-unknown", "error" in response, True)

    syntax = ast.parse((repo / "loopctl" / "mcp_runtime.py").read_text(encoding="utf-8"))
    symlink_calls = [
        node
        for node in ast.walk(syntax)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "symlink_to"
    ]
    case("no-owner-dependency-symlink", len(symlink_calls), 0)

    parent: Path | None = None
    with mcp_runtime.disposable_worktree(repo, commit) as (_, worktree):
        parent = worktree.parent
        closure = mcp_runtime.module_closure(tools[0]["_policy"]["module"], modules)
        kept, removed = mcp_runtime.prune_worktree(
            worktree,
            mcp_runtime.closure_prefixes(closure, modules),
        )
        case("selected-closure-keeps-files", kept > 0, True)
        case("selected-closure-removes-files", removed > 0, True)
        case("unselected-notebooklm-is-absent", (worktree / "notebooklm").exists(), False)
    case("disposable-worktree-is-cleaned", parent is not None and not parent.exists(), True)

    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


def check(repo: Path) -> int:
    process = subprocess.run(
        [
            sys.executable,
            str(repo / "loopctl" / "mcp_tools.py"),
            str(repo / "loopctl" / "contract.json"),
            "--policy",
            str(repo / ".arena" / "mcp-policy.json"),
        ],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        sys.stderr.write(process.stderr)
        return process.returncode
    try:
        value = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        print(f"MCP policy FATAL: generator output is not JSON: {exc}", file=sys.stderr)
        return 64
    tools = value.get("tools")
    if not isinstance(tools, list) or not tools:
        print("MCP policy RED: explicit policy generated no tools", file=sys.stderr)
        return 2
    names = [tool.get("name") for tool in tools]
    if len(names) != len(set(names)):
        print("MCP policy RED: duplicate tool names", file=sys.stderr)
        return 2
    if any(any(key.startswith("_") for key in tool) for tool in tools):
        print("MCP policy RED: public generator leaked internal fields", file=sys.stderr)
        return 2
    forbidden = {
        "loopctl_macro_run",
        "loopctl_mcp_serve",
        "loopctl_container_build",
        "loopctl_openwiki_run",
        "loopctl_notebooklm_run",
        "loopctl_equivalence_run",
    }
    leaked = sorted(forbidden.intersection(names))
    if leaked:
        print(f"MCP policy RED: dangerous tools exposed: {leaked}", file=sys.stderr)
        return 2
    print(f"PASS default-deny MCP policy ({len(tools)} tools)")
    return 0


def main(argv: list[str]) -> int:
    repo = root()
    if argv == ["--selftest"]:
        return run_selftest(repo)
    if argv:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    return check(repo)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
