# Knowledge Providers — subject-bound projection contracts

This module decouples repository knowledge capabilities from Serena, GrepAI,
Code-Graph-RAG, Mem0, or any future provider implementation.

It does **not** make a provider authoritative. The repository source, current
manifests, current tests, exact runtime receipts, current ADRs, and Human Admit
remain above every provider result.

## Data flow

```text
exact repository commit/tree
+ typed capability request
+ provider manifest digest
        ↓
provider adapter / index projection
        ↓
bounded read-only result
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
optional memory projection
```

## Authorities

| Artifact | What it can prove | What it cannot prove |
|---|---|---|
| provider manifest | reviewed capabilities, source identity, limits, denied operations | runtime health or query correctness |
| query request | exact subject, capability, provider identity, bounds | that a provider executed |
| query receipt | what the adapter observed for the exact request | current source truth, TESTED status, gate PASS |
| memory proposal | a bounded write/supersede/delete proposal | canonical memory mutation or repository law |
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
→ one relevant contract schema
→ current source/tests/receipt
```

## Deterministic verification

```bash
python3 scripts/check_knowledge_providers.py
python3 scripts/check_knowledge_providers.py --selftest
sh tests/knowledge-providers/run-all.sh
```

The self-test contains one positive request/receipt pair, one memory proposal,
one hollow false-PASS receipt, and independent mutations for duplicate
providers, undeclared capability, authority escalation, false live claims,
path escape, subject drift, digest drift, stale index PASS, direct memory
write, absent provenance, provider-marked TESTED, unbounded output, graph write
surface, PASS without execution, and cleanup failure.

## Current evidence state

```text
contract/schema parsing      IMPLEMENTED
registry digest checks       IMPLEMENTED
positive fixture             PASS
hollow control               PASS
mutation controls            PASS
live Serena                  NOT_EXERCISED
live GrepAI                  NOT_EXERCISED
Code-Graph-RAG runtime       NOT_CONFIGURED
Mem0 runtime/writeback       NOT_CONFIGURED
```

Provider installation, MCP trust, persistent-store retention, graph rebuild,
memory writeback, merge, promotion, and production rollback remain Human
Admit.
