#!/usr/bin/env python3
"""Schema identity, digest and vocabulary checks for the source-ingest contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from si_capture import RIGHTS_STATES
from si_common import (
    ADMISSIBLE_ORIGIN,
    CAPTURE_STATES,
    LOCATOR_ORIGINS,
    SOURCE_TYPES,
    ContractError,
    InputError,
    load_json,
)

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "source_types",
    "capture_states",
    "locator_origins",
    "admissible_locator_origin",
    "rights_states",
    "source_content_is_data",
    "blocked_sources_recorded",
    "schemas",
}

SCHEMA_VERSIONS = {
    "evidence-manifest.schema.json": "loopx/source-evidence-manifest/v1",
    "source-declaration.schema.json": "loopx/source-declaration/v1",
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

    if manifest["schema_version"] != "loopx/source-ingest-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["requires_capabilities"] != [
        "arena.proof-kernel/v1",
        "loopx.contracts/v1",
    ]:
        raise ContractError("manifest capability dependencies drifted")

    if manifest["source_types"] != sorted(SOURCE_TYPES):
        raise ContractError("source types drifted from the implementation")
    if manifest["capture_states"] != sorted(CAPTURE_STATES):
        raise ContractError("capture states drifted from the implementation")
    if manifest["locator_origins"] != sorted(LOCATOR_ORIGINS):
        raise ContractError("locator origins drifted from the implementation")
    if manifest["rights_states"] != sorted(RIGHTS_STATES):
        raise ContractError("rights states drifted from the implementation")

    # The one that matters most: widening this is the single edit that would let
    # an estimated timestamp become evidence while every other check kept passing.
    if manifest["admissible_locator_origin"] != ADMISSIBLE_ORIGIN:
        raise ContractError(
            f"the admissible locator origin is {manifest['admissible_locator_origin']!r}; "
            "only a locator read out of the captured bytes may become evidence, "
            "because an estimated one looks exactly like a real one"
        )
    if manifest["source_content_is_data"] is not True:
        raise ContractError(
            "source_content_is_data may not be false; a transcript that can change "
            "policy has been followed as an instruction"
        )
    if manifest["blocked_sources_recorded"] is not True:
        raise ContractError(
            "blocked sources must be recorded; silence is indistinguishable from "
            "having looked and found nothing"
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
        try:
            raw = (contracts / name).read_bytes()
        except OSError as exc:
            raise InputError(f"cannot read schema {name}: {exc}") from exc
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


def check_contracts(root: Path) -> tuple[int, int]:
    validate_manifest(root)
    return len(SCHEMA_VERSIONS), len(sorted((root / "contracts").glob("*.json")))


def run_contract_selftest(root: Path) -> int:
    manifest = load_json(root / "contracts" / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        (
            "estimated locators admitted",
            lambda m: m.__setitem__("admissible_locator_origin", "ESTIMATED"),
        ),
        (
            "source content made authoritative",
            lambda m: m.__setitem__("source_content_is_data", False),
        ),
        (
            "blocked sources no longer recorded",
            lambda m: m.__setitem__("blocked_sources_recorded", False),
        ),
        (
            "locator origin vocabulary narrowed",
            lambda m: m.__setitem__("locator_origins", ["READ_FROM_ARTIFACT"]),
        ),
        (
            "capture state dropped",
            lambda m: m.__setitem__("capture_states", ["CAPTURED"]),
        ),
        ("source type dropped", lambda m: m.__setitem__("source_types", ["MARKDOWN"])),
        (
            "rights state dropped",
            lambda m: m.__setitem__("rights_states", ["AUTHORIZED"]),
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
