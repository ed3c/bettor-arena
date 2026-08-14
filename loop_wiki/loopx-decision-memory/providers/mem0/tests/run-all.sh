#!/bin/sh
set -eu

MEM0=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$MEM0/mem0.py" check --root "$MEM0"
"$PYTHON" "$MEM0/mem0.py" selftest --root "$MEM0"
"$PYTHON" "$MEM0/control_mem0.py" >/dev/null
echo "mem0-projection physical control PASS: 4 controls on a real index file and store"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

"$PYTHON" "$MEM0/mem0.py" project --root "$MEM0" --output "$TMP/projection.json" >/dev/null
"$PYTHON" "$MEM0/mem0.py" writeback --root "$MEM0" --output "$TMP/writeback.json" >/dev/null
"$PYTHON" "$MEM0/mem0.py" rebuild --root "$MEM0" --output "$TMP/rebuild.json" >/dev/null

# The unavailable path must exit 70, not 0 and not 2. Checked through the real
# port, because that exit code is the only thing a caller sees.
set +e
"$PYTHON" "$MEM0/mem0.py" query --root "$MEM0" --availability UNAVAILABLE \
  --output "$TMP/down.json" >/dev/null 2>&1
rc=$?
set -e
test "$rc" = "70" || { echo "an unavailable provider exited $rc, expected 70" >&2; exit 2; }
echo "mem0-projection port PASS: unavailable provider exits 70, not 0 and not 2"

"$PYTHON" - "$TMP/projection.json" "$TMP/writeback.json" "$TMP/rebuild.json" "$TMP/down.json" <<'PY'
import json, sys
from pathlib import Path
load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
projection, writeback, rebuild, down = (load(p) for p in sys.argv[1:5])
if projection["canonical"] is not False or projection["authority"] != "PROJECTION_ONLY":
    raise SystemExit("the projection claimed authority")
if writeback["written"] is not False or writeback["state"] != "PROPOSED":
    raise SystemExit("the writeback claimed to have written")
if not rebuild["equivalent"] or rebuild["comparison"] != "RELATION_EQUIVALENT":
    raise SystemExit(f"rebuild reported {rebuild}")
if down["state"] != "PROVIDER_UNAVAILABLE" or down["hits"]:
    raise SystemExit("an unavailable provider returned an answer")
print(
    f"mem0-projection documents PASS: projection PROJECTION_ONLY, writeback PROPOSED, "
    f"rebuild {rebuild['comparison']}"
)
PY

"$PYTHON" -m py_compile \
  "$MEM0/mem0_identity.py" \
  "$MEM0/mem0_projection.py" \
  "$MEM0/mem0_authority.py" \
  "$MEM0/mem0_lifecycle.py" \
  "$MEM0/mem0_contract.py" \
  "$MEM0/mem0_selftest.py" \
  "$MEM0/mem0.py" \
  "$MEM0/control_mem0.py"

"$PYTHON" - "$MEM0" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no Mem0 JSON contracts found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"mem0-projection JSON PASS: {len(paths)} files")
PY
