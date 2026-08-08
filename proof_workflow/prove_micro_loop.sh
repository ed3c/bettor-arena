#!/bin/sh
# prove_micro_loop.sh — physical traversal proof of the 小迴圈 (micro loop):
# the perfect-seed repo factory sandbox.
#
# Entry point (ARCHITECTURE.md §2 loop_wiki/, §3 rule 1: the micro loop's gates
# are all CLI + exit code + receipt):
#
#   trigger.sh <packet> <output>
#     -> cli.ts validate / validate-output / refs-status   (input contract)
#     -> run.sh -> cli.ts build                            (materialization)
#     -> run_generated_fast_quality.ts                     (quality mount 2)
#     -> <output>/scripts/plan.ts                          (operator)
#     -> verify_generated_repo.ts                          (validator)
#     -> packets/outbox/route-result.<id>.json             (four exit codes)
#     -> data/wiki-update/request-<id>.json                (delivery terminus)
#
# What this script walks:
#   DETERMINISTIC harness — the input-contract CLIs (non-mutating), the
#     good/hollow negative control (selftest.sh) and the full T0 (verify.sh).
#   PROBABILISTIC read documents — the three context lanes trigger.sh writes
#     into _engine-run/exchange-context.<id>.md: fixed (PROMPT.md +
#     modules/semantic-truth-context.md), iteration (the generated context
#     file), emergent (the physical packet field).
#
# NOT fired here, by design: trigger.sh / run.sh / portability.sh. trigger.sh
# writes a route-result and a wiki-update request into tracked and ledger dirs,
# and portability.sh refuses a dirty subtree and pays for a clean bun install.
# A proof that mutates the ledger it is proving is not a proof. They are hashed
# and recorded state=hashed-not-run, which never reads as green.
#
# Usage: sh proof_workflow/prove_micro_loop.sh
# Exit:  0 pass · 2 a step went red / a terminus is absent · 64 FATAL.
set -u

PROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$PROVE_HOME/lib/prove.sh"

F=loop_wiki/evolve-perfect-seed-repo-factory
PACKET=$F/packets/inbox/dr-example.json

prove_init micro "$F/trigger.sh <packet> <output> -> route-result -> data/wiki-update/request"

# --- probabilistic lane: the three context lanes of the exchange -------------
prove_context fixed-prompt "$F/PROMPT.md" \
  "fixed lane -> engine turn: the invariant task statement"
prove_context fixed-semantic-truth "$F/modules/semantic-truth-context.md" \
  "fixed lane -> engine turn: semantic-truth / low-compression output contract"
prove_context eight-base-laws "$F/modules/eight-base-laws.md" \
  "fixed lane -> engine turn: the eight bases + the arrival table AGENTS.md routes global laws to"
prove_context exchange-formats "$F/modules/exchange-formats.md" \
  "fixed lane -> engine turn: packet/route-result wire formats"
prove_context emergent-packet "$PACKET" \
  "emergent lane -> engine turn: the physical packet field (emergent prompts ride the packet, never a standards module)"
prove_context sandbox-agents "$F/AGENTS.md" \
  "sandbox root -> engine session passive context (sandbox is its own host dir, §3 鐵律 3)"

# --- deterministic harness: the input contract trigger.sh runs first ---------
prove_harness cli-validate-packet "$F/src/cli.ts" \
  "packet JSON -> readInputPacket schema check -> exit" \
  -- bun run "$F/src/cli.ts" validate --packet "$PROVE_ROOT/$PACKET"
prove_harness cli-validate-output "$F/src/cli.ts" \
  "target output path -> validateOutputPath precondition -> exit" \
  -- bun run "$F/src/cli.ts" validate-output --output "$PROVE_TMP/candidate-output"
prove_harness cli-refs-status "$F/src/cli.ts" \
  "packet + resolve receipt -> refs_status declared|sentinel|resolved|stale -> JSON on stdout" \
  -- bun run "$F/src/cli.ts" refs-status --packet "$PROVE_ROOT/$PACKET"

# --- deterministic harness: the instrument's own negative control ------------
prove_harness selftest-good-hollow "$F/selftest.sh" \
  "built seed + hollowed copy -> verify_generated_repo -> good green AND hollow red (the validator is shown able to go red)" \
  -- sh "$F/selftest.sh"

# --- deterministic harness: the full T0 the loop iterates against ------------
prove_harness verify-t0 "$F/verify.sh" \
  "sandbox -> quality:fast + tests + migrate + build + operator + validator + governed-baseline byte compare -> exit" \
  -- sh "$F/verify.sh"

# --- hashed, deliberately not fired ------------------------------------------
prove_harness trigger "$F/trigger.sh" \
  "packet -> four staged exits -> route-result.<id>.json + data/wiki-update/request-<id>.json (mutates the ledger; not fired by a proof)"
prove_harness run "$F/run.sh" \
  "packet -> cli.ts build -> materialized seed repo at <output> (mutates the filesystem; not fired by a proof)"
prove_harness portability "$F/portability.sh" \
  "git archive HEAD:<prefix> -> clean bun install -> own T0 + two negative controls (refuses a dirty subtree; explicit human/CI act)"

# --- terminal artifacts: every route-result left by a real run, then the hand-off
# route-result.fixture-dr.json is excluded and said so: the verify-t0 step above
# regenerates it (seed_factory.test.ts writes that exact path), and its `output`
# field carries a fresh mktemp directory every run. Hashing it made the digest a
# function of when the test last ran instead of a function of the mechanism —
# two identical traversals produced two different digests until this was named.
for rr in "$PROVE_ROOT/$F"/packets/outbox/route-result.*.json; do
  [ -f "$rr" ] || continue
  id=$(basename "$rr" .json)
  if [ "$id" = "route-result.fixture-dr" ]; then
    prove_note "$id" \
      "not hashed: regenerated by the verify-t0 harness step above, and its output path is a per-run mktemp dir — test scratch, not a delivery terminus"
    continue
  fi
  prove_artifact "$id" "${rr#"$PROVE_ROOT"/}" \
    "trigger.sh -> build/fast_quality/operator/validator exits + next_edge=human_required_before_seed_admit"
done
for rq in "$PROVE_ROOT"/data/wiki-update/request-*.json; do
  [ -f "$rq" ] || continue
  id=$(basename "$rq" .json)
  prove_artifact "$id" "${rq#"$PROVE_ROOT"/}" \
    "trigger.sh delivery terminus -> arena ledger -> consumed by kb-ingest/port/wiki_update_worker.sh (see prove_openwiki.sh)"
done
prove_artifact governed-baseline "$F/baselines/seed-stats.json" \
  "update_baseline.ts -> governed baseline verify.sh byte-compares against"

prove_emit
