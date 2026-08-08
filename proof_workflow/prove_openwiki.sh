#!/bin/sh
# prove_openwiki.sh — physical traversal proof of the openwiki lane: the
# digestion station that turns the micro loop's delivery terminus into the
# as-built wiki.
#
# Entry point (ARCHITECTURE.md §2 kb-ingest/ + openwiki/):
#
#   kb-ingest/port/wiki_update_worker.sh <request.json> [--dry-run]
#     -> parse    typed request contract (schema + named delta states)
#     -> preflight fixed_prompt_context pointers + wiki + route_result present
#     -> regenerate  claude -p, official update prompts, writes gated to openwiki/
#     -> gates    openwiki_subagent.sh finder/verifier (physical read boundaries)
#     -> post     openwiki_post.py migrate + finalize (index.md, .last-update.json)
#     -> receipt  data/wiki-update/receipt-<id>.json back-linking the request
#
# This is the lane where the probabilistic side is the point, so the two halves
# are walked explicitly:
#   PROBABILISTIC read documents — every official OpenWiki prompt asset the run
#     composes its turn from, plus the host-runtime adapter appended to it.
#     Hashed, never executed: if any of these bytes move, the model that ran is
#     not the model this receipt describes.
#   DETERMINISTIC harness — the code-owned layer that makes those prompts'
#     promises true (openwiki_post.py), the module perception gate that proves
#     the assets are machine-generated and the three read boundaries physically
#     hold, and the worker's own fixture selftest plus a real --dry-run over an
#     actual request from the micro loop.
#
# The --dry-run stage runs with WIKI_UPDATE_FORCE_RECEIPT=1 on purpose: the
# worker refuses a colliding receipt (frozen evidence), and without the explicit
# override this proof would be a one-shot. The override is the declared rerun
# intent the house rule asks for, and the dry-run is byte-asserted not to touch
# the live wiki.
#
# Usage: sh proof_workflow/prove_openwiki.sh
# Exit:  0 pass · 2 a step went red / a terminus is absent · 64 FATAL.
set -u

PROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$PROVE_HOME/lib/prove.sh"

prove_init openwiki "kb-ingest/port/wiki_update_worker.sh <request.json> -> openwiki/ -> data/wiki-update/receipt-<id>.json"

# --- probabilistic lane: the official prompt assets the turn is composed from
prove_context update-system kb-ingest/openwiki/update.system.md \
  "OPENWIKI-OFFICIAL block -> claude -p --system-prompt (update mode)"
prove_context update-user kb-ingest/openwiki/user.update.md \
  "OPENWIKI-OFFICIAL block + {WIKI_GOAL}/{RUNTIME_CONTEXT} substitution -> claude -p prompt"
prove_context init-system kb-ingest/openwiki/init.system.md \
  "OPENWIKI-OFFICIAL block -> init-mode system prompt (skeleton generation)"
prove_context init-user kb-ingest/openwiki/user.init.md \
  "OPENWIKI-OFFICIAL block -> init-mode user prompt"
prove_context host-runtime kb-ingest/port/host-runtime.md \
  "adapter appendix appended after the official system prompt (the only local addition)"
prove_context subagent-critic kb-ingest/openwiki/subagents/skeleton-critic.md \
  "systemPrompt section -> critic child, sandbox = worktree at HEAD + skeleton"
prove_context subagent-finder kb-ingest/openwiki/subagents/question-finder.md \
  "systemPrompt section -> finder child, sandbox = worktree with openwiki/ DELETED"
prove_context subagent-verifier kb-ingest/openwiki/subagents/answer-verifier.md \
  "systemPrompt section -> verifier child, sandbox = wiki-only scratch copy"
# The emergent lane's landing site. The request names it
# (emergent_prompt_context: openwiki/quickstart.md#backlog) and the worker defers
# PARTIAL verifier findings into its ## Backlog under the bounded-round policy —
# so run-discovered content lands here and nowhere near a standards module. It
# was uncovered until control_openwiki_entry.sh ran the entry point and listed
# what it really reads: the same shape as the micro loop's iteration lane, named
# in the contract and missing from the coverage.
prove_context emergent-backlog openwiki/quickstart.md \
  "emergent lane -> ## Backlog: deferred PARTIAL findings, run-discovered only"

# --- deterministic harness: the code-owned layer under those prompts ---------
prove_harness openwiki-post kb-ingest/port/openwiki_post.py \
  "wiki root -> migrate (front matter) + finalize (mermaid, indexes, links, .last-update.json) -> exit" \
  -- python3 kb-ingest/port/openwiki_post.py --selftest
prove_harness converge-gate kb-ingest/check_repo_wiki_converge.py \
  "module + host profile -> prompt assets machine-generated, post passes runnable, three read boundaries hold, RepoDoc ingest accepts -> exit 0/1/3" \
  -- python3 kb-ingest/check_repo_wiki_converge.py
prove_harness subagent-runner kb-ingest/port/openwiki_subagent.sh \
  "role + target -> isolated child process whose READ BOUNDARY is the directory it can see (worktree / wiki-only copy)"
prove_harness worker-selftest kb-ingest/port/wiki_update_worker.sh \
  "fixture requests -> absent 64 / non-JSON 2 / foreign schema 2 / missing field 2 / good dry-run receipt / collision 64" \
  -- sh kb-ingest/port/wiki_update_worker.sh --selftest

# --- deterministic harness: a real request through the real chain ------------
# The newest request the micro loop left in the ledger, chosen by name so the
# choice is deterministic. Absence is named, never a silent skip.
REQUEST=$(ls "$PROVE_ROOT"/data/wiki-update/request-*.json 2>/dev/null | sort | tail -1)
if [ -n "$REQUEST" ]; then
  prove_artifact consumed-request "${REQUEST#"$PROVE_ROOT"/}" \
    "micro loop trigger.sh -> arena ledger -> this proof's dry-run input"
  prove_harness worker-dry-run kb-ingest/port/wiki_update_worker.sh \
    "real request -> parse + preflight + gate sandbox assembly (OPENWIKI_DRY_RUN) + post passes on a scratch copy, live wiki byte-compared untouched -> receipt" \
    -- env WIKI_UPDATE_FORCE_RECEIPT=1 sh kb-ingest/port/wiki_update_worker.sh "$REQUEST" --dry-run
else
  prove_artifact consumed-request "data/wiki-update/request-*.json" \
    "micro loop trigger.sh -> arena ledger (absent: run the micro loop's trigger.sh first)"
fi

# --- terminal artifacts ------------------------------------------------------
prove_artifact wiki-index openwiki/index.md \
  "finalize synchronizeWikiIndexes -> generated index (never hand-written)"
prove_artifact wiki-architecture openwiki/architecture.md \
  "regenerated as-built page: the projection of ARCHITECTURE.md's mechanism"
prove_artifact last-update openwiki/.last-update.json \
  "finalize -> gitHead stamp; bootstrap.sh reads it to decide wiki freshness"

# Commit traceability of the wiki itself: the gitHead it was generated at must
# resolve in this repository, and its distance to HEAD is the staleness fact
# bootstrap.sh warns on. Undecidable is a named red, not a shrug.
# The staleness distance is measured and carried as a FACT, not turned into a
# verdict. bootstrap already WARNs that the wiki is stale, and making the proof
# red on it would block every traversal until someone spends a model turn — but
# leaving the number only in a WARN means nobody can see it grow. On the receipt
# it is trackable; whether to regenerate stays a human call with a cost.
WIKI_HEAD=$(sed -n 's/.*"gitHead": *"\([0-9a-f]\{40\}\)".*/\1/p' "$PROVE_ROOT/openwiki/.last-update.json" | head -1)
BEHIND=$(git -C "$PROVE_ROOT" rev-list --count "$WIKI_HEAD..HEAD" 2>/dev/null || echo unknown)
DRIFTED=$(git -C "$PROVE_ROOT" diff --name-only "$WIKI_HEAD" HEAD -- . ':(exclude)openwiki/' 2>/dev/null | grep -c . || echo unknown)
prove_harness wiki-githead-resolves - \
  "openwiki/.last-update.json gitHead -> git cat-file -e; measured drift at this run: $BEHIND commit(s) behind HEAD, $DRIFTED non-wiki file(s) changed since" \
  -- sh -c 'h=$(sed -n "s/.*\"gitHead\": *\"\([0-9a-f]\{40\}\)\".*/\1/p" openwiki/.last-update.json | head -1); [ -n "$h" ] && git cat-file -e "$h"'

prove_emit
