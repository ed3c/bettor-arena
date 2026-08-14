#!/usr/bin/env python3
# ruff: noqa: F401,F403,F405  # this module family composes through star imports; the names ruff reads as unused are deliberate re-exports the downstream modules import through.
"""Operate the LoopX append-only ledger with deterministic 0/2/64 exits."""

from __future__ import annotations

import argparse
import copy
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Iterator
from contextlib import contextmanager

from ledger_common import *
from ledger_engine import *


def artifact_ref(
    path: Path, artifact_id: str, kind: str, producer: str
) -> dict[str, Any]:
    return {
        "artifact_id": artifact_id,
        "kind": kind,
        "path": path.name,
        "digest": file_digest(path),
        "bytes": path.stat().st_size,
        "media_type": "application/json"
        if path.suffix == ".json"
        else "application/x-ndjson",
        "producer": producer,
    }


@contextmanager
def writer_lease(store: Path) -> Iterator[None]:
    store.mkdir(parents=True, exist_ok=True)
    lock_path = store / ".writer.lock"
    handle = lock_path.open("a+b")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise BusyError("writer lease is already held") from exc
        yield
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def store_manifest(contract: dict[str, Any], created_at: str) -> dict[str, Any]:
    manifest = {
        "schema_version": "loopx/ledger-store/v1",
        "subject": copy.deepcopy(contract["subject"]),
        "contract_digest": contract["contract_digest"],
        "contract_path": "contract.json",
        "events_path": "events.jsonl",
        "snapshot_path": "snapshot.json",
        "writer_policy": "POSIX_FLOCK_SINGLE_WRITER",
        "created_at": created_at,
        "content_digest": None,
    }
    raw = copy.deepcopy(manifest)
    raw.pop("content_digest")
    manifest["content_digest"] = digest(raw)
    return manifest


def existing_snapshot(store: Path) -> dict[str, Any] | None:
    path = store / "snapshot.json"
    return load_json(path) if path.exists() else None


def write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    if path.exists():
        raise InputError(f"receipt already exists: {path}")
    atomic_write_json(path, receipt)


def initialize(
    contract_path: Path,
    store: Path,
    created_at: str,
    receipt_path: Path,
    operation_id: str,
) -> dict[str, Any]:
    contract = validate_contract(load_json(contract_path))
    if store.exists() and any(store.iterdir()):
        raise ContractError(f"store is not empty: {store}")
    store.mkdir(parents=True, exist_ok=True)
    with writer_lease(store):
        contract_out = store / "contract.json"
        events_out = store / "events.jsonl"
        snapshot_out = store / "snapshot.json"
        manifest_out = store / "store.json"
        atomic_write_json(contract_out, contract)
        with events_out.open("xb") as handle:
            handle.flush()
            os.fsync(handle.fileno())
        snapshot = make_snapshot(contract, copy.deepcopy(contract["initial_state"]), [])
        atomic_write_json(snapshot_out, snapshot)
        manifest = store_manifest(contract, created_at)
        atomic_write_json(manifest_out, manifest)
        validate_store_manifest(load_json(manifest_out), store)
        after = snapshot_summary(snapshot, events_out)
        receipt = operation_receipt(
            operation_id,
            "INIT",
            contract["subject"],
            "PASS",
            snapshot_summary(None, events_out),
            after,
            [
                artifact_ref(contract_out, "ledger-contract", "FILE", "loopx-ledger"),
                artifact_ref(
                    manifest_out, "ledger-store-manifest", "FILE", "loopx-ledger"
                ),
                artifact_ref(events_out, "ledger-events", "TRACE", "loopx-ledger"),
                artifact_ref(snapshot_out, "ledger-snapshot", "FILE", "loopx-ledger"),
            ],
            {
                "writer_policy": "POSIX_FLOCK_SINGLE_WRITER",
                "runtime_state_checked_in": False,
            },
        )
        write_receipt(receipt_path, receipt)
        return receipt


def append_event(
    store: Path, request_path: Path, receipt_path: Path, operation_id: str
) -> dict[str, Any]:
    with writer_lease(store):
        snapshot, events, contract, torn = replay_store(store)
        if torn is not None:
            raise ContractError("cannot append to a torn ledger")
        snapshot_path = store / "snapshot.json"
        events_path = store / "events.jsonl"
        checked = existing_snapshot(store)
        if checked != snapshot:
            raise ContractError("checked snapshot drifted from full replay")
        request = validate_append_request(load_json(request_path), contract["subject"])
        event_value = request["event"]
        same_id = [
            event
            for event in events
            if event["event_id"] == event_value.get("event_id")
        ]
        before = snapshot_summary(snapshot, events_path)
        if same_id:
            if len(same_id) == 1 and canonical_bytes(same_id[0]) == canonical_bytes(
                event_value
            ):
                receipt = operation_receipt(
                    operation_id,
                    "APPEND",
                    contract["subject"],
                    "NOOP",
                    before,
                    before,
                    [
                        artifact_ref(
                            events_path, "ledger-events", "TRACE", "loopx-ledger"
                        )
                    ],
                    {
                        "idempotency_key": event_value["event_id"],
                        "reason": "identical event already committed",
                    },
                )
                write_receipt(receipt_path, receipt)
                return receipt
            raise ContractError("event ID collision with different bytes")
        if request["expected_state_revision"] != snapshot["state_revision"]:
            raise ContractError(
                f"stale expected revision: {request['expected_state_revision']} != {snapshot['state_revision']}"
            )
        previous = events[-1]["event_digest"] if events else None
        event = validate_event_shape(
            event_value,
            contract["subject"],
            len(events),
            previous,
            command_ids={command["command_id"] for command in contract["commands"]},
            prior_event_ids={event["event_id"] for event in events},
        )
        gates = {gate["gate_id"]: gate for gate in contract["gate_definitions"]}
        candidate_state = apply_event(snapshot["state"], event, gates)
        candidate_events = [*events, event]
        candidate_snapshot = make_snapshot(contract, candidate_state, candidate_events)
        append_fsync(events_path, canonical_bytes(event))
        atomic_write_json(snapshot_path, candidate_snapshot)
        after = snapshot_summary(candidate_snapshot, events_path)
        receipt = operation_receipt(
            operation_id,
            "APPEND",
            contract["subject"],
            "PASS",
            before,
            after,
            [
                artifact_ref(request_path, "append-request", "FILE", "loopx-ledger"),
                artifact_ref(events_path, "ledger-events", "TRACE", "loopx-ledger"),
                artifact_ref(snapshot_path, "ledger-snapshot", "FILE", "loopx-ledger"),
            ],
            {
                "event_id": event["event_id"],
                "sequence": event["sequence"],
                "event_digest": event["event_digest"],
            },
        )
        write_receipt(receipt_path, receipt)
        return receipt


def verify_store(store: Path, receipt_path: Path, operation_id: str) -> dict[str, Any]:
    snapshot, _, contract, torn = replay_store(store)
    if torn is not None:
        raise ContractError("ledger has a torn tail")
    checked = existing_snapshot(store)
    events_path = store / "events.jsonl"
    before = (
        snapshot_summary(checked, events_path)
        if checked is not None
        else snapshot_summary(None, events_path)
    )
    if checked != snapshot:
        raise ContractError("snapshot differs from deterministic replay")
    after = snapshot_summary(snapshot, events_path)
    receipt = operation_receipt(
        operation_id,
        "VERIFY",
        contract["subject"],
        "PASS",
        before,
        after,
        [
            artifact_ref(events_path, "ledger-events", "TRACE", "loopx-ledger"),
            artifact_ref(
                store / "snapshot.json", "ledger-snapshot", "FILE", "loopx-ledger"
            ),
        ],
        {"full_replay": True, "snapshot_agrees": True},
    )
    write_receipt(receipt_path, receipt)
    return receipt


def replay_to(
    store: Path, output: Path, receipt_path: Path, operation_id: str
) -> dict[str, Any]:
    snapshot, _, contract, torn = replay_store(store)
    if torn is not None:
        raise ContractError("cannot replay a torn ledger")
    if output.exists():
        raise InputError(f"replay output already exists: {output}")
    atomic_write_json(output, snapshot)
    events_path = store / "events.jsonl"
    summary = snapshot_summary(snapshot, events_path)
    receipt = operation_receipt(
        operation_id,
        "REPLAY",
        contract["subject"],
        "PASS",
        summary,
        summary,
        [
            artifact_ref(events_path, "ledger-events", "TRACE", "loopx-ledger"),
            artifact_ref(output, "replayed-snapshot", "FILE", "loopx-ledger"),
        ],
        {"byte_identical_to_checked_snapshot": existing_snapshot(store) == snapshot},
    )
    write_receipt(receipt_path, receipt)
    return receipt


def recover_store(
    store: Path, apply: bool, receipt_path: Path, operation_id: str
) -> tuple[dict[str, Any], int]:
    with writer_lease(store):
        snapshot, _, contract, torn = replay_store(store, allow_torn_tail=True)
        events_path = store / "events.jsonl"
        before_snapshot = existing_snapshot(store)
        before = (
            snapshot_summary(before_snapshot, events_path)
            if before_snapshot is not None
            else snapshot_summary(None, events_path)
        )
        if torn is None:
            receipt = operation_receipt(
                operation_id,
                "RECOVER",
                contract["subject"],
                "NOOP",
                before,
                before,
                [artifact_ref(events_path, "ledger-events", "TRACE", "loopx-ledger")],
                {"reason": "no torn tail"},
            )
            write_receipt(receipt_path, receipt)
            return receipt, OK
        if not apply:
            receipt = operation_receipt(
                operation_id,
                "RECOVER",
                contract["subject"],
                "FAIL",
                before,
                before,
                [artifact_ref(events_path, "ledger-events", "TRACE", "loopx-ledger")],
                {"torn_tail": torn, "apply_required": True},
            )
            write_receipt(receipt_path, receipt)
            return receipt, BAD
        with events_path.open("r+b") as handle:
            handle.truncate(torn["valid_bytes"])
            handle.flush()
            os.fsync(handle.fileno())
        recovered, _, _, residual = replay_store(store)
        if residual is not None:
            raise ContractError("torn-tail recovery did not converge")
        atomic_write_json(store / "snapshot.json", recovered)
        after = snapshot_summary(recovered, events_path)
        receipt = operation_receipt(
            operation_id,
            "RECOVER",
            contract["subject"],
            "RECOVERED",
            before,
            after,
            [
                artifact_ref(events_path, "ledger-events", "TRACE", "loopx-ledger"),
                artifact_ref(
                    store / "snapshot.json", "ledger-snapshot", "FILE", "loopx-ledger"
                ),
            ],
            {"removed_tail": torn, "history_events_rewritten": False},
        )
        write_receipt(receipt_path, receipt)
        return receipt, OK
