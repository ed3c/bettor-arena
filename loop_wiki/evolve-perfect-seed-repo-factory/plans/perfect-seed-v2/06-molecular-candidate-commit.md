# Slice 06 — Molecular candidate commit and prompt lineage

## Goal

Create one CQ-0-gated candidate commit with a seven-field repo-relative index
card and content-addressed lineage manifest.

## Why now

Async evidence and Forgejo need an immutable candidate identity, while commit
messages must stay concise and retrievable.

## Patch boundary

Generated repo hooks, lineage scripts/schemas, prompt templates, and commit
fixtures. Do not reuse the plan-truth absolute-path message contract.

## Dispatch Plan

- actor: `codex`
- reason: Git index/commit-message validation and race-safe staging
- input packet: `WI-06`, passed CQ-0 receipt, prompt refs, packet, oracle IDs
- output packet: candidate commit/tree and minimum-lineage receipt
- completion evidence: validator positives/negatives and stable card parse
- fallback: leave HEAD unchanged and report owned/foreign staged paths

## Validation Contract

- validator: `OR-BEH-COMMIT-CARD` + `OR-MECH-COMMIT-CARD`
- acceptance commands: future `bun test tests/molecular-commit.test.ts`
- failure mode: missing/stale field, absolute path, prompt-role mismatch,
  unconsumed staged path, or volatile axis state fails
- completion evidence: commit/tree, manifest hash, CQ-0 binding, parsed seven fields

## Known risks

Hooks can race with index mutation. Snapshot the index and fail if it changes;
never stage unrelated user files.

## Human decisions

Candidate creation does not imply merge, release, verification, or admission.

## Completion evidence

The good card binds `Work-Item`, `Slice`, `Intent`, `Scope`, all three `Prompts`,
`Oracles`, and `Evidence`; every single-field hollow variant fails.
