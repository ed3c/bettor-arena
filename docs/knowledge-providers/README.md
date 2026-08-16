# Knowledge Providers — subject-bound projection contracts

This module decouples repository knowledge capabilities from Serena, GrepAI,
Mem0, deterministic compiler/AST projections, or any future implementation.
The historical Code-Graph-RAG manifest remains registered only as a rejected
migration/audit record; it is not an active provider selection.

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

The active code-intelligence funnel is deliberately split by role:

```text
natural-language intent
→ GrepAI candidate anchors
→ current-source readback
→ SCIP + SQLite exact-subject Def/Ref and impact projection when admitted
→ Tree-sitter AST/CST slicing and syntax checks
→ Serena bounded execution or deterministic fallback
→ optional LanceDB subject-bound candidate retrieval
```

No provider may combine those roles into an unverified second graph. A vector
or semantic match never proves type identity, call edges, code absence, task
state, or merge safety.

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
- GrepAI: `search.semantic`, `callgraph.trace` as candidate discovery only.
- Deterministic code intelligence: SCIP/LSP Def/Ref/type/call relations plus
  SQLite subject and coverage metadata; Tree-sitter provides structural slices.
  These are repository controls, not a provider authority class.
- Mem0: `memory.recall`, `memory.write-proposal`,
  `memory.delete-proposal`.
- Code-Graph-RAG: historical capability vocabulary remains in its immutable
  manifest, but admission is `REJECTED`, runtime is `ABSENT`, and it cannot be
  selected by a task or Worker.

Serena, GrepAI, and Mem0 remain subject-bound candidates until separate live
receipts exist. Code-Graph-RAG is not a candidate.

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
SCIP + SQLite exact-subject runtime    NOT_EXERCISED
Tree-sitter slicing runtime           NOT_EXERCISED
LanceDB subject-bound retrieval       NOT_EXERCISED
Code-Graph-RAG admission              REJECTED
Code-Graph-RAG runtime                ABSENT
Mem0 runtime/writeback                NOT_CONFIGURED
cross-provider winner                 NOT_EXERCISED
```

Provider installation, MCP trust, persistent-store retention, graph rebuild,
memory writeback, merge, promotion, and production rollback remain Human
Admit.
