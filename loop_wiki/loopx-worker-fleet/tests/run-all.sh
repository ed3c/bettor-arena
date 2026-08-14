#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/fleet.py" check --root "$ROOT"
"$PYTHON" "$ROOT/scripts/fleet.py" selftest --root "$ROOT"
"$PYTHON" "$ROOT/scripts/control_fleet.py" --root "$ROOT" >/dev/null
echo "loopx-worker-fleet physical control PASS: 5 controls on real processes and trees"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

"$PYTHON" "$ROOT/scripts/fleet.py" cycle --root "$ROOT" --output "$TMP/cycle.json" >/dev/null
"$PYTHON" - "$TMP/cycle.json" <<'PY'
import json, sys
from pathlib import Path
cycle = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if cycle["state_trace"][-1] != "GC_ORPHAN_RECOVERY":
    raise SystemExit(f"cycle ended at {cycle['state_trace'][-1]!r}")
if cycle["lease_refusals"]:
    raise SystemExit(f"the clean cycle refused leases: {cycle['lease_refusals']}")
if cycle["gc"]["default_is_destructive"] is not False:
    raise SystemExit("a scheduled GC run reported itself destructive")
print(
    f"loopx-worker-fleet port PASS: {len(cycle['state_trace'])} states, "
    f"{len(cycle['admitted'])} leases admitted, GC non-destructive by default"
)
PY

# The GC through its real port, on a real tree, with nothing admitted: it must
# remove nothing even with --apply, because admission is per workspace.
mkdir -p "$TMP/ws/leaseless" "$TMP/ws/keepme"
: > "$TMP/ws/leaseless/.worker-scaffold"
: > "$TMP/ws/keepme/.worker-dirty"
"$PYTHON" "$ROOT/scripts/fleet.py" gc --root "$ROOT" --workspaces "$TMP/ws" \
  --apply --output "$TMP/gc.json" >/dev/null
test -d "$TMP/ws/leaseless" || {
  echo "GC removed a workspace nobody admitted" >&2; exit 2; }
test -d "$TMP/ws/keepme" || {
  echo "GC removed a dirty workspace" >&2; exit 2; }
echo "loopx-worker-fleet GC PASS: --apply with no admission removed nothing"

"$PYTHON" -m py_compile \
  "$ROOT/scripts/wf_common.py" \
  "$ROOT/scripts/wf_lease.py" \
  "$ROOT/scripts/wf_queue.py" \
  "$ROOT/scripts/wf_adapter.py" \
  "$ROOT/scripts/wf_cleanup.py" \
  "$ROOT/scripts/wf_receipt.py" \
  "$ROOT/scripts/wf_pipeline.py" \
  "$ROOT/scripts/wf_contract.py" \
  "$ROOT/scripts/wf_selftest.py" \
  "$ROOT/scripts/fleet.py" \
  "$ROOT/scripts/control_fleet.py" \
  "$ROOT/scripts/probe_controls.py"

"$PYTHON" - "$ROOT" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no LoopX Worker Fleet JSON contracts or fixtures found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-worker-fleet JSON PASS: {len(paths)} files")
PY
