#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
PYTHON=${PYTHON:-python3}
API="$ROOT/loop_wiki/harness-console/service"

"$PYTHON" "$API/hitlapi.py" check --root "$ROOT"
"$PYTHON" "$API/hitlapi.py" selftest --root "$ROOT"
"$PYTHON" "$API/control_hitl.py"

TMP=$(mktemp -d)
cleanup() { chmod -R u+w "$TMP" 2>/dev/null || true; find "$TMP" -mindepth 1 -delete 2>/dev/null || true; rmdir "$TMP" 2>/dev/null || true; }
trap cleanup EXIT

"$PYTHON" - "$API" "$TMP" <<'PY'
import json, sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from hitl_selftest import EVENTS

Path(sys.argv[2], "events.json").write_text(json.dumps(EVENTS), encoding="utf-8")
PY

"$PYTHON" "$API/hitlapi.py" project --events "$TMP/events.json" \
  --head ledger-head-0f21ac --output "$TMP/projection.json" >/dev/null
"$PYTHON" "$API/hitlapi.py" views --projection "$TMP/projection.json" \
  --output "$TMP/views.json" >/dev/null

# An unknown subcommand is unusable input, not a refusal. 64, never 2.
set +e
"$PYTHON" "$API/hitlapi.py" merge --pr 1 >/dev/null 2>&1
rc=$?
set -e
test "$rc" = "64" || { echo "the port answered 'merge' with exit $rc, expected 64" >&2; exit 2; }
echo "harness-console port PASS: there is no merge route; unusable input exits 64"

"$PYTHON" - "$TMP/projection.json" "$TMP/views.json" <<'PY'
import json, sys
from pathlib import Path

projection, views = (json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:3])

if projection["authority"] != "READ_ONLY_PROJECTION":
    raise SystemExit(f"the projection claimed {projection['authority']}")
if projection["completeness"] != "COMPLETE" or projection["missing_sequences"]:
    raise SystemExit("the reference event list did not reduce to a COMPLETE projection")
if views["render_state"] != "NOT_IMPLEMENTED":
    raise SystemExit(f"the view layer claimed render_state {views['render_state']}")
if views["view_count"] != 8:
    raise SystemExit(f"{views['view_count']} views, expected 8")

graph = views["views"]["thread_task_graph"]
if graph["completed_with_exception"] != 1 or graph["completed_clean"] != 0:
    raise SystemExit(
        f"COMPLETED_WITH_EXCEPTION was folded into completion: {graph['counts_by_state']}"
    )
if views["views"]["gate_evidence_inspector"]["may_write_verdict"]:
    raise SystemExit("a view claimed authority over a gate verdict")

dialog = views["views"]["hitl_dialog"]
for refused in ("MERGE", "ROLLBACK_PRODUCTION", "UNSCOPED_FORCE_SKIP", "MARK_GATE_PASS"):
    if refused not in dialog["refused_actions"]:
        raise SystemExit(f"{refused} left the refused-action list")
    if refused in dialog["available_actions"]:
        raise SystemExit(f"{refused} appeared in the dialog")
if not dialog["requires_signature"]:
    raise SystemExit("the dialog stopped requiring a signature")

for name, view in views["views"].items():
    if name == "hitl_dialog":
        continue
    for field in ("shown", "total", "truncated", "limit"):
        if field not in view:
            raise SystemExit(f"view {name} is missing {field}; it is unbounded")

print(
    f"harness-console documents PASS: {views['view_count']} bounded views, "
    f"{projection['event_count']} events, {projection['completeness']}, "
    f"render {views['render_state']}"
)
PY

"$PYTHON" -m py_compile \
  "$ROOT/loop_wiki/harness-console/contracts/hc_vocab.py" \
  "$ROOT/loop_wiki/harness-console/contracts/hc_contract.py" \
  "$ROOT/loop_wiki/harness-console/app/hc_views.py" \
  "$API/hitl_reducer.py" \
  "$API/hitl_request.py" \
  "$API/hitl_selftest.py" \
  "$API/hitlapi.py" \
  "$API/control_hitl.py"

"$PYTHON" - "$ROOT" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
paths = sorted((root / "loop_wiki/harness-console/contracts/contracts").glob("*.json"))
if not paths:
    raise SystemExit("no harness-console JSON contracts found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"harness-console JSON PASS: {len(paths)} files")
PY
