# Knowledge Providers bounded context

This context applies only to `docs/knowledge-providers/`,
`scripts/check_knowledge_providers.py`, and the corresponding module manifest
and tests.

## Vocabulary

| Term | Meaning |
|---|---|
| provider | An implementation that offers one or more typed knowledge capabilities |
| projection | Rebuildable index or memory view derived from canonical artifacts |
| subject | Exact repository, commit, and tree the request and result refer to |
| provider manifest | Reviewed source identity, capabilities, adapter state, limits, and authority ceiling |
| query request | Read-only, bounded request tied to one provider and exact subject |
| query receipt | Adapter observation tied to the same request, provider, subject, query digest, and index state |
| candidate result | A retrieval or graph result that still requires current-authority readback |
| memory proposal | Evidence-bound request to add, supersede, or delete memory; never an automatic write |
| freshness | Whether an index binds the exact requested commit/tree |
| authority conflict | Provider or memory output disagrees with source, manifest, test, receipt, or current ADR |

## Non-negotiable order

```text
current source / manifest / test / runtime receipt / current ADR
    > provider query result
    > memory proposal
    > model summary
```

## Provider selection

Select by capability and evidence contract, not by brand or benchmark prose.

1. Use deterministic exact search and direct read first when the symbol/path is
   known.
2. Use Serena for symbol/reference/diagnostic candidates.
3. Use GrepAI for semantic or callgraph candidates after index health is known.
4. Use Code-Graph-RAG only through an admitted read-only adapter with exact
   graph coverage and freshness.
5. Use Mem0 only for bounded recall or mutation proposals with provenance,
   retention, redaction, and scope.
6. Read back every promoted result against current authority.

## Named non-success states

- `NOT_CONFIGURED`: no reproducible adapter is admitted.
- `NOT_EXERCISED`: a manifest exists but no current live receipt exists.
- `ABSENT`: a required provider, index, or input is unavailable.
- `STALE_SUBJECT`: index does not bind the requested commit/tree.
- `SKIPPED_BY_POLICY`: the request would require a denied operation.
- `FAIL`: the adapter ran and disagreed with the contract.

None is normalized into PASS.

## Change contract

A provider change must include:

- exact upstream source commit and license;
- adapter identity and transport;
- capability and denied-operation delta;
- index subject/freshness/rebuildability impact;
- positive and planted negative controls;
- source-readback and authority ceiling;
- secret, retention, cleanup, and cross-project boundaries;
- rollback subject and Human Admit requirements.
