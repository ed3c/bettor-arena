# `loopx-knowledge-compiler` module

`loopx-knowledge-compiler` owns the forward half of the abstraction ladder — pinned notes to candidate scaffold — under [`../../../loop_wiki/loopx-knowledge-compiler/`](../../../loop_wiki/loopx-knowledge-compiler/).

## Capabilities

```text
loopx.knowledge-compiler/v1
loopx.scaffold-candidate/v1
```

Required capabilities:

```text
loopx.contracts/v1
loopx.code-truth-graph/v2
arena.proof-kernel/v1
```

Terminal leaf of issue #61, on Contract v1 (#62) and Code Truth Graph v2 (#69). Answers issue #70. Intentionally not selected in the shared `bettor-arena` composition by this leaf.

## Public control port

```sh
python3 loop_wiki/loopx-knowledge-compiler/scripts/knowledge.py \
  <check|selftest|compile|verify-receipt>
```

## State Machine

```text
NOTES_SUBJECT_PINNED
→ SOURCE_INVENTORY
→ ASSERTIONS_COMPILED
→ CONFLICTS_UNKNOWNS_SCHEDULED
→ CARDS_COMPILED
→ SYSTEM_SPEC_EMITTED
→ CODEOPS_PLANNED
→ SCAFFOLD_RENDERED_IN_DISPOSABLE_TREE
→ STATIC_TEST_GATES
→ CANDIDATE_RECEIPT
→ HUMAN ADMIT OR REVISE
```

The last transition is not in this module. There is no `apply`, `merge` or `promote` subcommand.

## Boundaries

- A natural-language claim stays a source statement, inference, hypothesis or norm. It does not become a code fact because a scaffold was generated from it, and the claim kind caps the verification state it can reach.
- Corroboration is counted by dependency key. Four notes quoting one upstream document are one piece of evidence, not four.
- Unknowns carry no resolution and are carried forward into the spec; contradictions are escalated, never reconciled. A compiler that picked a winner would delete one side of the disagreement.
- Card ids are derived from content, so the same sources recompile to the same ids and no reference silently retargets.
- The notes subject must be an immutable commit. A branch names a different tree tomorrow.
- Every write is resolved against the leased output root, including after symlink resolution. This is checked physically, on real trees, not asserted in a fixture.
- The receipt state is `CANDIDATE` and requires Human Admit. `generated-tests-executed` is recorded as `NOT_EXERCISED` rather than omitted.
- No canonical state write, gate verdict, permission widening, secret rotation, merge, promotion or rollback occurs in this leaf.

## Evidence

```sh
sh loop_wiki/loopx-knowledge-compiler/tests/run-all.sh
```

Six schemas under a digest manifest, seven manifest mutations, seven positive properties, twenty-nine planted controls each asserting on the phrase its own rule raises, and four physical lease controls that build real trees and ask the filesystem what happened — including a symlink escape that every string prefix check would call clean.
