#!/bin/sh
set -eu

ROOT=$(cd "$(dirname "$0")" && pwd -P)
cd "$ROOT"

for required in AGENTS.md CLAUDE.md PROMPT.md PLAN.md ROUTES.md bun.lock eslint.config.mjs prettier.config.mjs tsconfig.json modules/architecture.md modules/eight-base-laws.md modules/exchange-formats.md modules/production-readiness.md modules/semantic-truth-context.md src/check_factory_minimum_lineage.ts src/run_fast_quality.ts src/run_generated_fast_quality.ts run.sh trigger.sh selftest.sh portability.sh; do
  [ -f "$required" ] || { echo "FAIL: missing $required" >&2; exit 2; }
done

bun run quality:fast
bun test tests/seed_factory.test.ts
bun run src/stats.ts --check
bun run src/check_template_lifecycle.ts

TMP=$(mktemp -d "${TMPDIR:-/tmp}/perfect-seed-verify.XXXXXX")
trap 'rm -rf "$TMP"' EXIT
bun run src/migrate_packet.ts --input "$ROOT/packets/inbox/legacy-dr-example.json" --output "$TMP/migrated.json"
bun run src/cli.ts validate --packet "$TMP/migrated.json"
bun run src/cli.ts build --packet "$ROOT/packets/inbox/dr-example.json" --output "$TMP/generated"
bun run src/run_generated_fast_quality.ts --repo "$TMP/generated"
bun run "$TMP/generated/scripts/plan.ts" --task "Choose the next bounded implementation action"
bun test "$TMP/generated/tests/operator.test.ts"
bun run src/verify_generated_repo.ts --repo "$TMP/generated"
bun run src/record_trend.ts --output "$TMP/trend.jsonl"
[ "$(wc -l <"$TMP/trend.jsonl" | tr -d ' ')" -eq 1 ] || { echo "FAIL: trend record missing" >&2; exit 2; }
bun run src/update_baseline.ts --packet "$ROOT/packets/outbox/baseline-update-example.json" --output "$TMP/seed-stats.json"
cmp -s "$ROOT/baselines/seed-stats.json" "$TMP/seed-stats.json" || { echo "FAIL: governed baseline output drift" >&2; exit 2; }

grep -Fq '"packet_kind": "baseline-update"' packets/outbox/baseline-update-example.json
grep -Fq '"human_gate": "required_before_seed_admit"' packets/outbox/behavior-eval.json

[ "$(grep -c '^## B' modules/eight-base-laws.md)" -eq 8 ] || { echo "FAIL: eight-base-laws must keep exactly eight base sections" >&2; exit 2; }
grep -Fq '兩種獨立抵達' modules/eight-base-laws.md || { echo "FAIL: settled criterion diluted in eight-base-laws" >&2; exit 2; }
grep -Fq '當初為什麼會信' modules/eight-base-laws.md || { echo "FAIL: refutation note discipline missing in eight-base-laws" >&2; exit 2; }
echo "PASS: perfect-seed repo factory candidate"
