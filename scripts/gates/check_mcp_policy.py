#!/usr/bin/env python3
"""Zero-network gate for the default-deny MCP exposure and runtime contract."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_selftest(repo: Path) -> int:
    commands = [
        [sys.executable, str(repo / "loopctl" / "mcp_tools.py"), "--selftest"],
        [sys.executable, str(repo / "loopctl" / "mcp_runtime.py"), "--selftest"],
    ]
    for command in commands:
        process = subprocess.run(command, cwd=repo, check=False)
        if process.returncode != 0:
            return process.returncode
    return 0


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
