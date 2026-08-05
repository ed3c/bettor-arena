# Slice 04 — Three standalone repo-local skills

## Goal

Materialize `seed-repo-operator`, `repo-neural-perception`, and
`repo-terminal-operator` with deep, non-overlapping interfaces.

## Why now

The current repo has only exact-20 reasoning. Perception and implementation
authority must be explicit before CQ-0 and commit automation.

## Patch boundary

Only the three template skill directories, their local scripts/contracts, and
skill conformance tests. Forgejo operation remains outside the product skills.

## Dispatch Plan

- actor: `codex`
- reason: skill contract plus executable adapter work
- input packet: `WI-04`, skill registry, capability/envelope schemas
- output packet: three materialized skills and conformance receipts
- completion evidence: permitted behavior plus forbidden-action tests
- fallback: keep the missing skill non-conforming; do not broaden another skill

## Validation Contract

- validator: `OR-BEH-SKILL-BOUNDARY` + `OR-BEH-TWENTY-CALL`
- acceptance commands: future `bun test tests/skill-boundaries.test.ts`; existing
  `bun test tests/operator.test.ts`
- failure mode: reason mutates, perceive implements, execute changes criteria,
  or any skill admits
- completion evidence: three typed receipts and exact-20 behavior trace

## Known risks

Copying the central terminal operator would import repo-specific complexity and
mother-repo paths. Rebuild the smallest sufficient profile and compare behavior.

## Human decisions

Human admits any extracted central mechanism after side-by-side behavior, not by
name similarity.

## Completion evidence

Each skill passes allowed operations and one adversarial forbidden operation;
the reason skill rejects constant-return twenty-call placebo.
