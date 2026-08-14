# Code Truth Graph v2 — evidence planes, coverage, and UNKNOWN preservation

This terminal leaf extends the existing `code-truth-graph.build/v1` mechanism with a subject-bound evidence graph. It separates direct source, AST, LSP/SCIP, build/config, sandbox runtime, production runtime, and provider/model candidates instead of flattening them into one confidence score.

## Evidence planes

```text
T0_DIRECT_SOURCE       exact Git/source/manifest fact
T1_AST                 syntax/structure observed by a pinned parser
T2_LSP_SCIP            symbol/reference fact from a pinned semantic index
T3_BUILD_CONFIG        build/config/generated dependency observation
T4_SANDBOX_RUNTIME     disposable runtime/test observation
T5_PRODUCTION_RUNTIME  redacted production observation
T6_PROVIDER_CANDIDATE  Serena/GrepAI/Code-Graph-RAG/model retrieval candidate
```

## State Machine

```text
EXACT_SUBJECT_LOCKED
→ SOURCE_MANIFESTED
→ ANALYZER_IDENTITIES_BOUND
→ COVERAGE_DECLARED
→ EVIDENCE_REGISTERED
→ NODES_AND_EDGES_COMPILED
→ PROVENANCE_AND_AUTHORITY_CHECKED
→ GRAPH_DIGESTED
→ QUERY
   ├─ FOUND
   ├─ CONTESTED
   ├─ NO_FLOW       only under complete relevant coverage
   └─ UNKNOWN       missing/stale/unsupported coverage is preserved
```

## Authority ceiling

- T6 provider/model output is a candidate only; it cannot become `OBSERVED`, `TESTED`, or absence proof.
- AST proves syntax, not runtime behavior.
- LSP/SCIP proves indexed semantic relations within declared coverage, not production reachability.
- Runtime observations must reference exact test/runtime artifacts.
- `NO_FLOW` is allowed only when both nodes are in scope and every required analyzer is fresh, subject-matched, executed, and complete for the relevant language.
- The graph is a rebuildable projection. Source, tests, ADRs, runtime receipts, and future LoopX ledger events remain canonical.

## Executable reference

```sh
python3 loop_wiki/code-truth-graph-v2/scripts/ctg_v2.py check
python3 loop_wiki/code-truth-graph-v2/scripts/ctg_v2.py selftest
python3 loop_wiki/code-truth-graph-v2/scripts/ctg_v2.py build-python \
  --repo <repo> --commit <sha> --paths app.py util.py --output graph.json
python3 loop_wiki/code-truth-graph-v2/scripts/ctg_v2.py query \
  --graph graph.json --source <node-id> --target <node-id>
```

The Python AST adapter is a white-box fixture/reference adapter. It does not claim multi-language, LSP, sandbox, production, or provider health.

## Non-goals

No repository writeback, auto-fix, MCP exposure, provider activation, live LSP server, production trace ingestion, Human Admit, composition selection, merge, or release promotion occurs in this leaf.
