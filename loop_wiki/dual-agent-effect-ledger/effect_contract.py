"""Deterministic Dual-Agent effect-admission contract for DA-EF-C / #208.

This module freezes identity, authority, state, readback, and reuse boundaries.
It performs no provider I/O, does not import the PR #196 SQLite fixture, and does
not commit canonical task state.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

RUNTIME_COMMIT = "1fd6a65a2e628ba1b31e89800297e7202dadf126"
RUNTIME_TREE = "cc287010c96391e0a718141c2f4afb92bac3db06"
RUNTIME_CONTRACT_SET = "e6671977dbf0a378474f924a142a82843bc0e3429f4546ffb0145af73f7827fe"
RUNTIME_EFFECT_SCHEMA_ID = "https://runtime-env.invalid/contracts/dual-agent/effect-intent.v1.schema.json"
RUNTIME_EFFECT_SCHEMA_BLOB = "7a50a125e77dc4daa9c4721fce0fa2fc9b37fc3b"
WORKFLOW_COMMIT = "7821e81f15d64ff3119d9bdb9278fc725e5aa398"
WORKFLOW_TREE = "60d486041b36608d5d03e33b2eb8944c9899b50b"
WORKFLOW_REDUCER_BLOB = "12f1048d5abf4fbfd8970815bc46bfdc797cb3d8"
SUBSTRATE_COMMIT = "c2613432736c65756ed13d871feb2df486c69118"
SUBSTRATE_TREE = "53680d47048f88b9402c6320355121b7ec2f7244"
SUBSTRATE_EFFECT_BLOB = "fedd4e6a7ee18438c122995be96694c8d26cf242"
SUBSTRATE_WORKER_BLOB = "7884038ee68a3eee08324b41c338c6001b8518a7"
CANONICAL_EFFECT_WRITER = "dual-agent-effect-ledger"
CANONICAL_TASK_WRITER = "loopx-ledger"

H40 = re.compile(r"^[0-9a-f]{40}$")
H64 = re.compile(r"^[0-9a-f]{64}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{2,127}$")
SENSITIVE_KEYS = {
    "credential", "credential_value", "password", "private_reasoning", "raw_secret",
    "secret", "secret_value", "token", "token_value",
}

STATES = (
    "EFFECT_PROPOSED",
    "INTENT_VALIDATED",
    "POLICY_AND_APPROVAL_CHECKED",
    "IDEMPOTENCY_RESERVED",
    "PRECONDITION_REVALIDATED",
    "EXECUTION_AUTHORIZED",
    "EFFECT_ATTEMPTED",
    "EFFECT_OBSERVED",
    "EFFECT_COMMITTED",
    "READ_ONLY_NO_EFFECT",
    "DUPLICATE_REFUSED",
    "POLICY_REFUSED",
    "APPROVAL_REQUIRED",
    "PRECONDITION_STALE",
    "ATTEMPT_FAILED",
    "RESULT_UNKNOWN",
    "RECONCILIATION_REQUIRED",
    "COMPENSATION_REQUIRED",
    "COMPENSATING",
    "COMPENSATED",
    "COMPENSATION_FAILED",
)
TERMINALS = {
    "EFFECT_COMMITTED", "READ_ONLY_NO_EFFECT", "DUPLICATE_REFUSED", "POLICY_REFUSED",
    "APPROVAL_REQUIRED", "PRECONDITION_STALE", "ATTEMPT_FAILED", "COMPENSATED",
    "COMPENSATION_FAILED",
}
TRANSITIONS = {
    "EFFECT_PROPOSED": {"INTENT_VALIDATED", "READ_ONLY_NO_EFFECT"},
    "INTENT_VALIDATED": {"POLICY_AND_APPROVAL_CHECKED"},
    "POLICY_AND_APPROVAL_CHECKED": {"IDEMPOTENCY_RESERVED", "POLICY_REFUSED", "APPROVAL_REQUIRED"},
    "IDEMPOTENCY_RESERVED": {"PRECONDITION_REVALIDATED", "DUPLICATE_REFUSED"},
    "PRECONDITION_REVALIDATED": {"EXECUTION_AUTHORIZED", "PRECONDITION_STALE"},
    "EXECUTION_AUTHORIZED": {"EFFECT_ATTEMPTED"},
    "EFFECT_ATTEMPTED": {"EFFECT_OBSERVED", "RESULT_UNKNOWN", "ATTEMPT_FAILED"},
    "EFFECT_OBSERVED": {"EFFECT_COMMITTED", "RECONCILIATION_REQUIRED"},
    "RESULT_UNKNOWN": {"RECONCILIATION_REQUIRED"},
    "RECONCILIATION_REQUIRED": {"EFFECT_OBSERVED", "COMPENSATION_REQUIRED"},
    "COMPENSATION_REQUIRED": {"COMPENSATING"},
    "COMPENSATING": {"COMPENSATED", "COMPENSATION_FAILED"},
}


class EffectContractError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise EffectContractError(code, detail)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _h40(value: Any, code: str = "MUTABLE_EFFECT_SUBJECT") -> str:
    text = str(value or "")
    if H40.fullmatch(text) is None:
        refuse(code)
    return text


def _h64(value: Any, code: str) -> str:
    text = str(value or "")
    if H64.fullmatch(text) is None:
        refuse(code)
    return text


def _id(value: Any, code: str = "EFFECT_IDENTITY_MISMATCH") -> str:
    text = str(value or "")
    if SAFE_ID.fullmatch(text) is None:
        refuse(code)
    return text


def _scan_sensitive(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                refuse("SECRET_OR_REASONING_LEAK", str(key))
            _scan_sensitive(item)
    elif isinstance(value, list):
        for item in value:
            _scan_sensitive(item)


def fixed_contract() -> dict[str, Any]:
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/contract/v1",
        "canonical_effect_writer": CANONICAL_EFFECT_WRITER,
        "canonical_task_writer": CANONICAL_TASK_WRITER,
        "workflow_interface": {
            "mode": "EFFECT_ADMISSION_REQUEST",
            "effect_owner": CANONICAL_EFFECT_WRITER,
            "commit": WORKFLOW_COMMIT,
            "tree": WORKFLOW_TREE,
            "reducer_blob": WORKFLOW_REDUCER_BLOB,
        },
        "runtime_contract": {
            "commit": RUNTIME_COMMIT,
            "tree": RUNTIME_TREE,
            "contract_set_digest": RUNTIME_CONTRACT_SET,
            "effect_intent_schema_id": RUNTIME_EFFECT_SCHEMA_ID,
            "effect_intent_blob": RUNTIME_EFFECT_SCHEMA_BLOB,
        },
        "substrate_reference": {
            "commit": SUBSTRATE_COMMIT,
            "tree": SUBSTRATE_TREE,
            "effect_contract_blob": SUBSTRATE_EFFECT_BLOB,
            "reconciliation_worker_blob": SUBSTRATE_WORKER_BLOB,
            "reuse_mode": "REFERENCE_SUBSTRATE_ONLY",
            "writer_authority": "NONE",
        },
        "provider_native_idempotency_is_authority": False,
        "states": list(STATES),
        "evidence_ceiling": "DETERMINISTIC_EFFECT_CONTRACT_INTERFACE_ONLY",
    }


def fixed_runtime_intent() -> dict[str, Any]:
    return {
        "schema": "runtime-env/dual-agent/effect-intent/v1",
        "effect_id": "effect-demo-001",
        "job_id": "dual-agent-workflow-job-1",
        "idempotency_key": "effect-idem-001",
        "normalized_request_digest": "a" * 64,
        "side_effect_class": "REVERSIBLE_WRITE",
        "target_subject": "provider://demo/resource/record-001",
        "preconditions": ["etag:version-7"],
        "approval_requirement": "BEFORE_EXTERNAL_WRITE",
        "compensation": {"disposition": "DECLARED", "plan_digest": "b" * 64},
        "contract_set_ref": {
            "schema": "runtime-env/dual-agent/contract-set-manifest/v1",
            "manifest_digest": RUNTIME_CONTRACT_SET,
        },
    }


def fixed_admission_request() -> dict[str, Any]:
    intent = fixed_runtime_intent()
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/admission-request/v1",
        "canonical_effect_writer": CANONICAL_EFFECT_WRITER,
        "tenant_scope": "tenant-demo",
        "project_scope": "project-demo",
        "logical_operation": "create-demo-record",
        "source_subject": {
            "repository": "example/workload",
            "commit": "c" * 40,
            "tree": "d" * 40,
        },
        "workflow_subject": {
            "repository": "ed3c/bettor-arena",
            "commit": WORKFLOW_COMMIT,
            "tree": WORKFLOW_TREE,
        },
        "task_id": "task-dual-agent-001",
        "attempt_id": "attempt-1",
        "workflow_request": {
            "mode": "EFFECT_ADMISSION_REQUEST",
            "effect_owner": CANONICAL_EFFECT_WRITER,
            "job_id": intent["job_id"],
            "tenant_scope": "tenant-demo",
            "idempotency_key": intent["idempotency_key"],
            "request_digest": intent["normalized_request_digest"],
            "execution_state": "NOT_EXERCISED",
        },
        "runtime_intent": intent,
        "target": {
            "provider_id": "provider-demo",
            "resource_id": "record-001",
            "action": "create",
            "provider_subject": {
                "repository": "provider/demo-adapter",
                "commit": "e" * 40,
                "tree": "f" * 40,
            },
        },
        "policy_binding": {
            "policy_digest": "1" * 64,
            "approval_receipt_digest": "2" * 64,
        },
        "precondition_binding": {
            "precondition_digest": "3" * 64,
            "expected_remote_version": "version-7",
        },
        "expected_evidence_class": "TARGET_READBACK",
        "readback_requirement": "REQUIRED_BEFORE_COMMIT",
        "substrate": {
            "commit": SUBSTRATE_COMMIT,
            "tree": SUBSTRATE_TREE,
            "reuse_mode": "REFERENCE_SUBSTRATE_ONLY",
            "writer_authority": "NONE",
            "evidence_state": "REFERENCE_ONLY",
        },
        "external_states": {
            "provider_write": "NOT_EXERCISED",
            "target_readback": "NOT_EXERCISED",
            "observable_effect": "NOT_EXERCISED",
            "compensation": "NOT_EXERCISED",
            "task": "NOT_EXERCISED",
            "user_outcome": "NOT_EXERCISED",
            "release": "NOT_EXERCISED",
        },
    }


def validate_contract(value: dict[str, Any]) -> None:
    if value.get("schema") != "bettor-arena/dual-agent-effect-ledger/contract/v1":
        refuse("EFFECT_CONTRACT_SCHEMA_MISMATCH")
    if value.get("canonical_effect_writer") != CANONICAL_EFFECT_WRITER:
        refuse("DUPLICATE_EFFECT_AUTHORITY")
    if value.get("canonical_task_writer") != CANONICAL_TASK_WRITER:
        refuse("SECOND_TASK_WRITER")
    if value.get("workflow_interface") != fixed_contract()["workflow_interface"]:
        refuse("UPSTREAM_SUBJECT_DRIFT")
    if value.get("runtime_contract") != fixed_contract()["runtime_contract"]:
        refuse("UPSTREAM_SUBJECT_DRIFT")
    if value.get("substrate_reference") != fixed_contract()["substrate_reference"]:
        refuse("SUBSTRATE_AUTHORITY_DRIFT")
    if value.get("provider_native_idempotency_is_authority") is not False:
        refuse("PROVIDER_IDEMPOTENCY_AS_AUTHORITY")
    if value.get("states") != list(STATES):
        refuse("EFFECT_STATE_VOCABULARY_DRIFT")


def validate_runtime_intent(intent: dict[str, Any]) -> None:
    required = {
        "schema", "effect_id", "job_id", "idempotency_key", "normalized_request_digest",
        "side_effect_class", "target_subject", "preconditions", "approval_requirement",
        "compensation", "contract_set_ref",
    }
    if set(intent) != required or intent.get("schema") != "runtime-env/dual-agent/effect-intent/v1":
        refuse("RUNTIME_EFFECT_INTENT_MISMATCH")
    for key in ("effect_id", "job_id", "idempotency_key"):
        _id(intent.get(key))
    _h64(intent.get("normalized_request_digest"), "EFFECT_IDENTITY_MISMATCH")
    if intent.get("side_effect_class") not in {"REVERSIBLE_WRITE", "IRREVERSIBLE_WRITE"}:
        refuse("RUNTIME_EFFECT_INTENT_MISMATCH")
    if not str(intent.get("target_subject", "")).strip():
        refuse("TARGET_IDENTITY_MISMATCH")
    preconditions = intent.get("preconditions")
    if not isinstance(preconditions, list) or not preconditions or any(not str(x).strip() for x in preconditions):
        refuse("PRECONDITION_MISSING")
    if intent.get("approval_requirement") not in {"BEFORE_EXTERNAL_WRITE", "BEFORE_IRREVERSIBLE_ACTION"}:
        refuse("APPROVAL_BINDING_MISMATCH")
    compensation = intent.get("compensation")
    if not isinstance(compensation, dict) or compensation.get("disposition") not in {"DECLARED", "HUMAN_OWNED", "NOT_POSSIBLE"}:
        refuse("COMPENSATION_CONTRACT_MISMATCH")
    _h64(compensation.get("plan_digest"), "COMPENSATION_CONTRACT_MISMATCH")
    contract_set = intent.get("contract_set_ref")
    if not isinstance(contract_set, dict) or contract_set.get("schema") != "runtime-env/dual-agent/contract-set-manifest/v1" or contract_set.get("manifest_digest") != RUNTIME_CONTRACT_SET:
        refuse("UPSTREAM_SUBJECT_DRIFT")


def validate_admission_request(request: dict[str, Any]) -> None:
    if request.get("schema") != "bettor-arena/dual-agent-effect-ledger/admission-request/v1":
        refuse("EFFECT_REQUEST_SCHEMA_MISMATCH")
    if request.get("canonical_effect_writer") != CANONICAL_EFFECT_WRITER:
        refuse("DUPLICATE_EFFECT_AUTHORITY")
    for key in ("tenant_scope", "project_scope", "logical_operation", "task_id", "attempt_id"):
        _id(request.get(key))

    for subject_key in ("source_subject", "workflow_subject"):
        subject = request.get(subject_key)
        if not isinstance(subject, dict) or not str(subject.get("repository", "")).strip():
            refuse("MUTABLE_EFFECT_SUBJECT")
        _h40(subject.get("commit"))
        _h40(subject.get("tree"))
    workflow_subject = request["workflow_subject"]
    if workflow_subject.get("repository") != "ed3c/bettor-arena" or workflow_subject.get("commit") != WORKFLOW_COMMIT or workflow_subject.get("tree") != WORKFLOW_TREE:
        refuse("UPSTREAM_SUBJECT_DRIFT")

    intent = request.get("runtime_intent")
    if not isinstance(intent, dict):
        refuse("RUNTIME_EFFECT_INTENT_MISMATCH")
    validate_runtime_intent(intent)
    workflow = request.get("workflow_request")
    if not isinstance(workflow, dict):
        refuse("WORKFLOW_EFFECT_INTERFACE_MISMATCH")
    expected_workflow = {
        "mode": "EFFECT_ADMISSION_REQUEST",
        "effect_owner": CANONICAL_EFFECT_WRITER,
        "job_id": intent["job_id"],
        "tenant_scope": request["tenant_scope"],
        "idempotency_key": intent["idempotency_key"],
        "request_digest": intent["normalized_request_digest"],
        "execution_state": "NOT_EXERCISED",
    }
    if workflow != expected_workflow:
        refuse("WORKFLOW_EFFECT_INTERFACE_MISMATCH")

    target = request.get("target")
    if not isinstance(target, dict) or any(not str(target.get(k, "")).strip() for k in ("provider_id", "resource_id", "action")):
        refuse("TARGET_IDENTITY_MISMATCH")
    provider_subject = target.get("provider_subject")
    if not isinstance(provider_subject, dict) or not str(provider_subject.get("repository", "")).strip():
        refuse("MUTABLE_EFFECT_SUBJECT")
    _h40(provider_subject.get("commit"))
    _h40(provider_subject.get("tree"))

    policy = request.get("policy_binding")
    if not isinstance(policy, dict):
        refuse("APPROVAL_BINDING_MISMATCH")
    _h64(policy.get("policy_digest"), "APPROVAL_BINDING_MISMATCH")
    _h64(policy.get("approval_receipt_digest"), "APPROVAL_BINDING_MISMATCH")
    precondition = request.get("precondition_binding")
    if not isinstance(precondition, dict) or not str(precondition.get("expected_remote_version", "")).strip():
        refuse("PRECONDITION_MISSING")
    _h64(precondition.get("precondition_digest"), "PRECONDITION_MISSING")

    if request.get("expected_evidence_class") != "TARGET_READBACK" or request.get("readback_requirement") != "REQUIRED_BEFORE_COMMIT":
        refuse("READBACK_REQUIRED")
    substrate = request.get("substrate")
    if substrate != {
        "commit": SUBSTRATE_COMMIT,
        "tree": SUBSTRATE_TREE,
        "reuse_mode": "REFERENCE_SUBSTRATE_ONLY",
        "writer_authority": "NONE",
        "evidence_state": "REFERENCE_ONLY",
    }:
        refuse("SUBSTRATE_AUTHORITY_DRIFT")
    external = request.get("external_states")
    if not isinstance(external, dict) or any(value != "NOT_EXERCISED" for value in external.values()):
        refuse("FIXTURE_AS_LIVE_EFFECT")
    _scan_sensitive(request)


def identity_key(request: dict[str, Any]) -> tuple[str, str, str, str]:
    validate_admission_request(request)
    intent = request["runtime_intent"]
    return (
        request["tenant_scope"],
        request["project_scope"],
        intent["effect_id"],
        intent["idempotency_key"],
    )


def classify_duplicate(existing: dict[str, Any], candidate: dict[str, Any]) -> str:
    validate_admission_request(existing)
    validate_admission_request(candidate)
    ei = existing["runtime_intent"]
    ci = candidate["runtime_intent"]
    same_effect_or_key = ei["effect_id"] == ci["effect_id"] or ei["idempotency_key"] == ci["idempotency_key"]
    if same_effect_or_key and (existing["tenant_scope"], existing["project_scope"]) != (candidate["tenant_scope"], candidate["project_scope"]):
        refuse("CROSS_TENANT_EFFECT_IDENTITY")
    if same_effect_or_key and ei["normalized_request_digest"] != ci["normalized_request_digest"]:
        refuse("IDEMPOTENCY_COLLISION")
    if identity_key(existing) == identity_key(candidate):
        return "DUPLICATE_REFUSED"
    return "DISTINCT_EFFECT"


def validate_transition(
    current: str,
    target: str,
    *,
    actor_class: str = "EFFECT_LEDGER",
    attempt_result: str | None = None,
    readback: dict[str, Any] | None = None,
    expected_remote_version: str = "version-7",
) -> None:
    if current not in STATES or target not in STATES:
        refuse("EFFECT_STATE_VOCABULARY_DRIFT")
    if actor_class != "EFFECT_LEDGER":
        refuse("WORKER_OR_PROVIDER_SELF_COMMIT")
    if current in TERMINALS:
        refuse("EVENT_AFTER_EFFECT_TERMINAL")
    if target == "EFFECT_COMMITTED":
        if current in {"EFFECT_ATTEMPTED", "RESULT_UNKNOWN", "RECONCILIATION_REQUIRED"}:
            refuse("READBACK_REQUIRED" if current == "EFFECT_ATTEMPTED" else "UNRESOLVED_EFFECT_COMMIT")
        if attempt_result in {"TIMEOUT", "CONNECTION_LOST", "UNKNOWN"}:
            refuse("TIMEOUT_AS_COMMIT")
        if not isinstance(readback, dict) or readback.get("verified") is not True:
            refuse("READBACK_REQUIRED")
        _h64(readback.get("digest"), "READBACK_REQUIRED")
        if readback.get("remote_version") != expected_remote_version:
            refuse("READBACK_DISAGREEMENT")
    if target not in TRANSITIONS.get(current, set()):
        refuse("ILLEGAL_EFFECT_TRANSITION", f"{current}->{target}")


def validate_task_projection(effect_state: str, task_state: str) -> None:
    if effect_state in {"RESULT_UNKNOWN", "RECONCILIATION_REQUIRED", "COMPENSATION_REQUIRED", "COMPENSATING"} and task_state in {"COMPLETED", "PASS"}:
        refuse("UNRESOLVED_EFFECT_HIDDEN")


def mechanism_receipt(request: dict[str, Any]) -> dict[str, Any]:
    validate_contract(fixed_contract())
    validate_admission_request(request)
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/contract-receipt/v1",
        "contract_state": "PASS",
        "canonical_effect_writer": CANONICAL_EFFECT_WRITER,
        "task_writer": CANONICAL_TASK_WRITER,
        "effect_identity_digest": digest(identity_key(request)),
        "substrate_state": "REFERENCE_ONLY",
        "provider_write_state": "NOT_EXERCISED",
        "target_readback_state": "NOT_EXERCISED",
        "observable_effect_state": "NOT_EXERCISED",
        "task_state": "NOT_EXERCISED",
        "user_outcome_state": "NOT_EXERCISED",
        "release_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_EFFECT_CONTRACT_INTERFACE_ONLY",
    }
