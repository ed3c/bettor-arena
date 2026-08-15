#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/resourcegc.py" check --root "$ROOT"
"$PYTHON" "$ROOT/scripts/resourcegc.py" selftest --root "$ROOT"
"$PYTHON" "$ROOT/scripts/control_resourcegc.py" --root "$ROOT" >/dev/null
echo "loopx-resource-gc physical control PASS: 4 controls on real trees and rebuilds"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

"$PYTHON" "$ROOT/scripts/resourcegc.py" plan --root "$ROOT" --output "$TMP/plan.json" >/dev/null
"$PYTHON" "$ROOT/scripts/resourcegc.py" run --root "$ROOT" --apply --output "$TMP/run.json" >/dev/null
"$PYTHON" - "$TMP/plan.json" "$TMP/run.json" "$TMP/receipt.json" <<'PY'
import json, sys
from pathlib import Path
plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
run = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
if plan["receipt"]["state"] != "DRY_RUN" or plan["receipt"]["removed"]:
    raise SystemExit("the plan subcommand removed something")
if run["receipt"]["state"] != "CLEAN":
    raise SystemExit(f"the applied run reported {run['receipt']['state']}")
kept = {entry["resource_id"] for entry in run["receipt"]["kept"]}
for required in ("ledger-seg-0001", "human-admit-0007", "wal-0003",
                 "blocked-conflict-12", "graph-divergent", "lsp-unprovable"):
    if required not in kept:
        raise SystemExit(f"{required} was not kept")
if len(run["receipt"]["tombstones"]) != len(run["receipt"]["removed"]):
    raise SystemExit("a removal left no tombstone")
Path(sys.argv[3]).write_text(
    json.dumps(run["receipt"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(
    f"loopx-resource-gc port PASS: {len(run['state_trace'])} states, "
    f"{len(run['receipt']['removed'])} removed with tombstones, "
    f"{len(kept)} kept including divergent and unprovable projections"
)
PY
"$PYTHON" "$ROOT/scripts/resourcegc.py" verify-receipt --receipt "$TMP/receipt.json"

"$PYTHON" -m py_compile \
  "$ROOT/scripts/rgc_common.py" \
  "$ROOT/scripts/rgc_rebuild.py" \
  "$ROOT/scripts/rgc_plan.py" \
  "$ROOT/scripts/rgc_execute.py" \
  "$ROOT/scripts/rgc_pipeline.py" \
  "$ROOT/scripts/rgc_fixtures.py" \
  "$ROOT/scripts/rgc_contract.py" \
  "$ROOT/scripts/rgc_selftest.py" \
  "$ROOT/scripts/resourcegc.py" \
  "$ROOT/scripts/control_resourcegc.py" \
  "$ROOT/scripts/probe_controls.py"

"$PYTHON" - "$ROOT" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no LoopX Resource GC JSON contracts or fixtures found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-resource-gc JSON PASS: {len(paths)} files")
PY
