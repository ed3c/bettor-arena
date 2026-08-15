# LoopX Knowledge Compiler v1

Compiles a pinned Notes Repo subject through the forward half of the abstraction
ladder and stops at a candidate scaffold. Terminal leaf of issue #61, on
LoopX Contract v1 (#62) and Code Truth Graph v2 (#69). Answers issue #70.

```text
raw note / transcript / diagram / source
→ source manifest      (locator, digest, dependency key)
→ assertion graph      (claim kind, verification state, contradictions, unknowns)
→ knowledge cards      (content-derived ids, typed links)
→ system spec IR       (components, invariants, one acceptance case per assertion)
→ CodeOp IR            (target, precondition, validation, rollback)
→ scaffold candidate   (rendered into a disposable leased tree)
→ CANDIDATE_RECEIPT    → Human Admit or revise
```

## Public port

```sh
python3 loop_wiki/loopx-knowledge-compiler/scripts/knowledge.py \
  <check|selftest|compile|verify-receipt>
```

Exit `0` ok, `2` a checked invariant disagreed, `64` the input is unusable.

There is no `apply`, no `merge` and no `promote`. The compiler renders a
candidate; applying it is Human Admit, and a subcommand that could do it would
make the boundary a matter of who remembers not to type it.

## What this module refuses, and why

**A source with no locator may carry no metadata.** A path, a timestamp or a
version that nobody read out of the source is a fabrication with a citation
attached, and downstream it is indistinguishable from one that was read.

**Corroboration is counted by dependency key, not by row.** Four notes quoting
one upstream RFC are one piece of evidence. `CORROBORATED` requires two distinct
dependency keys, so a claim cannot rise on the same source quoted twice.

**Claim kind caps verification state.** An `INFERENCE` cannot reach
`VERIFIED_BY_EXECUTION`: whatever was executed was a statement, not the
conclusion drawn from it. `VERIFIED_BY_EXECUTION` requires a receipt with a
command and a zero exit; prose asserting that something was tested is prose.

**Unknowns stay unknown.** An `UNKNOWN` assertion may cite no source and carry
no resolution, and every unknown must be carried forward into the spec's
`open_unknowns`. An unknown that stops being visible has been answered by
omission.

**Contradictions are escalated, never reconciled.** A contradiction record may
only be `OPEN` or `ESCALATED_TO_HUMAN`. A compiler that picks a winner has
deleted one side of the disagreement, and the graph then looks consistent
because the evidence was removed rather than settled.

**Card ids are derived from content.** `card-<sha256[:16]>` over the canonical
key and its assertions. There is no code path that allocates an id, so a rerun
on the same sources cannot produce a different one and silently retarget every
reference.

**Independent cases are not compressed.** A requirement derived from *n*
assertions must carry *n* acceptance cases. Folding three situations into
"handle errors" makes two of them untestable, and the scaffold that follows
renders one code path and looks complete.

**Every CodeOp has a target selector, a precondition, a validation and a
rollback.** A `CREATE` must require its path to be absent, or it is an overwrite
wearing the wrong intent. An operation that changes a public interface must
carry an explicit version decision — not because the compiler knows the right
bump, but because a scaffold that quietly alters a published symbol ships a
breaking change that reads like an addition.

**The notes subject is an immutable commit.** `ref_kind` must be
`IMMUTABLE_COMMIT`. A branch names a different tree tomorrow, and every claim
traced back to it loses its source without saying so.

**Nothing outside the notes fills a gap.** `external_knowledge_admitted` is
`false` in the contract manifest and checked on every run.

## Evidence

```sh
sh loop_wiki/loopx-knowledge-compiler/tests/run-all.sh
```

Six schemas under a digest manifest, seven manifest mutations, seven positive
properties, twenty-nine planted controls, and a **physical** control group.

The physical group is the part a fixture cannot answer. It builds real trees and
renders real files, then asks the filesystem — not the exception — what happened:

- a clean render writes only under the leased root and leaves a sentinel file
  outside it untouched (without this, a renderer that wrote nothing would pass
  every escape control below and prove nothing);
- `../../outside.py` is refused **and** absent from the parent directory;
- a symlink planted inside the output tree pointing outside it is refused, and
  nothing leaks into the target — every string prefix check passes this case,
  and only path resolution catches it;
- an absolute target path is refused, because `Path("/leased") / "/absolute"`
  discards the left side silently.

Each planted control asserts on the substring its own rule raises, so a control
satisfied by an unrelated error further up the pipeline fails rather than passes.
`scripts/probe_controls.py` prints the actual messages for a reader to check the
needles are not themselves vacuous.

## Boundaries

- The receipt state is `CANDIDATE` and `admit_required` is `true`. Both are
  checked, and the contract manifest pins `terminal_state` to
  `CANDIDATE_RECEIPT` and `admit_authority` to `HUMAN`.
- `generated-tests-executed` is recorded as `NOT_EXERCISED`, not omitted. This
  leaf renders a candidate; it does not run the generated code, and a receipt
  that left the gate out would read as though it had.
- Compiled candidate trees are not checked in. The default compile renders into
  a disposable tree and removes it, which the suite verifies by running from an
  empty directory and requiring it to stay empty.
- No canonical state write, gate verdict, merge, promotion, rollback, permission
  widening or secret access occurs in this leaf.
