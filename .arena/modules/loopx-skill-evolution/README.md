# `loopx-skill-evolution` module

`loopx-skill-evolution` owns the evidence-bound evolution loop for prompts, `SKILL.md` procedures and host projections under [`../../../loop_wiki/loopx-skill-evolution/`](../../../loop_wiki/loopx-skill-evolution/).

## Capabilities

```text
loopx.skill-evolution/v1
loopx.candidate-release-proposal/v1
```

Required capabilities:

```text
loopx.contracts/v1
loopx.worker-gateway/v1
arena.proof-kernel/v1
```

Terminal leaf of issue #61, on the six-host Worker Gateway (#64). Answers issue #72. Intentionally not selected in the shared `bettor-arena` composition by this leaf.

## Public control port

```sh
python3 loop_wiki/loopx-skill-evolution/scripts/skillevo.py \
  <check|selftest|evaluate|receipt|verify-receipt>
```

## State Machine

```text
CANDIDATE_PROPOSED
→ STATIC_CONTRACT_CHECK
→ PUBLIC_DEV_EVAL
→ MUTATION_TRAP_EVAL
→ SEALED_HOLDOUT
→ CROSS_HOST_REPLICATION
→ REGRESSION_RESOURCE_ANALYSIS
→ CANDIDATE | REJECTED | INCONCLUSIVE
→ HUMAN ADMIT
→ IMMUTABLE SKILL RELEASE (skills-shared)
→ BETTOR BINDING UPDATE (separate leaf)
```

The seal is opened at `SEALED_HOLDOUT` and nowhere earlier. Ordering here is load-bearing, not presentational.

## Boundaries

- Hard gates are deterministic and non-compensatory; judges are advisory and count only with a calibration receipt naming deterministic labels. A failed gate is not a low score.
- The holdout answers are committed to a seal before the run, and the runner payload is built from a whitelist and then scanned for every answer string. Both checks exist because they fail differently.
- Tools, model, provider, host and repetitions are declared once on the execution contract; arms have no field to carry their own, so a model swapped mid-comparison is not expressible.
- The no-skill baseline arm is mandatory: without it, a task the model does fine unaided reads as a win for the candidate.
- `INCONCLUSIVE` is a real outcome. Replication on one host is an unanswered question; cross-host rows are kept per host and never folded into a majority.
- A mutation suite derived from the candidate's observed failures is refused, as is a candidate prompt containing a timestamp or nonce.
- `canonical_mutation` is always `NONE_PERFORMED` and `consumer_binding_update` is always `SEPARATE_LEAF_NOT_PERFORMED`. Fixture-only evidence never unlocks a capability.
- Rejected and inconclusive experiments still produce receipts.
- No canonical state write, gate verdict, permission widening, secret rotation, merge, promotion or rollback occurs in this leaf.

## Evidence

```sh
sh loop_wiki/loopx-skill-evolution/tests/run-all.sh
```

Four schemas under a digest manifest, ten manifest mutations, eight positive properties, twenty-eight planted controls — twenty-one asserting a refusal phrase and seven asserting a verdict reached for a named reason — and five physical isolation controls that write real files, build the runner payload, and hand it to a real subprocess that recovers nothing, while the same subprocess given the holdout file recovers everything.
