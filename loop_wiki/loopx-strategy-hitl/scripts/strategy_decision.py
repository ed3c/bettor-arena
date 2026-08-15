#!/usr/bin/env python3
"""Human decision admission against `contracts/human-decision.schema.json`.

A decision is bound to one exact interrupt by digest, not to a task in general.
That binding is what makes "the Human approved it" checkable: an approval signed
against evidence that has since changed is refused rather than reinterpreted.

There is deliberately no generic skip. `force_skip` and its synonyms are
rejected by name at any depth, because the moment one route exists that is
neither scoped nor expiring nor revalidated, the other three properties stop
meaning anything.
"""

from __future__ import annotations

from typing import Any

from strategy_common import (
    ContractError,
    exact_object,
    iso_timestamp,
    non_empty_str,
    require,
    sha256_ref,
    validate_subject,
)

DECISION_KEYS = {
    "schema_version",
    "decision_id",
    "interrupt_digest",
    "subject",
    "decision",
    "authority",
    "rationale_artifact_ref",
    "revalidation_required",
    "exception",
    "created_at",
}
AUTHORITY_KEYS = {"kind", "signer_id", "authority_receipt_ref"}
EXCEPTION_KEYS = {"todo_id", "gate_ids", "expires_at", "terminal_visibility"}

DECISIONS = {"RETRY_AFTER_FIX", "UPDATE_CONTRACT", "CANCEL", "SCOPED_EXCEPTION"}

# Gate classes no exception may waive. Not a policy knob: an exception that
# waives one of these is indistinguishable from having no gate at all.
NON_WAIVABLE_GATE_CLASSES = {
    "CLEANUP",
    "DESTRUCTIVE",
    "RELEASE_SIGNING",
    "SECRET",
    "SECURITY",
    "SUBJECT_INTEGRITY",
}

FORBIDDEN_FIELDS = {"bypass", "force_skip", "override", "skip", "waive_all"}
FORBIDDEN_CONTENT_KEYS = {
    "chain_of_thought",
    "password",
    "private_key",
    "reasoning_trace",
    "scratchpad",
    "secret",
    "thought_stream",
    "token",
}


def scan_forbidden(value: Any, path: str = "decision") -> None:
    """Reject skip routes and durable private reasoning wherever they appear."""
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            if lowered in FORBIDDEN_FIELDS:
                raise ContractError(
                    f"{path}.{key} is a generic skip route; an exception must be "
                    "scoped, expiring and revalidated instead"
                )
            if lowered in FORBIDDEN_CONTENT_KEYS:
                raise ContractError(
                    f"{path}.{key} carries secret material or private reasoning"
                )
            scan_forbidden(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            scan_forbidden(item, f"{path}[{index}]")


def validate_decision(
    value: Any, gate_classes: dict[str, str] | None = None
) -> dict[str, Any]:
    scan_forbidden(value)
    decision = exact_object(value, DECISION_KEYS, "decision")
    require(
        decision["schema_version"] == "loopx/human-decision/v1",
        "decision schema version drifted",
    )
    non_empty_str(decision["decision_id"], "decision.decision_id")
    sha256_ref(decision["interrupt_digest"], "decision.interrupt_digest")
    sha256_ref(decision["rationale_artifact_ref"], "decision.rationale_artifact_ref")
    validate_subject(decision["subject"], "decision.subject")
    iso_timestamp(decision["created_at"], "decision.created_at")

    if decision["decision"] not in DECISIONS:
        raise ContractError(
            f"decision.decision must be one of {sorted(DECISIONS)}, "
            f"got {decision['decision']!r}"
        )

    # A const in the schema; asserted again here so the validator does not
    # depend on a schema library being present to hold the invariant.
    if decision["revalidation_required"] is not True:
        raise ContractError(
            "decision.revalidation_required must be true; approval is not evidence "
            "that the code now works"
        )

    authority = exact_object(
        decision["authority"], AUTHORITY_KEYS, "decision.authority"
    )
    if authority["kind"] != "HUMAN":
        raise ContractError("decision.authority.kind must be HUMAN")
    signer = non_empty_str(authority["signer_id"], "decision.authority.signer_id")
    if len(signer) < 3:
        raise ContractError(
            "decision.authority.signer_id must be at least 3 characters"
        )
    sha256_ref(
        authority["authority_receipt_ref"], "decision.authority.authority_receipt_ref"
    )

    exception = decision["exception"]
    if decision["decision"] == "SCOPED_EXCEPTION":
        if not isinstance(exception, dict):
            raise ContractError(
                "a SCOPED_EXCEPTION decision must carry an exception object"
            )
        exception = exact_object(exception, EXCEPTION_KEYS, "decision.exception")
        non_empty_str(exception["todo_id"], "decision.exception.todo_id")
        iso_timestamp(exception["expires_at"], "decision.exception.expires_at")

        gate_ids = exception["gate_ids"]
        if not isinstance(gate_ids, list) or not gate_ids:
            raise ContractError(
                "decision.exception.gate_ids must name at least one gate"
            )
        if len(set(gate_ids)) != len(gate_ids):
            raise ContractError("decision.exception.gate_ids must be unique")

        if exception["terminal_visibility"] != "COMPLETED_WITH_EXCEPTION":
            raise ContractError(
                "an exception must stay visible as COMPLETED_WITH_EXCEPTION; a clean "
                "terminal state would make it indistinguishable from a real pass"
            )

        classes = gate_classes or {}
        for gate_id in gate_ids:
            non_empty_str(gate_id, "decision.exception.gate_ids[]")
            gate_class = classes.get(gate_id)
            if gate_class is None:
                raise ContractError(
                    f"gate {gate_id} has no declared class; an exception cannot be "
                    "admitted against a gate whose waivability is unknown"
                )
            if gate_class in NON_WAIVABLE_GATE_CLASSES:
                raise ContractError(
                    f"gate {gate_id} is class {gate_class}, which no exception may waive"
                )
    elif exception is not None:
        raise ContractError(
            "decision.exception must be null unless the decision is SCOPED_EXCEPTION"
        )

    return decision
