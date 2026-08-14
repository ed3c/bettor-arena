# Knowledge-provider topology and authority ceilings

Owner: [`harness-wiki`](../SKILL.md). This module places Serena, GrepAI, Code-Graph-RAG and Mem0 behind capability interfaces instead of allowing four tools to become four competing truth stores.

## Selection rule

There is no single “best” provider across exact source, semantic recall, symbol edits, graph impact, runtime behavior and long-term memory. The production design is an authority ladder with fail-closed fallback:

```text
T0 exact source: git / rg / direct read
        ↓ candidates verified against current bytes
T1 structure: Tree-sitter / ast-grep / SCIP / LSP
        ↓ declared language, workspace and coverage
T2 semantic retrieval: GrepAI or equivalent
        ↓ index subject, freshness and source readback
T3 graph impact: deterministic graph projection / Code-Graph-RAG / Joern
        ↓ edge provenance and runtime uncertainty
T4 episodic memory: append-only LoopX capsule, optional Mem0/Graphiti projection
        ↓ freshness, scope, conflict and retention checks
T5 model synthesis
        ↓ never a repository authority by itself
current source / tests / runtime receipts / Human Admit
```

The output of a higher-numbered tier can nominate what to inspect. It cannot silently overrule a lower-numbered current authority.

## Provider roles

| Provider | Keep? | Exact role | Authority ceiling | Main risk / required control |
|---|---|---|---|---|
| Serena | yes | symbol lookup, references, diagnostics, bounded symbol edits through LSP or reviewed IDE backend | source candidate or edit plan until current body/workspace readback | overlapping file/shell/memory tools; language-server incompleteness; workspace drift |
| GrepAI | yes | local semantic candidate retrieval and call-oriented discovery | semantic candidate only; absence never proven by vector search | stale/wrong index, embedding drift, weak exactness; require index subject/freshness and `rg`/source verification |
| Code-Graph-RAG | experimental, read-only | cross-language graph/structural/data-flow candidate provider | graph candidate until source/manifest/test/runtime readback | heavy Memgraph/Qdrant stack, coverage gaps, destructive/write MCP surface; expose an allowlist only |
| Mem0 | optional projection | retrieve scoped incidents, preferences, rejected approaches and prior decisions | advisory memory; current repository authority always wins | cross-project leakage, stale facts, hidden model/embedding/store dependency, retention/delete policy |

### Serena

Serena is currently the strongest general symbol service among the four because it offers LSP-backed symbol retrieval, reference lookup, diagnostics and structured editing across many languages. Use it behind a `code.symbol.*` capability interface. Disable duplicate generic filesystem, shell and memory tools when the surrounding Harness already owns them. A successful MCP connection proves neither language coverage nor safe edit completeness.

Alternatives by use case:

- native editor/LSP clients when only read-only definitions/references are needed;
- SCIP for a stable cross-language symbol/reference index;
- ast-grep for deterministic structural matching and rewrite;
- Semgrep for rule-driven structural/security assertions;
- JetBrains APIs when the paid Serena backend's richer refactor semantics are admitted.

### GrepAI

GrepAI is useful because it is a local, lightweight semantic search and MCP candidate source. It should not replace `ripgrep`, AST matching or source readback. Run it after exact discovery when intent-based recall is useful, and record:

```text
repository identity
indexed commit/tree
included/excluded paths
embedding provider/model/dimension
index build/update time
query and returned source spans
readback status
```

Alternatives:

- Sourcegraph/Zoekt for large-scale exact and indexed code search;
- Qdrant/LanceDB-based custom indexes when you need a controlled schema;
- Continue/codebase retrieval for IDE integration;
- a repository-owned lexical+symbol retriever when reproducibility matters more than semantic breadth.

### Code-Graph-RAG

Code-Graph-RAG is feature-rich, not the best default canonical graph. Its standard deployment adds Memgraph and Qdrant, and its MCP can expose indexing, mutation, deletion and code-writing operations. Bettor should keep it in the child admission lane as a read-only provider with exact namespace, subject, parser coverage, freshness and cleanup receipts.

Normal Agent sessions should expose only reviewed read tools such as:

```text
list_projects
query_code_graph
get_code_snippet
read_file
list_directory
semantic_search
structural_search
flow_verdict
```

Keep index/update in a separate operator workflow. Never expose wipe/delete or code-write tools to a normal analysis session.

Stronger core alternatives:

- **SCIP** for deterministic symbol/reference interchange and index portability;
- **Joern** for code property graphs, data-flow and security analysis;
- **CodeQL** where its license and environment fit the project and query precision matters;
- a repository-owned Tree-sitter/LSP → JSONL/SQLite graph as the minimal auditable core.

Code-Graph-RAG can remain a comparative provider against that core rather than owning canonical Code Truth.

### Mem0

Mem0 is a strong general-purpose memory product, but it is not LoopX's canonical memory ledger. Its managed platform includes optimizations not identical to the open-source SDK, and normal configurations depend on an LLM, embeddings and a storage backend.

Canonical memory should remain:

```text
append-only execution/evidence events
→ deterministic capsule distillation proposal
→ provenance/freshness/privacy assertions
→ Human-reviewed or policy-admitted writeback
→ immutable capsule digest
```

Mem0 may index and retrieve admitted capsules. It may not automatically rewrite `CONTEXT.md`, ADRs, source, assertions, task state or Human decisions.

Alternatives:

- Graphiti for temporal, entity-linked provenance graphs;
- Letta for agent-owned memory experiments, with care not to import its state authority wholesale;
- plain SQLite/Postgres plus FTS/vector projections for the smallest reproducible control surface.

## Domain decoupling

Expose capabilities, not vendor names, to Skills:

```text
code.exact.search
code.symbol.lookup
code.symbol.references
code.structure.query
code.semantic.search
code.graph.impact
code.runtime.observe
memory.project.retrieve
memory.project.propose-writeback
```

The binding selects a provider and records its authority ceiling. Skills must define fallback behavior for every optional capability. A provider is `NOT_CONFIGURED` or `NOT_EXERCISED` until its exact runtime identity and canary receipt exist; installation on one developer machine is not portable truth.

## Current Bettor integration sequence

```text
repo-agent-native portable procedure in skills-shared
→ Bettor consumer binding and document routes
→ Serena / GrepAI / repo-context-pack configured candidate lanes
→ Code-Graph-RAG read-only child admission
→ Mem0 scoped-memory child admission
→ fresh-host A/B
→ Human Admit
```

Do not activate Code-Graph-RAG or Mem0 as a side effect of this documentation refactor. Their security, persistence, cost, cleanup, data-retention and mutation controls require independent receipts.
