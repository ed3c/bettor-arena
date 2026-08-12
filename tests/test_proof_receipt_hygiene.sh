#!/bin/sh
# Seam: per-run proof/control receipts may be read by the next entrypoint, but
# must not make an otherwise clean consumer fail broker-adapter cleanliness.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
SHORT=$(git -C "$ROOT" rev-parse --short=12 HEAD)

for receipt in \
  "data/proof-workflow/equivalence-${SHORT}.json" \
  "data/proof-workflow/control-equivalence-${SHORT}.json"
do
  git -C "$ROOT" check-ignore --no-index -q "$receipt" || {
    echo "FAIL: per-run receipt is not ignored: $receipt" >&2
    exit 1
  }
done

# Ignore rules do not remove already tracked historical evidence. This guards
# the migration boundary while making every newly generated receipt host-local.
git -C "$ROOT" ls-files 'data/proof-workflow/*.json' | grep -q . || {
  echo "FAIL: historical proof receipts are no longer tracked" >&2
  exit 1
}

echo "PASS: per-run proof receipts preserve broker-clean target state"
