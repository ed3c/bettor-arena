#!/usr/bin/env python3
"""Schema identity, digest and fixture checks for the three contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from obs_action import validate_request
from obs_common import ContractError, InputError, load_json
from obs_envelope import validate_chain, validate_ledger_event
from obs_redaction import DEFAULT_DROP_KEYS, validate_policy

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "canonical_authority",
    "projection_authority",
    "backend_adapters",
    "backend_admission_state",
    "redaction_floor_keys",
    "runtime_state_checked_in",
    "evidence_states",
    "schemas",
}
SCHEMA_VERSIONS = {
    "hitl-action-request.schema.json": "loopx/hitl-action-request/v1",
    "observability-envelope.schema.json": "loopx/observability-envelope/v1",
    "redaction-policy.schema.json": "loopx/redaction-policy/v1",
}


def exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    if set(value) != keys:
        raise ContractError(
            f"{label} fields drifted; missing={sorted(keys - set(value))}, "
            f"extra={sorted(set(value) - keys)}"
        )
    return value


def validate_manifest(root: Path, override: Any | None = None) -> dict[str, Any]:
    contracts = root / "contracts"
    loaded = load_json(contracts / "manifest.json") if override is None else override
    manifest = exact(loaded, MANIFEST_KEYS, "manifest")

    if manifest["schema_version"] != "loopx/observability-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["requires_capabilities"] != [
        "loopx.contracts/v1",
        "loopx.ledger/v1",
        "loopx.hitl/v1",
    ]:
        raise ContractError("manifest capability dependencies drifted")
    if manifest["canonical_authority"] != "LOOPX_LEDGER_REDUCER":
        raise ContractError("canonical authority drifted from the reducer")
    if manifest["projection_authority"] != "PROJECTION_ONLY":
        raise ContractError("projection authority drifted")
    if manifest["runtime_state_checked_in"] is not False:
        raise ContractError("runtime projection state must not be checked in")

    # A backend that has never been exercised may not be recorded as admitted.
    # This is the line that keeps "Langfuse is reachable" from being read as
    # "the task passed".
    if manifest["backend_admission_state"] != "NOT_EXERCISED":
        raise ContractError(
            "backend_admission_state may not claim admission; no adapter has been "
            "exercised and provider availability is not task evidence"
        )
    if manifest["redaction_floor_keys"] != sorted(DEFAULT_DROP_KEYS):
        raise ContractError(
            "redaction floor drifted from the implementation's own floor"
        )

    entries = manifest["schemas"]
    if not isinstance(entries, list) or len(entries) != len(SCHEMA_VERSIONS):
        raise ContractError(f"manifest must enumerate {len(SCHEMA_VERSIONS)} schemas")

    seen: set[str] = set()
    for index, entry in enumerate(entries):
        entry = exact(entry, {"id", "path", "sha256"}, f"manifest.schemas[{index}]")
        name = entry["path"]
        if name in seen or name not in SCHEMA_VERSIONS:
            raise ContractError(f"unexpected or duplicate schema: {name}")
        seen.add(name)
        path = contracts / name
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise InputError(f"cannot read schema {path}: {exc}") from exc
        if entry["sha256"] != hashlib.sha256(raw).hexdigest():
            raise ContractError(f"schema digest drifted: {name}")
        schema = json.loads(raw)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise ContractError(f"schema dialect drifted: {name}")
        if schema.get("$id") != entry["id"]:
            raise ContractError(f"schema identity drifted: {name}")
        if (
            schema.get("type") != "object"
            or schema.get("additionalProperties") is not False
        ):
            raise ContractError(f"schema must fail closed: {name}")
        const = schema.get("properties", {}).get("schema_version", {}).get("const")
        if const != SCHEMA_VERSIONS[name]:
            raise ContractError(f"schema version constant drifted: {name}")
    if seen != set(SCHEMA_VERSIONS):
        raise ContractError("schema coverage drifted")
    return manifest


def validate_fixtures(root: Path) -> int:
    good = root / "tests" / "fixtures" / "good"
    validate_policy(load_json(good / "redaction-policy.json"))
    events = load_json(good / "ledger.json")
    for event in events:
        validate_ledger_event(event)
    validate_chain(events)
    validate_request(load_json(good / "action-request.json"))
    return len(sorted(good.glob("*.json")))


def check_contracts(root: Path) -> tuple[int, int]:
    validate_manifest(root)
    return len(SCHEMA_VERSIONS), validate_fixtures(root)


def run_contract_selftest(root: Path) -> int:
    manifest = load_json(root / "contracts" / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        (
            "projection authority",
            lambda m: m.__setitem__("projection_authority", "CANONICAL"),
        ),
        (
            "canonical authority",
            lambda m: m.__setitem__("canonical_authority", "TRACE_STORE"),
        ),
        (
            "backend admitted",
            lambda m: m.__setitem__("backend_admission_state", "PASS"),
        ),
        (
            "redaction floor lowered",
            lambda m: m.__setitem__("redaction_floor_keys", ["token"]),
        ),
        (
            "checked-in runtime state",
            lambda m: m.__setitem__("runtime_state_checked_in", True),
        ),
    ]
    for name, mutate in mutations:
        mutated = copy.deepcopy(manifest)
        mutate(mutated)
        try:
            validate_manifest(root, mutated)
        except ContractError:
            continue
        raise ContractError(f"manifest mutation survived: {name}")
    return len(mutations)
