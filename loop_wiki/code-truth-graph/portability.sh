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
PYTHONPATH="$RELOCATED/src" python3 -m code_truth_graph.verify_artifacts \
  --output "$TMP/output" >/dev/null || exit 2
python3 - "$TMP/output/ctg-route-result.json" <<'PY'
import json
import sys
from pathlib import Path

result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert result["schema_version"] == "ctg-route-result@1.0.0"
assert result["overall"]["exit"] == 0
assert result["actual_runner"]["repo_commit"] == "UNVERIFIED_RELOCATED"
assert result["actual_runner"]["repo_tree"] == "UNVERIFIED_RELOCATED"
assert all("ctg-portability" not in item["artifact_ref"] for item in result["artifacts"])
PY

SUBJECT="$TMP/local-subject"
mkdir -p "$SUBJECT"
python3 - "$SUBJECT/manifest.json" <<'PY'
import json
import sys
from pathlib import Path

Path(sys.argv[1]).write_text(
    json.dumps(
        {
            "slice_id": "relocated-local-fixture",
            "title": "Relocated generic local graph",
            "snapshot": {"sha": "FIXTURE", "generated_at": "2026-08-09T00:00:00Z"},
            "scope": {"mode": "demo", "synthetic": True, "repo": "fixture/relocated"},
            "manual_static": {"nodes": [], "edges": []},
            "static": {},
            "lsp": {},
            "sandbox": {},
            "production": {},
            "sessions": [],
            "critical_path": {},
            "invariants": [],
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
PY
git -C "$SUBJECT" init -q || exit 64
git -C "$SUBJECT" config user.name ctg-portability
git -C "$SUBJECT" config user.email ctg-portability@example.invalid
git -C "$SUBJECT" add manifest.json
git -C "$SUBJECT" commit -qm 'fixture: pin relocated local manifest' || exit 64
sh "$RELOCATED/local-trigger.sh" \
  "$SUBJECT/manifest.json" "$SUBJECT/output" >/dev/null || exit $?
python3 - "$SUBJECT/output/ctg-local-build-receipt.json" <<'PY'
import json
import sys
from pathlib import Path

receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert receipt["overall"] == {"state": "PASSED"}, receipt
assert receipt["runner"]["repo_commit"] == "UNVERIFIED_RELOCATED", receipt
assert receipt["runner"]["repo_tree"] == "UNVERIFIED_RELOCATED", receipt
assert receipt["runner"]["dirty_before_run"] is None, receipt
assert receipt["subject"]["dirty_before_run"] is False, receipt
PY
