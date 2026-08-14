#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/notesretrieval.py" check --root "$ROOT"
"$PYTHON" "$ROOT/scripts/notesretrieval.py" selftest --root "$ROOT"
"$PYTHON" "$ROOT/scripts/control_notesretrieval.py" >/dev/null
echo "loopx-notes-retrieval physical control PASS: 5 controls on a real index and tree"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

"$PYTHON" "$ROOT/scripts/notesretrieval.py" build --root "$ROOT" --output "$TMP/built.json" >/dev/null
"$PYTHON" "$ROOT/scripts/notesretrieval.py" query --root "$ROOT" --output "$TMP/hit.json" >/dev/null

# A missing provider must exit 70, and the macro read must still work.
set +e
"$PYTHON" "$ROOT/scripts/notesretrieval.py" query --root "$ROOT" --no-provider \
  --output "$TMP/absent.json" >/dev/null 2>&1
rc=$?
set -e
test "$rc" = "70" || { echo "an absent provider exited $rc, expected 70" >&2; exit 2; }
echo "loopx-notes-retrieval port PASS: absent provider exits 70, not 0 and not 2"

"$PYTHON" - "$TMP/built.json" "$TMP/hit.json" "$TMP/absent.json" <<'PY'
import json, sys
from pathlib import Path
load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
built, hit, absent = (load(p) for p in sys.argv[1:4])
if built["openwiki"]["admissible_as_evidence"] is not False:
    raise SystemExit("the OpenWiki projection claimed to be admissible as evidence")
if hit["micro"]["state"] != "HIT" or hit["micro"]["absence_proof"] != "NONE":
    raise SystemExit(f"the query produced {hit['micro']['state']}")
if hit["claim"]["is_fact"] or hit["claim"]["is_gate_verdict"]:
    raise SystemExit("a hit was handed over as a fact or a gate verdict")
for entry in hit["readbacks"]:
    if entry["state"] != "CONFIRMED":
        raise SystemExit(f"readback reported {entry['state']}")
if absent["micro"]["state"] != "PROVIDER_ABSENT":
    raise SystemExit(f"an absent provider produced {absent['micro']['state']}")
if absent["macro"]["page_count"] != built["openwiki"]["page_count"]:
    raise SystemExit("the macro read needed a vector provider")
print(
    f"loopx-notes-retrieval documents PASS: {built['openwiki']['page_count']} wiki page(s) "
    f"with no provider, hit is a {hit['claim']['admitted_as']}, readback CONFIRMED"
)
PY

"$PYTHON" -m py_compile \
  "$ROOT/scripts/nr_common.py" \
  "$ROOT/scripts/nr_index.py" \
  "$ROOT/scripts/nr_openwiki.py" \
  "$ROOT/scripts/nr_query.py" \
  "$ROOT/scripts/nr_pipeline.py" \
  "$ROOT/scripts/nr_contract.py" \
  "$ROOT/scripts/nr_selftest.py" \
  "$ROOT/scripts/notesretrieval.py" \
  "$ROOT/scripts/control_notesretrieval.py"

"$PYTHON" - "$ROOT" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no notes-retrieval JSON contracts found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-notes-retrieval JSON PASS: {len(paths)} files")
PY
