#!/bin/sh
# prove_macro_loop.sh — physical traversal proof of the 大迴圈 (macro loop).
#
# Entry point (ARCHITECTURE.md §3 rule 1: the macro loop's gates hang off the
# HOST): `sh bootstrap.sh` registers core.hooksPath=.githooks, and from there
# every commit walks
#
#   pre-commit  -> scripts/gates/fast_quality.sh + the five repo gates
#   commit-msg  -> .githooks/lib/validate_molecular_message.ts
#   post-commit -> data/receipts/post-commit-<sha>.json
#
# What this script walks, in the order the mechanism itself runs:
#   DETERMINISTIC harness — every gate on the commit path, exercised through
#     the cheap verification surface its own author left (--selftest), plus the
#     terminal proof below. Nothing here touches the network or a model.
#   PROBABILISTIC read documents — the root passive context an agent session
#     loads before it may commit into this loop. Hashed, never executed.
#
# Terminal implementation proof: HEAD's real commit message and HEAD's real
# changed-path list are fed back through the commit-msg gate. A green there is
# not "the gate works on fixtures" — it is "the commit this proof is stamped
# with satisfies the gate that guards commits", traceable by sha.
#
# Usage: sh proof_workflow/prove_macro_loop.sh
# Exit:  0 pass · 2 a step went red / a terminus is absent · 64 FATAL.
set -u

PROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)
. "$PROVE_HOME/lib/prove.sh"

prove_init macro "sh bootstrap.sh -> core.hooksPath=.githooks -> .githooks/{pre-commit,commit-msg,post-commit}"

# --- probabilistic lane: what an agent reads before it may act in this loop --
prove_context arch-ssot ARCHITECTURE.md \
  "repo -> agent session: placement contract §2 + 鐵律 §3 (engineering SSOT)"
prove_context claude-tier CLAUDE.md \
  "ARCHITECTURE.md -> Claude Code passive context (thin tier derivation)"
prove_context agents-tier AGENTS.md \
  "ARCHITECTURE.md -> Codex/cross-host passive context + rule->evidence routing"
prove_context glossary CONTEXT.md \
  "repo -> agent session: canonical terms (admit / Intent-Slice / receipt)"
prove_context cross-repo-integration docs/integration/CROSS_REPO_INTEGRATION.md \
  "root routing -> macro session: four-repository and dual-origin delivery state machines"
# The document that tells an agent how to detect drift is itself a thing that can
# drift. Covering it here is not tidiness: an unstamped edit to the laws would
# change how every future reader interprets a red, and nothing would have said so.
prove_context proof-workflow-laws proof_workflow/README.md \
  "proof_workflow -> agent session: the laws, the -test loop, and the Harness of defects already found"
# Same argument one layer over: this one tells the next reader how the CLI surface
# is bound and which of its failures have already been paid for. Its own law 9 says
# a file no receipt hashes moves no digest and gets no trailer — so it is hashed
# here rather than being an exception to the rule it states.
prove_context loopctl-laws loopctl/README.md \
  "loopctl -> agent session: contract-vs-wiring, the surface lock, and the Harness of CLI defects already found"
# Hashed here even though NOTHING under mcp/ is — which is the point. That gap is
# real and named in the document itself, so at least the statement of it moves a
# digest and draws a trailer. Covering the mechanisms is blocked on a pre-existing
# red test in context-pack; wiring it in now would make this proof red for a
# reason that predates it.
prove_context mcp-laws mcp/README.md \
  "mcp -> agent session: mechanism-vs-policy, receipts that hash instead of transcribe, the narrow read-only tool surface, and the coverage gap"

# --- the MCP subsystem, which nothing measured until now ---------------------
# mcp/ had ZERO paths in the manifest against a 1044-line migration engine and a
# read-only server: editing either moved no digest and drew no trailer. The block
# was said to be a red test in context-pack; it is not a red test. test_server
# imports the `mcp` SDK, which lives only in the project venv, so it fails outside
# `uv run --frozen` and passes inside it — three consecutive green runs. An
# environment difference recorded as a code defect kept this uncovered.
prove_harness mcp-migrate mcp/production/migrate.py \
  "profile -> plan/apply/verify/rollback with six named refusals; receipts hash instead of transcribe and chain by the predecessor's sha256" \
  -- sh -c 'cd mcp/production && python3 -m unittest discover -s tests'
prove_harness mcp-probe mcp/production/probe_stdio.py \
  "a Codex-configured stdio MCP -> one real JSON-RPC handshake, fail-closed (hashed here; the suite above covers it)"
# Two explicit patterns, not one pattern plus `-k 'not server'`: unittest discover
# IMPORTS every matching module before any filter runs, so excluding by name still
# hit the missing SDK and this step went red for a reason that was not about the
# engine at all.
prove_harness context-pack-engine mcp/context-pack/src/context_pack_mcp/engine.py \
  "selected source -> AST evidence pack bound to source bytes, partial completeness reported; refuses traversal, symlink escape, oversized and mid-read mutation" \
  -- sh -c "cd mcp/context-pack && PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_engine.py' && PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_benchmark_receipt.py'"
prove_harness context-pack-server mcp/context-pack/src/context_pack_mcp/server.py \
  "two read-only tools over the engine (hashed, not run: its suite needs the project venv for the mcp SDK, and bootstrap.sh treats uv as a WARNING — making this proof require an optional tool would turn a legitimate environment into a red)"
prove_artifact benchmark-receipt mcp/context-pack/benchmarks/receipts/m1-pro-2026-07-29.json \
  "frozen comparison on a named machine and date; re-pinning it to satisfy a formatter would be falsifying evidence, which is why two files here keep their formatting debt"

# --- deterministic harness: activation ---------------------------------------
prove_harness bootstrap bootstrap.sh \
  "clone -> git config core.hooksPath=.githooks + tool doctor (exit 64 = FATAL)" \
  -- sh bootstrap.sh
prove_harness hookspath-registered - \
  "bootstrap.sh -> git config core.hooksPath == .githooks (the registration, asserted not assumed)" \
  -- sh -c '[ "$(git config core.hooksPath)" = ".githooks" ]'

# --- deterministic harness: the pre-commit closure ---------------------------
# pre-commit itself is staged-state dependent (it materializes the index into a
# temp tree); firing it from a proof would judge a commit nobody is making. It
# is hashed here and its whole closure is exercised below, gate by gate.
prove_harness pre-commit .githooks/pre-commit \
  "staged index -> checkout-index temp tree -> fast_quality.sh + five gates -> exit 0/2/64"
prove_harness fast-quality scripts/gates/fast_quality.sh \
  "file list on stdin -> format/lint/type/shell lanes -> receipt JSON + exit" \
  -- sh -c 'printf "%s\n" scripts/gates/fast_quality.sh | sh scripts/gates/fast_quality.sh >/dev/null'
prove_harness gate-root-coupling scripts/gates/check_root_coupling.py \
  "staged blobs -> absolute-home-path scan (§3 鐵律 2 T0) -> exit" \
  -- python3 scripts/gates/check_root_coupling.py --selftest
prove_harness gate-placement scripts/gates/check_placement.py \
  "git ls-files roots -> ARCHITECTURE.md §2 slots -> exit" \
  -- python3 scripts/gates/check_placement.py --selftest
prove_harness gate-readme-coverage scripts/gates/check_readme_coverage.py \
  "tracked README set + module manifests -> coverage/marker/link/path contract -> exit" \
  -- python3 scripts/gates/check_readme_coverage.py --selftest
prove_harness gate-skill-pointers scripts/gates/check_skill_pointers.py \
  ".claude/skills symlinks -> .agents/skills single-copy SSOT -> exit" \
  -- python3 scripts/gates/check_skill_pointers.py --selftest
prove_harness gate-credential-hygiene scripts/gates/check_credential_hygiene.py \
  "tracked files -> credential-material scan -> exit" \
  -- python3 scripts/gates/check_credential_hygiene.py --selftest
prove_harness gate-delivery-receipt scripts/gates/check_delivery_receipt.py \
  "delivery.json -> registry mapping (zero-network T0) -> exit" \
  -- python3 scripts/gates/check_delivery_receipt.py --selftest

# --- deterministic harness: the commit-msg gate ------------------------------
prove_harness commit-msg .githooks/commit-msg \
  "commit message file -> bun validator -> exit 0/2/64"
prove_harness molecular-validator .githooks/lib/validate_molecular_message.ts \
  "message + staged paths -> molecular field/role contract -> exit" \
  -- bun run .githooks/lib/validate_molecular_message.ts --selftest

# --- terminal implementation proof, anchored to this commit ------------------
git -C "$PROVE_ROOT" log -1 --format=%B >"$PROVE_TMP/head.msg"
git -C "$PROVE_ROOT" show --name-only --format= HEAD >"$PROVE_TMP/head.paths"
prove_harness head-commit-satisfies-gate - \
  "HEAD message + HEAD changed paths -> commit-msg gate -> exit 0 (the commit this proof is stamped with really passes the live gate)" \
  -- bun run .githooks/lib/validate_molecular_message.ts \
     --changed-paths-file "$PROVE_TMP/head.paths" "$PROVE_TMP/head.msg"

# --- terminal artifacts ------------------------------------------------------
prove_harness post-commit .githooks/post-commit \
  "commit created -> data/receipts/post-commit-<sha>.json (record-only, never blocks)"
prove_artifact head-receipt "data/receipts/post-commit-$PROVE_COMMIT.json" \
  "post-commit hook -> receipt naming this exact commit (physical evidence the hook fired here)"
prove_artifact delivery-receipt delivery.json \
  "macro loop -> four-layer delivery address + synced_at_commit (T0 of the delivery gate)"
# A host asset bootstrap tolerates the absence of — measured, not assumed:
# control_macro_entry.sh removes it in a throwaway worktree and bootstrap still
# exits 0, only WARNing. Covering it as an artifact would make a legitimate
# absence a red; leaving it out entirely is what let it sit uncovered while the
# control reported it every run. Its state now lands on the receipt either way.
prove_optional grepai-index .grepai/index.gob \
  "grepai init/watch -> semantic index for the MCP lane; absent = bootstrap WARN, never FATAL"

# --- the CLI surface the outside world is meant to use -----------------------
# Hashed here so that a change to the declared surface moves this digest. That is
# the point of the surface existing: internals drifting shows up in each loop's
# own proof, and the surface drifting shows up right here, so neither can move
# quietly to suit a call site.
prove_harness loopctl-surface loopctl/contract.json \
  "declared surface: loop x mode x required/optional flags x what each writes (data, not executed)"
prove_harness loopctl-surface-lock loopctl/surface.lock \
  "the pinned external promise: surface_version + the digest of loops x modes x flags only — internal iteration leaves it untouched by construction"
prove_harness loopctl-cli loopctl/loopctl.sh \
  "caller -> contract check -> dispatch -> target exit code passed through untouched" \
  -- sh loopctl/loopctl.sh --selftest
prove_harness loopctl-selftest loopctl/selftest.sh \
  "the CLI's own assertions: surface<->wiring both ways, declared targets exist, usage refused, exit codes passed through"
prove_harness loopctl-surface-digest loopctl/surface_digest.py \
  "contract.json -> the promise's canonical digest; internal iteration excluded by construction" \
  -- python3 loopctl/surface_digest.py --selftest
prove_harness loopctl-ingest loopctl/ingest.py \
  ".md/.txt passthrough, .html/.pdf extracted with provenance, directory -> repo kind; unknown format and absent extractor both FATAL" \
  -- python3 loopctl/ingest.py --selftest
prove_harness loopctl-lineage loopctl/lineage.py \
  "workflow.lock + staged paths -> the lineage trailer; kind:loop:path per touched file" \
  -- python3 loopctl/lineage.py --selftest
prove_harness loopctl-workflow-lock loopctl/workflow_lock.py \
  "the three proof receipts -> the manifest of what a traversal is made of" \
  -- python3 loopctl/workflow_lock.py --selftest
prove_harness loopctl-replay loopctl/replay.sh \
  "a commit or tag -> that ref's own CLI and proofs in a disposable worktree -> digest compared against what it recorded (needs a ref and a worktree; not fired here)"
prove_harness prepare-commit-msg .githooks/prepare-commit-msg \
  "staged paths -> workflow.lock -> Workflow-Lineage/Version/Touched trailers written into the message"
prove_note workflow-lock-not-hashed \
  "not hashed: loopctl/workflow.lock is BUILT FROM these receipts, so hashing it here would make this digest depend on a file that depends on this digest. Its integrity comes from being rebuildable — 'loopctl.sh workflow lock' regenerates it from the same receipts. (Quoted, not backticked: inside a double-quoted shell argument a backtick is command substitution, so the earlier wording silently RAN loopctl.sh and wrote the mangled remainder into the receipt.)"

prove_emit
