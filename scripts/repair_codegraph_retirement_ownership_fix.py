#!/usr/bin/env python3
import json
from pathlib import Path

path = Path('.arena/modules/knowledge-providers/module.json')
value = json.loads(path.read_text(encoding='utf-8'))
target = 'scripts/gates/check_code_graph_rag_retirement.py'
for paths in (value['roots'], value['components']['proof']['paths']):
    while target in paths:
        paths.remove(target)
path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
