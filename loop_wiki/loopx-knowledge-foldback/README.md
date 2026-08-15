# LoopX Knowledge Fold-back v1

Compiles a verified code change into **proposed** knowledge revisions and stops
at Human Admit. The reverse half of the abstraction ladder, and the semantic
counterpart of `loopx-knowledge-compiler` (#70). Terminal leaf of issue #61, on
Code Truth Graph v2 (#69) and the LoopX evidence subjects (#62/#63). Answers #71.

```text
verified code/test/runtime change
→ exact diff and symbol/edge delta
→ claim/evidence extraction         (STATIC / TEST / RUNTIME, kept apart)
→ affected card lookup              (by anchor, never by similarity alone)
→ revision / supersession / conflict / unknown proposal
→ source dependency and locator gates
→ candidate knowledge patch
→ Human Admit
→ immutable fold-back receipt
```

## Public port

```sh
python3 loop_wiki/loopx-knowledge-foldback/scripts/foldback.py \
  <check|selftest|fold-back|admit|verify-receipt|rollback>
```

Exit `0` ok, `2` a checked invariant disagreed, `64` the input is unusable.

`fold-back` and `admit` are separate subcommands. One call that compiled and
admitted in a single pass would make the Human Admit boundary depend on which
arguments happened to be supplied.

## The three ideas this module is built on

### Evidence classes do not imply one another

```text
STATIC    the code says this
TEST      this executed and produced this, under the inputs the test supplies
RUNTIME   this really ran in this environment and behaved this way
```

There is no ranking and no `max()` that could promote one into another. A patch
claiming `TEST` evidence needs a passing execution covering that symbol; a patch
claiming `RUNTIME` needs an **adapter-attested** observation of it. A diff on its
own supports `STATIC` and nothing else — and a static change recorded as observed
behaviour cannot be told apart from a real observation afterwards, which is why
this is a refusal rather than a warning.

### An anchor pins content, not a line number

`src/ledger.py:42` stops being true the moment someone inserts a line above it —
and it does not break loudly. It keeps resolving, to a different line. So an
anchor records the commit, the symbol, the range **and the digest of the lines
themselves**, and re-checking compares the digest:

| | |
|---|---|
| `FRESH` | the content is where the anchor said |
| `STALE_MOVED` | byte-identical, elsewhere — reported with its new range |
| `STALE_CHANGED` | the anchored code itself changed |
| `ABSENT` | the file is gone |

Nothing is repaired silently. A repaired anchor is indistinguishable from one
that was right all along.

### A conclusion that flipped is a SUPERSEDE, not an UPDATE

`UPDATE` rewrites the card. Afterwards nobody can see the system ever believed
the other thing — which is exactly what someone needs when the reversal turns out
to be wrong. `SUPERSEDE` appends and marks; the old claim stays readable.

Both directions are enforced: an `UPDATE` that reverses the claim is refused, and
so is a `SUPERSEDE` that does not reverse anything (superseding a live claim
buries it). The reversal test is a shallow, declared negation table rather than
an inference, because a supersession decided by inference is unauditable at
exactly the moment it matters.

## What else this module refuses

- **A similarity score may not produce a patch.** It surfaces a card as
  `CANDIDATE_FOR_REVIEW` and stops there. A missed card is a gap someone
  notices; an unrelated card rewritten because two paragraphs shared vocabulary
  is a wrong fact with a citation making it look checked.
- **Code does not amend a decision record.** A card whose kind is `ADR`, `NORM`
  or `POLICY` can only receive `CONFLICT` or `UNKNOWN` from a code change. Which
  side moves is a human's call.
- **A model summary is not evidence.** `MODEL_SUMMARY` is absent from the
  accepted anchor kinds entirely — a summary is a claim *about* evidence.
- **History is append-only.** Rejected patches become `REJECTED` revisions rather
  than disappearing; a declined proposal that leaves no trace gets re-proposed
  next month with nothing to say it was already considered. Rollback appends a
  reversal, because deleting the revision would also delete the evidence that
  justified it.
- **A rerun appends nothing.** Revision ids are content-addressed on the bundle
  and decision set they came from — not on the revision number, which is a
  position in a history that has already moved by the time a retry happens.

## Evidence

```sh
sh loop_wiki/loopx-knowledge-foldback/tests/run-all.sh
```

Four schemas under a digest manifest, eight manifest mutations, ten positive
properties, twenty-eight planted controls, and a **physical** anchor control
group.

The physical group is the part a fixture cannot honestly answer: a fixture can
hand `recheck` the answer `STALE_MOVED` and watch the pipeline refuse, but that
tests the refusal, not the detection. So it builds a real file, anchors real
lines, then edits it the four ways code actually changes — untouched, shifted ten
lines down, edited in place, deleted — and asks what `recheck` finds.

**Verified by deliberately breaking it.** Weakening `recheck` to a line-range
check makes shifted code report `FRESH`, and the control names it:

```
foldback control RED: code shifted ten lines down reported FRESH; the old line
numbers still resolve, they just resolve to something else, and a citation that
stays well-formed while changing meaning is the whole failure
exit=2
```

## Boundaries

- Nothing here writes a card, an ADR or a Notes file. The bundle is `CANDIDATE`
  with `admit_required: true`, and the manifest pins `terminal_state` to
  `CANDIDATE_FOLD_BACK_BUNDLE` and `admit_authority` to `HUMAN`.
- Every patch needs a decision. A receipt over a partial decision set would
  record a fold-back a human only partly saw.
- A rejection needs a note, so the next proposal has something to read.
- The receipt is content-addressed over the bundle and the decisions, so two
  receipts claiming the same fold-back are compared as digests rather than read.
- No canonical state write, gate verdict, merge, promotion, permission widening
  or secret access occurs in this leaf.
