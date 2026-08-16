#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
cd "$ROOT"
python3 -m compileall -q scripts/providers
python3 scripts/providers/serena_canary.py check
python3 scripts/providers/serena_canary.py --selftest
python3 scripts/providers/grepai_canary.py check
python3 scripts/providers/grepai_canary.py --selftest
echo "provider-canaries run-all PASS"
