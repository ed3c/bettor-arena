# Slice 08 — Forgejo projection, outbox, and readback

## Goal

Project local Work-Item/candidate facts into one idempotent Forgejo issue/status
flow with offline outbox and hash-bound readback.

## Why now

Forgejo is needed for human-visible intent slicing and progress, but cannot be
allowed to become identity or evidence SSOT.

## Patch boundary

Generated repo Forgejo request/outbox/readback schemas, projectors, and tests.
Live browser/Forgejo mutation stays behind the external Forgejo operator.

## Dispatch Plan

- actor: `codex`
- reason: deterministic local request/outbox/readback implementation
- input packet: `WI-08`, candidate, manifest, current attestation projection
- output packet: idempotent request, outbox state, readback validation result
- completion evidence: offline and local Forgejo journey receipts
- fallback: queue locally, allow candidate, block merge/release/admit

## Validation Contract

- validator: `OR-BEH-FORGEJO`; live edge: `OR-HUM-FORGEJO-LIVE`
- acceptance commands: future `bun test tests/forgejo-projection.test.ts`
- failure mode: wrong repository/marker/candidate, missing auth, or missing
  readback keeps promotion false
- completion evidence: request hash, idempotency marker, issue/comment bytes, readback hash

## Known risks

Projecting after Git may leave Forgejo temporarily behind. That is legal only if
the progress projection visibly blocks promotion.

## Human decisions

Human authorizes the live local Forgejo operation and accepts the exact readback.

## Completion evidence

Forgejo-down fixture reaches candidate + outbox-pending but cannot verify or
admit; repeated projection reuses exactly one issue marker.
