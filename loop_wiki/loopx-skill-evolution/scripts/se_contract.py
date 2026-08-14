#!/usr/bin/env python3
"""Schema identity, digest and fixture checks for the evolution contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from se_cases import validate_case_set
from se_common import ContractError, InputError, load_json
from se_decision import OUTCOMES
from se_experiment import ARMS, validate_experiment

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "arms",
    "outcomes",
    "judge_authority",
    "gate_authority",
    "holdout_reveal_authority",
    "minimum_repetitions",
    "minimum_replicating_hosts",
    "canonical_mutation_permitted",
    "fixture_evidence_unlocks_capability",
    "schemas",
}

SCHEMA_VERSIONS = {
    "case-set.schema.json": "loopx/skill-evolution-case-set/v1",
    "evolution-receipt.schema.json": "loopx/skill-evolution-receipt/v1",
    "experiment.schema.json": "loopx/skill-evolution-experiment/v1",
    "run-record.schema.json": "loopx/skill-evolution-run-record/v1",
}

MINIMUM_REPETITIONS = 3
MINIMUM_REPLICATING_HOSTS = 2


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

    if manifest["schema_version"] != "loopx/skill-evolution-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["requires_capabilities"] != [
        "arena.proof-kernel/v1",
        "loopx.contracts/v1",
        "loopx.worker-gateway/v1",
    ]:
        raise ContractError("manifest capability dependencies drifted")

    if manifest["arms"] != sorted(ARMS):
        raise ContractError("arms drifted from the implementation")
    if manifest["outcomes"] != sorted(OUTCOMES):
        raise ContractError("outcome vocabulary drifted from the implementation")

    # The five that are policy, pinned so changing any of them is a deliberate
    # edit to the contract rather than a parameter someone passes.
    if manifest["judge_authority"] != "ADVISORY_ONLY":
        raise ContractError(
            "judge_authority may not be widened; a judge that can move the decision "
            "can compensate for a failed hard gate, and a gate that can be "
            "compensated is not a gate"
        )
    if manifest["gate_authority"] != "DETERMINISTIC_AND_NON_COMPENSATORY":
        raise ContractError("gate_authority drifted")
    if manifest["holdout_reveal_authority"] != "GRADER_ONLY":
        raise ContractError(
            "holdout_reveal_authority may not be widened beyond the grader; anything "
            "else lets the thing being evaluated reach its own answers"
        )
    if manifest["minimum_repetitions"] != MINIMUM_REPETITIONS:
        raise ContractError(
            f"minimum_repetitions must be {MINIMUM_REPETITIONS}; below it, a single "
            "lucky run is a result"
        )
    if manifest["minimum_replicating_hosts"] != MINIMUM_REPLICATING_HOSTS:
        raise ContractError(
            f"minimum_replicating_hosts must be {MINIMUM_REPLICATING_HOSTS}; one host, "
            "model and provider cannot establish a universal result"
        )
    if manifest["canonical_mutation_permitted"] is not False:
        raise ContractError(
            "canonical_mutation_permitted may not be true; Bettor consumes immutable "
            "Skill releases and does not edit the shared body"
        )
    if manifest["fixture_evidence_unlocks_capability"] is not False:
        raise ContractError(
            "fixture evidence may not unlock a capability; a harness that passed "
            "against synthetic inputs has said nothing about a live host"
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
    validate_experiment(load_json(good / "experiment.json"))
    validate_case_set(load_json(good / "dev-cases.json"), "dev cases", "DEV")
    validate_case_set(
        load_json(good / "mutation-cases.json"), "mutation cases", "MUTATION"
    )
    validate_case_set(
        load_json(good / "holdout-cases.json"), "holdout cases", "HOLDOUT"
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
            "judge authority widened",
            lambda m: m.__setitem__("judge_authority", "DECIDING"),
        ),
        (
            "gate authority made compensatory",
            lambda m: m.__setitem__("gate_authority", "WEIGHTED"),
        ),
        (
            "holdout reveal widened",
            lambda m: m.__setitem__("holdout_reveal_authority", "RUNNER"),
        ),
        ("repetition floor lowered", lambda m: m.__setitem__("minimum_repetitions", 1)),
        (
            "single-host replication allowed",
            lambda m: m.__setitem__("minimum_replicating_hosts", 1),
        ),
        (
            "canonical mutation permitted",
            lambda m: m.__setitem__("canonical_mutation_permitted", True),
        ),
        (
            "fixture evidence unlocks capability",
            lambda m: m.__setitem__("fixture_evidence_unlocks_capability", True),
        ),
        (
            "baseline arm dropped",
            lambda m: m.__setitem__("arms", ["candidate", "current"]),
        ),
        (
            "inconclusive outcome removed",
            lambda m: m.__setitem__("outcomes", ["CANDIDATE", "REJECTED"]),
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
