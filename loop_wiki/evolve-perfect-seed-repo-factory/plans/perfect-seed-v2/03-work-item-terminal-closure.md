# Slice 03 — Work-Item, capability packet, and terminal envelope

## Goal

Define one local Work-Item identity, immutable terminal capability packet, and
one-attempt lease envelope without writable progress state.

## Why now

Skills and gates require a portable execution closure before mutation can be
authorized.

## Patch boundary

Work-Item/packet/envelope schemas, validators, projection code, and fixtures.
Do not add Forgejo issue IDs or mutable status to normative definitions.

## Dispatch Plan

- actor: `codex`
- reason: typed contract and portable bundle implementation
- input packet: `WI-03`, architecture subgraph, oracle IDs, expected base
- output packet: capability ref, envelope ref, validation receipt
- completion evidence: offline clean-clone validation and drift negatives
- fallback: emit typed `needs-enrichment` or `authorization-failed`

## Validation Contract

- validator: `OR-MECH-WORK-ITEM` + `OR-BEH-STANDALONE`
- acceptance commands: future `bun test tests/work-item-closure.test.ts`
- failure mode: criterion/scope/base change under the same packet hash, expired
  lease, or second candidate fails closed
- completion evidence: packet/envelope hash closure and clean-clone dry run

## Known risks

Making packets self-contained can duplicate graph/oracle data. Bind referenced
artifacts by manifest rather than hiding a global runtime dependency.

## Human decisions

Only a human may admit the Work-Item for execution; packet validity is not write
authorization.

## Completion evidence

Good packet passes; stale HEAD, scope drift, changed criterion, and missing
embedded manifest each fail with distinct reasons.
