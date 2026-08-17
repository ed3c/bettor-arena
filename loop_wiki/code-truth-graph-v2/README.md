# Code Truth Graph v2 — Blindspots evidence loop

This module compiles subject-bound evidence without turning any analyzer, provider, graph, or vector index into source truth. Its deterministic route is:

```text
exact source / Git subject
→ GrepAI candidate anchors
→ SCIP/LSP semantic facts when exact coverage exists
→ Tree-sitter structural facts when grammar coverage exists
→ SQLite subject-bound Blindspots ledger
→ exact-source readback
→ bounded context-funnel traversal
→ target source + dependency signatures + downstream callsites + tests
```

Code-Graph-RAG is **retired from the active route**. Historical provider/decision evidence may remain explicitly marked `REJECTED / ABSENT`; it is not a T6 candidate, runtime dependency, evaluator participant, or queue prerequisite.

## Evidence planes

```text
T0_DIRECT_SOURCE       exact Git/source/manifest fact
T1_AST                 syntax/structure observed by a pinned parser
T2_LSP_SCIP            symbol/reference fact from a pinned semantic index
T3_BUILD_CONFIG        build/config/generated dependency observation
T4_SANDBOX_RUNTIME     disposable runtime/test observation
T5_PRODUCTION_RUNTIME  redacted production observation
T6_PROVIDER_CANDIDATE  Serena/GrepAI/model retrieval candidate only
```

## Blindspots State Machine

```text
EXACT_SUBJECT_LOCKED
→ SOURCE_MANIFESTED
→ ANALYZER_IDENTITIES_BOUND
→ COVERAGE_DECLARED
→ NORMALIZED OBSERVATIONS IMPORTED
→ SQLITE LEDGER DIGESTED
→ CROSS-LENS QUERY
   ├─ fresh support + fresh denial → CONTESTED
   ├─ source-admissible support   → FOUND
   ├─ complete fresh mandatory coverage + no support → NO_FLOW
   └─ stale/partial/missing/unread-back/candidate-only → UNKNOWN
→ EXPORT / DELETE / REBUILD
→ WAL/SHM/TEMP RESIDUE CHECK
```

`NO_FLOW` is deliberately expensive: every lens named by the query must have `COMPLETE` and `FRESH` coverage for the language/subject. An empty GrepAI result, unsupported grammar, stale SCIP workspace, partial parse, missing source readback, or provider outage can never become absence proof.

## Context-funnel State Machine

The context compiler consumes the SQLite ledger but independently binds the requested Git subject and re-reads promoted source paths from that exact commit:

```text
REQUEST
→ COMMIT/TREE VERIFY
→ DATABASE SUBJECT CAS
→ REQUIRED-LENS FRESHNESS CHECK
→ SOURCE DIGEST READBACK
→ BOUNDED BIDIRECTIONAL TRAVERSAL
→ CONTEXT PLAN
   ├─ target_full_source
   ├─ dependency_signatures
   ├─ downstream_callsites
   ├─ tests
   └─ candidate_anchors
→ PASS | UNKNOWN | REFUSED
```

A candidate anchor can help locate context but never enters the fact traversal without source confirmation. Stale coverage, source drift, missing target source, subject mismatch, depth/node/path/output overflow, corrupt SQLite, and invalid input remain distinct failures. The compiler is read-only and cannot advance LoopX state.

## SQLite evidence contract

Each database binds exactly one repository/commit/tree. A second subject is rejected rather than mixed into the same ledger. Every observation has a content-addressed ID and records:

```text
path + source digest + language
lens + exact tool/index/grammar identity
source + target + relation
source-readback state
optional bounded span/note
```

SQLite is a rebuildable evidence projection. Source, tests, ADRs, runtime receipts, and LoopX ledger events remain higher authority. No provider may self-admit a claim.

## Executable ports

Existing JSON evidence graph:

```sh
python3 loop_wiki/code-truth-graph-v2/scripts/ctg_v2.py check
python3 loop_wiki/code-truth-graph-v2/scripts/ctg_v2.py selftest
```

SQLite Blindspots ledger:

```sh
python3 loop_wiki/code-truth-graph-v2/scripts/blindspots.py selftest
python3 loop_wiki/code-truth-graph-v2/scripts/blindspots.py import \
  --db /tmp/blindspots.sqlite --bundle observations.json
python3 loop_wiki/code-truth-graph-v2/scripts/blindspots.py query \
  --db /tmp/blindspots.sqlite --source A --target B --language python \
  --required-lens source --required-lens grepai \
  --required-lens scip-lsp --required-lens tree-sitter
```

Bounded context compiler:

```sh
python3 loop_wiki/code-truth-graph-v2/scripts/context_funnel.py compile \
  --repo . \
  --db /tmp/blindspots.sqlite \
  --request request.json \
  --output context-plan.json
```

The Python AST adapter remains a white-box reference adapter. Static tests do **not** claim live SCIP/LSP or Tree-sitter execution.

## Authority ceiling

- Provider/model output is candidate evidence only until current-source readback.
- AST proves syntax, not runtime behavior.
- LSP/SCIP proves emitted semantic relations only within declared exact coverage.
- Runtime observations must bind exact test/runtime artifacts.
- `NO_FLOW` requires fresh complete mandatory coverage; otherwise the answer is `UNKNOWN`.
- SQLite and the context compiler cannot write LoopX task state, admit a release, merge, publish, or activate a provider.

## Non-goals

No repository writeback, auto-fix, generic shell/MCP exposure, provider installation, live SCIP/LSP activation, live Tree-sitter grammar claim, production trace ingestion, composition selection, merge, release promotion, or destructive rollback occurs in this module.
