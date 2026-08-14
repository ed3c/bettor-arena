#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/foldback.py" check --root "$ROOT"
"$PYTHON" "$ROOT/scripts/foldback.py" selftest --root "$ROOT"
"$PYTHON" "$ROOT/scripts/control_foldback.py" >/dev/null
echo "loopx-knowledge-foldback physical control PASS: 5 anchor controls on real files"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# The port must stop at the candidate bundle. Read from a separate process so
# the terminal state comes from the emitted document rather than from an object
# still held in the interpreter that produced it.
"$PYTHON" "$ROOT/scripts/foldback.py" fold-back --root "$ROOT" --output "$TMP/fold.json" >/dev/null
"$PYTHON" "$ROOT/scripts/foldback.py" admit --root "$ROOT" --output "$TMP/admit.json" >/dev/null
"$PYTHON" - "$TMP/fold.json" "$TMP/admit.json" "$TMP/receipt.json" <<'PY'
import json, sys
from pathlib import Path
fold = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
admitted = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
if fold["state_trace"][-1] != "CANDIDATE_FOLD_BACK_BUNDLE":
    raise SystemExit(f"fold-back ended at {fold['state_trace'][-1]!r}")
if fold["bundle"]["state"] != "CANDIDATE" or fold["bundle"]["admit_required"] is not True:
    raise SystemExit("fold-back emitted something other than a candidate awaiting admit")
if admitted["outcome"] != "APPENDED":
    raise SystemExit(f"admit reported {admitted['outcome']}, expected APPENDED")
rejected = [r for r in admitted["history"]["revisions"] if r["state"] == "REJECTED"]
if not rejected:
    raise SystemExit("the rejected patch is absent from the appended history")
Path(sys.argv[3]).write_text(
    json.dumps(admitted["receipt"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print(
    f"loopx-knowledge-foldback port PASS: {len(fold['state_trace'])} states, bundle "
    f"CANDIDATE, {len(admitted['appended_revision_ids'])} revisions appended, "
    f"{len(rejected)} rejection kept"
)
PY
"$PYTHON" "$ROOT/scripts/foldback.py" verify-receipt --receipt "$TMP/receipt.json"

# Rerunning admit against the same inputs must append nothing new. Run it as a
# separate process against the history the first run produced.
"$PYTHON" - "$ROOT" "$TMP/admit.json" <<'PY'
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]) / "scripts"))
from fb_pipeline import admit_bundle, fold_back
from fb_selftest import load_bundle_inputs

root = Path(sys.argv[1])
inputs = load_bundle_inputs(root)
first = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
folded = fold_back(inputs["change-delta"], inputs["cards"], inputs["patches"],
                   inputs["similarity"], inputs["revision-history"])
again = admit_bundle(folded["bundle"], first["history"], inputs["decisions"], inputs["cards"])
if again["outcome"] != "NOOP" or again["appended_revision_ids"]:
    raise SystemExit(f"a rerun appended {again['appended_revision_ids']}")
print("loopx-knowledge-foldback idempotence PASS: rerun is NOOP across processes")
PY

"$PYTHON" -m py_compile \
  "$ROOT/scripts/fb_common.py" \
  "$ROOT/scripts/fb_anchor.py" \
  "$ROOT/scripts/fb_delta.py" \
  "$ROOT/scripts/fb_patch.py" \
  "$ROOT/scripts/fb_history.py" \
  "$ROOT/scripts/fb_bundle.py" \
  "$ROOT/scripts/fb_pipeline.py" \
  "$ROOT/scripts/fb_contract.py" \
  "$ROOT/scripts/fb_selftest.py" \
  "$ROOT/scripts/foldback.py" \
  "$ROOT/scripts/control_foldback.py" \
  "$ROOT/scripts/probe_controls.py"

"$PYTHON" - "$ROOT" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no LoopX Knowledge Fold-back JSON contracts or fixtures found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-knowledge-foldback JSON PASS: {len(paths)} files")
PY
