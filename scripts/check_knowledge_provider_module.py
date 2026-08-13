#!/usr/bin/env python3
"""Aggregate the provider contract and admission-eval hard gates."""
from __future__ import annotations
import argparse
import subprocess
import sys
from pathlib import Path
EXIT_OK, EXIT_CHECK_FAILED, EXIT_FATAL = 0, 2, 64

def run(command: list[str], cwd: Path) -> int:
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode == 0:
        return EXIT_OK
    if completed.returncode == EXIT_FATAL:
        return EXIT_FATAL
    return EXIT_CHECK_FAILED

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]
    if not (root / "scripts/check_knowledge_providers.py").is_file():
        print("knowledge-provider-module ERROR: repository root not found", file=sys.stderr)
        return EXIT_FATAL
    for command in [
        [sys.executable, "scripts/check_knowledge_providers.py", *(["--selftest"] if args.selftest else [])],
        [sys.executable, "scripts/evaluate_knowledge_providers.py", *(["--selftest"] if args.selftest else [])],
    ]:
        status = run(command, root)
        if status != EXIT_OK:
            return status
    print("knowledge-provider-module " + ("selftest PASS" if args.selftest else "PASS"))
    return EXIT_OK

if __name__ == "__main__":
    raise SystemExit(main())
