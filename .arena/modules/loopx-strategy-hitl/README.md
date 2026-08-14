# `loopx-strategy-hitl` module

`loopx-strategy-hitl` owns the strategy-proposal adapter and the Human-in-the-loop decision protocol under [`../../../loop_wiki/loopx-strategy-hitl/`](../../../loop_wiki/loopx-strategy-hitl/).

## Capabilities

```text
loopx.strategy-proposal/v1
loopx.hitl/v1
```

Required capabilities:

```text
loopx.contracts/v1
loopx.ledger/v1
arena.proof-kernel/v1
```

Terminal leaf of issue #61, sibling of `loopx-ledger` and `loopx-worker-gateway`. It consumes their contracts and is intentionally not selected in the shared `bettor-arena` composition by this leaf.

## Public control port

```sh
python3 loop_wiki/loopx-strategy-hitl/scripts/strategy.py \
  <validate-proposal|validate-checkpoint|validate-decision|admit-resume|admit-proposal|apply-decision|selftest>
```

## State Machine

```text
typed proposal from a strategy graph
→ subject and expected-revision check
→ COMMAND_ACCEPTED | COMMAND_REJECTED
→ gate observations
→ HITL_PENDING
→ signed Human decision bound to one revision and ledger head
→ REVALIDATE with fresh observations
→ ACTIVE | TODO_COMPLETED | COMPLETED_WITH_EXCEPTION | TASK_FAILED | CANCELLED
```

## Boundaries

- The strategy graph proposes; it never writes canonical state. `actor.class` must be `STRATEGY`, and a graph may not submit a Human decision.
- A graph checkpoint is a cursor. Carrying canonical task state, naming another subject, sitting behind the ledger head, diverging at the same revision, claiming a revision ahead, or replaying a consumed resume token all refuse.
- No generic skip exists. `force_skip`, `skip`, `override`, `bypass` and `waive_all` are rejected by name at any depth.
- A scoped exception must carry scope, expiry, affected assertions and revalidation gates, reaches `COMPLETED_WITH_EXCEPTION` rather than a clean pass, and may not target a `SECURITY`, `SECRET`, `DESTRUCTIVE`, `SUBJECT_INTEGRITY`, `CLEANUP` or `RELEASE_SIGNING` gate. A gate with no declared class cannot be excepted at all.
- Revalidation is required, not assumed: approval is not evidence that the code works.
- No Worker implementation, memory writeback, MCP exposure, composition selection, live host activation, Human Admit, promotion or rollback occurs in this leaf.

## Evidence

```sh
sh loop_wiki/loopx-strategy-hitl/tests/run-all.sh
```

Schema-digest and waiver-list controls, one positive pipeline run, fourteen controls covering every refusal named above, and an independent subprocess control that asserts on exit codes and emitted receipt bytes rather than on internal values.
