#!/bin/sh
# Independent behavior control for the public portable Skill execution port.
set -u

ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel) || exit 64
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)-skill-execution-$$
OUT="$ROOT/proof_workflow/data/$RUN_ID"
mkdir -p "$OUT" || exit 64

python3 "$ROOT/.agents/skills/harness-wiki/tests/run-execution-selftest.py" \
  --loopctl "$ROOT/loopctl/loopctl.sh" >"$OUT/stdout.txt" 2>"$OUT/stderr.txt"
RC=$?
STATUS=FAIL
[ "$RC" -eq 0 ] && STATUS=PASS
python3 - "$OUT/skill-execution-control.json" "$STATUS" "$RC" <<'PY'
import datetime as dt
import json
import sys
from pathlib import Path

Path(sys.argv[1]).write_text(json.dumps({
    "schema": "bettor-arena/skill-execution-control/v1",
    "status": sys.argv[2],
    "exit_code": int(sys.argv[3]),
    "observed_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    "axes": [
        "positive", "network-fail-closed", "assertion-digest", "skill-digest",
        "tree-subject", "exit-code", "timeout", "diff-boundary",
        "unsupported-assertion", "raw-shell", "append-only-receipt"
    ]
}, indent=2) + "\n", encoding="utf-8")
PY
cat "$OUT/stdout.txt"
cat "$OUT/stderr.txt" >&2
[ "$RC" -eq 0 ] && exit 0
exit 2
