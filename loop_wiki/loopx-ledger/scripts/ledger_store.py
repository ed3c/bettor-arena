#!/usr/bin/env python3
"""Append-only LoopX ledger parsing, replay, snapshots, and receipts."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from ledger_common import *
from ledger_contract import RECEIPT_KEYS, validate_contract, validate_event_shape, validate_store_manifest
from ledger_reduce import apply_event, make_snapshot

def read_events(path: Path) -> tuple[list[dict[str, Any]], int, dict[str, Any] | None]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise InputError(f"missing events file: {path}") from exc
    events: list[dict[str, Any]] = []
    offset = 0
    valid_bytes = 0
    for index, line in enumerate(raw.splitlines(keepends=True)):
        line_start = offset
        offset += len(line)
        is_last = offset == len(raw)
        if not line.endswith(b"\n"):
            if is_last:
                return events, valid_bytes, {"kind": "TORN_TAIL", "offset": line_start, "bytes": len(line), "digest": digest(line)}
            raise ContractError(f"events line {index} lacks a newline")
        payload = line[:-1]
        if not payload:
            raise ContractError(f"events line {index} is empty")
        try:
            event = json.loads(payload)
        except json.JSONDecodeError as exc:
            if is_last:
                return events, valid_bytes, {"kind": "TORN_TAIL", "offset": line_start, "bytes": len(line), "digest": digest(line)}
            raise ContractError(f"events line {index} is invalid JSON") from exc
        if not isinstance(event, dict):
            raise ContractError(f"events line {index} is not an object")
        events.append(event)
        valid_bytes = offset
    return events, valid_bytes, None


def replay_store(store: Path, allow_torn_tail: bool = False) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], dict[str, Any] | None]:
    manifest = validate_store_manifest(load_json(store / "store.json"), store)
    contract_path = store / manifest["contract_path"]
    events_path = store / manifest["events_path"]
    contract = validate_contract(load_json(contract_path))
    if contract["contract_digest"] != manifest["contract_digest"] or validate_subject(contract["subject"], "contract.subject") != validate_subject(manifest["subject"], "manifest.subject"):
        raise ContractError("store manifest and immutable contract disagree")
    events, valid_bytes, torn = read_events(events_path)
    if torn is not None and not allow_torn_tail:
        raise ContractError(f"events ledger has a torn tail at byte {torn['offset']}")
    state = copy.deepcopy(contract["initial_state"])
    gates = {gate["gate_id"]: gate for gate in contract["gate_definitions"]}
    previous: str | None = None
    ids: dict[str, dict[str, Any]] = {}
    command_ids = {command["command_id"] for command in contract["commands"]}
    for index, event in enumerate(events):
        event = validate_event_shape(
            event, contract["subject"], index, previous,
            command_ids=command_ids, prior_event_ids=set(ids),
        )
        if event["event_id"] in ids:
            raise ContractError(f"duplicate event ID in ledger: {event['event_id']}")
        ids[event["event_id"]] = event
        state = apply_event(state, event, gates)
        previous = event["event_digest"]
    snapshot = make_snapshot(contract, state, events)
    if torn is not None:
        torn["valid_bytes"] = valid_bytes
    return snapshot, events, contract, torn


def operation_receipt(operation_id: str, operation: str, subject: dict[str, Any], status: str, before: dict[str, Any], after: dict[str, Any], artifacts: list[dict[str, Any]], details: dict[str, Any]) -> dict[str, Any]:
    receipt = {
        "schema_version": "loopx/ledger-operation-receipt/v1",
        "operation_id": stable_id(operation_id, "operation receipt ID"),
        "operation": operation,
        "subject": copy.deepcopy(subject),
        "status": status,
        "before": before,
        "after": after,
        "artifacts": artifacts,
        "cleanup": "PASS",
        "details": details,
        "content_digest": None,
    }
    exact_object(receipt, RECEIPT_KEYS, "operation receipt")
    raw = copy.deepcopy(receipt)
    raw.pop("content_digest")
    receipt["content_digest"] = digest(raw)
    return receipt
