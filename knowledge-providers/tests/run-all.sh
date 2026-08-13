#!/bin/sh
set -eu

module_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

python3 "$module_root/scripts/check_knowledge_providers.py" check \
  --root "$module_root"
python3 "$module_root/tests/run_controls.py" --root "$module_root"
