# Knowledge Providers bounded context

This context applies only to `docs/knowledge-providers/`, the corresponding
provider/evaluation scripts, the module manifest, and proof-kernel-owned test
wrappers.

## Vocabulary

| Term | Meaning |
|---|---|
| provider | An implementation that offers one or more typed knowledge capabilities |
| projection | Rebuildable index or memory view derived from canonical artifacts |
| subject | Exact repository, commit, and tree a request, observation, and report refer to |
| provider manifest | Reviewed source identity, capabilities, adapter state, limits, and authority ceiling |
| query request | Read-only, bounded request tied to one provider and exact subject |
| query receipt | Adapter observation tied to the same request, provider, subject, query digest, and index state |
| eval participant | A provider or independent deterministic control evaluated through the same packet contract |
| eval case | Exact subject, query, paired participants, oracle, hard gates, and budgets |
| candidate result | Retrieval or graph output that still requires current-authority readback |
| memory proposal | Evidence-bound request to add, supersede, or delete memory; never an automatic write |
| freshness | Whether an index binds the exact requested commit/tree |
| authority conflict | Provider or memory output disagrees with source, manifest, test, receipt, or current ADR |
| fixture-only | Synthetic evidence that tests the evaluator and cannot establish live provider state |

## Non-negotiable order

```text
current source / manifest / test / runtime receipt / current ADR
    > provider query result
    > memory proposal
    > model summary
```

An evaluator report can compare evidence. It cannot reorder this authority
chain or admit a provider.

## Provider selection

Select by capability and evidence contract, not by brand or benchmark prose.

1. Use deterministic exact search and direct read first when the path or token
   is known.
2. Use Serena for symbol/reference/diagnostic candidates.
3. Use GrepAI for semantic or callgraph candidates after index health is known.
4. For cross-module impact, combine exact source readback with admitted
   SCIP/LSP semantic facts and Tree-sitter structural coverage in the
   subject-bound Blindspots/SQLite evidence loop. Missing or stale coverage is
   `UNKNOWN`. Code-Graph-RAG is historical `RETIRED` evidence only.
5. Use Mem0 only for bounded recall or mutation proposals with provenance,
   retention, redaction, and scope.
6. Read back every promoted result against current authority.
7. Compare each provider with an independent control on the same immutable
   subject; do not omit failed participants.

## Named non-success states

- `NOT_CONFIGURED`: no reproducible adapter is admitted.
- `NOT_EXERCISED`: a manifest exists but no current live receipt exists.
- `ABSENT`: a required provider, index, or input is unavailable.
- `STALE_SUBJECT`: index does not bind the requested commit/tree.
- `SKIPPED_BY_POLICY`: the request would require a denied operation.
- `FAIL`: the adapter ran and disagreed with the contract.

None is normalized into PASS.

## Change contract

A provider or evaluation change must include:

- exact upstream source commit and license;
- adapter identity and transport;
- capability and denied-operation delta;
- index subject/freshness/rebuildability impact;
- exact provider/control pairing and case subject;
- positive, hollow, and planted mutation controls;
- source-readback, coverage, and authority ceiling;
- secret, retention, cleanup, and cross-project boundaries;
- rollback subject and Human Admit requirements.

Changing `fixture_only` to permit live evidence is a separate Human-admitted
contract change. It must pin adapter, index/storage, runtime, privacy,
retention, cleanup, and canary identities first.
