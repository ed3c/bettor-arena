# Slice 07 — Append-only attestation refs

## Goal

Publish and reopen create-only CQ, PU, and architecture observations bound to an
exact candidate, tree, profile, oracle set, and evidence manifest.

## Why now

Async gates cannot safely project progress from mutable files or overwrite a
failed retry with a later pass.

## Patch boundary

Generated repo attestation scripts/schemas/tests and dedicated Git ref policy.
Do not put attestation truth into Forgejo or the RAG database.

## Dispatch Plan

- actor: `codex`
- reason: Git ref plumbing, immutable publication, reopen, and freshness logic
- input packet: `WI-07`, candidate commit/tree, profile, measurement receipt
- output packet: create-only attestation ref and effective-state projection
- completion evidence: local/fresh-clone ref receipts and retry preservation
- fallback: retain observation locally as unpublished and block verification

## Validation Contract

- validator: `OR-BEH-ATTESTATION` + `OR-BEH-ATTESTATION-FRESHNESS`
- acceptance commands: future `bun test tests/attestation-refs.test.ts`; future
  `bun test tests/attestation-freshness.test.ts`
- failure mode: ref overwrite, hash drift, candidate/profile/oracle mismatch,
  or missing fetch produces pending/repair, never pass
- completion evidence: ref object ID, artifact hash, fresh clone fetch and reopen

## Known risks

Custom refs may not be pushed/fetched by default. The refspec and Forgejo remote
policy must be physically tested; local-only success is insufficient.

## Human decisions

Human admits remote ref topology only after create, push, fresh-clone fetch, and
projection rebuild all pass.

## Completion evidence

Two retries coexist at distinct `<attestation-sha>` refs; copying another
candidate's passing observation cannot derive verified.
