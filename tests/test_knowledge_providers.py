#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check_knowledge_providers.py"

commands = [
    [sys.executable, str(CHECKER), "--root", str(ROOT)],
    [sys.executable, str(CHECKER), "--root", str(ROOT), "--selftest"],
]

for command in commands:
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

print("knowledge-providers integration test PASS")
