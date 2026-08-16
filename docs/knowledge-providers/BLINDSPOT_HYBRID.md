# Blindspot Hybrid Consumer Binding

`bettor-arena` adopts the shared Blindspot Hybrid contract without making any optional provider a source of truth.

```text
question
→ grepai Intent Anchor / bounded runtime MCP exploration
→ SCIP indexed relations + Tree-sitter AST structure
→ Serena symbol-aware Agent executor
→ current source read-back + targeted tests
→ SQLite authoritative ledger
→ optional LanceDB projection
```

## Active architecture

- grepai locates plausible paths/symbols from fuzzy intent. It does not replace SCIP or Tree-sitter.
- SCIP is exact only for relations emitted by the pinned index and language indexer for the exact subject.
- Tree-sitter supplies AST shape, slicing boundaries, and parse/error coverage.
- Serena owns bounded symbol-aware reads, diagnostics, edit proposals, and separately authorized execution.
- SQLite owns normalized events, links, admission state, and replay identity.
- LanceDB is disposable similarity recall keyed to SQLite observations; deleting it must not change admission.
- source read-back admits source claims; targeted execution admits behavioral claims.

## Code-Graph-RAG retirement

Code-Graph-RAG is absent from the active composition. Existing provider/eval artifacts remain compatibility records until their registry migration is completed. They may not be selected by the new binding or used to self-admit a claim.

## Runtime boundary

The binding and checker do not install or invoke providers, start MCP, create databases, create branches, contact Forgejo, or merge/publish. Those effects need consumer-owned adapters and subject-bound runtime receipts.

## Verification

```bash
bash tests/blindspot-hybrid/verify.sh
```

The static receipt reports `runtime_state=NOT_EXERCISED`. Live provider/index/grammar/project health remains a separate canary.
