# Knowledge provider context

This is the bounded context for optional repository-knowledge providers. It does not replace root `CONTEXT.md`, repository law, source, tests, receipts, or Human Admit.

## Read order

```text
README.md
→ AGENTS.md or CLAUDE.md
→ ARCHITECTURE.md
→ root CONTEXT.md
→ knowledge-providers/host-state.md for the four-state measurement protocol
→ knowledge-providers/README.md
→ architecture-decision.md
→ registry.json and the selected provider manifest
→ the matching request/receipt schema
→ scripts/check_knowledge_providers.py
→ exact source, tests, receipt, issue, and PR
```

## Local terms

| Term | Meaning | Machine authority |
|---|---|---|
| provider projection | Rebuildable symbol, semantic, graph, or memory view over an exact repository subject | provider manifest plus index identity |
| subject | Repository, commit, and tree to which a query and receipt are bound | query request and receipt |
| candidate result | Provider-nominated evidence that still requires current source, manifest, test, or runtime readback | query receipt |
| memory proposal | Evidence-bound request to write or delete memory; never the mutation itself | memory proposal schema |
| authority ceiling | Operations and claims a provider can never perform at the Bettor boundary | provider manifest and validator |

## Authority order

```text
current Git/source/manifest/test/runtime receipt/current ADR/LoopX event
    > provider projection or memory hint
    > model prose
```

Provider availability, a dashboard, an MCP declaration, or an index hit does not create source truth, a gate verdict, state transition, promotion, or Human Admit.
