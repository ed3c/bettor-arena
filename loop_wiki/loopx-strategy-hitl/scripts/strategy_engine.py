#!/usr/bin/env python3
"""Proposal admission, interrupt binding, and the resume envelope.

Nothing here commits. `compile_resume_envelope` returns a proposal describing
what the reducer should be asked to append; the reducer remains the only writer,
which is what keeps a planner from becoming a second authority no matter how
confident it is.
"""

from __future__ import annotations

from typing import Any

from strategy_common import (
    ContractError,
    digest,
    exact_object,
    iso_timestamp,
    non_empty_str,
    require,
    sha256_ref,
    validate_state,
    validate_subject,
)
from strategy_decision import validate_decision

PROPOSAL_KEYS = {
    "schema_version",
    "proposal_id",
    "subject",
    "based_on",
    "planner",
    "preconditions",
    "command",
    "authority",
}
PLANNER_KEYS = {"kind", "identity_digest", "checkpoint_ref", "checkpoint_authority"}
PRECONDITION_KEYS = {"todo_state", "critical_gates", "quota", "interrupt_reason"}
PROPOSAL_COMMAND_KEYS = {
    "type",
    "target_todo",
    "adapter_id",
    "expected_state_revision",
    "rationale_artifact_ref",
}
PROPOSAL_AUTHORITY_KEYS = {"state_write", "gate_verdict", "human_decision"}

COMMAND_TYPES = {"DISPATCH", "RETRY", "REQUEST_HUMAN", "CANCEL", "COMPLETE_TASK"}

INTERRUPT_KEYS = {
    "schema_version",
    "interrupt_id",
    "interrupt_digest",
    "subject",
    "state",
    "reason",
    "todo_id",
    "gate_ids",
    "allowed_decisions",
    "created_at",
}
INTERRUPT_REASONS = {
    "QUOTA_EXHAUSTED",
    "MANUAL_GATE",
    "CONTRACT_CONFLICT",
    "POLICY_REFUSAL",
}
DECISIONS = {"RETRY_AFTER_FIX", "UPDATE_CONTRACT", "CANCEL", "SCOPED_EXCEPTION"}

# Which reducer event each decision asks for, and the terminal it may reach. A
# scoped exception may never ask for a clean completion.
DECISION_OUTCOMES = {
    "RETRY_AFTER_FIX": ("REQUEST_RETRY", "ACTIVE"),
    "UPDATE_CONTRACT": ("UPDATE_CONTRACT", "ACTIVE"),
    "CANCEL": ("CANCEL_TASK", "CANCELLED"),
    "SCOPED_EXCEPTION": ("ADMIT_EXCEPTION", "COMPLETED_WITH_EXCEPTION"),
}


def validate_proposal(value: Any) -> dict[str, Any]:
    proposal = exact_object(value, PROPOSAL_KEYS, "proposal")
    require(
        proposal["schema_version"] == "loopx/strategy-proposal/v1",
        "proposal schema version drifted",
    )
    non_empty_str(proposal["proposal_id"], "proposal.proposal_id")
    validate_subject(proposal["subject"], "proposal.subject")
    validate_state(proposal["based_on"], "proposal.based_on")

    planner = exact_object(proposal["planner"], PLANNER_KEYS, "proposal.planner")
    non_empty_str(planner["kind"], "proposal.planner.kind")
    sha256_ref(planner["identity_digest"], "proposal.planner.identity_digest")
    if planner["checkpoint_ref"] is not None:
        sha256_ref(planner["checkpoint_ref"], "proposal.planner.checkpoint_ref")
    if planner["checkpoint_authority"] != "PROJECTION_ONLY":
        raise ContractError(
            "proposal.planner.checkpoint_authority must be PROJECTION_ONLY; a "
            "checkpoint that carries authority is a second state store"
        )

    # The three falses are the proposal declaring what it is not allowed to do.
    # Asserting them here means a proposal cannot claim otherwise even if a
    # schema validator is not in the path.
    authority = exact_object(
        proposal["authority"], PROPOSAL_AUTHORITY_KEYS, "proposal.authority"
    )
    for field in PROPOSAL_AUTHORITY_KEYS:
        if authority[field] is not False:
            raise ContractError(
                f"proposal.authority.{field} must be false; a planner proposes and "
                "never writes"
            )

    preconditions = exact_object(
        proposal["preconditions"], PRECONDITION_KEYS, "proposal.preconditions"
    )
    if not isinstance(preconditions["critical_gates"], list):
        raise ContractError("proposal.preconditions.critical_gates must be an array")

    command = exact_object(
        proposal["command"], PROPOSAL_COMMAND_KEYS, "proposal.command"
    )
    if command["type"] not in COMMAND_TYPES:
        raise ContractError(
            f"proposal.command.type must be one of {sorted(COMMAND_TYPES)}, "
            f"got {command['type']!r}"
        )
    revision = command["expected_state_revision"]
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise ContractError(
            "proposal.command.expected_state_revision must be a non-negative integer"
        )
    sha256_ref(
        command["rationale_artifact_ref"], "proposal.command.rationale_artifact_ref"
    )
    return proposal


def admit_proposal(
    proposal: dict[str, Any], state: dict[str, Any], subject: dict[str, Any]
) -> dict[str, Any]:
    """Accept or reject. Rejection is a recorded outcome, not an exception."""
    validate_proposal(proposal)
    validate_state(state, "state")
    validate_subject(subject, "subject")

    if proposal["subject"] != subject:
        return _rejection(proposal, "SUBJECT_MISMATCH")
    if proposal["based_on"]["state_revision"] != state["state_revision"]:
        return _rejection(proposal, "REVISION_STALE")
    if proposal["based_on"]["ledger_head"] != state["ledger_head"]:
        return _rejection(proposal, "LEDGER_HEAD_DIVERGED")
    if proposal["command"]["expected_state_revision"] != state["state_revision"]:
        return _rejection(proposal, "COMMAND_REVISION_STALE")

    return {
        "outcome": "ACCEPTED",
        "proposal_id": proposal["proposal_id"],
        "command_type": proposal["command"]["type"],
        "at_revision": state["state_revision"],
        "proposal_digest": digest(proposal),
    }


def _rejection(proposal: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "outcome": "REJECTED",
        "proposal_id": proposal["proposal_id"],
        "command_type": proposal["command"]["type"],
        "reason": reason,
        "proposal_digest": digest(proposal),
    }


def validate_interrupt(value: Any) -> dict[str, Any]:
    interrupt = exact_object(value, INTERRUPT_KEYS, "interrupt")
    require(
        interrupt["schema_version"] == "loopx/hitl-interrupt/v1",
        "interrupt schema version drifted",
    )
    non_empty_str(interrupt["interrupt_id"], "interrupt.interrupt_id")
    sha256_ref(interrupt["interrupt_digest"], "interrupt.interrupt_digest")
    validate_subject(interrupt["subject"], "interrupt.subject")
    validate_state(interrupt["state"], "interrupt.state")
    iso_timestamp(interrupt["created_at"], "interrupt.created_at")

    if interrupt["reason"] not in INTERRUPT_REASONS:
        raise ContractError(
            f"interrupt.reason must be one of {sorted(INTERRUPT_REASONS)}"
        )
    if interrupt["todo_id"] is not None:
        non_empty_str(interrupt["todo_id"], "interrupt.todo_id")

    gate_ids = interrupt["gate_ids"]
    if not isinstance(gate_ids, list) or len(set(gate_ids)) != len(gate_ids):
        raise ContractError("interrupt.gate_ids must be a unique array")

    allowed = interrupt["allowed_decisions"]
    if not isinstance(allowed, list) or not allowed:
        raise ContractError("interrupt.allowed_decisions must name at least one option")
    if len(set(allowed)) != len(allowed):
        raise ContractError("interrupt.allowed_decisions must be unique")
    unknown = sorted(set(allowed) - DECISIONS)
    if unknown:
        raise ContractError(
            f"interrupt.allowed_decisions has unknown entries {unknown}"
        )

    # The digest is over the interrupt without it, so a decision that binds to
    # this digest binds to these exact terms and not to a later edit of them.
    body = {k: v for k, v in interrupt.items() if k != "interrupt_digest"}
    if digest(body) != interrupt["interrupt_digest"]:
        raise ContractError(
            "interrupt.interrupt_digest does not match the interrupt it is on; "
            "the terms a Human would sign are not the terms recorded"
        )
    return interrupt


def compile_resume_envelope(
    interrupt: dict[str, Any],
    decision: dict[str, Any],
    state: dict[str, Any],
    gate_classes: dict[str, str],
    revalidation_observations: dict[str, str] | None = None,
    consumed_decision_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Bind a signed decision to its interrupt and emit a reducer proposal."""
    validate_interrupt(interrupt)
    validate_decision(decision, gate_classes)
    validate_state(state, "state")

    if decision["subject"] != interrupt["subject"]:
        raise ContractError("decision and interrupt name different subjects")
    if decision["interrupt_digest"] != interrupt["interrupt_digest"]:
        raise ContractError(
            "decision is signed against a different interrupt; the evidence it "
            "approved is not the evidence on record"
        )
    if interrupt["state"] != state:
        raise ContractError(
            f"interrupt was raised at revision {interrupt['state']['state_revision']} "
            f"but the task is at {state['state_revision']}; it must be re-raised"
        )
    if decision["decision"] not in interrupt["allowed_decisions"]:
        raise ContractError(
            f"{decision['decision']} is not among the decisions this interrupt "
            f"allows ({sorted(interrupt['allowed_decisions'])})"
        )
    if (
        consumed_decision_ids is not None
        and decision["decision_id"] in consumed_decision_ids
    ):
        raise ContractError(
            f"decision {decision['decision_id']} was already applied; a resume may "
            "not advance the task twice"
        )

    event_kind, terminal = DECISION_OUTCOMES[decision["decision"]]

    revalidated: list[str] = []
    if decision["decision"] != "CANCEL":
        observations = revalidation_observations or {}
        required = sorted(
            set(interrupt["gate_ids"])
            | set((decision["exception"] or {}).get("gate_ids", []))
        )
        if not required:
            raise ContractError(
                "no gate to revalidate; a resume must re-observe something"
            )
        missing = [gate for gate in required if gate not in observations]
        if missing:
            raise ContractError(
                f"revalidation observations absent for {missing}; a decision may not "
                "resume a task on approval alone"
            )
        failed = [gate for gate in required if observations[gate] != "PASS"]
        if failed and decision["decision"] != "SCOPED_EXCEPTION":
            raise ContractError(
                f"revalidation gates still failing: {failed}; the repair did not hold"
            )
        if failed:
            excepted = set((decision["exception"] or {}).get("gate_ids", []))
            outside = sorted(set(failed) - excepted)
            if outside:
                raise ContractError(
                    f"gates {outside} failed and are outside the exception's scope"
                )
        revalidated = required

    return {
        "schema_version": "loopx/resume-envelope/v1",
        "envelope_id": f"resume-{decision['decision_id']}",
        "subject": decision["subject"],
        "interrupt_id": interrupt["interrupt_id"],
        "interrupt_digest": interrupt["interrupt_digest"],
        "decision_id": decision["decision_id"],
        "decision": decision["decision"],
        "proposed_event": event_kind,
        "expected_state_revision": state["state_revision"],
        "expected_ledger_head": state["ledger_head"],
        "terminal_visibility": terminal,
        "revalidated_gates": revalidated,
        "exception_expires_at": (decision["exception"] or {}).get("expires_at"),
        "decision_digest": digest(decision),
        "canonical_writer": "LOOPX_LEDGER_REDUCER",
    }
