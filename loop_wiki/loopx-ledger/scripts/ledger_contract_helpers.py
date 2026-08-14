#!/usr/bin/env python3
# ruff: noqa: F401,F403,F405  # this module family composes through star imports; the names ruff reads as unused are deliberate re-exports the downstream modules import through.
"""Single-writer replay and reduction engine for LoopX Ledger v1."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

from ledger_common import *

CONTRACT_KEYS = {
    "schema_version",
    "subject",
    "gate_definitions",
    "commands",
    "initial_state",
    "contract_digest",
}
STORE_KEYS = {
    "schema_version",
    "subject",
    "contract_digest",
    "contract_path",
    "events_path",
    "snapshot_path",
    "writer_policy",
    "created_at",
    "content_digest",
}
APPEND_KEYS = {"schema_version", "request_id", "expected_state_revision", "event"}
RECEIPT_KEYS = {
    "schema_version",
    "operation_id",
    "operation",
    "subject",
    "status",
    "before",
    "after",
    "artifacts",
    "cleanup",
    "details",
    "content_digest",
}
STATE_KEYS = {
    "schema_version",
    "subject",
    "state_revision",
    "ledger_head_digest",
    "lifecycle",
    "objective",
    "current_todo_id",
    "todos",
    "evidence",
    "quota",
    "human_decision_refs",
}
TODO_KEYS = {
    "todo_id",
    "title",
    "status",
    "depends_on",
    "gate_ids",
    "gate_results",
    "evidence_refs",
    "attempts",
    "last_failure_ref",
    "exception_ref",
}
GATE_RESULT_KEYS = {
    "gate_id",
    "attempt",
    "verdict",
    "observation_ref",
    "evaluator_digest",
}
HUMAN_KEYS = {
    "decision_id",
    "signer_ref",
    "signature_ref",
    "action",
    "scope",
    "expires_at",
    "rationale_ref",
    "required_revalidation_gate_ids",
    "non_waivable_acknowledged",
}


def validate_human_decision(value: Any, label: str) -> dict[str, Any]:
    decision = exact_object(value, HUMAN_KEYS, label)
    stable_id(decision["decision_id"], f"{label}.decision_id")
    bounded_text(decision["signer_ref"], f"{label}.signer_ref", 256)
    signature = validate_artifact(decision["signature_ref"], f"{label}.signature_ref")
    if signature["kind"] != "HUMAN_DECISION":
        raise ContractError(f"{label}.signature_ref must be a Human decision artifact")
    if decision["action"] not in {
        "RETRY_AFTER_FIX",
        "UPDATE_CONTRACT",
        "CANCEL",
        "SCOPED_EXCEPTION",
    }:
        raise ContractError(f"{label}.action is not admitted")
    scope = decision["scope"]
    if not isinstance(scope, dict) or set(scope) != {
        "todo_id",
        "gate_ids",
        "assertion_ids",
    }:
        raise ContractError(f"{label}.scope is invalid")
    if scope["todo_id"] is not None:
        stable_id(scope["todo_id"], f"{label}.scope.todo_id")
    for key in ("gate_ids", "assertion_ids"):
        if not isinstance(scope[key], list) or len(scope[key]) != len(set(scope[key])):
            raise ContractError(f"{label}.scope.{key} is invalid")
        for item in scope[key]:
            stable_id(item, f"{label}.scope.{key}")
    if (
        scope["todo_id"] is None
        and not scope["gate_ids"]
        and not scope["assertion_ids"]
    ):
        raise ContractError(f"{label}.scope is empty")
    validate_rfc3339_utc(decision["expires_at"], f"{label}.expires_at")
    validate_artifact(decision["rationale_ref"], f"{label}.rationale_ref")
    revalidation = decision["required_revalidation_gate_ids"]
    if (
        not isinstance(revalidation, list)
        or not revalidation
        or len(revalidation) != len(set(revalidation))
    ):
        raise ContractError(f"{label}.required_revalidation_gate_ids is invalid")
    for gate_id in revalidation:
        stable_id(gate_id, f"{label}.required_revalidation_gate_ids")
    if decision["non_waivable_acknowledged"] is not True:
        raise ContractError(f"{label} does not acknowledge non-waivable gates")
    reject_private_fields(decision, label)
    return decision


def validate_gate_observation(value: Any, label: str) -> dict[str, Any]:
    keys = {
        "gate_id",
        "verdict",
        "observed_exit_code",
        "evaluator_digest",
        "artifact_refs",
    }
    observation = exact_object(value, keys, label)
    stable_id(observation["gate_id"], f"{label}.gate_id")
    if observation["verdict"] not in {"PASS", "FAIL", "NOT_RUN", "SKIPPED_BY_POLICY"}:
        raise ContractError(f"{label}.verdict is unsupported")
    if (
        observation["observed_exit_code"] is not None
        and type(observation["observed_exit_code"]) is not int
    ):
        raise ContractError(f"{label}.observed_exit_code is invalid")
    if observation["verdict"] == "PASS" and observation["observed_exit_code"] != 0:
        raise ContractError(f"{label} PASS lacks exit code zero")
    if observation["verdict"] == "FAIL" and observation["observed_exit_code"] in {
        None,
        0,
    }:
        raise ContractError(f"{label} FAIL lacks a nonzero exit code")
    sha256_ref(observation["evaluator_digest"], f"{label}.evaluator_digest")
    if (
        not isinstance(observation["artifact_refs"], list)
        or not observation["artifact_refs"]
    ):
        raise ContractError(f"{label}.artifact_refs is empty")
    for index, artifact in enumerate(observation["artifact_refs"]):
        validate_artifact(artifact, f"{label}.artifact_refs[{index}]")
    return observation


def validate_transition(
    value: Any, label: str, prior_event_ids: set[str] | None = None
) -> dict[str, Any]:
    transition = exact_object(value, {"from", "to", "reason_event_ids"}, label)
    if (transition["from"], transition["to"]) not in ALLOWED_TRANSITIONS:
        raise ContractError(f"{label} is not an allowed transition")
    reasons = transition["reason_event_ids"]
    if (
        not isinstance(reasons, list)
        or not reasons
        or len(reasons) != len(set(reasons))
    ):
        raise ContractError(f"{label}.reason_event_ids is invalid")
    for event_id in reasons:
        stable_id(event_id, f"{label}.reason_event_ids")
        if prior_event_ids is not None and event_id not in prior_event_ids:
            raise ContractError(
                f"{label} references a future or absent event: {event_id}"
            )
    return transition
