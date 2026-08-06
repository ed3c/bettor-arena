# Slice 09 — Derived progress, drift, and automatic repair prompts

## Goal

Derive Work-Item/milestone state and the next fixed/automatic/emergent prompt
packet from registries plus current physical facts.

## Why now

Without a deterministic projector, plans and Forgejo will drift into manually
claimed status and the system cannot correct execution safely.

## Patch boundary

Read-only perception/projector modules, disposable `_engine-run` outputs, and
repair fixtures. Never write status back into normative registries.

## Dispatch Plan

- actor: `codex`
- reason: deterministic reduction and drift classification
- input packet: `WI-09`, registries, HEAD/tree, worktree/index, attestations, readbacks
- output packet: progress projection and next automatic prompt or repair proposal
- completion evidence: deletion/rebuild byte comparison and route fixtures
- fallback: report blind spot or `repair_required`; do not infer completion

## Validation Contract

- validator: `OR-BEH-PROJECTION` + `OR-BEH-REPAIR`
- acceptance commands: future `bun test tests/projection-rebuild.test.ts`; future
  `bun test tests/repair-routing.test.ts`
- failure mode: hidden projection state, nondeterministic ordering, silent scope
  expansion, or stale HEAD blocks pass
- completion evidence: input fingerprint, projection hash, prompt refs/hashes

## Known risks

Worktree `in_progress` observation is transient and may include foreign changes.
It must intersect declared scope without claiming ownership of unrelated dirt.

## Human decisions

Any new path, dependency, criterion, plan, or architecture invariant requires a
new proposal and human admission.

## Completion evidence

Same physical inputs rebuild identically; same-slice repair routes automatically
within budget; scope-drift routes to human-required without mutation.
