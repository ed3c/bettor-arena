#!/usr/bin/env python3
"""Generate a default-deny MCP tool list from CLI contract + exposure policy.

    mcp_tools.py <contract> [--policy <policy>]     print tool list as JSON
    mcp_tools.py --selftest

The CLI contract remains the single source for argument names, descriptions,
carrier schema, and exit semantics.  The separate policy answers only the
security question "which already-declared commands may an external caller see,
and under which module/limits?"  No policy means no tools.  A command that was
explicitly marked `mcp_exposed: false` may not be re-enabled by policy.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

POLICY_SCHEMA = "bettor-arena/mcp-policy/v1"
POLICY_FIELDS = {
    "name",
    "module",
    "mutation",
    "network",
    "secrets",
    "max_seconds",
    "max_request_bytes",
    "max_output_bytes",
}


class PolicyError(ValueError):
    """The external MCP policy is malformed or references no CLI promise."""


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def tool_name(command: dict) -> str:
    return f"loopctl_{command['loop']}_{command['mode']}"


def describe(command: dict, contract: dict) -> str:
    io = command.get("io") or {}
    parts = [
        f"{command['mode']}: {contract['modes'].get(command['mode'], '')}".strip(),
        f"Loop: {command['loop']}.",
    ]
    if isinstance(io.get("input"), str):
        parts.append(f"Input: {io['input']}")
    outputs = io.get("output") or command.get("writes") or []
    if outputs:
        parts.append("Writes: " + "; ".join(outputs))
    if io.get("exit"):
        parts.append(f"Exit: {io['exit']}")
    for flag, why in (command.get("opt_in") or {}).items():
        parts.append(f"{flag} — {why}")
    parts.append(
        "Exit codes are the target's own and are never re-mapped: 0 ok, 2 the loop's "
        "own check failed, 64 usage or a FATAL. Do not fold 2 and 64 together."
    )
    return " ".join(part for part in parts if part)


def schema(command: dict) -> dict:
    carrier = command.get("mcp_carrier")
    if carrier:
        return carrier["input_schema"]
    io_input = (command.get("io") or {}).get("input")
    per_flag = io_input if isinstance(io_input, dict) else {}
    opt_in = command.get("opt_in") or {}
    properties: dict[str, dict] = {}
    for flag in sorted(set(command["required"]) | set(command["optional"])):
        key = flag.lstrip("-").replace("-", "_")
        boolean = flag in opt_in and flag not in per_flag
        properties[key] = {
            "type": "boolean" if boolean else "string",
            "description": per_flag.get(flag) or opt_in.get(flag) or flag,
        }
    return {
        "type": "object",
        "properties": properties,
        "required": [
            flag.lstrip("-").replace("-", "_") for flag in command["required"]
        ],
        "additionalProperties": False,
    }


def validate_policy(policy: dict | None, contract: dict) -> list[dict]:
    if policy is None:
        return []
    if not isinstance(policy, dict) or set(policy) != {"schema", "tools"}:
        raise PolicyError("MCP policy fields drifted")
    if policy["schema"] != POLICY_SCHEMA:
        raise PolicyError(f"MCP policy schema must be {POLICY_SCHEMA}")
    if not isinstance(policy["tools"], list):
        raise PolicyError("MCP policy tools must be an array")

    commands = {tool_name(command): command for command in contract["commands"]}
    seen: set[str] = set()
    normalized: list[dict] = []
    for index, entry in enumerate(policy["tools"]):
        if not isinstance(entry, dict) or set(entry) != POLICY_FIELDS:
            raise PolicyError(f"MCP policy tool[{index}] fields drifted")
        name = entry["name"]
        if not isinstance(name, str) or not name:
            raise PolicyError(f"MCP policy tool[{index}] name is required")
        if name in seen:
            raise PolicyError(f"duplicate MCP policy tool: {name}")
        seen.add(name)
        command = commands.get(name)
        if command is None:
            raise PolicyError(f"MCP policy references unknown CLI command: {name}")
        if command.get("mcp_exposed") is False:
            raise PolicyError(f"CLI contract explicitly forbids MCP exposure: {name}")
        if not isinstance(entry["module"], str) or not entry["module"]:
            raise PolicyError(f"MCP policy module is required: {name}")
        if entry["mutation"] not in {"none", "disposable-worktree"}:
            raise PolicyError(f"unsupported mutation policy: {name}")
        if entry["network"] not in {"none", "optional"}:
            raise PolicyError(f"unsupported network policy: {name}")
        if entry["secrets"] not in {"none", "broker-only"}:
            raise PolicyError(f"unsupported secrets policy: {name}")
        for field in ("max_seconds", "max_request_bytes", "max_output_bytes"):
            if not isinstance(entry[field], int) or entry[field] <= 0:
                raise PolicyError(f"{name}.{field} must be positive")
        normalized.append(dict(entry))
    return sorted(normalized, key=lambda item: item["name"])


def build(contract: dict, policy: dict | None = None) -> list[dict]:
    commands = {tool_name(command): command for command in contract["commands"]}
    entries = validate_policy(policy, contract)
    tools: list[dict] = []
    for entry in entries:
        command = commands[entry["name"]]
        tools.append(
            {
                "name": entry["name"],
                "description": describe(command, contract),
                "inputSchema": schema(command),
                "_argv": {
                    "loop": command["loop"],
                    "mode": command["mode"],
                    "flags": sorted(
                        set(command["required"]) | set(command["optional"])
                    ),
                },
                "_policy": entry,
                **(
                    {"_carrier": command["mcp_carrier"]}
                    if command.get("mcp_carrier")
                    else {}
                ),
            }
        )
    return tools


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    if not argv:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    contract_path = Path(argv[0])
    policy = None
    rest = argv[1:]
    if rest:
        if len(rest) != 2 or rest[0] != "--policy":
            print(__doc__.strip(), file=sys.stderr)
            return 64
        policy = json.loads(Path(rest[1]).read_text(encoding="utf-8"))
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    try:
        tools = build(contract, policy)
    except PolicyError as exc:
        print(f"MCP policy RED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"tools": tools}, indent=2, ensure_ascii=False))
    return 0


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

    contract = {
        "modes": {"run": "execute it", "prove": "traverse it"},
        "commands": [
            {
                "loop": "micro",
                "mode": "run",
                "target": "t.sh",
                "required": ["--packet"],
                "optional": ["--json", "--full"],
                "opt_in": {"--full": "spends real model turns"},
                "io": {
                    "input": {"--packet": "path to a packet"},
                    "output": ["out/"],
                    "exit": "0 ok · 2 failed",
                },
            },
            {
                "loop": "macro",
                "mode": "prove",
                "target": "p.sh",
                "required": [],
                "optional": [],
                "writes": ["receipt.json"],
            },
            {
                "loop": "ctg",
                "mode": "run",
                "target": "ctg.sh",
                "required": ["--packet", "--output"],
                "optional": ["--json"],
                "mcp_carrier": {
                    "kind": "fixture-inline@1.0.0",
                    "input_schema": {
                        "type": "object",
                        "properties": {"bundle": {"type": "object"}},
                        "required": ["bundle"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "loop": "ctg",
                "mode": "build-local",
                "target": "local.sh",
                "required": ["--manifest", "--output"],
                "optional": ["--json"],
                "mcp_exposed": False,
            },
        ],
    }
    case("no-policy-means-no-tools", build(contract), [])
    policy = {
        "schema": POLICY_SCHEMA,
        "tools": [
            {
                "name": "loopctl_ctg_run",
                "module": "ctg",
                "mutation": "disposable-worktree",
                "network": "none",
                "secrets": "none",
                "max_seconds": 60,
                "max_request_bytes": 1024,
                "max_output_bytes": 2048,
            },
            {
                "name": "loopctl_macro_prove",
                "module": "core",
                "mutation": "disposable-worktree",
                "network": "none",
                "secrets": "none",
                "max_seconds": 60,
                "max_request_bytes": 1024,
                "max_output_bytes": 2048,
            },
        ],
    }
    tools = build(contract, policy)
    case(
        "only-policy-tools-are-exposed",
        [tool["name"] for tool in tools],
        ["loopctl_ctg_run", "loopctl_macro_prove"],
    )
    ctg = tools[0]
    case("carrier-schema-still-comes-from-cli", ctg["inputSchema"]["required"], ["bundle"])
    case("module-policy-is-kept-internally", ctg["_policy"]["module"], "ctg")
    case("internal-fields-are-present-for-server", "_argv" in ctg, True)
    case(
        "exit-contract-on-every-tool",
        all("never re-mapped" in tool["description"] for tool in tools),
        True,
    )
    broken = json.loads(json.dumps(policy))
    broken["tools"][0]["name"] = "loopctl_nope_run"
    try:
        build(contract, broken)
    except PolicyError:
        pass
    else:
        case("unknown-policy-tool-is-red", "accepted", "PolicyError")
    broken = json.loads(json.dumps(policy))
    broken["tools"][0]["name"] = "loopctl_ctg_build-local"
    try:
        build(contract, broken)
    except PolicyError:
        pass
    else:
        case("explicitly-local-command-cannot-be-reenabled", "accepted", "PolicyError")

    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
