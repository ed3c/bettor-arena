"""Pure deterministic reducer/replay adapter for Dual-Agent offload history.

The reducer consumes ordered typed history only. It emits proposals and receipts;
it never contacts a provider, reads wall-clock/random/network state, appends the
canonical LoopX ledger, or executes an external effect.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
CONTRACT_PATH = ROOT / "workflow_contract.py"
PARENT_CONTRACT_COMMIT = "56cb74650bda20adfe84cc522977419158437f53"
PARENT_CONTRACT_TREE = "3b2f1a351296f87f6570a182b2d72b46be181bac"
FORBIDDEN_IMPORT_ROOTS = {
    "aiohttp", "http", "random", "requests", "socket", "subprocess", "time", "urllib",
}
SENSITIVE_KEYS = {
    "credential_value", "private_reasoning", "raw_secret", "secret_value", "token_value",
}

spec = importlib.util.spec_from_file_location("dual_agent_workflow_contract", CONTRACT_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("workflow contract unavailable")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)

EVENT_TO_STATE = {
    "ADMISSION_REQUESTED": "ADMISSION_PENDING",
    "ADMISSION_ALLOWED": "ADMITTED",
    "DELIVERY_REQUESTED": "DELIVERY_PENDING",
    "REMOTE_DISPATCHED": "REMOTE_DISPATCHED",
    "EXECUTION_STARTED": "RUNNING",
    "RESULT_WAITING": "WAITING_FOR_RESULT",
    "RESULT_RECEIVED": "VERIFYING",
    "RESULT_VERIFIED": "RECONCILING",
    "RECONCILED": "COMPLETED",
    "HUMAN_WAIT_REQUIRED": "WAITING_FOR_HUMAN",
    "HUMAN_APPROVED": "ADMITTED",
    "RETRY_REQUESTED": "RETRY_SCHEDULED",
    "RETRY_READY": "DELIVERY_PENDING",
    "CANCEL_REQUESTED": "CANCEL_REQUESTED",
    "CANCEL_STARTED": "CANCELLING",
    "CANCELLED": "CANCELLED",
    "DEADLINE_EXPIRED": "DEADLINE_EXPIRED",
    "POLICY_REFUSED": "POLICY_REFUSED",
    "RUNTIME_ABSENT": "RUNTIME_ABSENT",
    "ACTIVITY_FAILED": "ACTIVITY_FAILED",
    "RESULT_STALE": "RESULT_STALE",
    "RESULT_REFUSED": "RESULT_REFUSED",
    "COMPENSATION_REQUIRED": "COMPENSATING",
    "COMPENSATED": "COMPENSATED",
    "COMPENSATION_FAILED": "COMPENSATION_FAILED",
    "CLEANUP_FAILED": "FAILED_CLEANUP",
    "FAILED": "FAILED",
}
SIDE_EVENTS = {"EFFECT_REQUESTED"}


class ReplayError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise ReplayError(code, detail)


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _scan_sensitive(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                refuse("SECRET_OR_REASONING_LEAK", str(key))
            _scan_sensitive(item)
    elif isinstance(value, list):
        for item in value:
            _scan_sensitive(item)


def make_event(
    submission: dict[str, Any],
    sequence: int,
    event_type: str,
    payload: dict[str, Any] | None = None,
    previous_event_digest: str = "ROOT",
) -> dict[str, Any]:
    event = {
        "schema": "bettor-arena/dual-agent-offload-workflow/history-event/v1",
        "sequence": sequence,
        "previous_event_digest": previous_event_digest,
        "workflow_subject": submission["workflow_subject"],
        "job_id": submission["job"]["job_id"],
        "event_type": event_type,
        "payload": {} if payload is None else payload,
    }
    event["event_digest"] = digest(event)
    return event


def chain_events(
    submission: dict[str, Any],
    specs: list[tuple[str, dict[str, Any] | None]],
) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    previous = "ROOT"
    for sequence, (event_type, payload) in enumerate(specs):
        event = make_event(submission, sequence, event_type, payload, previous)
        history.append(event)
        previous = event["event_digest"]
    return history


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
                refuse("NONDETERMINISTIC_REDUCER_SOURCE", name)


def validate_event(
    submission: dict[str, Any],
    event: dict[str, Any],
    expected_sequence: int,
    expected_previous: str,
) -> None:
    if event.get("schema") != "bettor-arena/dual-agent-offload-workflow/history-event/v1":
        refuse("HISTORY_SCHEMA_MISMATCH")
    if event.get("sequence") != expected_sequence:
        refuse("HISTORY_SEQUENCE_MISMATCH")
    if event.get("previous_event_digest") != expected_previous:
        refuse("HISTORY_DIGEST_MISMATCH")
    if event.get("workflow_subject") != submission.get("workflow_subject"):
        refuse("HISTORY_SUBJECT_MISMATCH")
    if event.get("job_id") != submission.get("job", {}).get("job_id"):
        refuse("HISTORY_SUBJECT_MISMATCH")
    supplied_digest = event.get("event_digest")
    unsigned = {key: value for key, value in event.items() if key != "event_digest"}
    if supplied_digest != digest(unsigned):
        refuse("HISTORY_DIGEST_MISMATCH")
    event_type = event.get("event_type")
    if event_type not in EVENT_TO_STATE and event_type not in SIDE_EVENTS:
        refuse("UNKNOWN_HISTORY_EVENT")
    payload = event.get("payload")
    if not isinstance(payload, dict):
        refuse("HISTORY_SCHEMA_MISMATCH")
    _scan_sensitive(payload)
    if payload.get("loopx_write_mode") not in (None, "PROPOSAL_ONLY"):
        refuse("DIRECT_LOOPX_WRITE")


def _effect_request(
    submission: dict[str, Any],
    event: dict[str, Any],
) -> dict[str, Any]:
    if submission["job"]["side_effect_class"] == "READ_ONLY":
        refuse("UNEXPECTED_EFFECT_REQUEST")
    payload = event["payload"]
    if payload.get("mode") != "EFFECT_ADMISSION_REQUEST":
        refuse("EFFECT_OWNER_BYPASS")
    if payload.get("effect_owner") != "dual-agent-effect-ledger":
        refuse("EFFECT_OWNER_BYPASS")
    idempotency_key = payload.get("idempotency_key")
    if not isinstance(idempotency_key, str) or not idempotency_key:
        refuse("EFFECT_OWNER_BYPASS")
    return {
        "mode": "EFFECT_ADMISSION_REQUEST",
        "effect_owner": "dual-agent-effect-ledger",
        "job_id": submission["job"]["job_id"],
        "tenant_scope": submission["job"]["tenant_scope"],
        "idempotency_key": idempotency_key,
        "request_digest": digest(payload),
        "execution_state": "NOT_EXERCISED",
    }


def reduce_history(
    submission: dict[str, Any],
    history: list[dict[str, Any]],
) -> dict[str, Any]:
    contract.validate_submission(submission)
    state = "SUBMITTED"
    previous = "ROOT"
    retries = 0
    max_attempts = submission["job"]["retry_policy"]["max_attempts"]
    effect_requests: list[dict[str, Any]] = []

    for expected_sequence, event in enumerate(history):
        validate_event(submission, event, expected_sequence, previous)
        event_type = event["event_type"]

        if state == "RESULT_STALE" and event_type in {
            "RESULT_RECEIVED", "RESULT_VERIFIED", "RECONCILED"
        }:
            refuse("STALE_RESULT_RECONCILIATION")
        if state in contract.TERMINALS:
            refuse("EVENT_AFTER_TERMINAL", state)

        if event_type == "EFFECT_REQUESTED":
            effect_requests.append(_effect_request(submission, event))
            previous = event["event_digest"]
            continue

        if event_type == "RETRY_REQUESTED":
            retries += 1
            if retries > max_attempts - 1:
                refuse("RETRY_BUDGET_EXCEEDED")

        target = EVENT_TO_STATE[event_type]
        try:
            contract.validate_transition(state, target)
        except contract.WorkflowContractError as exc:
            if exc.code == "HUMAN_WAIT_AS_SUCCESS":
                refuse("HUMAN_WAIT_AS_SUCCESS")
            if exc.code == "TERMINAL_COMPLETION_LAUNDERING":
                refuse("TERMINAL_COMPLETION_LAUNDERING")
            refuse("ILLEGAL_HISTORY_TRANSITION", f"{state}->{target}")

        state = target
        previous = event["event_digest"]

    proposal = {
        "mode": "PROPOSAL_ONLY",
        "target_authority": "loopx-ledger",
        "event_type": "WORKFLOW_STATE_OBSERVED",
        "workflow_state": state,
        "job_id": submission["job"]["job_id"],
        "workflow_subject": submission["workflow_subject"],
        "history_head": previous,
        "history_count": len(history),
    }
    result = {
        "schema": "bettor-arena/dual-agent-offload-workflow/replay-result/v1",
        "parent_contract_subject": {
            "commit": PARENT_CONTRACT_COMMIT,
            "tree": PARENT_CONTRACT_TREE,
        },
        "workflow_state": state,
        "retry_count": retries,
        "effect_requests": effect_requests,
        "loopx_proposal": proposal,
        "transport_state": "NOT_EXERCISED",
        "provider_state": "NOT_EXERCISED",
        "effect_state": "NOT_EXERCISED",
        "gate_state": "NOT_EXERCISED",
        "task_state": "NOT_EXERCISED",
        "user_outcome_state": "NOT_EXERCISED",
        "release_state": "NOT_EXERCISED",
        "evidence_ceiling": "DETERMINISTIC_WORKFLOW_REPLAY_ONLY",
    }
    result["replay_digest"] = digest(result)
    return result


def replay_bytes(
    submission: dict[str, Any],
    history: list[dict[str, Any]],
) -> bytes:
    return canonical_json(reduce_history(submission, history)).encode("utf-8")
