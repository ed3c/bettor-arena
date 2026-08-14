# LoopX Skill Evolution v1

An evidence-bound evolution loop for system prompts, `SKILL.md` procedures and
host projections. Reaches `CANDIDATE`, `REJECTED` or `INCONCLUSIVE`, and proposes
a **versioned release to `skills-shared`** — it never edits a canonical Skill
body and never rebinds Bettor to one. Terminal leaf of issue #61, on the Worker
Gateway (#64) and LoopX evidence subjects (#62/#63). Answers #72.

## Public port

```sh
python3 loop_wiki/loopx-skill-evolution/scripts/skillevo.py \
  <check|selftest|evaluate|receipt|verify-receipt>
```

Exit `0` ok, `2` a checked invariant disagreed, `64` the input is unusable.

## The four ideas

### A failed hard gate is not a low score

`score_run` returns `gate_state` (PASS/FAIL, deterministic) and `judge_score` (a
number, advisory) and never a blend. Averaging them turns "this must hold" into
"this usually holds", and the difference only becomes visible the one time it
matters. A judge counts toward the decision only if `calibrated_against` names
deterministic labels and a calibration receipt exists — calibration is a field,
not an adjective. Uncalibrated judges are still reported, so a reader can see how
much of the scoring rested on nothing.

### The runner never has the answers

`runner_payload` builds what an arm sees from an explicit whitelist rather than
copying a case and deleting `expected`. Deletion is a step someone can forget;
construction from a whitelist has no equivalent step. On top of it,
`scan_payload_for_leaks` serialises the built payload and searches for every
sealed answer — deliberately redundant, because the two fail differently: the
whitelist protects against forgetting to strip a field, and the scan catches an
answer that ended up *inside* a field the whitelist allows.

The holdout answers are committed to a `seal` before the run. Revealing compares
against it, so an answer set swapped afterwards to match what the candidate said
does not open, and the run is refused rather than scored.

### One execution contract, three arms

Tools, context policy, model, provider, host and repetitions are declared once,
and arms have no field to carry their own. A model swapped between arms is not
expressible rather than merely discouraged. The **baseline** arm — no skill at
all — is not optional: without it, "candidate beats current" cannot distinguish a
better procedure from a task the model does fine without one, and that case means
the Skill should shrink.

### Three-valued outcome

`INCONCLUSIVE` exists so a null result is not forced into `REJECTED`. An
experiment replicated on one host is an unanswered question, not a verdict — one
host, model and provider cannot establish that a prompt is better in general, and
cross-host rows are kept per host rather than folded into a majority that would
let a strong result on one hide a regression on another.

## What this module refuses

- a mutation suite `derived_from` the candidate's observed failures — that tests
  the failures it was transcribed from;
- a candidate prompt containing a timestamp or nonce — it is not comparable
  across runs and defeats prompt-cache reuse at the same time;
- fewer than 3 repetitions, or a `stopping_rule` of "when it looks significant";
- a case appearing in both the dev set and the holdout, or a `HOLDOUT`-kind case
  sitting in the dev set;
- a check declared as both a hard gate and an advisory judge;
- a candidate whose content digest equals current's;
- a Skill subject identified by anything but an immutable release;
- a receipt recording a canonical mutation or a consumer binding update.

## Evidence

```sh
sh loop_wiki/loopx-skill-evolution/tests/run-all.sh
```

Four schemas under a digest manifest, ten manifest mutations, eight positive
properties, twenty-eight planted controls, and a **physical** isolation control
group.

Twenty-one controls assert a refusal message containing the phrase their own rule
raises. The other seven assert a *verdict*: the failures #72 names are mostly
failures of interpretation, so the only way to plant one is to hand the decision
a result set a careless reading would score in the candidate's favour — every
candidate run failing a gate while a calibrated judge scores it 5/5, for
instance. That one must reach `REJECTED` naming the gates.

### The physical group

A fixture can assert that `runner_payload` omits `expected`. The question is
whether the bytes a runner *receives* contain the answer, so this writes the
cases to disk, builds the payload, writes that to disk, and greps the file:

1. the holdout file really does contain its answers (without this, every leak
   check below passes because there was nothing to leak);
2. the payload file on disk contains none of them;
3. an answer embedded in a prompt is caught — the whitelist allows `prompt`, so
   only the content scan can see this one;
4. a subprocess given only the payload recovers nothing;
5. the same subprocess given the holdout file recovers everything — so control
   4's silence is attributable to the payload, not to a broken probe.

**Verified by deliberately breaking it.** Weakening `scan_payload_for_leaks` to
return nothing:

```
skill-evolution control RED: an answer embedded in a prompt was not detected;
the field whitelist allows `prompt`, so nothing else in this module would have
seen it
exit=2
```

## Boundaries

- `canonical_mutation` is `NONE_PERFORMED` on every receipt, and validation
  refuses any other value. Bettor consumes immutable Skill releases; editing the
  shared body from here would make the consumer the author.
- `consumer_binding_update` is `SEPARATE_LEAF_NOT_PERFORMED`. Rebinding Bettor to
  a new release is a separate Human-admitted leaf.
- `FIXTURE_ONLY` evidence yields `capability_state: NOT_UNLOCKED`, and no
  argument to this module can change that — there is no parameter for it.
- Rejected and inconclusive experiments get receipts too. A rejection that leaves
  no artifact is one nobody can find when the same candidate returns.
- No canonical state write, gate verdict, merge, promotion, permission widening
  or secret access occurs in this leaf.
