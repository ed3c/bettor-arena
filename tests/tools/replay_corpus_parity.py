#!/usr/bin/env python3
"""replay_corpus_parity — re-measure original-vs-rebuilt molecular validator parity.

Reproduces data/receipts/molecular-corpus-parity.json: run the last N commit
messages of --source-repo through both the original UDPT validator (inside the
source repo, read-only) and this repo's rebuilt .githooks/lib validator, in
message-only mode (an empty --changed-paths-file), and report exit-code parity.

Mismatches are expected by design: the rebuild deliberately stripped the
UDPT-specific rules S1–S5 (see the rebuilt validator's header), so commits the
original rejects under those rules pass the rebuild. This script measures the
gap; it does not judge it.

Usage:
  python3 tests/tools/replay_corpus_parity.py --source-repo <path> [--commits N] [--out FILE]

Exit codes: 0 measurement completed · 64 precondition (missing repo/validator/bun).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ARENA_ROOT = Path(__file__).resolve().parents[2]
REBUILT_REL = ".githooks/lib/validate_molecular_message.ts"
ORIGINAL_REL = ("loop_wiki/evolve-unknown-discovery-plan-truth/adapters/typescript/"
                "runtime/scripts/validate_molecular_commit_message.ts")


def die(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(64)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True)
    if result.returncode != 0:
        die(f"git {' '.join(args)} failed in {repo.name}: {result.stderr.strip()}")
    return result.stdout


def run_validator(validator: Path, message_file: Path, empty_paths_file: Path) -> tuple[int, str]:
    result = subprocess.run(
        ["bun", "run", str(validator), "--changed-paths-file", str(empty_paths_file),
         str(message_file)],
        text=True, capture_output=True, cwd=str(validator.parent))
    return result.returncode, result.stderr


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True,
                        help="root of the source repo carrying the original validator (read-only)")
    parser.add_argument("--commits", type=int, default=100)
    parser.add_argument("--out", type=Path, help="receipt file (default: stdout)")
    args = parser.parse_args(argv)

    if not subprocess.run(["bun", "--version"], capture_output=True).returncode == 0:
        die("bun not on PATH (both validators run under bun)")
    source = args.source_repo.expanduser().resolve()
    original = source / ORIGINAL_REL
    rebuilt = ARENA_ROOT / REBUILT_REL
    if not original.is_file():
        die(f"original validator missing: {original}")
    if not rebuilt.is_file():
        die(f"rebuilt validator missing: {rebuilt}")

    shas = git(source, "rev-list", "-n", str(args.commits), "HEAD").split()
    if not shas:
        die(f"no commits enumerated in {source.name}")

    mismatches = []
    matched = 0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        empty = tmp / "no-changed-paths"
        empty.write_text("", encoding="utf-8")
        msg = tmp / "COMMIT_MSG"
        for sha in shas:
            msg.write_text(git(source, "log", "-1", "--format=%B", sha), encoding="utf-8")
            orig_rc, orig_err = run_validator(original, msg, empty)
            rebuilt_rc, _ = run_validator(rebuilt, msg, empty)
            if orig_rc == rebuilt_rc:
                matched += 1
            else:
                mismatches.append({
                    "sha": sha,
                    "subject": git(source, "log", "-1", "--format=%s", sha).strip(),
                    "original_exit": orig_rc,
                    "rebuilt_exit": rebuilt_rc,
                    "original_stderr": [l for l in orig_err.splitlines() if l.strip()],
                })

    receipt = {
        "kind": "molecular-corpus-parity",
        "utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "corpus": {
            "repo_name": source.name,  # name only: no absolute paths in output
            "head": shas[0],
            "commits": len(shas),
            "mode": "message-only (empty --changed-paths-file)",
        },
        "matched": matched,
        "mismatched": len(mismatches),
        "mismatches": mismatches,
    }
    text = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"parity: {matched}/{len(shas)} matched — receipt written to {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
