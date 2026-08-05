---
target: {REPO_ROOT}/loop_wiki/evolve-perfect-seed-repo-factory
title: v1.1 factory and central candidate primitives
commit_hash: 4ee6c72460d628a9184e5521c67949e99d33b452
worktree_overlay_sha256: b3a7699fd4e69c8e3c6fc46ef0f84ed1d85cf3c732cda93ea7f9036ca85267ce
covers: [message-contract, state-machine, api-contract, implicit-deps, negative-invariants]
extracted_at: 2026-08-04
---

# Source-anchored invariants

The target had an uncommitted overlay during extraction. Source refs below bind
the observed bytes, while `commit_hash` alone does not reproduce that overlay.
No v2 plan premise treats the overlay as admitted product state.

## Message and API contracts

- INV-001 [A] Input accepts exactly `dr`, `gcr`, `repo`, and `grill-me`, and
  materialization requires an admitted packet and human gate. — src:
  `src/contracts.ts:4-17`, `src/contracts.ts:23-61`
- INV-002 [A] The target contract requires a standalone repo and exactly twenty
  dependency-valid local calls ending at `human_required`. — src:
  `PROMPT.md:3-24`
- INV-003 [A] The materializer is currently `perfect-seed-repo@1.1.0`, copies
  the template, writes reduced IR and hash manifest, and does not initialize
  Git. — src: `src/materialize.ts:6-85`
- INV-004 [A] The generated repo validator requires only
  `seed-repo-operator`; there is no perception or terminal-implementation skill
  requirement. — src: `src/verify_generated_repo.ts:10-25`
- INV-005 [A] The reasoning skill is read-oriented, exact-20, local-only, and
  routes mutation to a later bounded slice. — src:
  `templates/repo/.agents/skills/seed-repo-operator/SKILL.md:9-45`

## State and gate contracts

- INV-006 [A] Current route state ends at a human gate; the fast receipt is not
  an asynchronous CQ or PU axis. — src: `ROUTES.md:5-14`, `ROUTES.md:43-52`
- INV-007 [A] Current fast stages are minimum lineage, full-tree Prettier,
  full-tree ESLint, and full TypeScript; there is no dependency-boundary stage.
  — src: `src/run_fast_quality.ts:17-31`
- INV-008 [A] The fast receipt explicitly claims
  `preflight-only-not-code-quality-axis`. — src:
  `src/run_fast_quality.ts:69-92`
- INV-009 [A] Full asynchronous CQ/PU request, worker, terminal receipt, stale,
  retry, and promotion owners are explicitly absent. — src:
  `modules/production-readiness.md:23-30`
- INV-010 [A] The factory template is code SSOT and source/lineage must not be
  rewritten to improve a result. — src: `modules/architecture.md:17-24`

## Central candidate primitives

- INV-011 [A] Central minimum lineage binds fixed, iteration-auto, and emergent
  prompt roles to a staged manifest and verifies staged scope, evidence, and
  plan transition. — src: `runtime/lineage/minimum-lineage-orchestrator.ts:23-31`,
  `runtime/lineage/minimum-lineage-orchestrator.ts:141-182`
- INV-012 [A] That central gate does not protect the perfect-seed factory path.
  — src: `runtime/lineage/minimum-lineage-orchestrator.ts:32-52`
- INV-013 [A] The central molecular message validator is plan-truth-specific,
  requires eleven fields, canonical absolute paths, and at least five absolute
  dataflow paths; it is unsuitable as the v2 RAG card without extraction. — src:
  `loop_wiki/evolve-unknown-discovery-plan-truth/adapters/typescript/runtime/scripts/validate_molecular_commit_message.ts:8-24`,
  `.../validate_molecular_commit_message.ts:97-123`
- INV-014 [A] Central verification projection reopens commit/tree/profile-bound
  receipts, derives stale/repair/promotion state, and emits a next prompt. — src:
  `runtime/verification/project-verification-state.ts:49-98`,
  `runtime/verification/project-verification-state.ts:166-240`
- INV-015 [A] Central post-commit projection never starts workers, mutates
  Forgejo, or advances plan state. — src:
  `runtime/verification/project-commit-verification.ts:470-490`,
  `.githooks/post-commit:10-18`
- INV-016 [A] Forgejo issue requests are deterministic projections with
  `automatic_execution:false`; the issue is not direct execution. — src:
  `runtime/forgejo/terminal-issue-payload.ts:40-47`,
  `runtime/forgejo/terminal-issue-payload.ts:68-90`
- INV-017 [A] Central terminal operator already separates static task-quality
  work from production admission and forbids plan/admit authority, but it is a
  large repo-specific profile rather than a standalone factory template. — src:
  `repo/agent-skills-repo/.agents/skills/repo-terminal-operator/SKILL.md:10-35`,
  `.../SKILL.md:39-60`
- INV-018 [A] The central repo-neural-perception skill treats retrieval scores
  as candidates, reopens artifacts, separates CQ and PU, and reserves admission
  to a human/main session. — src: `skills/repo-neural-perception/SKILL.md:10-25`

## Negative invariants

The following exhaustive searches were run over the factory target. Exit 1
means no match in the enumerated target, not universal absence.

- NEG-001 [A] No `plan-registry`, `plan_registry`, or `progress-projection`
  reference exists in the factory target.
- NEG-002 [A] No intended/observed architecture or `repair_required` contract
  exists in the factory target.
- NEG-003 [A] Template skill inventory contains only
  `seed-repo-operator/{SKILL.md,cases.json}`.
- NEG-004 [A] No attestation ref, Forgejo, Work-Item, or work-item contract
  exists in the factory target.
- NEG-005 [A] No LanceDB reference exists; incidental `coverage` matches are not
  RAG capability evidence.

## Runtime observations

- OBS-001 [A] `bun test tests/seed_factory.test.ts` passed 13 tests and 189
  assertions on 2026-08-04.
- OBS-002 [A] `bun run quality:fast` passed and wrote a preflight-only receipt on
  2026-08-04.
- OBS-003 [A] Targeted central Forgejo, lineage, and verification tests passed 73
  tests and 207 assertions on 2026-08-04.

These commands prove candidate primitives run. They do not prove v2 integration
or technical equivalence.

## Implicit dependencies

- IMPL-001 [A] Dedicated Git attestation refs require the generated product to
  be a Git repository with a stable HEAD/tree. V1 materialization does not
  establish that prerequisite. — derived from `src/materialize.ts:32-85`
- IMPL-002 [A] Forgejo/RAG/progress views must be reconstructable from local Git
  and receipts or the generated repo would depend on external projection state.
  — ownership boundary: `AGENTS.md:26-32`; central projection non-execution:
  `.githooks/post-commit:13-18`

## SURFACE

`a_ratio=1.00`, `unverified_count=0`, `worktree_overlay=true`.

The interface choice and future backend performance remain design candidates;
they are not included as extracted facts.
