#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
MODULE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}
BENCH="$MODULE/scripts/loopxbench.py"

"$PYTHON" "$BENCH" check --root "$ROOT"
"$PYTHON" "$BENCH" selftest --root "$ROOT"
"$PYTHON" "$MODULE/scripts/control_loopxbench.py"

TMP=$(mktemp -d)
cleanup() { chmod -R u+w "$TMP" 2>/dev/null || true; find "$TMP" -mindepth 1 -delete 2>/dev/null || true; rmdir "$TMP" 2>/dev/null || true; }
trap cleanup EXIT

# CI runs `synthetic`, never `measure`. A duration from a shared runner whose
# neighbours nobody can see is a number about that runner at that moment, and
# publishing it as a repository fact is what this module exists to stop.
"$PYTHON" "$BENCH" synthetic --root "$ROOT" --output "$TMP/synthetic.json" >/dev/null
"$PYTHON" "$BENCH" synthetic --root "$ROOT" --output "$TMP/synthetic-again.json" >/dev/null
cmp "$TMP/synthetic.json" "$TMP/synthetic-again.json" || {
  echo "the synthetic run is not deterministic" >&2; exit 2; }
echo "loopx-benchmark determinism PASS: two synthetic runs are byte-identical"

set +e
"$PYTHON" "$BENCH" promote --claim rss-under-30mb >/dev/null 2>&1
rc=$?
set -e
test "$rc" = "64" || { echo "the port answered 'promote' with exit $rc, expected 64" >&2; exit 2; }
echo "loopx-benchmark port PASS: there is no promote route; unusable input exits 64"

"$PYTHON" "$BENCH" verdict --root "$ROOT" --reports "$TMP/synthetic.json" \
  --output "$TMP/verdict.json" >/dev/null 2>&1

"$PYTHON" - "$TMP/synthetic.json" "$TMP/verdict.json" "$ROOT" <<'PY'
import json, sys
from pathlib import Path

report, verdict = (json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:3])

if report["locale"] != "SYNTHETIC":
    raise SystemExit(f"CI produced a {report['locale']} report; it must not publish a timing number")
if report["numbers_are_claims"] is not False:
    raise SystemExit("a report described its numbers as claims")
if report["failure_count"] != 1:
    raise SystemExit("the synthetic run retained no failure, so it never exercises that path")
if report["trial_count"] != len(report["trials"]):
    raise SystemExit("the trial count and the retained trials disagree")
if report["success_rate"] >= 1.0:
    raise SystemExit("a run with a retained failure reported a perfect success rate")

if verdict["verdict"] != "CLAIM_UNVERIFIED":
    raise SystemExit(f"a synthetic report produced {verdict['verdict']}")
if verdict["promotable_by_gate"] is not False or verdict["promotion_owner"] != "HUMAN_ADMIT":
    raise SystemExit("claim promotion ownership drifted out of the verdict")
if not any("synthetic" in note for note in verdict["notes"]):
    raise SystemExit("the synthetic exclusion was not stated in the verdict")

# The checked-in receipts must say the same thing as the code that made them.
receipts = sorted((Path(sys.argv[3]) / "data/benchmarks").glob("*.json"))
if not receipts:
    raise SystemExit("no benchmark receipts are checked in")
for path in receipts:
    entry = json.loads(path.read_text(encoding="utf-8"))
    if entry.get("promotion_owner") not in (None, "HUMAN_ADMIT"):
        raise SystemExit(f"{path.name} moved claim promotion off Human Admit")
    if entry.get("numbers_are_claims") not in (None, False):
        raise SystemExit(f"{path.name} described its numbers as claims")

print(
    f"loopx-benchmark documents PASS: {report['trial_count']} trials "
    f"({report['failure_count']} retained failure), verdict {verdict['verdict']}, "
    f"{len(receipts)} receipt(s)"
)
PY

"$PYTHON" -m py_compile \
  "$MODULE/scripts/bm_common.py" \
  "$MODULE/scripts/bm_run.py" \
  "$MODULE/scripts/bm_report.py" \
  "$MODULE/scripts/bm_claim.py" \
  "$MODULE/scripts/bm_contract.py" \
  "$MODULE/scripts/bm_selftest.py" \
  "$MODULE/scripts/loopxbench.py" \
  "$MODULE/scripts/control_loopxbench.py"

"$PYTHON" - "$MODULE" <<'PY'
import json, sys
from pathlib import Path
module = Path(sys.argv[1])
paths = sorted((module / "contracts").glob("*.json"))
if not paths:
    raise SystemExit("no benchmark JSON contracts found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-benchmark JSON PASS: {len(paths)} files")
PY
