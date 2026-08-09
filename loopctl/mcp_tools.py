#!/usr/bin/env python3
"""Generate the MCP tool definitions from contract.json.

    mcp_tools.py <contract>     print the tool list as JSON
    mcp_tools.py --selftest

Generated, never hand-written. A hand-kept MCP surface is a second copy of the
CLI surface, and two copies of the same promise drift the first time one is
edited alone — which is the entire failure this CLI was built to stop, one layer
up. Generating them means `surface.lock` guards both: an external caller pinning
surface_version is pinning what the MCP tools accept.

Descriptions are assembled from the contract's own io/opt_in prose rather than
written again here, so an agent reading the tool list sees the same constraints
a human reading `loopctl.sh contract` sees. The one that matters most is carried
verbatim into every description: exit codes are the target's own and are never
re-mapped, so 2 and 64 mean different things and a caller must not fold them.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


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
    return " ".join(p for p in parts if p)


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
        # A boolean is a flag the caller either passes or does not; anything the
        # contract documents per-value takes a string. Guessing the other way
        # would make an agent send `--full "true"`.
        boolean = flag in opt_in and flag not in per_flag
        properties[key] = {
            "type": "boolean" if boolean else "string",
            "description": per_flag.get(flag) or opt_in.get(flag) or f"{flag}",
        }
    return {
        "type": "object",
        "properties": properties,
        "required": [f.lstrip("-").replace("-", "_") for f in command["required"]],
        "additionalProperties": False,
    }


def build(contract: dict) -> list[dict]:
    return [
        {
            "name": tool_name(c),
            "description": describe(c, contract),
            "inputSchema": schema(c),
            "_argv": {
                "loop": c["loop"],
                "mode": c["mode"],
                "flags": sorted(set(c["required"]) | set(c["optional"])),
            },
            **({"_carrier": c["mcp_carrier"]} if c.get("mcp_carrier") else {}),
        }
        for c in sorted(contract["commands"], key=lambda c: (c["loop"], c["mode"]))
        if c.get("mcp_exposed", True)
    ]


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    if not argv:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    contract = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    print(json.dumps({"tools": build(contract)}, indent=2, ensure_ascii=False))
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
    tools = build(contract)
    case("local-only-command-is-not-an-mcp-tool", len(tools), 3)
    case(
        "names-are-stable-and-sorted",
        [t["name"] for t in tools],
        ["loopctl_ctg_run", "loopctl_macro_prove", "loopctl_micro_run"],
    )

    micro = next(t for t in tools if t["name"] == "loopctl_micro_run")
    ctg = next(t for t in tools if t["name"] == "loopctl_ctg_run")
    case("required-flag-is-required", micro["inputSchema"]["required"], ["packet"])
    case("carrier-overrides-path-flags", ctg["inputSchema"]["required"], ["bundle"])
    case(
        "carrier-is-kept-for-dispatch", ctg["_carrier"]["kind"], "fixture-inline@1.0.0"
    )
    case(
        "documented-flag-is-a-string",
        micro["inputSchema"]["properties"]["packet"]["type"],
        "string",
    )
    # An opt-in switch with no documented value is a boolean; getting this wrong
    # makes an agent send `--full "true"` and the CLI refuse it.
    case(
        "opt-in-switch-is-a-boolean",
        micro["inputSchema"]["properties"]["full"]["type"],
        "boolean",
    )
    case("no-extra-properties", micro["inputSchema"]["additionalProperties"], False)
    case(
        "per-flag-prose-is-reused",
        micro["inputSchema"]["properties"]["packet"]["description"],
        "path to a packet",
    )
    # The exit-code warning must be on EVERY tool: a caller that folds 2 and 64
    # cannot tell a red gate from a missing tool.
    case(
        "exit-contract-on-every-tool",
        all("never re-mapped" in t["description"] for t in tools),
        True,
    )
    case(
        "mode-prose-is-reused", micro["description"].startswith("run: execute it"), True
    )

    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
