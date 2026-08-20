"""Deterministic provider-attempt/readback adapter boundary for DA-EF-A / #219.

The adapter builds and validates provider observation packets only. It never
performs provider I/O and never commits canonical effect/task state.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_effect_policy", ROOT / "effect_policy_gate.py")
assert SPEC is not None and SPEC.loader is not None
policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(policy)
reducer = policy.reducer
contract = reducer.contract
H64 = re.compile(r"^[0-9a-f]{64}$")
SENSITIVE_KEYS = {"credential", "credential_value", "password", "raw_secret", "secret", "secret_value", "token", "token_value"}


class ProviderBoundaryError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise ProviderBoundaryError(code, detail)


def _h64(value: Any, code: str) -> str:
    text = str(value or "")
    if H64.fullmatch(text) is None:
        refuse(code)
    return text


def _scan_sensitive(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                refuse("RAW_CREDENTIAL", str(key))
            _scan_sensitive(item)
    elif isinstance(value, list):
        for item in value:
            _scan_sensitive(item)


def build_attempt_packet(
    authorization: dict[str, Any], *, credential_handle: str, route_kind: str = "API"
) -> dict[str, Any]:
    if authorization.get("schema") != "bettor-arena/dual-agent-effect-ledger/execution-authorization/v1":
        refuse("AUTHORIZATION_PACKET_MISMATCH")
    if authorization.get("mode") != "EFFECT_EXECUTION_AUTHORIZATION":
        refuse("AUTHORIZATION_PACKET_MISMATCH")
    if authorization.get("canonical_effect_writer") != contract.CANONICAL_EFFECT_WRITER:
        refuse("PROVIDER_SELF_COMMIT")
    if authorization.get("provider_io_state") != "NOT_EXERCISED":
        refuse("FIXTURE_AS_LIVE_PROVIDER_PASS")
    provider_subject = authorization.get("provider_subject")
    if not isinstance(provider_subject, dict):
        refuse("MUTABLE_PROVIDER_SUBJECT")
    contract._h40(provider_subject.get("commit"))
    contract._h40(provider_subject.get("tree"))
    if not isinstance(credential_handle, str) or not credential_handle.startswith("secret://"):
        refuse("RAW_CREDENTIAL")
    if route_kind not in {"API", "BROWSER"}:
        refuse("ROUTE_KIND_MISMATCH")
    packet = {
        "schema": "bettor-arena/dual-agent-effect-ledger/provider-attempt/v1",
        "mode": "PROVIDER_ATTEMPT_REQUEST",
        "effect_identity_digest": authorization["effect_identity_digest"],
        "attempt_id": authorization["attempt_id"],
        "tenant_scope": authorization["tenant_scope"],
        "project_scope": authorization["project_scope"],
        "provider_id": authorization["provider_id"],
        "resource_id": authorization["resource_id"],
        "action": authorization["action"],
        "provider_subject": provider_subject,
        "normalized_request_digest": authorization["normalized_request_digest"],
        "policy_digest": authorization["policy_digest"],
        "approval_receipt_digest": authorization["approval_receipt_digest"],
        "precondition_digest": authorization["precondition_digest"],
        "expected_remote_version": authorization["expected_remote_version"],
        "credential_handle": credential_handle,
        "route_kind": route_kind,
        "provider_native_idempotency_is_authority": False,
        "canonical_write_mode": "OBSERVATION_ONLY",
        "provider_io_state": "NOT_EXERCISED",
    }
    _scan_sensitive({k: v for k, v in packet.items() if k != "credential_handle"})
    return packet


def classify_attempt_result(packet: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    if packet.get("schema") != "bettor-arena/dual-agent-effect-ledger/provider-attempt/v1":
        refuse("PROVIDER_PACKET_MISMATCH")
    if result.get("schema") != "bettor-arena/dual-agent-effect-ledger/provider-observation/v1":
        refuse("PROVIDER_RESULT_SCHEMA_MISMATCH")
    _scan_sensitive(result)
    for key in ("effect_identity_digest", "attempt_id", "provider_id", "resource_id", "action"):
        if result.get(key) != packet.get(key):
            refuse("PROVIDER_TARGET_MISMATCH")
    provider_subject = result.get("provider_subject")
    if provider_subject != packet.get("provider_subject"):
        refuse("MUTABLE_PROVIDER_SUBJECT")
    if result.get("canonical_write_mode") != "OBSERVATION_ONLY":
        refuse("PROVIDER_SELF_COMMIT")
    if result.get("provider_native_idempotency_is_authority") is not False:
        refuse("PROVIDER_IDEMPOTENCY_AS_AUTHORITY")
    if result.get("evidence_class") != "DETERMINISTIC_FIXTURE":
        refuse("FIXTURE_AS_LIVE_PROVIDER_PASS")
    if result.get("cleanup_state") != "CLEAN":
        refuse("CLEANUP_RESIDUE_HIDDEN")
    _h64(result.get("provider_result_digest"), "PROVIDER_RESULT_SCHEMA_MISMATCH")
    outcome = result.get("outcome")
    if outcome not in {"SUCCESS", "FAILURE", "TIMEOUT", "CONNECTION_LOST"}:
        refuse("PROVIDER_RESULT_SCHEMA_MISMATCH")
    if result.get("canonical_effect_state") == "EFFECT_COMMITTED":
        refuse("PROVIDER_SELF_COMMIT")
    if outcome == "SUCCESS":
        proposal = "EFFECT_OBSERVED_PENDING_READBACK"
    elif outcome == "FAILURE":
        proposal = "ATTEMPT_FAILED"
    else:
        proposal = "RESULT_UNKNOWN"
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/provider-result-receipt/v1",
        "effect_identity_digest": packet["effect_identity_digest"],
        "attempt_id": packet["attempt_id"],
        "outcome": outcome,
        "effect_state_proposal": proposal,
        "provider_result_digest": result["provider_result_digest"],
        "provider_native_idempotency_observed": bool(result.get("provider_native_idempotency_observed", False)),
        "provider_native_idempotency_is_authority": False,
        "route_kind": packet["route_kind"],
        "readback_state": "REQUIRED",
        "canonical_write_mode": "OBSERVATION_ONLY",
        "provider_io_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_PROVIDER_OBSERVATION_ONLY",
    }


def validate_target_readback(
    packet: dict[str, Any], observation: dict[str, Any], readback: dict[str, Any]
) -> dict[str, Any]:
    if observation.get("schema") != "bettor-arena/dual-agent-effect-ledger/provider-result-receipt/v1":
        refuse("PROVIDER_RESULT_SCHEMA_MISMATCH")
    if observation.get("effect_identity_digest") != packet.get("effect_identity_digest") or observation.get("attempt_id") != packet.get("attempt_id"):
        refuse("PROVIDER_TARGET_MISMATCH")
    if observation.get("outcome") == "FAILURE":
        refuse("READBACK_NOT_ADMISSIBLE_FOR_FAILED_ATTEMPT")
    if readback.get("schema") != "bettor-arena/dual-agent-effect-ledger/target-readback/v1":
        refuse("READBACK_SCHEMA_MISMATCH")
    _scan_sensitive(readback)
    for key in ("provider_id", "resource_id", "action"):
        if readback.get(key) != packet.get(key):
            refuse("READBACK_TARGET_MISMATCH")
    if readback.get("verified") is not True:
        refuse("READBACK_REQUIRED")
    _h64(readback.get("digest"), "READBACK_REQUIRED")
    if readback.get("remote_version") != packet.get("expected_remote_version"):
        refuse("READBACK_DISAGREEMENT")
    expected_evidence = "API_READBACK_FIXTURE" if packet.get("route_kind") == "API" else "BROWSER_READBACK_FIXTURE"
    if readback.get("evidence_class") != expected_evidence:
        refuse("BROWSER_API_EVIDENCE_SUBSTITUTION")
    if readback.get("cleanup_state") != "CLEAN":
        refuse("CLEANUP_RESIDUE_HIDDEN")
    return {
        "schema": "bettor-arena/dual-agent-effect-ledger/readback-receipt/v1",
        "effect_identity_digest": packet["effect_identity_digest"],
        "attempt_id": packet["attempt_id"],
        "provider_id": packet["provider_id"],
        "resource_id": packet["resource_id"],
        "action": packet["action"],
        "remote_version": readback["remote_version"],
        "digest": readback["digest"],
        "verified": True,
        "route_kind": packet["route_kind"],
        "commit_authority": contract.CANONICAL_EFFECT_WRITER,
        "canonical_write_mode": "OBSERVATION_ONLY",
        "provider_io_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_TARGET_READBACK_ONLY",
    }


def propose_commit(packet: dict[str, Any], observation: dict[str, Any], readback_receipt: dict[str, Any] | None) -> dict[str, Any]:
    if observation.get("outcome") not in {"SUCCESS", "TIMEOUT", "CONNECTION_LOST"}:
        refuse("COMMIT_NOT_ADMISSIBLE")
    if readback_receipt is None or readback_receipt.get("verified") is not True:
        refuse("READBACK_REQUIRED")
    if readback_receipt.get("effect_identity_digest") != packet.get("effect_identity_digest"):
        refuse("READBACK_TARGET_MISMATCH")
    return {
        "mode": "EFFECT_COMMIT_PROPOSAL",
        "canonical_effect_writer": contract.CANONICAL_EFFECT_WRITER,
        "effect_identity_digest": packet["effect_identity_digest"],
        "attempt_id": packet["attempt_id"],
        "readback_digest": readback_receipt["digest"],
        "provider_result_digest": observation["provider_result_digest"],
        "canonical_write_mode": "PROPOSAL_ONLY",
        "external_effect_state": "NOT_EXERCISED",
        "task_state": "NOT_EXERCISED",
        "user_outcome_state": "NOT_EXERCISED",
        "release_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_PROVIDER_READBACK_ADAPTER_ONLY",
    }
