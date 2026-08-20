"""Deterministic retry/timer/restart/cancel boundary for DA-WF-R.

This layer validates typed operational history around the canonical DA-WF-K
reducer. It performs no wall-clock, network, provider, or canonical-ledger I/O.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_workflow_reducer", ROOT / "workflow_reducer.py")
assert SPEC is not None and SPEC.loader is not None
reducer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reducer)

H64 = re.compile(r"^[0-9a-f]{64}$")
ATTEMPT = re.compile(r"^attempt-[A-Za-z0-9._:-]+$")


class BoundaryError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise BoundaryError(code, detail)


def _h64(value: Any, code: str) -> str:
    text = str(value or "")
    if H64.fullmatch(text) is None:
        refuse(code)
    return text


def validate_operational_history(submission: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate retry lineage and typed timer/cancel/deadline observations, then replay."""
    state = "SUBMITTED"
    current_attempt = "attempt-1"
    retries = 0
    max_attempts = submission["job"]["retry_policy"]["max_attempts"]

    for event in history:
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            refuse("OPERATIONAL_HISTORY_SCHEMA_MISMATCH")
        if "wall_clock" in payload or "now" in payload:
            refuse("WALL_CLOCK_DECISION_SOURCE")

        if event_type == "RETRY_REQUESTED":
            retries += 1
            if retries > max_attempts - 1:
                refuse("RETRY_BUDGET_EXCEEDED")
            if payload.get("parent_attempt_id") != current_attempt:
                refuse("LOST_PARENT_ATTEMPT")
            next_attempt = str(payload.get("next_attempt_id", ""))
            if ATTEMPT.fullmatch(next_attempt) is None or next_attempt == current_attempt:
                refuse("INVALID_NEXT_ATTEMPT")
            current_attempt = next_attempt

        elif event_type == "RETRY_READY":
            if payload.get("attempt_id") != current_attempt:
                refuse("LOST_PARENT_ATTEMPT")
            _h64(payload.get("timer_receipt_digest"), "UNTYPED_TIMER")

        elif event_type == "DEADLINE_EXPIRED":
            if payload.get("decision_source") != "HISTORY_EVENT":
                refuse("WALL_CLOCK_DECISION_SOURCE")
            _h64(payload.get("observation_digest"), "UNTYPED_DEADLINE")

        elif event_type == "CANCEL_REQUESTED":
            if payload.get("requested_from") != state:
                refuse("CANCEL_STATE_MISMATCH")
            if payload.get("decision_source") != "HISTORY_EVENT":
                refuse("CANCEL_STATE_MISMATCH")

        elif event_type == "CANCEL_STARTED":
            _h64(payload.get("cancellation_activity_digest"), "UNTYPED_CANCELLATION")

        elif event_type == "CANCELLED":
            _h64(payload.get("cancellation_receipt_digest"), "UNTYPED_CANCELLATION")

        if event_type in reducer.EVENT_TO_STATE:
            state = reducer.EVENT_TO_STATE[event_type]

    result = reducer.reduce_history(submission, history)
    result = dict(result)
    result["operational_boundary"] = {
        "retry_lineage_state": "PASS",
        "current_attempt_id": current_attempt,
        "typed_timer_state": "PASS",
        "typed_cancel_state": "PASS",
        "physical_transport_cancel_state": "NOT_EXERCISED",
        "durable_engine_restart_state": "NOT_EXERCISED",
    }
    result["evidence_ceiling"] = "DETERMINISTIC_RETRY_TIMER_RESTART_CANCEL_ONLY"
    result["replay_digest"] = reducer.digest({k: v for k, v in result.items() if k != "replay_digest"})
    return result
