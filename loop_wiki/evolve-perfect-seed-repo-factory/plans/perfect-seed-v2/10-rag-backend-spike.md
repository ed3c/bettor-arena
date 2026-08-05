# Slice 10 — LanceDB versus SQLite FTS5

## Goal

Measure two rebuildable local retrieval implementations over the same Work-Item,
commit-card, attestation, graph, and projection corpus.

## Why now

Choosing LanceDB by feature list would repeat name-based equivalence. Runtime
packaging, update cost, provenance, and deletion/rebuild behavior are load-bearing.

## Patch boundary

Index adapters and benchmark fixtures only. Do not wire either backend into
commit, verification, or admission gates before selection.

## Dispatch Plan

- actor: `codex`
- reason: build and run both local implementations under one evaluator
- input packet: `WI-10`, fixed corpus/query/update workload and resource limits
- output packet: dual-backend comparison receipt and selection evidence packet
- completion evidence: commands, versions, retrieval results, cost observations
- fallback: if LanceDB runtime/native packaging is unproven, retain SQLite FTS5

## Validation Contract

- validator: `OR-BEH-RAG-SPIKE` + `OR-EXT-RAG-RUNTIME`; admit:
  `OR-HUM-RAG-SELECT`
- acceptance commands: future
  `bun run scripts/indexing/compare_backends.ts --fixture tests/indexing/corpus.json`
- failure mode: different workload, missing provenance, non-rebuildable index,
  unverified runtime, or gate dependency makes a backend ineligible
- completion evidence: precision/recall, provenance coverage, p95, RSS, disk,
  update locality, rebuild, and package/runtime receipts

## Known risks

LanceDB Node support must not be inferred as Bun support. FTS behavior and index
maintenance also need local measurement, not documentation-only claims.

## Human decisions

Human selects the Pareto winner. SQLite FTS5 is the declared fallback when
LanceDB does not win or cannot be packaged reliably.

## Completion evidence

Deleting either index and rebuilding leaves all non-retrieval gate/admission
outputs unchanged; both answer the same traceability queries.
