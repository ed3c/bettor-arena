# CONTEXT.md — LoopX Decision Memory

## Read order

```text
README.md
→ contracts/manifest.json
→ scripts/memory.py
→ tests/run-all.sh
→ .arena/modules/loopx-decision-memory/module.json
→ exact issue #42 and PR metadata
```

## Vocabulary

- **proposal**: untrusted candidate produced from observable evidence.
- **candidate capsule**: deterministic output after a Human admission receipt; not yet persisted.
- **canonical authority**: current source, tests, ADR, runtime receipts and future LoopX memory ledger.
- **projection**: optional rebuildable Mem0/vector/graph index; never canonical.
- **conflict**: incompatible current authority or evidence; it remains visible as `CONTESTED`.
- **expiry**: a schedulable time/subject boundary after which retrieval must not treat a capsule as current.

## Non-negotiable boundary

```text
Worker proposes
Validator checks
Human admits
LoopX reducer persists
Provider indexes
```

No model or provider may collapse those roles.
