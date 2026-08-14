#!/usr/bin/env python3
"""Aggregate offline verification for the Agent runtime integration module."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = [
    [sys.executable, "scripts/agent_runtime.py", "check", "--offline"],
    [
        sys.executable,
        ".agents/skills/harness-wiki/scripts/run_portable_skill.py",
        "selftest",
    ],
]


def main() -> int:
    red = False
    for command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, check=False)
        red = red or result.returncode != 0
    print("agent-runtime module: " + ("FAIL" if red else "PASS"))
    return 2 if red else 0


if __name__ == "__main__":
    raise SystemExit(main())
