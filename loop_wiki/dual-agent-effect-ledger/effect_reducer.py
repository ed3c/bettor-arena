"""Pure deterministic canonical effect-ledger reducer for DA-EF-K / #217.

This module serializes effect reservation/state decisions over immutable typed
history. It performs no provider I/O, owns no production database, never writes
LoopX task state, and never promotes the PR #196 reference substrate to writer.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CONTRACT_PATH = ROOT / "effect_contract.py"
PARENT_CONTRACT_COMMIT = "f9b64994979042fc3726c524944a61da4f9cb8b5"
PARENT_CONTRACT_TREE = "e0f0ff4bf0b55627b420ace027043c3b7fee5d1d"
FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp", "http", "requests", "socket", "subprocess", "urllib",
}
SENSITIVE_KEYS = {
    "credential", "credential_value", "password", "private_reasoning",
    "raw_secret", "secret", "secret_value", "token", "token_value",
}
ATTEMPT_OUTCOMES = {
    "RETRYABLE_FAILURE", "SUCCESS", "TIMEOUT", "CONNECTION_LOST", "UNKNOWN",
}
SIDE_EVENTS = {"ATTEMPT_RECORDED", "READBACK_RECORDED", "TASK_PROJECTION"}

spec = importlib.util.spec_from_file_location("dual_agent_effect_contract", CONTRACT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("effect contract unavailable")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class EffectReducerError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise EffectReducerError(code, detail)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def effect_identity_digest(request: dict[str, Any]) -> str:
    return contract.digest(contract.identity_key(request))


def _scan_sensitive(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                refuse("SECRET_OR_REASONING_PERSISTENCE", str(key))
            _scan_sensitive(item)
    elif isinstance(value, list):
        for item in value:
            _scan_sensitive(item)


def assert_deterministic_source(source: str) -> None:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name.split(".", 1)[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [] if node.module is None else [node.module.split(".", 1)[0]]
        else:
            continue
        for name in names:
            if name in FORBIDDEN_IMPORT_ROOTS:
                refuse("PROVIDER_IO_IN_REDUCER", name)


def make_event(
    request: dict[str, Any],
    sequence: int,
    event_type: str,
    payload: dict[str, Any] | None = None,
    previous_event_digest: str = "ROOT",
) -> dict[str, Any]:
    event = {
        "schema": "bettor-arena/dual-agent-effect-ledger/history-event/v1",
        "sequence": sequence,
        "previous_event_digest": previous_event_digest,
        "effect_identity_digest": effect_identity_digest(request),
        "event_type": event_type,
        "payload": {} if payload is None else payload,
    }
    event["event_digest"] = digest(event)
    return event


def chain_events(
    request: dict[str, Any],
    specs: list[tuple[str, dict[str, Any] | None]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    previous = "ROOT"
    for sequence, (event_type, payload) in enumerate(specs):
        event = make_event(request, sequence, event_type, payload, previous)
        result.append(event)
        previous = event["event_digest"]
    return result


def validate_event(
    request: dict[str, Any],
    event: dict[str, Any],
    expected_sequence: int,
    expected_previous: str,
) -> None:
    if event.get("schema") != "bettor-arena/dual-agent-effect-ledger/history-event/v1":
        refuse("EFFECT_HISTORY_SCHEMA_MISMATCH")
    if event.get("sequence") != expected_sequence:
        refuse("EFFECT_HISTORY_SEQUENCE_MISMATCH")
    if event.get("previous_event_digest") != expected_previous:
        refuse("EFFECT_HISTORY_DIGEST_MISMATCH")
    if event.get("effect_identity_digest") != effect_identity_digest(request):
        refuse("EFFECT_HISTORY_IDENTITY_MISMATCH")
    supplied = event.get("event_digest")
    unsigned = {key: value for key, value in event.items() if key != "event_digest"}
    if supplied != digest(unsigned):
        refuse("EFFECT_HISTORY_DIGEST_MISMATCH")
    event_type = event.get("event_type")
    if event_type != "STATE_TRANSITION" and event_type not in SIDE_EVENTS:
        refuse("UNKNOWN_EFFECT_HISTORY_EVENT")
    payload = event.get("payload")
    if not isinstance(payload, dict):
        refuse("EFFECT_HISTORY_SCHEMA_MISMATCH")
    _scan_sensitive(payload)
    if payload.get("loopx_write_mode") not in (None, "PROPOSAL_ONLY"):
        refuse("DIRECT_LOOPX_WRITE")
    if payload.get("canonical_writer") not in (None, contract.CANONICAL_EFFECT_WRITER):
        refuse("DUPLICATE_EFFECT_AUTHORITY")


def reservation_batch(
    existing: list[dict[str, Any]], candidate: dict[str, Any]
) -> dict[str, Any]:
    """Deterministic serialized reservation decision; not a distributed DB claim."""
    contract.validate_admission_request(candidate)
    for prior in existing:
        classification = contract.classify_duplicate(prior, candidate)
        if classification == "DUPLICATE_REFUSED":
            return {
                "decision": "DUPLICATE_REFUSED",
                "execute": False,
                "existing_effect_identity_digest": effect_identity_digest(prior),
            }
    return {
        "decision": "RESERVATION_ACCEPTED",
        "execute": False,
        "effect_identity_digest": effect_identity_digest(candidate),
    }


def _validate_attempt(payload: dict[str, Any], attempts: list[dict[str, Any]], state: str) -> None:
    if state in {"RESULT_UNKNOWN", "RECONCILIATION_REQUIRED"}:
        refuse("UNKNOWN_EFFECT_RETRY_FORBIDDEN")
    attempt_id = str(payload.get("attempt_id", ""))
    if not attempt_id:
        refuse("ATTEMPT_IDENTITY_MISSING")
    if any(item["attempt_id"] == attempt_id for item in attempts):
        refuse("DUPLICATE_ATTEMPT_IDENTITY")
    outcome = payload.get("outcome")
    if outcome not in ATTEMPT_OUTCOMES:
        refuse("ATTEMPT_OUTCOME_INVALID")
    if payload.get("actor_class") != "EFFECT_LEDGER":
        refuse("WORKER_OR_PROVIDER_SELF_COMMIT")
    request_digest = str(payload.get("request_digest", ""))
    if request_digest != str(payload.get("normalized_request_digest", request_digest)):
        refuse("ATTEMPT_REQUEST_DRIFT")
    provider_subject = payload.get("provider_subject")
    if not isinstance(provider_subject, dict):
        refuse("MUTABLE_EFFECT_SUBJECT")
    contract._h40(provider_subject.get("commit"))
    contract._h40(provider_subject.get("tree"))


def _validate_readback(
    request: dict[str, Any], payload: dict[str, Any], readbacks: list[dict[str, Any]]
) -> dict[str, Any]:
    if payload.get("actor_class") != "EFFECT_LEDGER":
        refuse("WORKER_OR_PROVIDER_SELF_COMMIT")
    if payload.get("verified") is not True:
        refuse("READBACK_REQUIRED")
    contract._h64(payload.get("digest"), "READBACK_REQUIRED")
    expected = request["precondition_binding"]["expected_remote_version"]
    if payload.get("remote_version") != expected:
        refuse("READBACK_DISAGREEMENT")
    target = request["target"]
    if payload.get("provider_id") != target["provider_id"] or payload.get("resource_id") != target["resource_id"] or payload.get("action") != target["action"]:
        refuse("READBACK_TARGET_MISMATCH")
    readback = {
        "remote_version": payload["remote_version"],
        "digest": payload["digest"],
        "verified": True,
        "provider_id": payload["provider_id"],
        "resource_id": payload["resource_id"],
        "action": payload["action"],
    }
    readbacks.append(readback)
    return readback


def reduce_effect_history(
    request: dict[str, Any], history: list[dict[str, Any]]
) -> dict[str, Any]:
    contract.validate_contract(contract.fixed_contract())
    contract.validate_admission_request(request)
    state = "EFFECT_PROPOSED"
    previous = "ROOT"
    attempts: list[dict[str, Any]] = []
    readbacks: list[dict[str, Any]] = []
    commit_count = 0

    for expected_sequence, event in enumerate(history):
        validate_event(request, event, expected_sequence, previous)
        event_type = event["event_type"]
        payload = event["payload"]

        if state in contract.TERMINALS:
            if state == "EFFECT_COMMITTED" and event_type == "STATE_TRANSITION" and payload.get("target_state") == "EFFECT_COMMITTED":
                refuse("DOUBLE_COMMIT")
            refuse("EVENT_AFTER_EFFECT_TERMINAL", state)

        if event_type == "ATTEMPT_RECORDED":
            _validate_attempt(payload, attempts, state)
            attempts.append({
                "attempt_id": str(payload["attempt_id"]),
                "outcome": str(payload["outcome"]),
                "request_digest": str(payload["request_digest"]),
                "provider_subject": payload["provider_subject"],
            })
            previous = event["event_digest"]
            continue

        if event_type == "READBACK_RECORDED":
            _validate_readback(request, payload, readbacks)
            previous = event["event_digest"]
            continue

        if event_type == "TASK_PROJECTION":
            contract.validate_task_projection(state, str(payload.get("task_state", "NOT_EXERCISED")))
            previous = event["event_digest"]
            continue

        target = str(payload.get("target_state", ""))
        actor_class = str(payload.get("actor_class", "EFFECT_LEDGER"))
        attempt_result = payload.get("attempt_result")
        latest_readback = None if not readbacks else readbacks[-1]
        if target == "EFFECT_ATTEMPTED" and not attempts:
            refuse("ATTEMPT_DENOMINATOR_MISSING")
        if target == "EFFECT_COMMITTED":
            if not attempts:
                refuse("ATTEMPT_DENOMINATOR_MISSING")
            if commit_count:
                refuse("DOUBLE_COMMIT")
            if latest_readback is None:
                refuse("READBACK_REQUIRED")
        try:
            contract.validate_transition(
                state,
                target,
                actor_class=actor_class,
                attempt_result=None if attempt_result is None else str(attempt_result),
                readback=latest_readback,
                expected_remote_version=request["precondition_binding"]["expected_remote_version"],
            )
        except contract.EffectContractError as exc:
            raise EffectReducerError(exc.code, str(exc)) from exc
        state = target
        if state == "EFFECT_COMMITTED":
            commit_count += 1
        previous = event["event_digest"]

    result = {
        "schema": "bettor-arena/dual-agent-effect-ledger/reducer-result/v1",
        "parent_contract_subject": {
            "commit": PARENT_CONTRACT_COMMIT,
            "tree": PARENT_CONTRACT_TREE,
        },
        "canonical_effect_writer": contract.CANONICAL_EFFECT_WRITER,
        "canonical_task_writer": contract.CANONICAL_TASK_WRITER,
        "effect_identity_digest": effect_identity_digest(request),
        "effect_state": state,
        "attempts": attempts,
        "attempt_count": len(attempts),
        "readbacks": readbacks,
        "accepted_commit_count": commit_count,
        "history_head": previous,
        "history_count": len(history),
        "loopx_write_mode": "PROPOSAL_ONLY",
        "provider_io_state": "NOT_EXERCISED",
        "production_database_state": "NOT_EXERCISED",
        "distributed_lease_state": "NOT_EXERCISED",
        "task_state": "NOT_EXERCISED",
        "user_outcome_state": "NOT_EXERCISED",
        "release_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_EFFECT_LEDGER_REDUCER_ONLY",
    }
    result["replay_digest"] = digest(result)
    return result


def replay_bytes(request: dict[str, Any], history: list[dict[str, Any]]) -> bytes:
    return canonical_json(reduce_effect_history(request, history)).encode("utf-8")
