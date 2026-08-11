#!/usr/bin/env python3
"""Zero-network gate for the checked-in bettor-arena module catalog.

The implementation lives in scripts/arena_modules.py so the CLI and commit gate
consume one resolver. This file is only the stable gate entrypoint.

Exit codes are passed through unchanged.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys


def default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_module_catalog.py")
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    script = root / "scripts" / "arena_modules.py"
    if not script.is_file():
        print(f"module catalog FATAL: missing resolver: {script}", file=sys.stderr)
        return 64
    command = [sys.executable, str(script)]
    if args.selftest:
        command.append("--selftest")
    else:
        command.extend(["--root", str(root), "check"])
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
