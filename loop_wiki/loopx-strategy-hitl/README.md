# LoopX Strategy Graph + HITL Contracts v1

This terminal leaf defines the contract between a strategy planner, the canonical LoopX state authority, and a Human reviewer. It does not embed LangGraph as state authority and does not execute Workers.

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
  --output resume-envelope.json
```

The compiler emits a proposal envelope only. It does not append to the ledger, resume LangGraph, dispatch a Worker, waive a Gate, merge, promote or Human Admit.

## Current evidence boundary

Contract validation and deterministic fixture simulation may become `IMPLEMENTED`. A real LangGraph checkpoint store, Human signing service, interrupt/resume UI, ledger append and production recovery remain `NOT_IMPLEMENTED` or `NOT_EXERCISED` until separate exact receipts exist.
