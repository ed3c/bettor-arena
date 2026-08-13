#!/bin/sh
set -eu

python3 scripts/check_knowledge_provider_module.py
python3 scripts/check_knowledge_provider_module.py --selftest
python3 -m compileall -q scripts/check_knowledge_provider_module.py scripts/evaluate_knowledge_providers.py scripts/knowledge_provider_eval_common.py scripts/knowledge_provider_eval_registry.py scripts/knowledge_provider_eval_cases.py scripts/knowledge_provider_eval_packet.py scripts/knowledge_provider_eval_metrics.py scripts/knowledge_provider_eval_engine.py scripts/knowledge_provider_eval_selftest.py
python3 - <<'PY'
import json
from pathlib import Path
for path in sorted(Path("docs/knowledge-providers/evals").rglob("*.json")):
    json.loads(path.read_text(encoding="utf-8"))
print("knowledge-provider-eval JSON parse PASS")
PY
