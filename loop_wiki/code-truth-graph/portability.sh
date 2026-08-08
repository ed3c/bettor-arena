#!/bin/sh
set -u

HERE=$(cd "$(dirname "$0")" && pwd -P) || exit 64
TMP=$(mktemp -d "${TMPDIR:-/tmp}/ctg-portability.XXXXXX") || exit 64
trap 'rm -rf "$TMP"' EXIT HUP INT TERM

RELOCATED="$TMP/relocated/at/a/different/depth/code-truth-graph"
mkdir -p "$(dirname "$RELOCATED")"
cp -R "$HERE" "$RELOCATED"

PACKET=$(PYTHONPATH="$RELOCATED/src" python3 -m code_truth_graph.fixture --out "$TMP/bundle") || exit 64
sh "$RELOCATED/run.sh" --packet "$PACKET" --output "$TMP/output" >/dev/null || exit $?
python3 - "$TMP/output/ctg-route-result.json" <<'PY'
import json
import sys
from pathlib import Path

result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert result["schema_version"] == "ctg-route-result@1.0.0"
assert result["overall"]["exit"] == 0
assert all("ctg-portability" not in item["artifact_ref"] for item in result["artifacts"])
PY
