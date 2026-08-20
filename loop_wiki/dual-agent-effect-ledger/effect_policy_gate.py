"""Deterministic policy/Human/precondition admission gate for DA-EF-P / #218.

The gate consumes the exact canonical effect request and emits an execution
authorization packet only. It performs no provider I/O and no live Human/policy
lookup; those remain separate evidence lanes.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_effect_reducer", ROOT / "effect_reducer.py")
assert SPEC is not None and SPEC.loader is not None
reducer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reducer)
contract = reducer.contract
H64 = re.compile(r"^[0-9a-f]{64}$")


class EffectPolicyError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise EffectPolicyError(code, detail)


def _h64(value: Any, code: str) -> str:
    text = str(value or "")
    if H64.fullmatch(text) is None:
        refuse(code)
    return text


def fixed_policy_observation(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/policy-observation/v1",
        "decision_source": "HISTORY_EVENT",
        "decision": "ALLOW",
        "policy_digest": request["policy_binding"]["policy_digest"],
        "policy_epoch": 7,
        "effect_identity_digest": reducer.effect_identity_digest(request),
        "tenant_scope": request["tenant_scope"],
        "project_scope": request["project_scope"],
        "transport_authenticated": True,
        "provider_healthy": True,
        "evidence_class": "DETERMINISTIC_FIXTURE",
    }


def fixed_approval(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/human-approval/v1",
        "decision_source": "HISTORY_EVENT",
        "actor_class": "HUMAN",
        "decision": "APPROVE",
        "approval_state": "VALID",
        "approval_receipt_digest": request["policy_binding"]["approval_receipt_digest"],
        "effect_identity_digest": reducer.effect_identity_digest(request),
        "job_id": request["runtime_intent"]["job_id"],
        "task_id": request["task_id"],
        "attempt_id": request["attempt_id"],
        "tenant_scope": request["tenant_scope"],
        "project_scope": request["project_scope"],
        "evidence_class": "DETERMINISTIC_FIXTURE",
    }


def fixed_precondition(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/precondition-observation/v1",
        "decision_source": "HISTORY_EVENT",
        "effect_identity_digest": reducer.effect_identity_digest(request),
        "precondition_digest": request["precondition_binding"]["precondition_digest"],
        "remote_version": request["precondition_binding"]["expected_remote_version"],
        "target_subject": request["runtime_intent"]["target_subject"],
        "evidence_class": "DETERMINISTIC_FIXTURE",
    }


def validate_policy(request: dict[str, Any], value: dict[str, Any]) -> None:
    if value.get("schema") != "bettor-arena/dual-agent-effect-ledger/policy-observation/v1":
        refuse("POLICY_OBSERVATION_SCHEMA_MISMATCH")
    if value.get("decision_source") != "HISTORY_EVENT":
        refuse("TRANSPORT_AUTH_AS_AUTHORIZATION")
    if value.get("decision") != "ALLOW":
        refuse("POLICY_REFUSED")
    if value.get("policy_digest") != request["policy_binding"]["policy_digest"]:
        refuse("STALE_POLICY")
    epoch = value.get("policy_epoch")
    if not isinstance(epoch, int) or epoch < 1:
        refuse("STALE_POLICY")
    if value.get("effect_identity_digest") != reducer.effect_identity_digest(request):
        refuse("POLICY_SCOPE_MISMATCH")
    if value.get("tenant_scope") != request["tenant_scope"] or value.get("project_scope") != request["project_scope"]:
        refuse("POLICY_SCOPE_MISMATCH")
    if value.get("evidence_class") != "DETERMINISTIC_FIXTURE":
        refuse("FIXTURE_AS_LIVE_POLICY_PASS")
    # These may be observations but can never be the authorization source.
    if value.get("transport_authenticated") not in {True, False} or value.get("provider_healthy") not in {True, False}:
        refuse("POLICY_OBSERVATION_SCHEMA_MISMATCH")


def validate_approval(request: dict[str, Any], value: dict[str, Any]) -> None:
    if value.get("schema") != "bettor-arena/dual-agent-effect-ledger/human-approval/v1":
        refuse("APPROVAL_SCHEMA_MISMATCH")
    if value.get("decision_source") != "HISTORY_EVENT":
        refuse("APPROVAL_SCHEMA_MISMATCH")
    if value.get("actor_class") != "HUMAN":
        refuse("WORKER_SELF_APPROVAL")
    if value.get("decision") != "APPROVE":
        refuse("APPROVAL_REQUIRED")
    if value.get("approval_state") != "VALID":
        refuse("EXPIRED_APPROVAL")
    if value.get("approval_receipt_digest") != request["policy_binding"]["approval_receipt_digest"]:
        refuse("APPROVAL_SCOPE_MISMATCH")
    _h64(value.get("approval_receipt_digest"), "APPROVAL_SCHEMA_MISMATCH")
    expected = {
        "effect_identity_digest": reducer.effect_identity_digest(request),
        "job_id": request["runtime_intent"]["job_id"],
        "task_id": request["task_id"],
        "attempt_id": request["attempt_id"],
        "tenant_scope": request["tenant_scope"],
        "project_scope": request["project_scope"],
    }
    if any(value.get(key) != expected_value for key, expected_value in expected.items()):
        refuse("APPROVAL_SCOPE_MISMATCH")
    if value.get("evidence_class") != "DETERMINISTIC_FIXTURE":
        refuse("FIXTURE_AS_LIVE_HUMAN_PASS")


def validate_precondition(request: dict[str, Any], value: dict[str, Any]) -> None:
    if value.get("schema") != "bettor-arena/dual-agent-effect-ledger/precondition-observation/v1":
        refuse("PRECONDITION_OBSERVATION_SCHEMA_MISMATCH")
    if value.get("decision_source") != "HISTORY_EVENT":
        refuse("PRECONDITION_OBSERVATION_SCHEMA_MISMATCH")
    if value.get("effect_identity_digest") != reducer.effect_identity_digest(request):
        refuse("PRECONDITION_SCOPE_MISMATCH")
    if value.get("precondition_digest") != request["precondition_binding"]["precondition_digest"]:
        refuse("PRECONDITION_STALE")
    _h64(value.get("precondition_digest"), "PRECONDITION_OBSERVATION_SCHEMA_MISMATCH")
    if value.get("remote_version") != request["precondition_binding"]["expected_remote_version"]:
        refuse("PRECONDITION_STALE")
    if value.get("target_subject") != request["runtime_intent"]["target_subject"]:
        refuse("PRECONDITION_SCOPE_MISMATCH")
    if value.get("evidence_class") != "DETERMINISTIC_FIXTURE":
        refuse("FIXTURE_AS_LIVE_PRECONDITION_PASS")


def authorize_effect(
    request: dict[str, Any],
    policy: dict[str, Any],
    approval: dict[str, Any],
    precondition: dict[str, Any],
) -> dict[str, Any]:
    contract.validate_admission_request(request)
    validate_policy(request, policy)
    validate_approval(request, approval)
    validate_precondition(request, precondition)

    intent = request["runtime_intent"]
    if intent["side_effect_class"] == "IRREVERSIBLE_WRITE" and intent["approval_requirement"] != "BEFORE_IRREVERSIBLE_ACTION":
        refuse("IRREVERSIBLE_EFFECT_REQUIRES_STRONG_APPROVAL")

    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/execution-authorization/v1",
        "mode": "EFFECT_EXECUTION_AUTHORIZATION",
        "canonical_effect_writer": contract.CANONICAL_EFFECT_WRITER,
        "effect_identity_digest": reducer.effect_identity_digest(request),
        "attempt_id": request["attempt_id"],
        "tenant_scope": request["tenant_scope"],
        "project_scope": request["project_scope"],
        "provider_id": request["target"]["provider_id"],
        "resource_id": request["target"]["resource_id"],
        "action": request["target"]["action"],
        "provider_subject": request["target"]["provider_subject"],
        "normalized_request_digest": intent["normalized_request_digest"],
        "policy_digest": policy["policy_digest"],
        "policy_epoch": policy["policy_epoch"],
        "approval_receipt_digest": approval["approval_receipt_digest"],
        "precondition_digest": precondition["precondition_digest"],
        "expected_remote_version": precondition["remote_version"],
        "credential_handle_state": "OPAQUE_ONLY",
        "provider_io_state": "NOT_EXERCISED",
        "live_policy_state": "NOT_EXERCISED",
        "live_human_state": "NOT_EXERCISED",
        "task_state": "NOT_EXERCISED",
        "user_outcome_state": "NOT_EXERCISED",
        "release_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_EFFECT_ADMISSION_GATE_ONLY",
    }
