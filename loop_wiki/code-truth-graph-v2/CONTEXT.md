# CONTEXT.md — Code Truth Graph v2

## Read order

```text
README.md
→ contracts/manifest.json
→ scripts/ctg_v2.py
→ tests/run-all.sh
→ .arena/modules/code-truth-graph-v2/module.json
→ exact issue #69 and PR metadata
```

## Stable vocabulary

- **evidence plane**: how an edge arrived; it fixes the maximum claim strength.
- **analyzer identity**: pinned parser/LSP/index/runtime/provider digest plus exact subject and freshness.
- **coverage**: languages and paths actually parsed/indexed/observed, including exclusions and missing reasons.
- **candidate edge**: useful retrieval hint that still requires current-source or runtime readback.
- **NO_FLOW**: checked absence under complete relevant coverage.
- **UNKNOWN**: coverage, freshness, subject, parser, semantic index, or runtime evidence is insufficient.

## Authority

```text
source/tests/ADR/runtime receipts
    > T0–T5 evidence-bound graph projection
    > T6 provider/model candidates
```

A graph result never writes LoopX state, modifies source, decides a Gate, admits memory, or performs Human promotion.
