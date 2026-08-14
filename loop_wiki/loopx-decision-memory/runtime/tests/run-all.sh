#!/bin/sh
set -eu

RUNTIME=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
MODULE=$(CDPATH= cd -- "$RUNTIME/.." && pwd)
PYTHON=${PYTHON:-python3}

# The contracts this runtime sits on are validated by their own port, not by a
# second copy here. A duplicate validator is a second thing to keep in step.
"$PYTHON" "$MODULE/scripts/memory.py" check
"$PYTHON" "$MODULE/scripts/memory.py" selftest

"$PYTHON" "$RUNTIME/memory_runtime.py" check
"$PYTHON" "$RUNTIME/memory_runtime.py" selftest
"$PYTHON" "$RUNTIME/control_memory_runtime.py" >/dev/null
echo "loopx-decision-memory-runtime physical control PASS: 4 controls on a real log file"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

"$PYTHON" "$RUNTIME/memory_runtime.py" admit --output "$TMP/admitted.json" >/dev/null
"$PYTHON" - "$TMP/admitted.json" "$TMP/log.json" <<'PY'
import json, sys
from pathlib import Path
result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if result["outcome"] != "APPENDED" or len(result["appended"]) != 1:
    raise SystemExit(f"admission produced {result['outcome']}")
event = result["log"][0]
if event["writer"] != "LOOPX_LEDGER_REDUCER":
    raise SystemExit(f"the event was written by {event['writer']}")
if event["state"] != "ACTIVE":
    raise SystemExit(f"the admitted event is {event['state']}")
Path(sys.argv[2]).write_text(json.dumps(result["log"]), encoding="utf-8")
print(
    f"loopx-decision-memory-runtime port PASS: {len(result['state_trace'])} states, "
    "reducer-written ACTIVE event"
)
PY

"$PYTHON" "$RUNTIME/memory_runtime.py" delete --log "$TMP/log.json" \
  --output "$TMP/deleted.json" >/dev/null
"$PYTHON" "$RUNTIME/memory_runtime.py" rebuild --log "$TMP/log.json" \
  --output "$TMP/projection.json" >/dev/null
"$PYTHON" - "$TMP/deleted.json" "$TMP/projection.json" "$TMP/log.json" <<'PY'
import json, sys
from pathlib import Path
deleted = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
projection = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
log = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
if deleted["residue"] or deleted["content_retrievable"]:
    raise SystemExit(f"content survived deletion: {deleted['residue']}")
if not deleted["history_preserved"] or len(deleted["log"]) <= len(log):
    raise SystemExit("deletion did not append a tombstone event")
if deleted["projection"]["entry_count"] != 0:
    raise SystemExit("a tombstoned memory survived into the projection")
if projection["canonical"] is not False:
    raise SystemExit("the projection claimed to be canonical")
if projection["entry_count"] != 1:
    raise SystemExit(f"the live projection has {projection['entry_count']} entries")
print(
    "loopx-decision-memory-runtime delete PASS: content unretrievable, "
    f"{len(deleted['log'])} events kept, projection empty"
)
PY

"$PYTHON" "$RUNTIME/memory_runtime.py" handoff --log "$TMP/log.json" --max-bytes 256 \
  --output "$TMP/tiny.json" >/dev/null
"$PYTHON" - "$TMP/tiny.json" <<'PY'
import json, sys
from pathlib import Path
handoff = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
capsule = handoff["capsule"]
if capsule["approx_bytes"] > capsule["max_bytes"]:
    raise SystemExit("the capsule exceeded its budget")
if capsule["dropped_for_budget"] and capsule["complete"]:
    raise SystemExit("a truncated capsule reported itself complete")
print(
    f"loopx-decision-memory-runtime capsule PASS: bounded at {capsule['max_bytes']}B, "
    f"{capsule['dropped_for_budget']} dropped and said so"
)
PY

"$PYTHON" -m py_compile \
  "$RUNTIME/dmr_event.py" \
  "$RUNTIME/dmr_authority.py" \
  "$RUNTIME/dmr_lifecycle.py" \
  "$RUNTIME/dmr_projection.py" \
  "$RUNTIME/dmr_pipeline.py" \
  "$RUNTIME/dmr_contract.py" \
  "$RUNTIME/dmr_selftest.py" \
  "$RUNTIME/memory_runtime.py" \
  "$RUNTIME/control_memory_runtime.py"

"$PYTHON" - "$RUNTIME" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no memory-runtime JSON contracts found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-decision-memory-runtime JSON PASS: {len(paths)} files")
PY
