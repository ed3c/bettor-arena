#!/usr/bin/env python3
"""Schema identity, digest and fixture checks for the LSP pool contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from lsp_common import (
    EVIDENCE_BEARING,
    QUERY_STATES,
    ContractError,
    InputError,
    load_json,
)
from lsp_fallback import CEILING
from lsp_pool import SLOT_STATES, validate_server, validate_slot
from lsp_query import FRESHNESS, QUERY_KINDS, validate_request

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "query_states",
    "evidence_bearing_states",
    "query_kinds",
    "slot_states",
    "index_freshness",
    "fallback_ceiling",
    "lsp_output_authority",
    "canary_state",
    "schemas",
}

SCHEMA_VERSIONS = {
    "pool-slot.schema.json": "loopx/lsp-pool-slot/v1",
    "query-request.schema.json": "loopx/lsp-pool-query-request/v1",
    "query-result.schema.json": "loopx/lsp-pool-query-result/v1",
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

    if manifest["schema_version"] != "loopx/lsp-pool-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["requires_capabilities"] != [
        "arena.proof-kernel/v1",
        "loopx.code-truth-graph/v2",
        "loopx.runtime-fabric/v1",
        "loopx.worker-fleet/v1",
    ]:
        raise ContractError("manifest capability dependencies drifted")

    if manifest["query_states"] != sorted(QUERY_STATES):
        raise ContractError("query states drifted from the implementation")
    if manifest["evidence_bearing_states"] != sorted(EVIDENCE_BEARING):
        raise ContractError("evidence-bearing states drifted")
    if manifest["query_kinds"] != sorted(QUERY_KINDS):
        raise ContractError("query kinds drifted")
    if manifest["slot_states"] != sorted(SLOT_STATES):
        raise ContractError("slot states drifted")
    if manifest["index_freshness"] != sorted(FRESHNESS):
        raise ContractError("freshness vocabulary drifted")
    if manifest["fallback_ceiling"] != CEILING:
        raise ContractError("the fallback capability ceiling drifted")

    # UNKNOWN and SERVER_FAILED must stay outside the evidence-bearing set. Adding
    # either is the single edit that would make a crashed server read as a clean
    # tree while every other test kept passing.
    for state in ("UNKNOWN", "SERVER_FAILED", "NOT_EXERCISED"):
        if state in manifest["evidence_bearing_states"]:
            raise ContractError(
                f"{state} may not bear evidence; a crashed server returns no "
                "diagnostics and so does a clean file, and admitting one as the other "
                "makes them identical downstream"
            )
    if manifest["lsp_output_authority"] != "EVIDENCE_INPUT_NOT_GATE_VERDICT":
        raise ContractError(
            "LSP output authority drifted; a language server reads source, and its "
            "output is input to a graph rather than a verdict"
        )
    if manifest["canary_state"] != "NOT_EXERCISED":
        raise ContractError(
            "the real-server canary may not claim admission; no real language server "
            "has been exercised, and a deterministic fixture is not a live host"
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
    validate_server(load_json(good / "server.json"), "server")
    validate_server(load_json(good / "server-multi-root.json"), "server-multi-root")
    for index, slot in enumerate(load_json(good / "slots.json")):
        validate_slot(slot, f"slots[{index}]")
    validate_request(load_json(good / "request.json"))
    return len(sorted(good.glob("*.json")))


def check_contracts(root: Path) -> tuple[int, int]:
    validate_manifest(root)
    return len(SCHEMA_VERSIONS), validate_fixtures(root)


def run_contract_selftest(root: Path) -> int:
    manifest = load_json(root / "contracts" / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        (
            "unknown admitted as evidence",
            lambda m: m.__setitem__(
                "evidence_bearing_states", sorted([*EVIDENCE_BEARING, "UNKNOWN"])
            ),
        ),
        (
            "server failure admitted as evidence",
            lambda m: m.__setitem__(
                "evidence_bearing_states", sorted([*EVIDENCE_BEARING, "SERVER_FAILED"])
            ),
        ),
        (
            "lsp output made a gate verdict",
            lambda m: m.__setitem__("lsp_output_authority", "GATE_VERDICT"),
        ),
        ("canary claimed admitted", lambda m: m.__setitem__("canary_state", "PASS")),
        (
            "fallback claims project-wide answers",
            lambda m: m.__setitem__(
                "fallback_ceiling", {**CEILING, "REFERENCES": "FULL_PROJECT"}
            ),
        ),
        ("query state dropped", lambda m: m.__setitem__("query_states", ["CLEAN"])),
        ("slot state dropped", lambda m: m.__setitem__("slot_states", ["WARM"])),
        (
            "freshness collapsed",
            lambda m: m.__setitem__("index_freshness", ["CURRENT"]),
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
