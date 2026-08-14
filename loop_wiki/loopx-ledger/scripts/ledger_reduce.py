#!/usr/bin/env python3
# ruff: noqa: F401,F403,F405  # this module family composes through star imports; the names ruff reads as unused are deliberate re-exports the downstream modules import through.
"""Deterministic LoopX task-state reducer."""

from __future__ import annotations

import copy
from typing import Any

from ledger_common import *
from ledger_contract import validate_gate_observation, validate_human_decision


def find_todo(state: dict[str, Any], todo_id: str | None) -> dict[str, Any]:
    if todo_id is None:
        raise ContractError("event lacks a Todo ID")
    for todo in state["todos"]:
        if todo["todo_id"] == todo_id:
            return todo
    raise ContractError(f"unknown Todo: {todo_id}")


def add_evidence(
    state: dict[str, Any], todo: dict[str, Any], artifact: dict[str, Any]
) -> None:
    artifact_id = artifact["artifact_id"]
    existing = {item["artifact_id"]: item for item in state["evidence"]}
    if artifact_id in existing and existing[artifact_id] != artifact:
        raise ContractError(f"Evidence ID collision: {artifact_id}")
    if artifact_id not in existing:
        state["evidence"].append(copy.deepcopy(artifact))
    if artifact_id not in todo["evidence_refs"]:
        todo["evidence_refs"].append(artifact_id)


def apply_event(
    state: dict[str, Any], event: dict[str, Any], gates: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    next_state = copy.deepcopy(state)
    payload = event["payload"]
    event_type = event["type"]
    if event_type == "TASK_INITIALIZED":
        if event["sequence"] != 0 or next_state["lifecycle"] != "READY":
            raise ContractError(
                "TASK_INITIALIZED is only valid for an empty READY task"
            )
        next_state["lifecycle"] = "ACTIVE"
    elif event_type == "COMMAND_ACCEPTED":
        todo = find_todo(next_state, payload["todo_id"])
        if todo["status"] not in {"READY", "RETRY"}:
            raise ContractError("COMMAND_ACCEPTED Todo is not dispatchable")
        todo["status"] = "DISPATCHED"
        next_state["current_todo_id"] = todo["todo_id"]
    elif event_type == "COMMAND_REJECTED":
        find_todo(next_state, payload["todo_id"])
    elif event_type == "WORKER_OBSERVED":
        todo = find_todo(next_state, payload["todo_id"])
        if todo["status"] != "DISPATCHED":
            raise ContractError("WORKER_OBSERVED Todo is not DISPATCHED")
        todo["status"] = "RUNNING"
        todo["attempts"] += 1
        next_state["quota"]["used"]["attempts"] += 1
        add_evidence(next_state, todo, payload["worker_result_ref"])
    elif event_type == "GATE_OBSERVED":
        todo = find_todo(next_state, payload["todo_id"])
        if todo["status"] != "RUNNING":
            raise ContractError("GATE_OBSERVED Todo is not RUNNING")
        observation = validate_gate_observation(
            payload["gate_observation"], "Gate observation"
        )
        gate_id = observation["gate_id"]
        if gate_id not in gates or observation["verdict"] not in {
            "PASS",
            "FAIL",
            "NOT_RUN",
            "SKIPPED_BY_POLICY",
        }:
            raise ContractError("Gate observation references an unknown Gate/verdict")
        if observation["verdict"] == "PASS" and observation["observed_exit_code"] != 0:
            raise ContractError("Gate PASS lacks exit code zero")
        for artifact in observation["artifact_refs"]:
            validate_artifact(artifact, "gate observation artifact")
            add_evidence(next_state, todo, artifact)
        result = {
            "gate_id": gate_id,
            "attempt": todo["attempts"],
            "verdict": observation["verdict"],
            "observation_ref": copy.deepcopy(observation["artifact_refs"][0]),
            "evaluator_digest": observation["evaluator_digest"],
        }
        todo["gate_results"] = [
            item for item in todo["gate_results"] if item["gate_id"] != gate_id
        ]
        todo["gate_results"].append(result)
        if observation["verdict"] == "FAIL":
            todo["last_failure_ref"] = result["observation_ref"]["artifact_id"]
    elif event_type == "QUOTA_DEBITED":
        delta = payload["quota_delta"]
        if not isinstance(delta, dict) or set(delta) != set(
            next_state["quota"]["used"]
        ):
            raise ContractError("Quota delta shape invalid")
        for key, amount in delta.items():
            if type(amount) is not int or amount < 0:
                raise ContractError("Quota delta cannot be negative")
            next_state["quota"]["used"][key] += amount
    elif event_type == "HITL_REQUESTED":
        todo = find_todo(next_state, payload["todo_id"])
        if todo["status"] not in {"RUNNING", "RETRY"}:
            raise ContractError("HITL request is not attached to a failed/running Todo")
        todo["status"] = "HITL_PENDING"
        next_state["lifecycle"] = "HITL_PENDING"
    elif event_type == "HUMAN_DECISION_RECORDED":
        decision = validate_human_decision(payload["human_decision"], "Human decision")
        if decision["decision_id"] not in next_state["human_decision_refs"]:
            next_state["human_decision_refs"].append(decision["decision_id"])
        if (
            decision["action"] == "SCOPED_EXCEPTION"
            and decision["scope"]["todo_id"] is not None
        ):
            scoped_todo = find_todo(next_state, decision["scope"]["todo_id"])
            scoped_todo["exception_ref"] = decision["decision_id"]
    elif event_type == "STATE_TRANSITION_COMMITTED":
        transition = payload["transition"]
        todo = find_todo(next_state, payload["todo_id"])
        if todo["status"] != transition["from"]:
            raise ContractError("transition source does not match current Todo")
        target = transition["to"]
        if target == "COMPLETED":
            results = {item["gate_id"]: item for item in todo["gate_results"]}
            for gate_id in todo["gate_ids"]:
                if gates[gate_id]["severity"] == "CRITICAL" and (
                    gate_id not in results or results[gate_id]["verdict"] != "PASS"
                ):
                    raise ContractError(
                        "Todo completion lacks every critical Gate PASS"
                    )
            if todo["exception_ref"] is not None:
                raise ContractError("ordinary completion cannot carry an exception")
        if target == "COMPLETED_WITH_EXCEPTION" and todo["exception_ref"] is None:
            raise ContractError("exception completion lacks an admitted Human decision")
        todo["status"] = target
        if target in {"COMPLETED", "COMPLETED_WITH_EXCEPTION"}:
            unfinished = [
                item
                for item in next_state["todos"]
                if item["todo_id"] != todo["todo_id"]
                and item["status"] not in {"COMPLETED", "COMPLETED_WITH_EXCEPTION"}
            ]
            if unfinished:
                next_state["current_todo_id"] = unfinished[0]["todo_id"]
                if unfinished[0]["status"] == "PENDING":
                    unfinished[0]["status"] = "READY"
                next_state["lifecycle"] = "ACTIVE"
            else:
                next_state["current_todo_id"] = None
                next_state["lifecycle"] = (
                    "COMPLETED_WITH_EXCEPTION"
                    if any(
                        item["status"] == "COMPLETED_WITH_EXCEPTION"
                        for item in next_state["todos"]
                    )
                    else "COMPLETED"
                )
        elif target == "HITL_PENDING":
            next_state["lifecycle"] = "HITL_PENDING"
        elif target in {"FAILED", "CANCELLED"}:
            next_state["lifecycle"] = target
            next_state["current_todo_id"] = None
    update_quota_state(next_state)
    next_state["state_revision"] += 1
    next_state["ledger_head_digest"] = event["event_digest"]
    reject_private_fields(next_state, "reduced state")
    return next_state


def update_quota_state(state: dict[str, Any]) -> None:
    limits = state["quota"]["limits"]
    used = state["quota"]["used"]
    pairs = {
        "attempts": "max_attempts",
        "worker_seconds": "max_worker_seconds",
        "output_bytes": "max_output_bytes",
        "tokens": "max_tokens",
        "cost_microunits": "max_cost_microunits",
    }
    exhausted = any(
        limits[limit] is not None and used[key] >= limits[limit]
        for key, limit in pairs.items()
    )
    state["quota"]["state"] = "EXHAUSTED" if exhausted else "AVAILABLE"
    if exhausted and state["lifecycle"] == "ACTIVE":
        state["lifecycle"] = "HITL_PENDING"
        if state["current_todo_id"] is not None:
            find_todo(state, state["current_todo_id"])["status"] = "HITL_PENDING"


def make_snapshot(
    contract: dict[str, Any], state: dict[str, Any], events: list[dict[str, Any]]
) -> dict[str, Any]:
    reducer = {
        "id": "loopx-ledger-reducer",
        "version": "1.0.0",
        "digest": digest(
            {"implementation": "loopx-ledger-reducer", "version": "1.0.0"}
        ),
    }
    snapshot = {
        "schema_version": "loopx/snapshot/v1",
        "subject": copy.deepcopy(contract["subject"]),
        "reducer": reducer,
        "state_revision": state["state_revision"],
        "ledger": {
            "event_count": len(events),
            "last_sequence": len(events) - 1,
            "head_digest": events[-1]["event_digest"] if events else None,
        },
        "canonical_authority": "LOOPX_LEDGER_REDUCER",
        "rebuildable": True,
        "state": copy.deepcopy(state),
        "state_digest": digest(state),
        "content_digest": None,
    }
    raw = copy.deepcopy(snapshot)
    raw.pop("content_digest")
    snapshot["content_digest"] = digest(raw)
    return snapshot
