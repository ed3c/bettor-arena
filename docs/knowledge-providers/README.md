# Knowledge Providers — subject-bound projection contracts

This module decouples repository knowledge capabilities from Serena, GrepAI,
Code-Graph-RAG, Mem0, or any future implementation.

It does **not** make a provider authoritative. Current source, manifests,
tests, exact runtime receipts, current ADRs, LoopX state transitions, and
Human Admit remain above every provider result.

## Data flow

```text
exact repository commit/tree
+ typed capability request
+ provider manifest digest
        ↓
provider adapter / rebuildable index projection
        ↓
bounded read-only candidate result
        ↓
subject-bound query receipt
        ↓
source / manifest / test / runtime readback
        ↓
downstream hard assertion
```

Memory uses a separate proposal lane:

```text
observed incident / preference / rejected approach
        ↓
knowledge-memory-proposal/v1
        ↓
provenance + subject + retention + redaction checks
        ↓
Human Admit when durable mutation is requested
        ↓
optional rebuildable memory projection
```

## Authorities

| Artifact | What it can prove | What it cannot prove |
|---|---|---|
| provider manifest | reviewed capabilities, source identity, limits, denied operations | runtime health or query correctness |
| query request | exact subject, capability, provider identity, bounds | that a provider executed |
| query receipt | what the adapter observed for the exact request | current source truth, `TESTED`, hard-gate PASS |
| memory proposal | a bounded add/supersede/delete proposal | canonical memory mutation or repository law |
| eval report | paired metrics and hard-gate outcome for exact observations | automatic admission or a universal winner |
| source/test/runtime receipt | current mechanism or executed result for its exact subject | Human Admit or future availability |

## Public capability vocabulary

- Serena: `symbol.lookup`, `symbol.references`, `symbol.rename-plan`,
  `diagnostics.read`.
- GrepAI: `search.semantic`, `callgraph.trace`.
- Code-Graph-RAG: `graph.neighbors`, `graph.path`, `graph.impact`,
  `structural.search`, `dataflow.trace`.
- Mem0: `memory.recall`, `memory.write-proposal`,
  `memory.delete-proposal`.

All current providers are `CANDIDATE`; live execution remains
`NOT_EXERCISED` or `NOT_CONFIGURED`.

## Read order

```text
AGENTS.md / CLAUDE.md
→ ARCHITECTURE.md
→ root CONTEXT.md
→ docs/agents/domain.md
→ this README
→ CONTEXT.md
→ registry.json
→ one provider manifest
→ one relevant query/memory contract
→ evals/README.md when comparing implementations
→ current source/tests/receipt
```

## Deterministic verification

Provider query and memory contracts:

```bash
python3 scripts/check_knowledge_providers.py
python3 scripts/check_knowledge_providers.py --selftest
sh tests/knowledge-providers/run-all.sh
```

Provider-versus-control admission evaluator:

```bash
python3 scripts/evaluate_knowledge_providers.py
python3 scripts/evaluate_knowledge_providers.py --selftest
python3 scripts/check_knowledge_provider_module.py
sh tests/knowledge-provider-evals/run-all.sh
```

The query/memory self-test covers positive, hollow, and independent mutations
for provider identity, capability, authority, freshness, path, state, memory,
output bounds, and cleanup. The admission evaluator adds complete paired
coverage, fixture/live scope separation, source-readback, `UNKNOWN`
preservation, resource budgets, and memory-conflict controls.

## Current evidence state

```text
query/memory contract validator       IMPLEMENTED
provider registry digest checks       IMPLEMENTED
admission evaluation schemas          IMPLEMENTED on feature branch
paired fixture evaluator              IMPLEMENTED on feature branch
exact-head evaluation CI              NOT_EXERCISED
live Serena                           NOT_EXERCISED
live GrepAI                           NOT_EXERCISED
Code-Graph-RAG runtime                NOT_CONFIGURED
Mem0 runtime/writeback                NOT_CONFIGURED
cross-provider winner                 NOT_EXERCISED
```

Provider installation, MCP trust, persistent-store retention, graph rebuild,
memory writeback, merge, promotion, and production rollback remain Human
Admit.
