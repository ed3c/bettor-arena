#!/bin/sh
set -eu

ROOT=$(cd "$(dirname "$0")" && pwd -P)
if [ "$#" -ne 2 ]; then
  echo "usage: trigger.sh <packet> <absolute-output>" >&2
  exit 64
fi
PACKET=$(cd "$(dirname "$1")" && pwd -P)/$(basename "$1")
OUTPUT=$2
bun run "$ROOT/src/cli.ts" validate --packet "$PACKET" >/dev/null
bun run "$ROOT/src/cli.ts" validate-output --output "$OUTPUT" >/dev/null
PACKET_ID=$(sed -n 's/.*"packet_id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$PACKET" | head -1)
if [ -z "$PACKET_ID" ]; then
  echo "FAIL: packet_id missing" >&2
  exit 2
fi
# Sentinel/resolution judgement is owned by contracts.ts; the shell only relays the cli JSON.
REFS_STATUS_JSON=$(bun run "$ROOT/src/cli.ts" refs-status --packet "$PACKET")
REFS_STATUS=$(REFS_STATUS_JSON="$REFS_STATUS_JSON" bun -e 'console.log(JSON.parse(process.env.REFS_STATUS_JSON).refs_status)')
SOURCE_REFS=$(REFS_STATUS_JSON="$REFS_STATUS_JSON" bun -e 'console.log(JSON.stringify(JSON.parse(process.env.REFS_STATUS_JSON).source_refs))')
case "$REFS_STATUS" in
  declared|sentinel|resolved) ;;
  *) echo "FAIL: unrecognized refs_status: $REFS_STATUS" >&2; exit 2 ;;
esac
mkdir -p "$ROOT/_engine-run"
CONTEXT="$ROOT/_engine-run/exchange-context.$PACKET_ID.md"
{
  echo "# Exchange context $PACKET_ID"
  echo
  echo "- packet: $PACKET"
  echo "- fixed_prompt_context: PROMPT.md + modules/semantic-truth-context.md"
  echo "- iteration_auto_context: $CONTEXT"
  echo "- emergent_prompt_context: physical packet field"
  echo "- source_refs: $SOURCE_REFS"
  echo "- refs_status: $REFS_STATUS"
  echo "- human_gate: required_before_seed_admit"
  echo "- target_output: $OUTPUT"
} >"$CONTEXT"

set +e
"$ROOT/run.sh" "$PACKET" "$OUTPUT" >"$ROOT/_engine-run/build.$PACKET_ID.out" 2>"$ROOT/_engine-run/build.$PACKET_ID.err"
BUILD_RC=$?
set -e
VALIDATOR_RC=1
FAST_QUALITY_RC=1
OPERATOR_RC=1
if [ "$BUILD_RC" -eq 0 ]; then
  set +e
  bun run "$ROOT/src/run_generated_fast_quality.ts" --repo "$OUTPUT" >/dev/null
  FAST_QUALITY_RC=$?
  set -e
  if [ "$FAST_QUALITY_RC" -eq 0 ]; then
    set +e
    bun run "$OUTPUT/scripts/plan.ts" --task "Validate the generated seed and surface the next bounded action" >/dev/null
    OPERATOR_RC=$?
    set -e
  fi
  if [ "$OPERATOR_RC" -eq 0 ]; then
    set +e
    bun run "$ROOT/src/verify_generated_repo.ts" --repo "$OUTPUT" >/dev/null
    VALIDATOR_RC=$?
    set -e
  fi
fi
ROUTE_RESULT="$ROOT/packets/outbox/route-result.$PACKET_ID.json"
cat >"$ROUTE_RESULT" <<EOF
{
  "schema_version": "perfect-seed-route-result@1.0.0",
  "packet_id": "$PACKET_ID",
  "build_exit": $BUILD_RC,
  "fast_quality_exit": $FAST_QUALITY_RC,
  "operator_exit": $OPERATOR_RC,
  "validator_exit": $VALIDATOR_RC,
  "source_refs": $SOURCE_REFS,
  "refs_status": "$REFS_STATUS",
  "output": "$OUTPUT",
  "next_edge": "human_required_before_seed_admit",
  "human_gate": "required_before_seed_admit"
}
EOF
if [ "$BUILD_RC" -ne 0 ] || [ "$FAST_QUALITY_RC" -ne 0 ] || [ "$OPERATOR_RC" -ne 0 ] || [ "$VALIDATOR_RC" -ne 0 ]; then
  echo "FAIL: build=$BUILD_RC fast_quality=$FAST_QUALITY_RC operator=$OPERATOR_RC validator=$VALIDATOR_RC route_result=$ROUTE_RESULT" >&2
  exit 2
fi
echo "PASS: route_result=$ROUTE_RESULT"
