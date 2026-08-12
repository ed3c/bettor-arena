#!/bin/sh
set -eu

ROOT=$(git rev-parse --show-toplevel)
TEMP=$(mktemp -d "${TMPDIR:-/tmp}/module-catalog-test.XXXXXX")
trap 'rm -rf "$TEMP"' EXIT

# Model the staged-only pre-commit seam: copy exactly the index into a plain
# directory with no .git metadata, then run the repository-contained gate.
git -C "$ROOT" checkout-index -a --prefix="$TEMP/tree/"
git -C "$ROOT" ls-files --stage -z > "$TEMP/index.zlist"

python3 "$TEMP/tree/scripts/gates/check_module_catalog.py" \
  --root "$TEMP/tree" \
  --index-manifest "$TEMP/index.zlist"

python3 "$TEMP/tree/scripts/arena_proof.py" \
  --root "$TEMP/tree" \
  --index-manifest "$TEMP/index.zlist" \
  check

python3 "$TEMP/tree/scripts/arena_context.py" \
  --root "$TEMP/tree" \
  --index-manifest "$TEMP/index.zlist" \
  check

python3 "$TEMP/tree/scripts/gates/check_mcp_policy.py" --materialized-index

printf 'not-an-index-entry\0' > "$TEMP/bad-index.zlist"
if python3 "$TEMP/tree/scripts/gates/check_module_catalog.py" \
  --root "$TEMP/tree" \
  --index-manifest "$TEMP/bad-index.zlist" >/dev/null 2>&1; then
  echo "FAIL: malformed index manifest was accepted" >&2
  exit 1
fi

printf '%s\n' "PASS: modular gates accept a materialized index tree"
