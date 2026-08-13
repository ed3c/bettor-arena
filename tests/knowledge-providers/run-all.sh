#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
python3 "$ROOT/scripts/check_knowledge_providers.py" --root "$ROOT"
python3 "$ROOT/scripts/check_knowledge_providers.py" --root "$ROOT" --selftest
python3 -m compileall -q "$ROOT/scripts/check_knowledge_providers.py" "$ROOT/tests/test_knowledge_providers.py"
echo "knowledge-providers run-all PASS"
