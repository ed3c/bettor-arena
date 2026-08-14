# `loopx-knowledge-foldback` module

`loopx-knowledge-foldback` owns the reverse half of the abstraction ladder — verified code change to proposed knowledge revision — under [`../../../loop_wiki/loopx-knowledge-foldback/`](../../../loop_wiki/loopx-knowledge-foldback/).

## Capabilities

```text
loopx.knowledge-foldback/v1
loopx.knowledge-revision-history/v1
```

Required capabilities:

```text
loopx.contracts/v1
loopx.ledger/v1
loopx.code-truth-graph/v2
arena.proof-kernel/v1
```

Terminal leaf of issue #61 and the semantic counterpart of `loopx-knowledge-compiler` (#70). Answers issue #71. Intentionally not selected in the shared `bettor-arena` composition by this leaf.

## Public control port

```sh
python3 loop_wiki/loopx-knowledge-foldback/scripts/foldback.py \
  <check|selftest|fold-back|admit|verify-receipt|rollback>
```

## State Machine

```text
BEFORE_AFTER_SUBJECTS_PINNED
→ DIFF_SYMBOL_EDGE_DELTA
→ TEST_RUNTIME_EVIDENCE_JOIN
→ AFFECTED_KNOWLEDGE_LOCATED
→ PATCH_CANDIDATES_COMPILED
→ CONTRADICTIONS_UNKNOWNS_PRESERVED
→ IDENTITY_DEPENDENCY_LOCATOR_GATES
→ CANDIDATE_FOLD_BACK_BUNDLE
→ HUMAN_ADMIT
→ REVISION_HISTORY_APPENDED
```

`fold-back` stops at the candidate bundle. `admit` is a separate call requiring an explicit decision per patch.

## Boundaries

- STATIC, TEST and RUNTIME are separate evidence classes and none implies another. A diff supports STATIC only; TEST needs a passing execution covering the symbol; RUNTIME needs an adapter-attested observation of it.
- An anchor pins the digest of the lines it cites, not just their numbers. Re-checking reports `FRESH`, `STALE_MOVED`, `STALE_CHANGED` or `ABSENT`, and nothing is repaired silently.
- A conclusion that flipped is `SUPERSEDE`, never `UPDATE`. Both directions are enforced.
- A similarity score surfaces a card for review and may not patch one.
- Code changes may not amend an `ADR`, `NORM` or `POLICY` card — that is a `CONFLICT`, and which side moves is a human's call.
- `MODEL_SUMMARY` is not an accepted anchor kind: a summary is a claim about evidence.
- History is append-only. Rejections stay, supersessions mark rather than replace, and rollback appends a reversal instead of deleting.
- A rerun appends nothing and reports `NOOP`; revision ids are content-addressed on the bundle and decisions they came from, not on a revision number.
- No canonical state write, gate verdict, permission widening, secret rotation, merge, promotion or rollback of a release occurs in this leaf.

## Evidence

```sh
sh loop_wiki/loopx-knowledge-foldback/tests/run-all.sh
```

Four schemas under a digest manifest, eight manifest mutations, ten positive properties, twenty-eight planted controls each asserting on the phrase its own rule raises, and five physical anchor controls that edit real files the four ways code actually changes and ask what the re-check finds — including code shifted ten lines down, which a line-number check calls fresh.
