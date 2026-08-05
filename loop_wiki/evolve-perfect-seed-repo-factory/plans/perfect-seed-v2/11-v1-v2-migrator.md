# Slice 11 — Explicit v1.1-to-v2 migrator

## Goal

Convert a v1.1 generated product into a separate v2 product while preserving
all source/IR/lineage bytes and exposing every synthesized or unmapped semantic.

## Why now

V1.1 must remain usable; silent in-place upgrade would erase whether Work-Item,
oracle, architecture, Git, and async meaning was measured or invented.

## Patch boundary

New repo migrator, migration schemas/fixtures, and focused factory tests. Do not
rewrite `src/migrate_packet.ts` as if packet migration equals repo migration.

## Dispatch Plan

- actor: `codex`
- reason: content-preserving filesystem/Git/schema migration with receipts
- input packet: `WI-11`, v1.1 artifact manifest and explicit output path
- output packet: separate v2 repo plus mapped/synthesized/unmapped receipt
- completion evidence: byte/hash comparison and needs-enrichment negatives
- fallback: retain v1 untouched and fail with critical unmapped fields

## Validation Contract

- validator: `OR-BEH-MIGRATION` + `OR-MECH-SCHEMA`
- acceptance commands: future `bun test tests/v1-v2-migration.test.ts`
- failure mode: in-place edit, dropped unknown field, legacy preflight promoted to
  CQ/PU, or invented oracle/architecture meaning
- completion evidence: parent manifest hash, preserved hashes, mappings, assumptions

## Known risks

V1 products lack Git genesis. Migrator must create the v2 deterministic genesis
for the new output; it must not pretend the old tree had commit history.

## Human decisions

Critical `unmapped` fields require enrichment/admission; a migrator never chooses
product intent for the human.

## Completion evidence

Good fixture preserves every v1 byte; missing-oracle and unknown-field fixtures
produce `needs-enrichment`, never a complete or admitted result.
