#!/bin/sh
# Seam: the versioned registry and as-run ledger must name the live Forgejo
# projection of GitHub issue #25. delivery.json is deliberately not checked:
# it is a historical materialization receipt, not a live progress snapshot.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
REGISTRY="$ROOT/.skill-bindings/forgejo-delivery-loop/registry.json"
AS_RUN="$ROOT/docs/plans/2026-08-06-bettor-arena-migration/as-run.md"
ISSUE_URL="http://localhost:3000/neon/bettor-arena/issues/34"

jq -e --arg url "$ISSUE_URL" \
  '.lines[] | select(.line == "bettor-arena-migration") | .issue_urls | index($url) != null' \
  "$REGISTRY" >/dev/null || {
    echo "FAIL: registry does not name the Forgejo projection of GitHub #25" >&2
    exit 1
  }

grep -q '| #34 |' "$AS_RUN" || {
  echo "FAIL: as-run ledger omits the active L5 slice" >&2
  exit 1
}

grep -q 'Forgejo `main` 同 SHA' "$AS_RUN" || {
  echo "FAIL: as-run ledger omits the dual-origin exact-commit claim" >&2
  exit 1
}

echo "PASS: Forgejo L5 tracking projection is versioned without rewriting the delivery receipt"
