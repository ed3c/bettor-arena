"""Deterministic Human-wait/revalidation boundary for DA-WF-H."""
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


class HumanBoundaryError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise HumanBoundaryError(code, detail)


def _digest(value: Any, code: str) -> None:
    if H64.fullmatch(str(value or "")) is None:
        refuse(code)


def validate_human_history(submission: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    waiting_seen = False
    decision_seen = False
    current_policy = submission["job"]["bindings"]["policy_digest"]
    current_runtime = submission["job"]["bindings"]["runtime_digest"]
    current_source = submission["job"]["source_subject"]

    for event in history:
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            refuse("HUMAN_DECISION_SCHEMA_MISMATCH")

        if event_type == "HUMAN_WAIT_REQUIRED":
            waiting_seen = True
            if payload.get("approval_requirement") not in {"BEFORE_EXTERNAL_WRITE", "BEFORE_IRREVERSIBLE_ACTION"}:
                refuse("HUMAN_WAIT_SCHEMA_MISMATCH")
            _digest(payload.get("required_evidence_digest"), "APPROVAL_BEFORE_REQUIRED_EVIDENCE")

        if event_type in {"HUMAN_APPROVED", "POLICY_REFUSED"} and payload.get("human_decision") in {"APPROVE", "REFUSE"}:
            if not waiting_seen:
                refuse("APPROVAL_BEFORE_WAIT")
            if decision_seen:
                refuse("DUPLICATE_HUMAN_DECISION")
            decision_seen = True
            if payload.get("actor_class") != "HUMAN":
                refuse("WORKER_SELF_APPROVAL")
            if payload.get("job_id") != submission["job"]["job_id"] or payload.get("tenant_scope") != submission["job"]["tenant_scope"]:
                refuse("HUMAN_DECISION_SCOPE_MISMATCH")
            if payload.get("policy_digest") != current_policy or payload.get("runtime_digest") != current_runtime or payload.get("source_subject") != current_source:
                refuse("STALE_HUMAN_DECISION")
            _digest(payload.get("decision_digest"), "HUMAN_DECISION_SCHEMA_MISMATCH")
            _digest(payload.get("evidence_digest"), "APPROVAL_BEFORE_REQUIRED_EVIDENCE")
            if payload.get("evidence_class") != "DETERMINISTIC_FIXTURE":
                refuse("FIXTURE_AS_LIVE_HUMAN_PASS")
            if event_type == "HUMAN_APPROVED" and payload.get("human_decision") != "APPROVE":
                refuse("HUMAN_DECISION_SCHEMA_MISMATCH")
            if event_type == "POLICY_REFUSED" and payload.get("human_decision") != "REFUSE":
                refuse("HUMAN_DECISION_SCHEMA_MISMATCH")

    result = reducer.reduce_history(submission, history)
    result = dict(result)
    result["human_boundary"] = {
        "wait_observed": waiting_seen,
        "decision_observed": decision_seen,
        "live_human_session_state": "NOT_EXERCISED",
        "live_policy_revalidation_state": "NOT_EXERCISED",
    }
    result["evidence_ceiling"] = "DETERMINISTIC_HUMAN_WAIT_REVALIDATION_ONLY"
    result["replay_digest"] = reducer.digest({k: v for k, v in result.items() if k != "replay_digest"})
    return result
