# Slice 12 — Full v2 materialization and adversarial E2E

## Goal

Prove the complete four-input lifecycle, seed reset, fresh-clone operation,
candidate/async projection, and human stop edge using good and adversarial controls.

## Why now

Individual contracts can all pass while their cross-boundary dataflow is hollow.
This slice measures the physical product journey.

## Patch boundary

Factory/materializer integration, template, tests, docs, `verify.sh`, and
`selftest.sh`. No threshold or fixture edits solely to make the target pass.

## Dispatch Plan

- actor: `codex`
- reason: cross-stack TDD integration and physical reproduction
- input packet: `WI-12`, all current milestone receipts and four source fixtures
- output packet: four generated v2 repos and E2E receipt bundle
- completion evidence: good/hollow/stale/scope-drift and reset/fresh-clone logs
- fallback: name the failing node and keep v2 candidate, never admit partial E2E

## Validation Contract

- validator: `OR-BEH-E2E` + `OR-BEH-SEED-RESET`; final admit:
  `OR-HUM-V2-ADMIT`
- acceptance commands: `sh verify.sh`; `sh selftest.sh`
- failure mode: any source route, skill boundary, CQ-0, commit, attestation,
  Forgejo block, projection rebuild, RAG rebuild, migration, reset, or human gate fails
- completion evidence: current commit/tree-bound receipt matrix and hollow opposites

## Known risks

An E2E can accidentally depend on mother-repo paths, network, cached indices, or
pre-existing Git config. Run from clean temporary roots with network disabled.

## Human decisions

Human alone decides whether v2 becomes the admitted seed after current CQ/PU/
architecture evidence, Forgejo readback, blind spots, and migration gaps are shown.

## Completion evidence

DR, GCR, repo, and grill-me all complete the same standalone lifecycle; hollow,
stale, and scope-drift fixtures fail at named edges; reset preserves user/domain
data while restoring seed hashes; final state remains human-required.
