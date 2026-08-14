#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/skillevo.py" check --root "$ROOT"
"$PYTHON" "$ROOT/scripts/skillevo.py" selftest --root "$ROOT"
"$PYTHON" "$ROOT/scripts/control_skillevo.py" --root "$ROOT" >/dev/null
echo "loopx-skill-evolution physical control PASS: 5 isolation controls on real bytes"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

"$PYTHON" "$ROOT/scripts/skillevo.py" evaluate --root "$ROOT" --output "$TMP/eval.json" >/dev/null
"$PYTHON" "$ROOT/scripts/skillevo.py" receipt --root "$ROOT" \
  --evidence-kind FIXTURE_ONLY --at 2026-08-15T12:00:00Z --output "$TMP/fixture.json" >/dev/null
"$PYTHON" "$ROOT/scripts/skillevo.py" receipt --root "$ROOT" \
  --evidence-kind LIVE_EXERCISED --at 2026-08-15T12:00:00Z --output "$TMP/live.json" >/dev/null
"$PYTHON" "$ROOT/scripts/skillevo.py" verify-receipt --receipt "$TMP/fixture.json"
"$PYTHON" "$ROOT/scripts/skillevo.py" verify-receipt --receipt "$TMP/live.json"

"$PYTHON" - "$TMP/eval.json" "$TMP/fixture.json" "$TMP/live.json" <<'PY'
import json, sys
from pathlib import Path
ev = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
fixture = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
live = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
if ev["state_trace"][-1] != "DECIDED":
    raise SystemExit(f"evaluation ended at {ev['state_trace'][-1]!r}")
trace = ev["state_trace"]
if trace.index("SEALED_HOLDOUT") < trace.index("MUTATION_TRAP_EVAL"):
    raise SystemExit("the seal was opened before the mutation stage")
if ev["decision"]["judge_authority"] != "ADVISORY_ONLY":
    raise SystemExit("the decision does not declare judges advisory")
# The pair that matters: the same decision, two evidence kinds, two capability
# states. Read from separate emitted documents rather than from one object.
if fixture["capability_state"] != "NOT_UNLOCKED":
    raise SystemExit("fixture-only evidence unlocked a capability")
if live["capability_state"] != "UNLOCKED_PENDING_ADMIT":
    raise SystemExit("live evidence did not reach pending-admit")
for receipt, label in ((fixture, "fixture"), (live, "live")):
    if receipt["canonical_mutation"] != "NONE_PERFORMED":
        raise SystemExit(f"{label} receipt recorded a canonical mutation")
    if receipt["consumer_binding_update"] != "SEPARATE_LEAF_NOT_PERFORMED":
        raise SystemExit(f"{label} receipt recorded a consumer binding update")
print(
    f"loopx-skill-evolution port PASS: {len(trace)} states, {ev['decision']['outcome']}, "
    "fixture NOT_UNLOCKED and live UNLOCKED_PENDING_ADMIT from one decision"
)
PY

"$PYTHON" -m py_compile \
  "$ROOT/scripts/se_common.py" \
  "$ROOT/scripts/se_experiment.py" \
  "$ROOT/scripts/se_cases.py" \
  "$ROOT/scripts/se_decision.py" \
  "$ROOT/scripts/se_release.py" \
  "$ROOT/scripts/se_pipeline.py" \
  "$ROOT/scripts/se_contract.py" \
  "$ROOT/scripts/se_selftest.py" \
  "$ROOT/scripts/skillevo.py" \
  "$ROOT/scripts/control_skillevo.py" \
  "$ROOT/scripts/probe_controls.py"

"$PYTHON" - "$ROOT" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no LoopX Skill Evolution JSON contracts or fixtures found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-skill-evolution JSON PASS: {len(paths)} files")
PY
