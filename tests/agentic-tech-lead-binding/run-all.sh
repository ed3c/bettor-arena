#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
python3 "$ROOT/scripts/gates/check_agentic_tech_lead_binding.py" --selftest
python3 "$ROOT/scripts/gates/check_agentic_tech_lead_binding.py" --root "$ROOT"
python3 -m py_compile "$ROOT/scripts/gates/check_agentic_tech_lead_binding.py"
