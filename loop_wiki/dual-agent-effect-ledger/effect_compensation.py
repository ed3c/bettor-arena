"""Linked compensation-effect semantics for DA-EF-COMP / #220.

Compensation is a new canonical effect request with its own identity, admission,
and later provider/readback path. Original effect history is immutable.
"""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_effect_policy", ROOT / "effect_policy_gate.py")
assert SPEC is not None and SPEC.loader is not None
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)
reducer = policy.reducer
contract = reducer.contract
WORKFLOW_COMPENSATION_COMMIT = "e425ec026c4792b94cf8b2214b4179260e2f1834"
WORKFLOW_COMPENSATION_TREE = "4a50ff3a58785eb50363304725641e8b3a0e003e"


class CompensationLedgerError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise CompensationLedgerError(code, detail)


def build_compensation_link(
    parent_request: dict[str, Any], parent_result: dict[str, Any]
) -> dict[str, Any]:
    contract.validate_admission_request(parent_request)
    if parent_request["runtime_intent"]["side_effect_class"] != "REVERSIBLE_WRITE":
        refuse("COMPENSATION_REQUIRES_REVERSIBLE_PARENT")
    compensation = parent_request["runtime_intent"]["compensation"]
    if compensation.get("disposition") != "DECLARED":
        refuse("COMPENSATION_CONTRACT_NOT_DECLARED")
    if parent_result.get("effect_state") in {"RESULT_UNKNOWN", "RECONCILIATION_REQUIRED"}:
        refuse("UNKNOWN_EFFECT_COMPENSATION_FORBIDDEN")
    if parent_result.get("effect_state") != "EFFECT_COMMITTED" or parent_result.get("accepted_commit_count") != 1:
        refuse("COMPENSATION_REQUIRES_COMMITTED_PARENT")
    attempts = parent_result.get("attempts")
    readbacks = parent_result.get("readbacks")
    if not isinstance(attempts, list) or not attempts or not isinstance(readbacks, list) or not readbacks:
        refuse("COMPENSATION_REQUIRES_COMMITTED_PARENT")

    parent_identity = reducer.effect_identity_digest(parent_request)
    latest_readback = readbacks[-1]
    child = copy.deepcopy(parent_request)
    child["runtime_intent"]["effect_id"] = parent_request["runtime_intent"]["effect_id"] + ":comp"
    child["runtime_intent"]["idempotency_key"] = parent_request["runtime_intent"]["idempotency_key"] + ":comp"
    child["runtime_intent"]["normalized_request_digest"] = contract.digest({
        "parent_effect_identity": parent_identity,
        "plan_digest": compensation["plan_digest"],
        "parent_readback_digest": latest_readback["digest"],
    })
    child["runtime_intent"]["target_subject"] = parent_request["runtime_intent"]["target_subject"] + "/compensation"
    child["runtime_intent"]["compensation"] = {
        "disposition": "HUMAN_OWNED",
        "plan_digest": compensation["plan_digest"],
    }
    child["logical_operation"] = parent_request["logical_operation"] + ":compensate"
    child["attempt_id"] = parent_request["attempt_id"] + ":comp"
    child["target"]["action"] = "compensate"
    child["workflow_request"]["idempotency_key"] = child["runtime_intent"]["idempotency_key"]
    child["workflow_request"]["request_digest"] = child["runtime_intent"]["normalized_request_digest"]
    child["policy_binding"]["approval_receipt_digest"] = contract.digest({
        "parent_approval": parent_request["policy_binding"]["approval_receipt_digest"],
        "child_effect_id": child["runtime_intent"]["effect_id"],
    })
    child["precondition_binding"]["precondition_digest"] = contract.digest({
        "parent_readback_digest": latest_readback["digest"],
        "parent_remote_version": latest_readback["remote_version"],
    })
    child["precondition_binding"]["expected_remote_version"] = latest_readback["remote_version"]

    contract.validate_admission_request(child)
    child_identity = reducer.effect_identity_digest(child)
    if child["runtime_intent"]["idempotency_key"] == parent_request["runtime_intent"]["idempotency_key"]:
        refuse("COMPENSATION_IDEMPOTENCY_REUSE")
    if child_identity == parent_identity:
        refuse("COMPENSATION_IDENTITY_REUSE")

    authorization = policy.authorize_effect(
        child,
        policy.fixed_policy_observation(child),
        policy.fixed_approval(child),
        policy.fixed_precondition(child),
    )
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/compensation-link/v1",
        "effect_authority": contract.CANONICAL_EFFECT_WRITER,
        "workflow_compensation_reference": {
            "commit": WORKFLOW_COMPENSATION_COMMIT,
            "tree": WORKFLOW_COMPENSATION_TREE,
            "authority": "REQUEST_SEMANTICS_ONLY",
        },
        "parent_effect_identity_digest": parent_identity,
        "parent_effect_id": parent_request["runtime_intent"]["effect_id"],
        "parent_idempotency_key": parent_request["runtime_intent"]["idempotency_key"],
        "parent_history_head": parent_result["history_head"],
        "parent_readback_digest": latest_readback["digest"],
        "parent_remote_version": latest_readback["remote_version"],
        "child_effect_identity_digest": child_identity,
        "child_effect_id": child["runtime_intent"]["effect_id"],
        "child_idempotency_key": child["runtime_intent"]["idempotency_key"],
        "child_request": child,
        "authorization": authorization,
        "original_history_mutation": "FORBIDDEN",
        "external_compensation_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_LINKED_COMPENSATION_ONLY",
    }


def validate_compensation_link(
    parent_request: dict[str, Any], parent_result: dict[str, Any], link: dict[str, Any]
) -> None:
    if link.get("schema") != "bettor-arena/dual-agent-effect-ledger/compensation-link/v1":
        refuse("COMPENSATION_LINK_SCHEMA_MISMATCH")
    if link.get("effect_authority") != contract.CANONICAL_EFFECT_WRITER:
        refuse("DIRECT_PROVIDER_COMPENSATION")
    parent_identity = reducer.effect_identity_digest(parent_request)
    if link.get("parent_effect_identity_digest") != parent_identity:
        refuse("COMPENSATION_PARENT_IDENTITY_DRIFT")
    if link.get("parent_effect_id") != parent_request["runtime_intent"]["effect_id"]:
        refuse("COMPENSATION_PARENT_IDENTITY_DRIFT")
    if link.get("parent_idempotency_key") != parent_request["runtime_intent"]["idempotency_key"]:
        refuse("COMPENSATION_PARENT_IDENTITY_DRIFT")
    if link.get("parent_history_head") != parent_result.get("history_head"):
        refuse("COMPENSATION_AUDIT_DELETION")
    child = link.get("child_request")
    if not isinstance(child, dict):
        refuse("COMPENSATION_LINK_SCHEMA_MISMATCH")
    contract.validate_admission_request(child)
    if link.get("child_effect_identity_digest") != reducer.effect_identity_digest(child):
        refuse("COMPENSATION_LINEAGE_MISMATCH")
    if link.get("child_idempotency_key") == link.get("parent_idempotency_key"):
        refuse("COMPENSATION_IDEMPOTENCY_REUSE")
    if link.get("original_history_mutation") != "FORBIDDEN":
        refuse("COMPENSATION_AUDIT_DELETION")
    authorization = link.get("authorization")
    if not isinstance(authorization, dict) or authorization.get("mode") != "EFFECT_EXECUTION_AUTHORIZATION":
        refuse("COMPENSATION_ADMISSION_REQUIRED")
    if authorization.get("effect_identity_digest") != link.get("child_effect_identity_digest"):
        refuse("COMPENSATION_ADMISSION_REQUIRED")
    if link.get("external_compensation_state") != "NOT_EXERCISED":
        refuse("FIXTURE_AS_LIVE_COMPENSATION")


def compensation_result(link: dict[str, Any], state: str, *, accepted: bool = False) -> dict[str, Any]:
    if state not in {"COMPENSATED", "COMPENSATION_FAILED"}:
        refuse("COMPENSATION_RESULT_STATE_MISMATCH")
    if accepted and state != "COMPENSATED":
        refuse("COMPENSATION_FAILURE_AS_SUCCESS")
    if link.get("effect_authority") != contract.CANONICAL_EFFECT_WRITER:
        refuse("DIRECT_PROVIDER_COMPENSATION")
    if link.get("external_compensation_state") != "NOT_EXERCISED":
        refuse("FIXTURE_AS_LIVE_COMPENSATION")
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/compensation-result/v1",
        "parent_effect_identity_digest": link["parent_effect_identity_digest"],
        "child_effect_identity_digest": link["child_effect_identity_digest"],
        "state": state,
        "accepted": accepted,
        "canonical_write_mode": "PROPOSAL_ONLY",
        "external_execution_state": "NOT_EXERCISED",
        "cleanup_state": "NOT_EXERCISED",
        "task_state": "NOT_EXERCISED",
        "user_outcome_state": "NOT_EXERCISED",
        "release_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_LINKED_COMPENSATION_ONLY",
    }
