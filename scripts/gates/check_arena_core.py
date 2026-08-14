#!/usr/bin/env python3
"""Run all arena-core Agent/document integration gates as one module proof port."""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path
EXIT_OK, EXIT_CHECK_FAILED, EXIT_FATAL = 0, 2, 64
def run(argv:list[str],root:Path)->int:
    completed=subprocess.run(argv,cwd=root,check=False)
    if completed.returncode==EXIT_OK:return EXIT_OK
    if completed.returncode==EXIT_FATAL:return EXIT_FATAL
    return EXIT_CHECK_FAILED
def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(prog="check_arena_core.py"); parser.add_argument("--root",type=Path); parser.add_argument("--selftest",action="store_true"); args=parser.parse_args(argv); root=args.root.resolve() if args.root else Path(__file__).resolve().parents[2]
    if not (root/"AGENTS.md").is_file(): print("arena-core FATAL: repository root not found",file=sys.stderr); return EXIT_FATAL
    suffix=["--selftest"] if args.selftest else []
    for command in [[sys.executable,"scripts/gates/check_agent_docs.py",*suffix],[sys.executable,"scripts/gates/check_pdf_loopx_harness_integration.py",*suffix]]:
        status=run(command,root)
        if status!=EXIT_OK:return status
    print("PASS arena-core aggregate"+(" selftest" if args.selftest else "")); return EXIT_OK
if __name__=="__main__": raise SystemExit(main())
