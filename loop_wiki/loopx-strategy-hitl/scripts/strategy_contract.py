#!/usr/bin/env python3
"""Schema identity, digest and fixture checks for the five contracts.

The digest check is the point. A schema whose bytes moved without its manifest
entry moving is a contract that changed without anyone declaring it, and every
downstream validator would keep reporting green against the old promise.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from strategy_common import ContractError, InputError, load_json
from strategy_checkpoint import validate_checkpoint
from strategy_decision import validate_decision
from strategy_engine import validate_interrupt, validate_proposal

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "canonical_authority",
    "planner_authority",
    "non_waivable_gate_classes",
    "forbidden_decision_fields",
    "runtime_state_checked_in",
    "runtime_state_path",
    "evidence_states",
    "schemas",
}
SCHEMA_VERSIONS = {
    "graph-checkpoint.schema.json": "loopx/graph-checkpoint/v1",
    "hitl-interrupt.schema.json": "loopx/hitl-interrupt/v1",
    "human-decision.schema.json": "loopx/human-decision/v1",
    "resume-envelope.schema.json": "loopx/resume-envelope/v1",
    "strategy-proposal.schema.json": "loopx/strategy-proposal/v1",
}
NON_WAIVABLE = [
    "CLEANUP",
    "DESTRUCTIVE",
    "RELEASE_SIGNING",
    "SECRET",
    "SECURITY",
    "SUBJECT_INTEGRITY",
]
FORBIDDEN_FIELDS = ["bypass", "force_skip", "override", "skip", "waive_all"]


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

    if manifest["schema_version"] != "loopx/strategy-hitl-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["requires_capabilities"] != ["loopx.contracts/v1", "loopx.ledger/v1"]:
        raise ContractError("manifest capability dependencies drifted")
    if manifest["canonical_authority"] != "LOOPX_LEDGER_REDUCER":
        raise ContractError("canonical authority drifted from the reducer")
    if manifest["planner_authority"] != "PROPOSE_ONLY":
        raise ContractError("planner authority drifted from propose-only")
    if manifest["runtime_state_checked_in"] is not False:
        raise ContractError("runtime task state must not be checked in")

    # These two lists are the leaf's whole reason to exist. A silent edit to
    # either would widen what an exception can do with no test noticing.
    if manifest["non_waivable_gate_classes"] != NON_WAIVABLE:
        raise ContractError("non-waivable gate class list drifted")
    if manifest["forbidden_decision_fields"] != FORBIDDEN_FIELDS:
        raise ContractError("forbidden decision field list drifted")

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
    validate_checkpoint(load_json(good / "checkpoint.json"))
    validate_proposal(load_json(good / "proposal.json"))
    validate_interrupt(load_json(good / "interrupt.json"))
    validate_decision(
        load_json(good / "decision.json"), load_json(good / "gate-classes.json")
    )
    return len(sorted(good.glob("*.json")))


def check_contracts(root: Path) -> tuple[int, int]:
    validate_manifest(root)
    return len(SCHEMA_VERSIONS), validate_fixtures(root)


def run_contract_selftest(root: Path) -> int:
    manifest = load_json(root / "contracts" / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        (
            "non-waivable list",
            lambda m: m.__setitem__("non_waivable_gate_classes", ["CLEANUP"]),
        ),
        (
            "forbidden field list",
            lambda m: m.__setitem__("forbidden_decision_fields", []),
        ),
        (
            "planner authority",
            lambda m: m.__setitem__("planner_authority", "CANONICAL"),
        ),
        (
            "canonical authority",
            lambda m: m.__setitem__("canonical_authority", "PLANNER"),
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
