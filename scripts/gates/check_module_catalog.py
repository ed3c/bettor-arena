#!/usr/bin/env python3
"""Zero-network gate for the checked-in bettor-arena module catalog.

The Phase 0 manifest/capability resolver lives in `scripts/arena_modules.py`.
`scripts/arena_lock.py` adds Phase 1 complete tracked-path ownership and binds
its digest into the same checked-in composition lock.  This file remains the
stable commit-gate entrypoint and passes exit codes through unchanged.
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
    parser.add_argument("--index-manifest", type=Path)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    script = root / "scripts" / "arena_lock.py"
    if not script.is_file():
        print(f"module catalog FATAL: missing lock resolver: {script}", file=sys.stderr)
        return 64
    command = [sys.executable, str(script)]
    if args.selftest:
        command.append("--selftest")
    else:
        command.extend(["--root", str(root), "check"])
        if args.index_manifest:
            command.extend(["--index-manifest", str(args.index_manifest)])
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
