#!/usr/bin/env python3
# ruff: noqa: F401,F403,F405  # this module family composes through star imports; the names ruff reads as unused are deliberate re-exports the downstream modules import through.
"""LoopX Ledger event shape and authority validator."""

from __future__ import annotations

from typing import Any
from ledger_common import *
from ledger_contract_helpers import *


def validate_event_shape(
    event: Any,
    subject: dict[str, Any],
    sequence: int,
    previous_digest: str | None,
    *,
    command_ids: set[str] | None = None,
    prior_event_ids: set[str] | None = None,
) -> dict[str, Any]:
    event = exact_object(event, EVENT_KEYS, "event")
    if (
        event["schema_version"] != "loopx/event/v1"
        or validate_subject(event["subject"], "event.subject") != subject
    ):
        raise ContractError("event version/subject mismatch")
    stable_id(event["event_id"], "event.event_id")
    if (
        event["sequence"] != sequence
        or event["previous_event_digest"] != previous_digest
    ):
        raise ContractError("event sequence or previous digest mismatch")
    sha256_ref(event["event_digest"], "event.event_digest")
    validate_event_digest(event, "event")
    validate_rfc3339_utc(event["occurred_at"], "event.occurred_at")
    actor = event["actor"]
    if not isinstance(actor, dict) or set(actor) != {"actor_id", "class", "authority"}:
        raise ContractError("event actor invalid")
    stable_id(actor["actor_id"], "event.actor.actor_id")
    payload = exact_object(event["payload"], EVENT_PAYLOAD_KEYS, "event.payload")
    for key in ("request_ref", "worker_result_ref"):
        if payload[key] is not None:
            validate_artifact(payload[key], f"event.payload.{key}")
    if payload["gate_observation"] is not None:
        validate_gate_observation(
            payload["gate_observation"], "event.payload.gate_observation"
        )
    if payload["human_decision"] is not None:
        validate_human_decision(
            payload["human_decision"], "event.payload.human_decision"
        )
    if payload["quota_delta"] is not None:
        if not isinstance(payload["quota_delta"], dict) or set(
            payload["quota_delta"]
        ) != {
            "attempts",
            "worker_seconds",
            "output_bytes",
            "tokens",
            "cost_microunits",
        }:
            raise ContractError("event.payload.quota_delta shape invalid")
        if any(
            type(amount) is not int or amount < 0
            for amount in payload["quota_delta"].values()
        ):
            raise ContractError("event.payload.quota_delta cannot be negative")
    if payload["transition"] is not None:
        validate_transition(
            payload["transition"], "event.payload.transition", prior_event_ids
        )
    expected = {
        "TASK_INITIALIZED": ("LOOPX", "STATE_COMMIT", {"request_ref"}),
        "COMMAND_ACCEPTED": ("LOOPX", "STATE_COMMIT", {"command_id"}),
        "COMMAND_REJECTED": ("LOOPX", "STATE_COMMIT", {"command_id"}),
        "WORKER_OBSERVED": ("WORKER", "OBSERVATION", {"worker_result_ref"}),
        "GATE_OBSERVED": ("GATE_ENGINE", "OBSERVATION", {"gate_observation"}),
        "QUOTA_DEBITED": ("LOOPX", "STATE_COMMIT", {"quota_delta"}),
        "HITL_REQUESTED": ("LOOPX", "STATE_COMMIT", {"transition"}),
        "HUMAN_DECISION_RECORDED": ("HUMAN", "DECISION", {"human_decision"}),
        "STATE_TRANSITION_COMMITTED": ("LOOPX", "STATE_COMMIT", {"transition"}),
    }
    if event["type"] not in expected:
        raise ContractError(f"unsupported event type: {event['type']}")
    cls, authority, required = expected[event["type"]]
    if (actor.get("class"), actor.get("authority")) != (cls, authority):
        raise ContractError("event actor authority mismatch")
    populated = {key for key, value in payload.items() if value is not None}
    allowed = set(required) | {"todo_id"}
    if event["type"] in {"COMMAND_ACCEPTED", "COMMAND_REJECTED", "WORKER_OBSERVED"}:
        allowed.add("command_id")
        command_id = payload["command_id"]
        if command_ids is not None and command_id not in command_ids:
            raise ContractError(f"event references an unknown command: {command_id}")
    if not required <= populated or populated - allowed:
        raise ContractError(f"event payload authority drift: {sorted(populated)}")
    if event["type"] == "WORKER_OBSERVED" and payload["gate_observation"] is not None:
        raise ContractError("Worker attempted to submit a Gate verdict")
    reject_private_fields(event, "event")
    return event
