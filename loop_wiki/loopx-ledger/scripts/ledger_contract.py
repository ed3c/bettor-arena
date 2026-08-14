#!/usr/bin/env python3
# ruff: noqa: F401,F403,F405  # this module family composes through star imports; the names ruff reads as unused are deliberate re-exports the downstream modules import through.
"""LoopX Ledger contract and store validators."""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

from ledger_common import *
from ledger_contract_helpers import *
from ledger_event import validate_event_shape


def validate_contract(value: Any) -> dict[str, Any]:
    contract = exact_object(value, CONTRACT_KEYS, "ledger contract")
    if contract["schema_version"] != "loopx/ledger-contract/v1":
        raise ContractError("ledger contract schema version drifted")
    subject = validate_subject(contract["subject"], "ledger contract.subject")
    gates = contract["gate_definitions"]
    commands = contract["commands"]
    if not isinstance(gates, list) or not gates or not isinstance(commands, list):
        raise ContractError("ledger contract gates/commands are invalid")
    gate_ids: set[str] = set()
    for index, gate in enumerate(gates):
        if (
            not isinstance(gate, dict)
            or gate.get("schema_version") != "loopx/gate-definition/v1"
        ):
            raise ContractError(f"gate_definitions[{index}] is not LoopX Contract v1")
        gate_id = stable_id(gate.get("gate_id"), f"gate_definitions[{index}].gate_id")
        if gate_id in gate_ids or gate.get("severity") not in {"CRITICAL", "ADVISORY"}:
            raise ContractError(f"gate_definitions[{index}] duplicate/invalid")
        execution = gate.get("execution")
        if (
            not isinstance(execution, dict)
            or "shell" in execution
            or "raw_command" in execution
        ):
            raise ContractError(f"gate_definitions[{index}] exposes a raw shell")
        gate_ids.add(gate_id)
    command_ids: set[str] = set()
    for index, command in enumerate(commands):
        if (
            not isinstance(command, dict)
            or command.get("schema_version") != "loopx/command/v1"
        ):
            raise ContractError(f"commands[{index}] is not LoopX Contract v1")
        command_id = stable_id(
            command.get("command_id"), f"commands[{index}].command_id"
        )
        if command_id in command_ids:
            raise ContractError("duplicate command ID")
        if (
            validate_subject(command.get("subject"), f"commands[{index}].subject")
            != subject
        ):
            raise ContractError("command subject mismatch")
        command_ids.add(command_id)
    state = validate_initial_state(contract["initial_state"], subject, gate_ids)
    if (
        state["state_revision"] != 0
        or state["ledger_head_digest"] is not None
        or state["lifecycle"] != "READY"
    ):
        raise ContractError(
            "initial state must be READY at revision zero with no ledger head"
        )
    raw = copy.deepcopy(contract)
    raw.pop("contract_digest")
    if contract["contract_digest"] != digest(raw):
        raise ContractError("ledger contract digest mismatch")
    reject_private_fields(contract, "ledger contract")
    return contract


def validate_initial_state(
    value: Any, subject: dict[str, Any], gate_ids: set[str]
) -> dict[str, Any]:
    state = exact_object(value, STATE_KEYS, "initial_state")
    if (
        state["schema_version"] != "loopx/task-state/v1"
        or validate_subject(state["subject"], "initial_state.subject") != subject
    ):
        raise ContractError("initial state identity mismatch")
    if type(state["state_revision"]) is not int or state["state_revision"] < 0:
        raise ContractError("initial state revision invalid")
    sha256_ref(
        state["ledger_head_digest"], "initial_state.ledger_head_digest", nullable=True
    )
    if state["lifecycle"] not in {
        "READY",
        "ACTIVE",
        "HITL_PENDING",
        "COMPLETED",
        "COMPLETED_WITH_EXCEPTION",
        "FAILED",
        "CANCELLED",
    }:
        raise ContractError("initial state lifecycle invalid")
    evidence = state["evidence"]
    if not isinstance(evidence, list):
        raise ContractError("initial state evidence invalid")
    evidence_ids: set[str] = set()
    for index, item in enumerate(evidence):
        artifact = validate_artifact(item, f"initial_state.evidence[{index}]")
        if artifact["artifact_id"] in evidence_ids:
            raise ContractError("duplicate initial evidence")
        evidence_ids.add(artifact["artifact_id"])
    if not isinstance(state["todos"], list) or not state["todos"]:
        raise ContractError("initial state Todos are absent")
    todo_ids: set[str] = set()
    for index, todo in enumerate(state["todos"]):
        todo = exact_object(todo, TODO_KEYS, f"initial_state.todos[{index}]")
        todo_id = stable_id(todo["todo_id"], f"initial_state.todos[{index}].todo_id")
        if todo_id in todo_ids or todo["status"] not in {"PENDING", "READY"}:
            raise ContractError("initial Todo duplicate or not dispatchable")
        if not isinstance(todo["gate_ids"], list) or set(todo["gate_ids"]) - gate_ids:
            raise ContractError("initial Todo references an unknown Gate")
        if (
            not isinstance(todo["evidence_refs"], list)
            or set(todo["evidence_refs"]) - evidence_ids
        ):
            raise ContractError("initial Todo references unknown Evidence")
        if (
            todo["gate_results"]
            or todo["attempts"] != 0
            or todo["last_failure_ref"] is not None
            or todo["exception_ref"] is not None
        ):
            raise ContractError("initial Todo already contains execution state")
        todo_ids.add(todo_id)
    if state["current_todo_id"] not in todo_ids:
        raise ContractError("initial current Todo is absent")
    quota = state["quota"]
    if (
        not isinstance(quota, dict)
        or set(quota) != {"limits", "used", "state"}
        or quota["state"] != "AVAILABLE"
    ):
        raise ContractError("initial Quota invalid")
    if not isinstance(quota["used"], dict) or any(
        type(v) is not int or v != 0 for v in quota["used"].values()
    ):
        raise ContractError("initial Quota usage must be zero")
    if state["human_decision_refs"] != []:
        raise ContractError("initial state cannot contain Human decisions")
    reject_private_fields(state, "initial_state")
    return state


def validate_store_manifest(value: Any, store: Path) -> dict[str, Any]:
    manifest = exact_object(value, STORE_KEYS, "store manifest")
    if (
        manifest["schema_version"] != "loopx/ledger-store/v1"
        or manifest["writer_policy"] != "POSIX_FLOCK_SINGLE_WRITER"
    ):
        raise ContractError("store manifest policy/version drifted")
    validate_subject(manifest["subject"], "store manifest.subject")
    sha256_ref(manifest["contract_digest"], "store manifest.contract_digest")
    for key in ("contract_path", "events_path", "snapshot_path"):
        relative_path(manifest[key], f"store manifest.{key}")
        if (store / manifest[key]).resolve().parent != store.resolve() and not str(
            (store / manifest[key]).resolve()
        ).startswith(str(store.resolve()) + os.sep):
            raise ContractError("store manifest path escaped the store")
    validate_rfc3339_utc(manifest["created_at"], "store manifest.created_at")
    raw = copy.deepcopy(manifest)
    raw.pop("content_digest")
    if manifest["content_digest"] != digest(raw):
        raise ContractError("store manifest digest mismatch")
    return manifest


def validate_append_request(value: Any, subject: dict[str, Any]) -> dict[str, Any]:
    request = exact_object(value, APPEND_KEYS, "append request")
    if request["schema_version"] != "loopx/append-request/v1":
        raise ContractError("append request version drifted")
    stable_id(request["request_id"], "append request.request_id")
    if (
        type(request["expected_state_revision"]) is not int
        or request["expected_state_revision"] < 0
    ):
        raise ContractError("append request expected revision invalid")
    event = request["event"]
    if (
        not isinstance(event, dict)
        or validate_subject(event.get("subject"), "append request.event.subject")
        != subject
    ):
        raise ContractError("append request event subject mismatch")
    return request
