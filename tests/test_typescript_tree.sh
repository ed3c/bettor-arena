#!/bin/sh
set -eu

ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"

# Full-tree quality seam. The staged hook stays budgeted and incremental; this
# suite proves every tracked TypeScript source against the same locked tools.
git ls-files '*.ts' | sh scripts/gates/fast_quality.sh

printf '%s\n' "PASS: all tracked TypeScript files pass format, lint, and strict typecheck"
