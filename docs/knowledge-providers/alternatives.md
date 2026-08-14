# Provider alternatives and selection boundaries

This is a decision matrix, not a winner declaration. No alternative is promoted
without a same-subject benchmark and negative controls.

## Symbol and reference layer

| Candidate | Strength | Main uncertainty | Bettor role |
|---|---|---|---|
| Serena + LSP | interactive symbol lookup, references, diagnostics, bounded edit plans | language-server completeness and workspace freshness vary | current candidate provider |
| SCIP indexers | portable symbol/reference index with stable data format | language/indexer coverage and update cost | benchmark alternative |
| native LSP client | smallest dependency surface and direct diagnostics | more adapter work and inconsistent server behavior | deterministic fallback |
| ast-grep / Tree-sitter | deterministic structural matching and rewrite | not full type/reference semantics | hard structural assertion lane |

## Semantic search layer

| Candidate | Strength | Main uncertainty | Bettor role |
|---|---|---|---|
| GrepAI | local semantic search and call-oriented candidates | embedding/index identity and negative-result completeness | current candidate provider |
| Zoekt | fast exact/regex-oriented indexed search | not semantic by itself | high-scale deterministic alternative |
| local embeddings + SQLite/Qdrant/LanceDB | fully controlled vector projection | chunking, model, freshness, and retrieval policy become Bettor-owned | build-vs-buy alternative |
| ripgrep/direct read | zero index ambiguity | higher tool and token cost on unknown concepts | authoritative fallback after readback |

## Graph and data-flow layer

| Candidate | Strength | Main uncertainty | Bettor role |
|---|---|---|---|
| Code-Graph-RAG | cross-language graph, structural and semantic query, data-flow candidates | heavier stores, parser coverage, mutable MCP surface | read-only admission candidate |
| Joern / CPG | mature code property graph and security/data-flow analysis | operational weight and language variance | security/data-flow benchmark alternative |
| SCIP + deterministic edges | transparent symbol graph with rebuildable provenance | fewer high-level graph features | canonical-core candidate |
| CodeQL | deep static analysis for supported languages | query authoring and licensing/CI constraints | optional verification lane |

## Memory layer

| Candidate | Strength | Main uncertainty | Bettor role |
|---|---|---|---|
| append-only LoopX/event ledger | exact provenance, replay, and state authority separation | retrieval UX must be built | canonical event source |
| Mem0 | ready-made extraction, retrieval, and managed/self-hosted options | model/storage identity, retention, writeback, managed-vs-OSS delta | optional projection candidate |
| Graphiti-style temporal graph | temporal/entity relations and conflict representation | operational and extraction complexity | temporal-memory benchmark alternative |
| SQLite/Postgres + FTS/vector projection | simple, inspectable, rebuildable | fewer automatic memory features | minimum production baseline |

## Admission test

A provider is not selected because it is popular or installed. It must show:

```text
same repository commit/tree
+ same query/task contract
+ exact provider/index identity
+ bounded output
+ source readback
+ positive and coverage-gap controls
+ cleanup and residue evidence
+ no authority escalation
```

Until then its state remains `CANDIDATE`, `NOT_EXERCISED`, or
`NOT_CONFIGURED`.
