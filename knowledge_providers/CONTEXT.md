# CONTEXT.md — Knowledge Provider Integration

## Read order

For tasks under `knowledge_providers/`:

1. repository [`../CONTEXT.md`](../CONTEXT.md);
2. harness contract [`../.agents/skills/harness-wiki/modules/knowledge-provider-topology.md`](../.agents/skills/harness-wiki/modules/knowledge-provider-topology.md);
3. this file;
4. [`README.md`](README.md);
5. [`registry/providers.json`](registry/providers.json);
6. only the contract or test file needed for the current task.

Do not preload provider source repositories, generated indexes, MCP logs, vector stores, graph stores, or memory contents.

## Scope

This module owns the provider-neutral boundary for:

```text
symbolic code intelligence
semantic retrieval
code graph retrieval
episodic memory projection
```

It does not own:

```text
Git/source truth
Code Truth Graph canonical artifacts
LoopX event/state transitions
hard-gate verdicts
runtime-env provider installation
provider credentials
Human Admit, promotion, or rollback
```

## Invariants

- All repository queries bind exact `repository + commit + tree`.
- Every successful receipt binds a provider source ref/digest, adapter digest, index digest, and canonical request digest.
- Provider results are non-canonical projections and require source verification.
- Code-provider mutation is denied.
- Episodic mutation is proposal-only.
- Candidate providers remain `NOT_EXERCISED` until a live, immutable runtime binding and canary exist.
- Provider absence, stale index, empty semantic recall, and execution failure are distinct outcomes.
- Skills request capabilities; host/runtime bindings select providers.

## Local commands

```bash
sh knowledge_providers/verify.sh
sh knowledge_providers/selftest.sh
python3 -S knowledge_providers/src/provider_contract.py registry \
  --registry knowledge_providers/registry/providers.json
```

## Change rule

Changing schema fields, capability names, status semantics, authority ceilings, or the meaning of a successful receipt requires an interface-version bump in `.arena/modules/knowledge-provider-integration/module.json`.
