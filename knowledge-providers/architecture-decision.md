# Provider-neutral repository knowledge boundary

## Decision

Bettor selects capabilities through a closed provider contract. Product names are bindings behind that contract, not the architecture. Exact search and direct source read remain the zero-index control and final repository fact surface.

## Why the four tools are not a four-stage brain

Serena, GrepAI, Code-Graph-RAG, and Mem0 project different information, but each can be stale, incomplete, mis-scoped, or unavailable. Chaining all four for every task multiplies latency and creates four competing claims to authority. Routing is therefore task-specific and optional:

| Need | Candidate route | Required confirmation |
|---|---|---|
| known symbol or reference | symbol capability | current source and diagnostics |
| intent known, location unknown | semantic capability | exact source readback |
| cross-module impact | graph capability | source, manifest, build, test, or runtime evidence per edge |
| historical preference or decision | memory recall | current CONTEXT, ADR, issue, source, test, or receipt |
| exact path or token | `rg`, Git, direct read | the bytes themselves |

## Alternative matrix

No row is a global winner. Admission is per case family using precision/recall, staleness detection, provenance, latency, context volume, privacy, retention, cleanup, license, and interface stability.

| Capability | Initial candidate | Deterministic or mature alternatives | Unresolved admission question |
|---|---|---|---|
| symbol/edit plan | Serena | native LSP, SCIP/LSIF indexes, ast-grep structural queries | Does it improve reference/edit precision on supported Bettor languages without hiding workspace drift? |
| semantic retrieval | GrepAI | exact `rg`/Git control, Zoekt/Sourcegraph, local embedding index, compact repo map | Does it improve intent-location recall per tool/context cost while reliably rejecting a stale subject? |
| graph/impact | Code-Graph-RAG | LSP/SCIP references, build dependency graph, Joern/CPG, CodeQL, Kythe | Does it improve verified impact recall, especially across languages, without presenting heuristic edges as runtime facts? |
| project memory | Mem0 | Git/ADR/issue/LoopX event ledger, Graphiti-style temporal graph, Letta, LangGraph stores/checkpoints | Can it improve relevant-history recall while preserving namespace, provenance, expiry, deletion, and current-authority precedence? |

## Admission states

```text
CANDIDATE / NOT_EXERCISED
→ exact adapter and runtime identity
→ exact repository and index subject
→ positive, hollow, mutation, privacy, and cleanup controls
→ paired A/B against the deterministic control
→ PRIMARY, SECONDARY, EXPERIMENTAL, or REJECTED per case family
→ Human Admit
```

Installation, stars, documentation breadth, or an upstream benchmark cannot skip a state. The current registry deliberately stops at the first state.
