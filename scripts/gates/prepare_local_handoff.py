#!/usr/bin/env python3
"""Prepare one Local Handoff queue epoch without executing its active mutation."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "docs/traceability/local-handoff-execution-queue.json"
BRIDGE = ROOT / "scripts/gates/check_local_handoff_queue.py"


def run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False)


def git(repo: Path, *args: str) -> str:
    proc = run(["git", "-C", str(repo), *args])
    if proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def digest_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills-shared-root", type=Path, required=True)
    parser.add_argument("--consumer-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    bridge = run(
        [
            sys.executable,
            str(BRIDGE),
            "--skills-shared-root",
            str(args.skills_shared_root.resolve()),
            "--selftest",
        ],
        cwd=ROOT,
    )
    if bridge.returncode != 0:
        print(bridge.stdout, end="")
        print(bridge.stderr, end="", file=sys.stderr)
        return 2

    consumer = args.consumer_root.resolve()
    subject = queue["subject"]
    try:
        head = git(consumer, "rev-parse", "HEAD")
        tree = git(consumer, "rev-parse", "HEAD^{tree}")
        dirty = git(consumer, "status", "--porcelain", "--untracked-files=all")
        rollback_type = git(consumer, "cat-file", "-t", subject["rollback_commit"])
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    if head != subject["commit"]:
        errors.append(
            f"consumer head mismatch: expected {subject['commit']}, got {head}"
        )
    if tree != subject["tree"]:
        errors.append(f"consumer tree mismatch: expected {subject['tree']}, got {tree}")
    if dirty:
        errors.append("consumer execution worktree must be clean")
    if rollback_type != "commit":
        errors.append("rollback subject is not an available commit")
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 2

    active_id = queue["current"]["active_item"]
    active = next(item for item in queue["items"] if item["id"] == active_id)
    receipt = {
        "schema": "bettor-arena/local-handoff-admission/v1",
        "state": "READY_FOR_ACTIVE_ITEM_EXECUTION",
        "queue_sha256": digest_json(queue),
        "active_item": active_id,
        "task_ref": active["task_ref"],
        "consumer": {"commit": head, "tree": tree, "clean": True},
        "skills_shared": {
            "commit": "dbcfdb4df76609822893aeb595e5f8ada8483435",
            "validator": "agentic-tech-lead-orchestration/assert_local_handoff_queue.py",
        },
        "queue_advance": "HUMAN_OWNED",
        "live_execution": "NOT_EXERCISED",
        "next_epoch_rule": "after active-item PASS, freeze a new exact consumer commit/tree before compiling the next queue epoch",
    }
    payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
