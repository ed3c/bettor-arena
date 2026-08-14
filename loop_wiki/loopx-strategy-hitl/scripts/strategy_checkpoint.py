#!/usr/bin/env python3
"""Checkpoint admission: a planner projection may never become a second state.

The proposal schema already declares `checkpoint_authority: PROJECTION_ONLY`.
This is where that declaration is checked against the checkpoint itself, because
a field saying a thing is a projection does not make it one -- the contents do.
"""

from __future__ import annotations

from typing import Any

from strategy_common import (
    ContractError,
    digest,
    exact_object,
    non_empty_str,
    require,
    validate_state,
    validate_subject,
)

CHECKPOINT_KEYS = {
    "schema_version",
    "checkpoint_id",
    "subject",
    "based_on",
    "graph_cursor",
    "graph_cache",
    "resume_token",
}

# Keys a checkpoint may never carry. Each names canonical task state; a
# checkpoint holding one has stopped being a cursor and become a second writer.
CANONICAL_STATE_KEYS = {
    "evidence",
    "gate_verdicts",
    "gates",
    "lifecycle",
    "quota",
    "state_revision",
    "task_state",
    "todo_state",
    "todos",
}


def validate_checkpoint(value: Any) -> dict[str, Any]:
    checkpoint = exact_object(value, CHECKPOINT_KEYS, "checkpoint")
    require(
        checkpoint["schema_version"] == "loopx/graph-checkpoint/v1",
        "checkpoint schema version drifted",
    )
    non_empty_str(checkpoint["checkpoint_id"], "checkpoint.checkpoint_id")
    validate_subject(checkpoint["subject"], "checkpoint.subject")
    validate_state(checkpoint["based_on"], "checkpoint.based_on")
    non_empty_str(checkpoint["resume_token"], "checkpoint.resume_token")

    for field in ("graph_cursor", "graph_cache"):
        section = checkpoint[field]
        if not isinstance(section, dict):
            raise ContractError(f"checkpoint.{field} must be an object")
        intruders = sorted(CANONICAL_STATE_KEYS & set(section))
        if intruders:
            raise ContractError(
                f"checkpoint.{field} carries canonical task state: {intruders}; "
                "a projection is a cursor, not a second authority"
            )
    return checkpoint


def admit_resume(
    checkpoint: dict[str, Any],
    state: dict[str, Any],
    subject: dict[str, Any],
    consumed_resume_tokens: set[str] | None = None,
) -> dict[str, Any]:
    """Decide whether a checkpoint may resume against the ledger as it is now.

    Stale and divergent are separate verdicts on purpose. A checkpoint behind
    the head can be refreshed; one whose digest disagrees at the same revision
    means two writers produced different history from the same point, and
    refreshing would paper over it.
    """
    validate_checkpoint(checkpoint)
    validate_state(state, "state")
    validate_subject(subject, "subject")

    if checkpoint["subject"] != subject:
        raise ContractError(
            "checkpoint subject does not match the task subject; a checkpoint may "
            "not be replayed onto another task"
        )

    stored = checkpoint["based_on"]
    if stored["state_revision"] > state["state_revision"]:
        raise ContractError(
            "checkpoint claims a revision ahead of the ledger head; the planner "
            "recorded state the reducer never committed"
        )
    if stored["state_revision"] < state["state_revision"]:
        raise ContractError(
            f"stale checkpoint: recorded revision {stored['state_revision']} is "
            f"behind ledger head {state['state_revision']}"
        )
    if stored["ledger_head"] != state["ledger_head"]:
        raise ContractError(
            "divergent checkpoint: same revision, different ledger head; two "
            "writers produced different history from one point"
        )

    token = checkpoint["resume_token"]
    if consumed_resume_tokens is not None and token in consumed_resume_tokens:
        raise ContractError(
            f"duplicate resume: token {token} was already consumed; a checkpoint "
            "replay may not advance the task twice"
        )

    return {
        "admitted": True,
        "checkpoint_id": checkpoint["checkpoint_id"],
        "resume_token": token,
        "at_revision": state["state_revision"],
        "checkpoint_digest": digest(checkpoint),
    }
