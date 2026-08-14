#!/usr/bin/env python3
"""Validate LoopX Ledger v1 schemas and deterministic fixture projection."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from ledger_common import BAD, OK, USAGE, ContractError, InputError, canonical_bytes, load_json
from ledger_engine import apply_event, make_snapshot, validate_contract, validate_event_shape

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "writer_policy",
    "canonical_authority",
    "schemas",
    "runtime_state_checked_in",
    "runtime_store_layout",
    "evidence_states",
}
SCHEMA_NAMES = {
    "append-request.schema.json": "loopx/append-request/v1",
    "ledger-contract.schema.json": "loopx/ledger-contract/v1",
    "operation-receipt.schema.json": "loopx/ledger-operation-receipt/v1",
    "store-manifest.schema.json": "loopx/ledger-store/v1",
}


def exact_object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    if set(value) != keys:
        raise ContractError(
            f"{label} fields drifted; missing={sorted(keys - set(value))}, "
            f"extra={sorted(set(value) - keys)}"
        )
    return value


def validate_manifest(root: Path, manifest_value: Any | None = None) -> dict[str, Any]:
    contracts = root / "contracts"
    loaded = load_json(contracts / "manifest.json") if manifest_value is None else manifest_value
    manifest = exact_object(loaded, MANIFEST_KEYS, "ledger manifest")
    if manifest["schema_version"] != "loopx/ledger-contract-manifest/v1":
        raise ContractError("ledger manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("ledger manifest interface version drifted")
    if manifest["requires_capabilities"] != ["loopx.contracts/v1"]:
        raise ContractError("ledger manifest capability dependency drifted")
    if manifest["writer_policy"] != "POSIX_FLOCK_SINGLE_WRITER":
        raise ContractError("ledger writer policy drifted")
    if manifest["canonical_authority"] != "LOOPX_LEDGER_REDUCER":
        raise ContractError("ledger authority drifted")
    if manifest["runtime_state_checked_in"] is not False:
        raise ContractError("runtime ledger state must not be checked in")
    if manifest["runtime_store_layout"] != [
        "contract.json",
        "store.json",
        "events.jsonl",
        "snapshot.json",
        ".writer.lock",
    ]:
        raise ContractError("runtime store layout drifted")
    if manifest["evidence_states"] != [
        "PASS",
        "FAIL",
        "ABSENT",
        "NOT_IMPLEMENTED",
        "NOT_EXERCISED",
        "SKIPPED_BY_POLICY",
    ]:
        raise ContractError("evidence state vocabulary drifted")
    entries = manifest["schemas"]
    if not isinstance(entries, list) or len(entries) != len(SCHEMA_NAMES):
        raise ContractError("ledger manifest must enumerate four schemas")
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        entry = exact_object(entry, {"id", "path", "sha256"}, f"ledger manifest.schemas[{index}]")
        name = entry["path"]
        if name in seen or name not in SCHEMA_NAMES:
            raise ContractError(f"unexpected or duplicate ledger schema: {name}")
        seen.add(name)
        path = contracts / name
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise InputError(f"cannot read schema {path}: {exc}") from exc
        if entry["sha256"] != hashlib.sha256(raw).hexdigest():
            raise ContractError(f"ledger schema digest drifted: {name}")
        schema = load_json(path)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise ContractError(f"ledger schema dialect drifted: {name}")
        if schema.get("$id") != entry["id"] or not entry["id"].endswith("/" + name):
            raise ContractError(f"ledger schema identity drifted: {name}")
        if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
            raise ContractError(f"ledger schema must fail closed: {name}")
        version = schema.get("properties", {}).get("schema_version", {}).get("const")
        if version != SCHEMA_NAMES[name]:
            raise ContractError(f"ledger schema version constant drifted: {name}")
    if seen != set(SCHEMA_NAMES):
        raise ContractError("ledger schema coverage drifted")
    return manifest


def replay_fixture(root: Path) -> tuple[dict[str, Any], int]:
    fixtures = root / "tests" / "fixtures" / "good"
    contract = validate_contract(load_json(fixtures / "contract.json"))
    state = copy.deepcopy(contract["initial_state"])
    gates = {gate["gate_id"]: gate for gate in contract["gate_definitions"]}
    commands = {command["command_id"] for command in contract["commands"]}
    previous: str | None = None
    events: list[dict[str, Any]] = []
    event_ids: set[str] = set()
    paths = sorted((fixtures / "events").glob("*.json"))
    if not paths:
        raise InputError("positive ledger event fixtures are absent")
    for index, path in enumerate(paths):
        event = validate_event_shape(
            load_json(path),
            contract["subject"],
            index,
            previous,
            command_ids=commands,
            prior_event_ids=event_ids,
        )
        state = apply_event(state, event, gates)
        previous = event["event_digest"]
        event_ids.add(event["event_id"])
        events.append(event)
    snapshot = make_snapshot(contract, state, events)
    expected = load_json(fixtures / "expected-snapshot.json")
    if canonical_bytes(snapshot) != canonical_bytes(expected):
        raise ContractError("positive expected snapshot disagrees with deterministic replay")
    return snapshot, len(events)


def run_selftest(root: Path) -> None:
    validate_manifest(root)
    replay_fixture(root)
    manifest = load_json(root / "contracts" / "manifest.json")
    mutated = copy.deepcopy(manifest)
    mutated["schemas"][0]["sha256"] = "0" * 64
    try:
        validate_manifest(root, mutated)
    except ContractError:
        pass
    else:
        raise ContractError("schema-digest mutation unexpectedly passed")
    bad_snapshot = load_json(root / "tests" / "fixtures" / "good" / "expected-snapshot.json")
    bad_snapshot["state_revision"] += 1
    if canonical_bytes(bad_snapshot) == canonical_bytes(replay_fixture(root)[0]):
        raise ContractError("snapshot-drift mutation did not disagree")
    print("loopx-ledger-contracts selftest PASS: schema digest and snapshot drift controls")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        validate_manifest(root)
        snapshot, count = replay_fixture(root)
        if args.selftest:
            run_selftest(root)
        else:
            print(
                "loopx-ledger-contracts PASS: "
                f"{len(SCHEMA_NAMES)} schemas, {count} events, "
                f"revision={snapshot['state_revision']}"
            )
        return OK
    except ContractError as exc:
        print(f"loopx-ledger-contracts RED: {exc}", file=sys.stderr)
        return BAD
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
