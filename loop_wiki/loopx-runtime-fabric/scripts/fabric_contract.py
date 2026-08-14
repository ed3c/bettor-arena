#!/usr/bin/env python3
"""Schema identity, digest and adapter-admission checks."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from fabric_common import ContractError, InputError, load_json
from fabric_lease import validate_lease
from fabric_local import ENFORCEMENT_CEILING
from fabric_request import validate_request

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "canonical_authority",
    "runtime_authority",
    "declared_adapters",
    "admitted_adapters",
    "adapter_admission_states",
    "local_enforcement_ceiling",
    "runtime_state_checked_in",
    "evidence_states",
    "schemas",
}
SCHEMA_VERSIONS = {
    "runtime-lease.schema.json": "loopx/runtime-lease/v1",
    "runtime-receipt.schema.json": "loopx/runtime-receipt/v1",
    "runtime-request.schema.json": "loopx/runtime-request/v1",
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

    if manifest["schema_version"] != "loopx/runtime-fabric-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["canonical_authority"] != "LOOPX_LEDGER_REDUCER":
        raise ContractError("canonical authority drifted from the reducer")
    if manifest["runtime_authority"] != "OBSERVATION_ONLY":
        raise ContractError(
            "runtime authority drifted; a fabric observes and never decides a gate"
        )
    if manifest["runtime_state_checked_in"] is not False:
        raise ContractError("runtime workspace state must not be checked in")

    # The ceiling in the manifest must be the ceiling the adapter actually has.
    # A documented ceiling that has drifted from the implementation is worse
    # than none: it is read as a guarantee.
    if manifest["local_enforcement_ceiling"] != dict(ENFORCEMENT_CEILING):
        raise ContractError(
            "declared local enforcement ceiling does not match the adapter's own; "
            "a documented ceiling that has drifted is read as a guarantee"
        )

    declared = manifest["declared_adapters"]
    admitted = manifest["admitted_adapters"]
    states = manifest["adapter_admission_states"]
    if not isinstance(declared, list) or sorted(declared) != declared:
        raise ContractError("declared_adapters must be a sorted array")
    if not set(admitted) <= set(declared):
        raise ContractError("an admitted adapter must also be declared")
    if set(states) != set(declared):
        raise ContractError(
            "every declared adapter needs an admission state; an adapter with no "
            "state is indistinguishable from one that was never considered"
        )
    for adapter, state in states.items():
        if state not in {
            "NOT_EXERCISED",
            "EXERCISED_FIXTURE_ONLY",
            "EXERCISED_PHYSICAL",
        }:
            raise ContractError(f"unknown admission state {state!r} for {adapter}")
        if adapter not in admitted and state != "NOT_EXERCISED":
            raise ContractError(
                f"{adapter} is not admitted but claims {state}; an unadmitted "
                "provider may not carry exercise evidence"
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
    validate_request(load_json(good / "request.json"))
    validate_lease(load_json(good / "lease.json"))
    return len(sorted(good.glob("*.json")))


def check_contracts(root: Path) -> tuple[int, int]:
    validate_manifest(root)
    return len(SCHEMA_VERSIONS), validate_fixtures(root)


def run_contract_selftest(root: Path) -> int:
    manifest = load_json(root / "contracts" / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        (
            "runtime authority",
            lambda m: m.__setitem__("runtime_authority", "CANONICAL"),
        ),
        (
            "canonical authority",
            lambda m: m.__setitem__("canonical_authority", "RUNTIME"),
        ),
        (
            "ceiling overstated",
            lambda m: m["local_enforcement_ceiling"].__setitem__("network", "ENFORCED"),
        ),
        (
            "unadmitted adapter claims exercise",
            lambda m: m["adapter_admission_states"].__setitem__(
                "e2b-sandbox", "EXERCISED_PHYSICAL"
            ),
        ),
        (
            "adapter without an admission state",
            lambda m: m["adapter_admission_states"].pop("firecracker-vm"),
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
