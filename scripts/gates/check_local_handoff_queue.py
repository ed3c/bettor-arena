#!/usr/bin/env python3
"""Thin consumer bridge to the canonical skills-shared Local Handoff queue validator."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "docs/traceability/local-handoff-execution-queue.json"
SKILLS_SHARED_COMMIT = "dbcfdb4df76609822893aeb595e5f8ada8483435"
VALIDATOR_RELATIVE = Path("skills/agentic-tech-lead-orchestration/scripts/assert_local_handoff_queue.py")


def git_value(repo: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed for {repo}")
    return proc.stdout.strip()


def validate_skills_shared(root: Path) -> Path:
    root = root.resolve()
    validator = root / VALIDATOR_RELATIVE
    if not validator.is_file():
        raise RuntimeError("canonical Local Handoff validator missing")
    observed = git_value(root, "rev-parse", "HEAD")
    if observed != SKILLS_SHARED_COMMIT:
        raise RuntimeError(f"skills-shared exact subject mismatch: expected {SKILLS_SHARED_COMMIT}, got {observed}")
    if git_value(root, "status", "--porcelain", "--untracked-files=all"):
        raise RuntimeError("skills-shared checkout must be clean")
    return validator


def validate_consumer_queue(validator: Path) -> int:
    return subprocess.run(
        [sys.executable, str(validator), "--queue", str(QUEUE)],
        cwd=ROOT,
        check=False,
    ).returncode


def run_canonical_selftests(validator: Path) -> int:
    # Planted controls belong to the shared Skill's canonical fixture. Consumer
    # instances are validated as data and do not fork/copy the shared test logic.
    return subprocess.run(
        [sys.executable, str(validator), "--selftest"],
        cwd=validator.parent,
        check=False,
    ).returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills-shared-root", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.skills_shared_root is None:
        print("FAIL: --skills-shared-root is required", file=sys.stderr)
        return 2
    try:
        validator = validate_skills_shared(args.skills_shared_root)
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    first = validate_consumer_queue(validator)
    if first != 0:
        return first
    if args.selftest:
        second = run_canonical_selftests(validator)
        if second != 0:
            return second
    print(f"PASS: bettor Local Handoff queue bound to skills-shared@{SKILLS_SHARED_COMMIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
