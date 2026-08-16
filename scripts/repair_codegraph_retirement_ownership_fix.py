#!/usr/bin/env python3
import json
from pathlib import Path

# scripts/gates/** is already owned by arena-core; do not double-own the checker.
path = Path('.arena/modules/knowledge-providers/module.json')
value = json.loads(path.read_text(encoding='utf-8'))
target = 'scripts/gates/check_code_graph_rag_retirement.py'
for paths in (value['roots'], value['components']['proof']['paths']):
    while target in paths:
        paths.remove(target)
path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# The Context Capsule is generated from this explicit source list. Removing the
# active evaluator participant must remove its exact path before regeneration.
path = Path('.arena/contexts/knowledge-providers.json')
value = json.loads(path.read_text(encoding='utf-8'))
retired = 'docs/knowledge-providers/evals/participants/code-graph-rag.json'
value['common'] = [item for item in value['common'] if item != retired]
path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
