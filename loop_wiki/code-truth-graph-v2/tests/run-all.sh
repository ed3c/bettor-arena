#!/bin/sh
set -eu
ROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
python3 "$ROOT/loop_wiki/code-truth-graph-v2/scripts/ctg_v2.py" check
python3 "$ROOT/loop_wiki/code-truth-graph-v2/scripts/ctg_v2.py" selftest
python3 -m py_compile "$ROOT/loop_wiki/code-truth-graph-v2/scripts/ctg_v2.py"
python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path
root = Path(sys.argv[1]) / "loop_wiki/code-truth-graph-v2"
files = sorted(root.rglob("*.json"))
for path in files:
    json.loads(path.read_text(encoding="utf-8"))
print(f"code-truth-graph-v2 JSON PASS: {len(files)} files")
PY
