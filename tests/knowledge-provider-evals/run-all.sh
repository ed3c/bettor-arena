#!/bin/sh
set -eu

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT HUP INT TERM

python3 scripts/check_knowledge_provider_module.py
python3 scripts/check_knowledge_provider_module.py --selftest

python3 -m compileall -q   scripts/check_knowledge_provider_module.py   scripts/evaluate_knowledge_providers.py   scripts/knowledge_provider_eval_common.py   scripts/knowledge_provider_eval_contracts.py   scripts/knowledge_provider_eval_registry.py   scripts/knowledge_provider_eval_cases.py   scripts/knowledge_provider_eval_packet.py   scripts/knowledge_provider_eval_metrics.py   scripts/knowledge_provider_eval_engine.py   scripts/knowledge_provider_eval_selftest.py

python3 scripts/evaluate_knowledge_providers.py   --output "$TMP_DIR/report.json"

python3 - "$TMP_DIR/report.json" <<'PY'
import gzip
import json
import sys
from pathlib import Path

report_path = Path(sys.argv[1])
report = json.loads(report_path.read_text(encoding="utf-8"))
assert report["schema_version"] == "knowledge-provider-eval-report/v1"
assert report["status"] == "PASS"
assert report["evidence_scope"] == "FIXTURE_ONLY"
assert report["pair_coverage"] == {
    "complete": True,
    "expected": 7,
    "missing": [],
    "observed": 7,
    "unexpected": [],
}
assert report["admission"]["automatic_admission"] is False
assert report["admission"]["winner"] is None

root = Path("docs/knowledge-providers/evals")
for path in sorted(root.rglob("*.json")):
    json.loads(path.read_text(encoding="utf-8"))
for path in sorted(root.rglob("*.json.gz")):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        value = json.load(handle)
    assert isinstance(value, list) and value

print("knowledge-provider-eval artifact checks PASS")
PY
