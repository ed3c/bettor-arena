# Knowledge Provider Integration

This module prevents code-intelligence and memory products from becoming independent truth authorities.

## Decision

Bettor integrates capabilities, not vendor-native tool surfaces:

```text
exact repository commit/tree
+ typed read-only query or evidence-bound memory proposal
+ provider manifest
        ↓
provider adapter / index projection
        ↓
subject-bound receipt
        ↓
current source, AST/LSP, tests, runtime evidence, or Human Admit
```

A provider may nominate source spans, symbols, graph paths, or prior incidents. It cannot mark a claim `TESTED`, advance LoopX state, waive a hard gate, promote a release, or sign Human Admit.

## Current state

The production registry contains four **candidates**:

| Provider | Upstream role | Bettor capability lane | Bettor authority | Current state |
|---|---|---|---|---|
| Serena | LSP/IDE-style symbolic retrieval and editing | `symbol.lookup`, `symbol.references`, `symbol.rename_plan` | read-only result or rename plan | `CANDIDATE · NOT_EXERCISED` |
| GrepAI | local semantic search and call-graph discovery | `search.semantic`, `callgraph.trace` | read-only candidate spans/relations | `CANDIDATE · NOT_EXERCISED` |
| Code-Graph-RAG | Tree-sitter/graph/semantic/structural code analysis | `graph.neighbors`, `graph.path`, `graph.impact`, `structural.search` | experimental read-only graph projection | `CANDIDATE · NOT_EXERCISED` |
| Mem0 | long-term agent memory | `memory.recall`, `memory.write_proposal`, `memory.delete_proposal` | recall plus proposal-only mutation | `CANDIDATE · NOT_EXERCISED` |

The registry records source-reported license and capability evidence from the official repositories:

- Serena: <https://github.com/oraios/serena> — MIT.
- GrepAI: <https://github.com/yoanbernabeu/grepai> — MIT.
- Code-Graph-RAG: <https://github.com/vitali87/code-graph-rag> — MIT.
- Mem0: <https://github.com/mem0ai/mem0> — Apache-2.0.

No immutable source ref, runtime-env module, MCP process, database, model call, index build, or live canary is created by this module.

## Canonical authority ladder

```text
T0  Git bytes / direct file read / exact lexical match
T1  parser, AST, LSP, SCIP or deterministic structural artifact
T2  semantic retrieval projection
T3  graph projection
T4  episodic-memory projection
T5  model synthesis
        ↓
independent tests / runtime receipts / Human Admit
```

Higher tiers improve recall and planning. They cannot silently overrule a lower, fresher authority.

## Contracts

| Contract | Purpose |
|---|---|
| `provider-registry/v1` | candidate/bound provider identity, capability, authority ceiling, projection semantics and execution status |
| `query-request/v1` | exact repository subject, read-only operation, bounded query and provider requirement |
| `query-receipt/v1` | exact request digest, provider/adapter/index identity, staleness, bounded results and non-canonical status |
| `memory-proposal/v1` | evidence-bound ADD/UPDATE/DELETE proposal with invalidation conditions and explicit Human Admit |

The verifier rejects:

- duplicate provider ids;
- unknown or undeclared capabilities;
- direct code mutation or canonical memory writes;
- LoopX/gate/promotion/Human-Admit authority;
- a `BOUND`/`TESTED` provider without immutable source identity;
- a candidate claiming live `PASS`;
- subject, index, or query-digest drift;
- stale index represented as successful execution;
- absolute/traversal result paths;
- unbounded result sets;
- memory proposals without evidence or invalidation rules.

## Why native MCP tools are not exposed directly

The upstream products have broader surfaces than Bettor needs. Examples include symbolic editing, generic file/shell tools, graph mutation/deletion, database wipe, and direct memory add/delete operations. Normal Agent sessions receive a capability allowlist rendered by a future adapter. Operator-only indexing and destructive maintenance remain separate workflows.

The current module exposes no MCP tool and changes no `.runtime-env/requirements.json`. A later runtime-env slice must add immutable modules such as:

```text
code-intelligence-symbolic-serena
code-intelligence-semantic-grepai
code-intelligence-graph-code-graph-rag
memory-episodic-mem0
```

Only after those modules, policies, workloads, source refs, adapter digests, and canaries exist may Bettor change a provider from `CANDIDATE`.

## Is the selected four-tool stack “best”?

No winner is established. The tools solve different problems and have not been evaluated under one subject, workload, budget, language matrix, freshness contract, or mutation suite.

The required comparison baseline is in [`docs/decision-record.md`](docs/decision-record.md). The likely production shape is:

- Serena or direct LSP/SCIP for symbolic navigation;
- exact search (`rg`/Zoekt) plus an optional semantic provider such as GrepAI;
- repository-owned Code Truth Graph as canonical projection, with Code-Graph-RAG or Joern as comparative providers;
- append-only LoopX/evidence ledger as canonical memory, with Mem0 or Graphiti as optional retrieval projections.

## Verify

```bash
sh knowledge_providers/verify.sh
sh knowledge_providers/selftest.sh
```

The selftest contains three positive controls and seventeen independent planted defects. Passing these tests proves the contract logic only. It does not prove any candidate provider is installed or works against a real repository.
