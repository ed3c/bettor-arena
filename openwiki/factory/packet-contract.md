---
type: Contract
title: Seed input packet contract and refs tri-state
description: The perfect-seed-input@1.0.0 schema, source_refs shape rules, the declared/sentinel/resolved/stale refs_status states, the explicit resolve-refs --peer audit, and the legacy migration edge with its marked sentinel.
tags: [factory, packet, source-refs]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [seed-input-packet, refs-status, resolve-refs, sentinel]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Seed input packet contract and refs tri-state

`src/contracts.ts` is the packet contract's single owner — the M0 MATCH validator in [the workflow](overview.md). All shell layers relay its JSON verbatim; "sentinel/resolution judgement is owned by contracts.ts; the shell only relays the cli JSON" (src: loop_wiki/evolve-perfect-seed-repo-factory/trigger.sh:18).

## perfect-seed-input@1.0.0 — readInputPacket assertions

`readInputPacket` (src: loop_wiki/evolve-perfect-seed-repo-factory/src/contracts.ts:99-138) enforces, in order: absolute packet path; packet exists; `schema_version === "perfect-seed-input@1.0.0"`; `packet_id` matching `^[a-zA-Z0-9][a-zA-Z0-9._-]{2,80}$`; `packet_state === "admitted"` ("packet_state must be admitted before build"); a known `source_kind` (`dr`/`gcr`/`repo`/`grill-me`, src: contracts.ts:4); non-empty `source_path` free of NUL/CR/LF; source existence with kind/shape agreement (`repo` must be a directory, others a file); `task` of 12–4000 characters; `fixed_prompt_context` an array that MUST include `modules/semantic-truth-context.md` (src: contracts.ts:129-130); non-empty `emergent_prompt_context`; valid `source_refs` (below); and `human_gate === "required_before_seed_admit"` ("human_gate must preserve seed admission", src: contracts.ts:137).

## source_refs — provenance chain shape

Added by commit 568f5d7 ("source_refs make every packet carry its provenance chain"). `assertSourceRefs` requires a non-empty array of `{repo, commit, path, anchor}` where commit is 7–40 lowercase hex and path is repo-relative with no traversal (src: loop_wiki/evolve-perfect-seed-repo-factory/src/contracts.ts:31-49). Validation checks SHAPE only and never dereferences `repo` — standing validate/build/verify gates read zero sibling checkouts (src: loop_wiki/evolve-perfect-seed-repo-factory/modules/exchange-formats.md:9-14), which is iron law 4 (src: ARCHITECTURE.md:49-50).

## refs_status — four states plus a typed failure

First made a tri-state by commit c329882 ("so the human gate cannot misread it", issue #20), then extended by commit 2c36ddf (issue #22) so audited-then-broken stays distinguishable from never-audited. Owned entirely by `refsShapeStatus` / `refsStatusForPacket` (src: loop_wiki/evolve-perfect-seed-repo-factory/src/contracts.ts:61-97):

- **`sentinel`** — the packet carries the migrate-injected `unknown` placeholder (any ref with `repo === "unknown"`); sentinel dominates any receipt (src: contracts.ts:67-69, 80-81).
- **`declared`** — shape-validated, never audited: no resolve receipt exists (src: contracts.ts:82-83).
- **`resolved`** — granted ONLY by a `resolve-refs --peer` audit receipt (`perfect-seed-resolve-receipt@1.0.0` at `<packet>.resolve-receipt.json`) whose `packet_sha256` still matches the packet bytes; "standing gates read that local receipt, never a sibling checkout" (src: contracts.ts:76-77).
- **`stale`** — a receipt exists but no longer binds (packet sha mismatch or missing binding fields): "audited-then-broken must stay distinguishable from never-audited" (src: contracts.ts:78-79, 96).
- A receipt that exists but cannot be parsed as JSON is not a status at all: it throws the typed `ReceiptCheckError`, which `cli.ts` maps to exit 2 with a named diagnostic — "a failed check, not a status … never a bare parse traceback" (src: contracts.ts:63-65, 86-90; loop_wiki/evolve-perfect-seed-repo-factory/src/cli.ts:123).

## resolve-refs — the explicit peer audit

`cli.ts resolve-refs --packet <p> --peer <absolute-path>` verifies each ref's commit exists (`git cat-file -e <commit>^{commit}`) and each path is tracked at that commit (`git ls-tree -r --name-only`) in the peer clone, then writes the receipt with packet hash, peer, ref count (src: loop_wiki/evolve-perfect-seed-repo-factory/src/cli.ts:37-81). Without `--peer` it prints `NOT_RUN: resolve-refs requires --peer <absolute-path>; refs were not audited` and exits 2 — never PASS (src: cli.ts:44-45). `cli.ts refs-status --packet <p>` emits the status JSON (`perfect-seed-refs-status@1.0.0`) that `trigger.sh` relays verbatim into exchange context and route result (src: cli.ts:26-35; trigger.sh:19-25).

## Legacy migration edge

`src/migrate_packet.ts` is the only current migration edge: `perfect-seed-input@0.1.0` → `@1.0.0`. It adds explicit context and human-gate fields but never auto-admits a draft packet. A legacy packet without `source_refs` receives the marked sentinel `{repo:"unknown", commit:"0000000", path:"unmigrated/unknown", anchor:"pre-source-refs"}` — the exported `SENTINEL_SOURCE_REF` (src: loop_wiki/evolve-perfect-seed-repo-factory/src/contracts.ts:52-59) — so "an unmigrated packet never fakes an anchor" (src: loop_wiki/evolve-perfect-seed-repo-factory/modules/exchange-formats.md:28-37). The schema replay is exercised every `verify.sh` run against `packets/inbox/legacy-dr-example.json` (src: loop_wiki/evolve-perfect-seed-repo-factory/verify.sh:18-19).

## Focused tests

The refs lifecycle is pinned behavior-by-behavior in `tests/seed_factory.test.ts`: "rejects a packet without source_refs" (:299) and "rejects malformed source_refs shapes" (:307) at validate; "resolve-refs without --peer reports NOT_RUN with exit 2" (:325) and "resolve-refs audits commit existence and tracked path against an explicit peer" (:334) for the audit; "refs-status reports declared for shape-valid refs and sentinel for migrated placeholders" (:384); "resolved status is granted only by a receipt bound to the audited packet bytes" (:405); "a receipt missing its binding fields reads stale, never declared or resolved" (:443); "a corrupted receipt fails the check with exit 2 and a named diagnostic" (:456); and "migrated legacy packet builds with sentinel refs and refs_status sentinel" (:468) (src: loop_wiki/evolve-perfect-seed-repo-factory/tests/seed_factory.test.ts).

## Example packets

`packets/inbox/dr-example.json` (v1 packet with real anchors — grounded by commit 4d9f279) and its committed `dr-example.json.resolve-receipt.json`; `packets/inbox/legacy-dr-example.json` (v0.1.0 replay input); `packets/outbox/baseline-update-example.json` (`packet_kind: baseline-update`, the governed path for baseline changes) and `packets/outbox/behavior-eval.json` — both grep-asserted in `verify.sh` for their governance fields (src: loop_wiki/evolve-perfect-seed-repo-factory/verify.sh:30-31).
