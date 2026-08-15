# `code-truth-graph-v2` module

Machine authority: [`module.json`](module.json)

This module provides `code-truth-graph.evidence/v2` as an unselected, MCP-denied projection layer over the existing `code-truth-graph.build/v1` capability.

## State Machine

```text
exact subject
→ analyzer identities/freshness
→ coverage accounting
→ evidence registry
→ nodes/edges
→ authority/plane validation
→ deterministic graph digest
→ FOUND | CONTESTED | NO_FLOW | UNKNOWN
```

## Public control port

```sh
python3 loop_wiki/code-truth-graph-v2/scripts/ctg_v2.py check
python3 loop_wiki/code-truth-graph-v2/scripts/ctg_v2.py selftest
```

## Authority ceiling

The graph is a rebuildable projection. Provider/model results remain T6 candidates; AST/LSP evidence cannot claim runtime observation; incomplete/stale/unsupported coverage cannot produce `NO_FLOW`. The module cannot edit code, write LoopX state, decide Gates, admit memory, perform Human Admit, merge or promote.

## Evidence

The selftest builds a real temporary Python Git subject with the stdlib AST reference adapter and exercises `FOUND`, complete-coverage `NO_FLOW`, incomplete-coverage `UNKNOWN`, plus planted subject, provenance, coverage, provider, runtime, path and digest failures. It does not claim live LSP/SCIP, sandbox, production or provider evidence.
