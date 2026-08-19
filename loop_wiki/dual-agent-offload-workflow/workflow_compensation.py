"""Deterministic compensation/cleanup boundary for DA-WF-COMP.

This layer validates effect-owner requests and lineage only. It never performs
provider writes or becomes the canonical effect ledger.
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


class CompensationError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code + (f": {detail}" if detail else ""))


def refuse(code: str, detail: str = "") -> None:
    raise CompensationError(code, detail)


def _h64(value: Any, code: str) -> None:
    if H64.fullmatch(str(value or "")) is None:
        refuse(code)


def validate_compensation_history(submission: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    if submission["job"]["side_effect_class"] != "REVERSIBLE_WRITE":
        refuse("COMPENSATION_REQUIRES_REVERSIBLE_EFFECT")

    lineage: dict[str, Any] | None = None
    for event in history:
        event_type = event.get("event_type")
        payload = event.get("payload", {})
        if not isinstance(payload, dict):
            refuse("COMPENSATION_SCHEMA_MISMATCH")

        if event_type == "COMPENSATION_REQUIRED":
            if payload.get("mode") != "EFFECT_COMPENSATION_REQUEST" or payload.get("effect_owner") != "dual-agent-effect-ledger":
                refuse("DIRECT_PROVIDER_COMPENSATION")
            if payload.get("reversible") is not True:
                refuse("COMPENSATION_REQUIRES_REVERSIBLE_EFFECT")
            if payload.get("original_effect_state") == "UNKNOWN_EFFECT":
                refuse("UNKNOWN_EFFECT_BLIND_COMPENSATION")
            if payload.get("original_effect_state") != "COMMITTED":
                refuse("COMPENSATION_REQUIRES_COMMITTED_EFFECT")
            effect_id = str(payload.get("effect_id", ""))
            parent_key = str(payload.get("parent_idempotency_key", ""))
            compensation_key = str(payload.get("compensation_idempotency_key", ""))
            if not effect_id or not parent_key or not compensation_key or parent_key == compensation_key:
                refuse("COMPENSATION_LINEAGE_MISMATCH")
            _h64(payload.get("original_effect_receipt_digest"), "COMPENSATION_LINEAGE_MISMATCH")
            if payload.get("external_execution_state") != "NOT_EXERCISED":
                refuse("FIXTURE_AS_LIVE_COMPENSATION")
            lineage = {
                "effect_id": effect_id,
                "parent_idempotency_key": parent_key,
                "compensation_idempotency_key": compensation_key,
            }

        elif event_type in {"COMPENSATED", "COMPENSATION_FAILED"}:
            if lineage is None:
                refuse("COMPENSATION_WITHOUT_PARENT")
            if payload.get("effect_owner") != "dual-agent-effect-ledger" or payload.get("effect_id") != lineage["effect_id"]:
                refuse("COMPENSATION_LINEAGE_MISMATCH")
            if payload.get("compensation_idempotency_key") != lineage["compensation_idempotency_key"]:
                refuse("COMPENSATION_LINEAGE_MISMATCH")
            _h64(payload.get("compensation_receipt_digest"), "COMPENSATION_LINEAGE_MISMATCH")
            if payload.get("external_execution_state") != "NOT_EXERCISED":
                refuse("FIXTURE_AS_LIVE_COMPENSATION")

        if payload.get("provider_write") is True:
            refuse("DIRECT_PROVIDER_COMPENSATION")

    result = reducer.reduce_history(submission, history)
    result = dict(result)
    result["compensation_boundary"] = {
        "lineage": lineage,
        "effect_authority": "dual-agent-effect-ledger",
        "external_compensation_state": "NOT_EXERCISED",
        "provider_state": "NOT_EXERCISED",
    }
    result["evidence_ceiling"] = "DETERMINISTIC_COMPENSATION_REQUEST_REPLAY_ONLY"
    result["replay_digest"] = reducer.digest({k: v for k, v in result.items() if k != "replay_digest"})
    return result
