# Slice 01 — V2 contracts, schemas, Git genesis, and seed boundary

## Goal

Materialize a schema-valid `perfect-seed-repo@2.0.0` with a hash-bound ontology,
ownership manifest, and reproducible Git genesis while preserving v1.1.

## Why now

Every later lease, commit, stale check, and attestation ref requires a stable
HEAD/tree. V1.1 creates files but not a Git repository.

## Patch boundary

`templates/repo/.perfect-seed/`, `templates/template-metadata.json`,
`src/contracts.ts`, `src/materialize.ts`, and focused factory tests. Do not
change v1.1 semantics in place.

## Dispatch Plan

- actor: `codex`
- reason: bounded TypeScript/schema/Git implementation with runnable tests
- input packet: `WI-01`, v1.1 source refs, `EC-01A`, `EC-01B`
- output packet: v2 schema bundle, seed manifest, genesis receipt, fresh-clone receipt
- completion evidence: changed files plus red/green test and schema receipts
- fallback: keep v2 candidate unmaterializable; do not fake HEAD or copy mother `.git`

## Validation Contract

- validator: TDD + `OR-MECH-SCHEMA` + `OR-BEH-STANDALONE`
- acceptance commands: `bun test tests/seed_factory.test.ts`; future
  `bun test tests/standalone-v2.test.ts`
- failure mode: nondeterministic genesis, unknown-field coercion, missing Git, or
  seed hash drift fails nonzero
- completion evidence: exact genesis commit/tree and clean offline clone replay

## Known risks

Git commit identity/time can destroy reproducibility. The contract must define
canonical author, committer, timestamp, file mode, ordering, and object format.

## Human decisions

Human later admits whether the deterministic genesis contract is acceptable;
the implementation may only produce a candidate.

## Completion evidence

Schema-positive/negative fixtures, byte-identical repeated genesis, and a
fresh-clone seed-manifest verification receipt.
