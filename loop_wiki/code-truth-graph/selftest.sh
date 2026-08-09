#!/bin/sh
set -u

HERE=$(cd "$(dirname "$0")" && pwd -P) || exit 64
TMP=$(mktemp -d "${TMPDIR:-/tmp}/ctg-selftest.XXXXXX") || exit 64
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

PACKET=$(PYTHONPATH="$HERE/src" python3 -m code_truth_graph.fixture --out "$TMP/bundle") || exit 64
sh "$HERE/trigger.sh" "$PACKET" "$TMP/good" >/dev/null || exit 1
PYTHONPATH="$HERE/src" python3 -m code_truth_graph.verify_artifacts --output "$TMP/good" >/dev/null || {
  echo "FAIL: good CTG output did not verify" >&2
  exit 2
}

cp -R "$TMP/good" "$TMP/hollow"
python3 - "$TMP/hollow/ctg-route-result.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
value = json.loads(path.read_text(encoding="utf-8"))
del value["human_gate"]
path.write_text(json.dumps(value) + "\n", encoding="utf-8")
PY
if PYTHONPATH="$HERE/src" python3 -m code_truth_graph.verify_artifacts --output "$TMP/hollow" >/dev/null 2>&1; then
  echo "FAIL: hollow route-result unexpectedly verified" >&2
  exit 2
fi

echo "PASS: good CTG output passed and hollow route-result failed"
