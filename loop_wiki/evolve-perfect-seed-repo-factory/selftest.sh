#!/bin/sh
set -eu

ROOT=$(cd "$(dirname "$0")" && pwd -P)
cd "$ROOT"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/perfect-seed-selftest.XXXXXX")
trap 'rm -rf "$TMP"' EXIT

bun run src/cli.ts build --packet "$ROOT/packets/inbox/dr-example.json" --output "$TMP/good" >/dev/null
bun run "$TMP/good/scripts/plan.ts" --task "Choose one tested implementation slice" >/dev/null
bun run src/verify_generated_repo.ts --repo "$TMP/good" >/dev/null

cp -R "$TMP/good" "$TMP/hollow"
mv "$TMP/hollow/.agents/skills/seed-repo-operator/SKILL.md" "$TMP/hollow/.agents/skills/seed-repo-operator/SKILL.md.disabled"
if bun run src/verify_generated_repo.ts --repo "$TMP/hollow" >/dev/null 2>&1; then
  echo "FAIL: hollow repo unexpectedly passed" >&2
  exit 2
fi
echo "PASS: good repo passed and hollow repo failed"
