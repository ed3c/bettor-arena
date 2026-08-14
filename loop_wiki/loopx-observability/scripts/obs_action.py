#!/usr/bin/env python3
"""Signed HITL action requests from a console that has no authority.

A console may prepare a request. It may not decide. Every clause here exists to
keep that distinction from eroding in the one place it usually does -- the
moment the UI is confident and the reducer is slow.

The request is bound to an exact state revision and ledger head. That binding is
what makes a stale console detectable: an operator looking at a five-minute-old
page and clicking retry is not proposing what they think they are proposing, and
the request they send says so.
"""

from __future__ import annotations

from typing import Any

from obs_common import (
    ContractError,
    exact_object,
    iso_timestamp,
    non_empty_str,
    require,
    sha256_ref,
    validate_subject,
)

REQUEST_KEYS = {
    "schema_version",
    "request_id",
    "subject",
    "todo_id",
    "observed_state",
    "requested_action",
    "signer",
    "rationale_artifact_ref",
    "displayed_projection_digest",
    "created_at",
}
STATE_KEYS = {"state_revision", "ledger_head"}
SIGNER_KEYS = {"identity", "reference", "signature_ref"}

# The four actions the Strategy + HITL leaf admits. A console may prepare these
# and nothing else; anything wider would be a second decision surface.
ACTIONS = {"RETRY_AFTER_FIX", "UPDATE_CONTRACT", "CANCEL", "SCOPED_EXCEPTION"}

# Fields that would turn a request into a command.
#
# Deliberately *not* here: "commit". It reads as a verb, but in this repository
# it is overwhelmingly a noun -- subject.commit is a git sha on every packet in
# the system. Banning the word rejected the positive fixture on its own subject.
# A name-based ban has to be read as names, not as vocabulary: "commit_state"
# and "do_commit" would be commands; "commit" is a field a valid request needs.
FORBIDDEN_FIELDS = {
    "bypass",
    "commit_state",
    "do_commit",
    "force",
    "force_skip",
    "gate_verdict",
    "mark_pass",
    "override",
    "promote",
    "rollback",
    "skip",
    "state_write",
    "waive_all",
}
FORBIDDEN_CONTENT_KEYS = {
    "chain_of_thought",
    "cookie",
    "password",
    "private_key",
    "reasoning_trace",
    "scratchpad",
    "secret",
    "session",
    "thought_stream",
    "token",
}


def _scan_forbidden(value: Any, path: str = "request") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            if lowered in FORBIDDEN_FIELDS:
                raise ContractError(
                    f"{path}.{key} would make this a command; a console prepares "
                    "requests and never decides"
                )
            if lowered in FORBIDDEN_CONTENT_KEYS:
                raise ContractError(
                    f"{path}.{key} carries secret material or private reasoning"
                )
            _scan_forbidden(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_forbidden(item, f"{path}[{index}]")


def validate_state(value: Any, label: str) -> dict[str, Any]:
    state = exact_object(value, STATE_KEYS, label)
    revision = state["state_revision"]
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise ContractError(f"{label}.state_revision must be a non-negative integer")
    sha256_ref(state["ledger_head"], f"{label}.ledger_head")
    return state


def validate_request(value: Any) -> dict[str, Any]:
    _scan_forbidden(value)
    request = exact_object(value, REQUEST_KEYS, "request")
    require(
        request["schema_version"] == "loopx/hitl-action-request/v1",
        "action request schema version drifted",
    )
    non_empty_str(request["request_id"], "request.request_id")
    validate_subject(request["subject"], "request.subject")
    non_empty_str(request["todo_id"], "request.todo_id")
    validate_state(request["observed_state"], "request.observed_state")
    iso_timestamp(request["created_at"], "request.created_at")
    sha256_ref(request["rationale_artifact_ref"], "request.rationale_artifact_ref")
    sha256_ref(
        request["displayed_projection_digest"], "request.displayed_projection_digest"
    )

    if request["requested_action"] not in ACTIONS:
        raise ContractError(
            f"request.requested_action must be one of {sorted(ACTIONS)}, "
            f"got {request['requested_action']!r}"
        )

    signer = exact_object(request["signer"], SIGNER_KEYS, "request.signer")
    for field in SIGNER_KEYS:
        non_empty_str(signer[field], f"request.signer.{field}")
    sha256_ref(signer["signature_ref"], "request.signer.signature_ref")
    return request


def admit_request(
    request: dict[str, Any],
    current_state: dict[str, Any],
    projection: dict[str, Any],
    consumed_request_ids: set[str] | None = None,
) -> dict[str, Any]:
    """Turn a console request into a proposal for the reducer, or refuse it."""
    validate_request(request)
    validate_state(current_state, "current_state")

    observed = request["observed_state"]
    if observed["state_revision"] != current_state["state_revision"]:
        raise ContractError(
            f"console observed revision {observed['state_revision']} but the task is "
            f"at {current_state['state_revision']}; the operator acted on a page that "
            "no longer describes the task"
        )
    if observed["ledger_head"] != current_state["ledger_head"]:
        raise ContractError(
            "console observed a different ledger head at the same revision; the "
            "page and the ledger disagree about what happened"
        )
    if request["displayed_projection_digest"] != projection.get("projection_digest"):
        raise ContractError(
            "the projection the operator was shown is not the current projection; "
            "the evidence behind the decision is not the evidence on record"
        )
    if (
        consumed_request_ids is not None
        and request["request_id"] in consumed_request_ids
    ):
        raise ContractError(
            f"request {request['request_id']} was already applied; a resubmitted "
            "console action may not commit twice"
        )

    return {
        "schema_version": "loopx/hitl-action-proposal/v1",
        "request_id": request["request_id"],
        "subject": request["subject"],
        "todo_id": request["todo_id"],
        "requested_action": request["requested_action"],
        "at_revision": current_state["state_revision"],
        "at_ledger_head": current_state["ledger_head"],
        "signer_reference": request["signer"]["reference"],
        "outcome": "FORWARDED_TO_REDUCER",
        # The console never reaches a terminal state itself. This names who does.
        "canonical_writer": "LOOPX_LEDGER_REDUCER",
    }
