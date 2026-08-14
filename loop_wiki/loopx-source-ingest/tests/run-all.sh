#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON=${PYTHON:-python3}

"$PYTHON" "$ROOT/scripts/ingest.py" check --root "$ROOT"
"$PYTHON" "$ROOT/scripts/ingest.py" selftest --root "$ROOT"
"$PYTHON" "$ROOT/scripts/control_ingest.py" >/dev/null
echo "loopx-source-ingest physical control PASS: 5 controls on real artifacts"

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

"$PYTHON" "$ROOT/scripts/ingest.py" ingest --root "$ROOT" --output "$TMP/result.json" >/dev/null
"$PYTHON" - "$TMP/result.json" "$TMP/manifest.json" <<'PY'
import json, sys
from pathlib import Path
result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
manifest = result["manifest"]
if result["state_trace"][-1] != "READY_FOR_KNOWLEDGE_COMPILATION":
    raise SystemExit(f"ingest ended at {result['state_trace'][-1]!r}")
if manifest["authority"] != "EVIDENCE_INVENTORY_ONLY":
    raise SystemExit("the manifest claimed more than an inventory")
for record in manifest["evidence"]:
    if record["locator_origin"] != "READ_FROM_ARTIFACT":
        raise SystemExit(f"{record['evidence_id']} carries a {record['locator_origin']} locator")
blocked = [gap for gap in manifest["gaps"] if gap["state"] == "BLOCKED_BY_RIGHTS"]
if not blocked:
    raise SystemExit("the rights-blocked source was omitted rather than recorded")
if not manifest["injection_findings"]:
    raise SystemExit("the injection string was not recorded as a finding")
Path(sys.argv[2]).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(
    f"loopx-source-ingest port PASS: {len(result['state_trace'])} states, "
    f"{manifest['evidence_count']} evidence all READ_FROM_ARTIFACT, "
    f"{len(manifest['gaps'])} gap(s) recorded"
)
PY
"$PYTHON" "$ROOT/scripts/ingest.py" verify-manifest --manifest "$TMP/manifest.json"

"$PYTHON" -m py_compile \
  "$ROOT/scripts/si_common.py" \
  "$ROOT/scripts/si_capture.py" \
  "$ROOT/scripts/si_locator.py" \
  "$ROOT/scripts/si_injection.py" \
  "$ROOT/scripts/si_manifest.py" \
  "$ROOT/scripts/si_pipeline.py" \
  "$ROOT/scripts/si_contract.py" \
  "$ROOT/scripts/si_selftest.py" \
  "$ROOT/scripts/ingest.py" \
  "$ROOT/scripts/control_ingest.py"

"$PYTHON" - "$ROOT" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

root = Path(sys.argv[1])
paths = sorted(root.rglob("*.json"))
if not paths:
    raise SystemExit("no source-ingest JSON contracts found")
for path in paths:
    json.loads(path.read_text(encoding="utf-8"))
print(f"loopx-source-ingest JSON PASS: {len(paths)} files")
PY
