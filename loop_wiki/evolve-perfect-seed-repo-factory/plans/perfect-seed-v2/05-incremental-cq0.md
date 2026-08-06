# Slice 05 — Incremental low-cost CQ-0

## Goal

Harden a synchronous pre-commit gate that catches cheap, high-rework defects
without waiting for complete CQ-1 or Production Use.

## Why now

The current full-tree preflight is green but lacks affected-closure proof,
dependency boundaries, and candidate-commit semantics.

## Patch boundary

Generated repo CQ-0 scripts/profiles, package commands, closure tests, and the
factory wrapper. Preserve the current receipt as legacy preflight evidence.

## Dispatch Plan

- actor: `codex`
- reason: incremental dependency analysis and test-first gate hardening
- input packet: `WI-05`, changed paths, expected HEAD, policy hash
- output packet: `perfect-seed-cq0-receipt@2.0.0`
- completion evidence: stage receipts, closure comparison, HEAD-unchanged failures
- fallback: when closure proof is uncertain, run full repo and record why

## Validation Contract

- validator: `OR-BEH-CQ0` + `OR-BEH-CQ0-CLOSURE`
- acceptance commands: future `bun test tests/cq0-closure.test.ts`; future
  `bun run quality:cq0 --packet <fixture>`
- failure mode: any failed/not-observed required stage blocks candidate commit
- completion evidence: declared and actual scope plus per-stage exit/time/hash

## Known risks

The CQ-0 receipt cannot naively hash-bind the final commit tree because adding
the receipt changes the tree. Bind canonical business payload scope pre-commit,
then seal against the committed tree post-commit.

## Human decisions

No threshold relaxation is automatic. A future cost/coverage tradeoff change
requires a plan amendment.

## Completion evidence

Format, lint, type, dependency, scope, and behavior defects each fail at the
physical stage; cross-project defects match full-repo detection.
