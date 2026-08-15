#!/usr/bin/env python3
"""Schema identity, digest and fixture checks for the resource-GC contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from rgc_common import (
    NEVER_DELETABLE,
    RESOURCE_CLASSES,
    RETENTION_KINDS,
    ContractError,
    InputError,
    load_json,
)
from rgc_plan import DESTRUCTIVE_AUTHORITIES, SETS, validate_resource
from rgc_rebuild import PROOF_STATES, validate_spec

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "resource_classes",
    "retention_kinds",
    "never_deletable_retentions",
    "derived_sets",
    "rebuild_proof_states",
    "deletion_admitting_proof_state",
    "destructive_authorities",
    "default_is_dry_run",
    "immutable_evidence_admittable",
    "schemas",
}

SCHEMA_VERSIONS = {
    "gc-plan.schema.json": "loopx/resource-gc-plan/v1",
    "inventory.schema.json": "loopx/resource-gc-inventory/v1",
    "receipt.schema.json": "loopx/resource-gc-receipt/v1",
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

    if manifest["schema_version"] != "loopx/resource-gc-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["requires_capabilities"] != [
        "arena.proof-kernel/v1",
        "loopx.contracts/v1",
        "loopx.ledger/v1",
        "loopx.runtime-fabric/v1",
        "loopx.worker-fleet/v1",
    ]:
        raise ContractError("manifest capability dependencies drifted")

    if manifest["resource_classes"] != sorted(RESOURCE_CLASSES):
        raise ContractError("resource classes drifted from the implementation")
    if manifest["retention_kinds"] != sorted(RETENTION_KINDS):
        raise ContractError("retention kinds drifted from the implementation")
    if manifest["never_deletable_retentions"] != sorted(NEVER_DELETABLE):
        raise ContractError("the never-deletable set drifted")
    if manifest["derived_sets"] != sorted(SETS):
        raise ContractError("derived sets drifted from the implementation")
    if manifest["rebuild_proof_states"] != sorted(PROOF_STATES):
        raise ContractError("rebuild proof states drifted")
    if manifest["destructive_authorities"] != sorted(DESTRUCTIVE_AUTHORITIES):
        raise ContractError("destructive authorities drifted")

    # Only PROVEN admits deletion. Widening this to include DIVERGENT is the
    # single change that would make the whole module unsafe while every test
    # about plans and sets kept passing.
    if manifest["deletion_admitting_proof_state"] != "PROVEN":
        raise ContractError(
            "only PROVEN may admit deletion; DIVERGENT means the rebuild works and "
            "does not reproduce this content, so admitting it deletes whatever the "
            "difference encoded"
        )
    if manifest["default_is_dry_run"] is not True:
        raise ContractError(
            "the default must be a dry run; a GC that deletes unless told otherwise "
            "will eventually be run by someone who did not read the flags"
        )
    if manifest["immutable_evidence_admittable"] is not False:
        raise ContractError(
            "immutable evidence may not be admittable; deleting a ledger segment or a "
            "Human decision destroys the record of why everything else was allowed"
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
    for index, resource in enumerate(load_json(good / "resources.json")):
        validate_resource(resource, f"resources[{index}]")
    for index, spec in enumerate(load_json(good / "rebuild-specs.json")):
        validate_spec(spec, f"rebuild-specs[{index}]")
    return len(sorted(good.glob("*.json")))


def check_contracts(root: Path) -> tuple[int, int]:
    validate_manifest(root)
    return len(SCHEMA_VERSIONS), validate_fixtures(root)


def run_contract_selftest(root: Path) -> int:
    manifest = load_json(root / "contracts" / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        (
            "divergent admits deletion",
            lambda m: m.__setitem__("deletion_admitting_proof_state", "DIVERGENT"),
        ),
        (
            "default made destructive",
            lambda m: m.__setitem__("default_is_dry_run", False),
        ),
        (
            "immutable evidence made admittable",
            lambda m: m.__setitem__("immutable_evidence_admittable", True),
        ),
        (
            "agent added as a destructive authority",
            lambda m: m.__setitem__(
                "destructive_authorities", sorted([*DESTRUCTIVE_AUTHORITIES, "AGENT"])
            ),
        ),
        (
            "never-deletable set emptied",
            lambda m: m.__setitem__("never_deletable_retentions", []),
        ),
        (
            "resource class dropped",
            lambda m: m.__setitem__("resource_classes", ["WORKTREE"]),
        ),
        (
            "proof state dropped",
            lambda m: m.__setitem__("rebuild_proof_states", ["PROVEN", "UNPROVABLE"]),
        ),
        ("derived set dropped", lambda m: m.__setitem__("derived_sets", ["EXPIRED"])),
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
