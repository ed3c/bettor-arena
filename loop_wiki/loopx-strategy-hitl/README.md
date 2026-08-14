# LoopX Strategy Graph + HITL Contracts v1

This terminal leaf defines the contract between a strategy planner, the canonical LoopX state authority, and a Human reviewer. It does not embed LangGraph as state authority and does not execute Workers.

Machine authority: [`../../.arena/modules/loopx-strategy-hitl/module.json`](../../.arena/modules/loopx-strategy-hitl/module.json)

## State Machine

```text
CANONICAL_SNAPSHOT
→ STRATEGY_PROPOSAL
→ REDUCER_ACCEPTS | REJECTS
→ EXECUTION / GATE OBSERVATION (outside this leaf)
→ RETRY_AVAILABLE
   | HITL_INTERRUPT
   | TERMINAL_CANDIDATE

HITL_INTERRUPT
→ HUMAN_RETRY_AFTER_FIX
   | HUMAN_UPDATE_CONTRACT
   | HUMAN_CANCEL
   | HUMAN_SCOPED_EXCEPTION
→ RESUME_ENVELOPE
→ REDUCER_REVALIDATES
→ NEW CANONICAL_EVENT
```

## Authority

```text
Strategy proposes typed commands
LangGraph checkpoint is a replayable projection only
Human signs decisions for one exact interrupt/subject
Resume envelope proposes a reducer event
LoopX reducer alone commits state
```

There is no generic `force_skip`. A scoped exception must name exact Todo/Gate scope, expiry, Human authority, rationale artifact, revalidation requirement and visible exception state.

## Public control port

```sh
python3 loop_wiki/loopx-strategy-hitl/scripts/hitl.py check
python3 loop_wiki/loopx-strategy-hitl/scripts/hitl.py selftest
python3 loop_wiki/loopx-strategy-hitl/scripts/hitl.py resume \
  --interrupt interrupt.json \
  --decision decision.json \
  --state state.json \
  --gate-classes gate-classes.json \
  --observations observations.json \
  --output resume-envelope.json
```

Also `admit-proposal`, `admit-checkpoint`, `validate-interrupt`, `validate-checkpoint` and `validate-decision`.

Exits are `0` admitted, `2` refused, `64` unusable input. The split between 2 and 64 is load-bearing: an absent decision file and a rejected decision must not look the same to a caller.

The compiler emits a proposal envelope only. It does not append to the ledger, resume LangGraph, dispatch a Worker, waive a Gate, merge, promote or Human Admit.

## What is refused, and why

**A planner that starts writing.** `authority.state_write`, `gate_verdict` and `human_decision` must all be `false`, and `planner.checkpoint_authority` must be `PROJECTION_ONLY`. A checkpoint carrying `todos`, `gates`, `quota`, `state_revision` or any other canonical key is refused outright — a field declaring itself a projection does not make it one, the contents do.

**A checkpoint that has drifted.** Stale (behind the head), divergent (same revision, different head) and ahead-of-head are three separate verdicts. Stale is resumable after a refresh; divergent means two writers produced different history from one point, and refreshing would paper over it.

**A decision that is not bound to what it approved.** Every decision carries the `interrupt_digest` of the exact interrupt it answers, and the interrupt's digest is computed over its own terms. Editing the interrupt after signing breaks the digest. Signing against a revision the task has since left is refused rather than reinterpreted.

**An exception that is really a skip.** `force_skip`, `skip`, `override`, `bypass` and `waive_all` are rejected by name at any depth, as are keys carrying secret material or private reasoning. An exception must name its Todo, its gates, an expiry and `terminal_visibility: COMPLETED_WITH_EXCEPTION` — it may never claim a clean terminal. It may not target a `SECURITY`, `SECRET`, `DESTRUCTIVE`, `SUBJECT_INTEGRITY`, `CLEANUP` or `RELEASE_SIGNING` gate, and a gate with no declared class cannot be excepted at all: unknown waivability is not permission.

**Approval standing in for evidence.** `revalidation_required` is a const `true`, and a resume without fresh observations for the interrupt's gates is refused. A gate still failing outside the exception's scope fails the resume even when the exception itself is valid.

## Evidence

```sh
sh loop_wiki/loopx-strategy-hitl/tests/run-all.sh
```

Five schemas under a digest manifest, six manifest mutations, one positive pipeline run, twenty-five controls, and a subprocess control asserting on exit codes and emitted envelope bytes.

Each control was checked to fail for its own reason rather than incidentally:

```sh
python3 loop_wiki/loopx-strategy-hitl/scripts/probe_controls.py
```

A control that turns red for an unrelated reason is a false negative wearing a green badge — the failure it names would still get through.

## Current evidence boundary

Contract validation and deterministic fixture simulation are `IMPLEMENTED`. A real LangGraph checkpoint store, Human signing service, interrupt/resume UI, ledger append and production recovery remain `NOT_IMPLEMENTED` or `NOT_EXERCISED` until separate exact receipts exist.
