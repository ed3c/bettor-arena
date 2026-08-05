# Slice 02 — Intended/observed architecture and conformance

## Goal

Compile the intended graph, observe the exact repo commit/tree, and emit a
rebuildable conformance projection with blind spots.

## Why now

Terminal scope cannot be authorized safely until the system can distinguish
declared ownership and dataflow from observed drift.

## Patch boundary

Template registries/schemas, new read-only perception modules, and focused graph
fixtures. Do not edit product code merely to make the observer pass.

## Dispatch Plan

- actor: `codex`
- reason: source scanning, graph normalization, and deterministic projection
- input packet: `WI-02`, intended graph, exact HEAD/tree
- output packet: observed graph and conformance receipt
- completion evidence: good/hollow graph fixture results and projection hashes
- fallback: report `opaque-unobserved`; never infer an edge from a filename

## Validation Contract

- validator: `OR-MECH-GRAPH-CONFORMANCE`, then `OR-SEM-INTERFACE` findings
- acceptance commands: future `bun test tests/architecture-perception.test.ts`
- failure mode: missing edge, owner drift, symlink escape, or unreported opaque
  edge prevents conformant
- completion evidence: source-bound graph receipt plus fresh semantic findings

## Known risks

Dynamic imports, generated code, and external services cannot always be
enumerated statically. They must become typed blind spots, not silent success.

## Human decisions

Human judges whether remaining blind spots are admissible for repo-level claims.

## Completion evidence

The hollow fixture retains filenames but removes a load-bearing edge and fails.
