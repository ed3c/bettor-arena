#!/usr/bin/env python3
"""Manifest identity, digests and vocabulary for the CI parity contracts.

The manifest states the things that, if they drifted, would turn this gate into
the thing it was built against: a local result standing in for a billed one, a
non-pass conclusion promoted to PASS, or a simulator counted as a hosted runner.
Each has a mutation below.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from cp_common import (
    CONCLUSIONS,
    GITHUB_ONLY,
    NOT_EVIDENCE,
    STATES,
    VERDICTS,
    ContractError,
    InputError,
    load_json,
)
from cp_simulator import SIMULATOR_STATES

CONTRACTS_REL = ".github-delivery/ci-parity"

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "states",
    "verdicts",
    "github_only_surfaces",
    "github_conclusions",
    "not_evidence_conclusions",
    "simulator_states",
    "local_proxies_remote",
    "simulator_equals_hosted_runner",
    "stale_head_may_be_reused",
    "skipped_is_pass",
    "publication_owner",
    "live_simulator_state",
    "schemas",
}

SCHEMA_VERSIONS = {
    "parity-receipt.schema.json": "loopx/ci-parity-receipt/v1",
    "workflow-index.schema.json": "loopx/ci-parity-index/v1",
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
    contracts = root / CONTRACTS_REL
    loaded = load_json(contracts / "manifest.json") if override is None else override
    manifest = exact(loaded, MANIFEST_KEYS, "manifest")

    if manifest["schema_version"] != "loopx/ci-parity-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")

    if manifest["states"] != STATES:
        raise ContractError("the state sequence drifted from the implementation")
    if manifest["verdicts"] != sorted(VERDICTS):
        raise ContractError("the verdict vocabulary drifted from the implementation")
    if manifest["github_only_surfaces"] != sorted(GITHUB_ONLY):
        raise ContractError(
            "the GitHub-only surface list drifted; a surface dropped from it becomes "
            "one a local run is silently allowed to claim"
        )
    if manifest["github_conclusions"] != sorted(CONCLUSIONS):
        raise ContractError(
            "the GitHub conclusion list drifted; a conclusion this gate does not know "
            "must be refused, and it can only refuse what it enumerates"
        )
    if manifest["not_evidence_conclusions"] != sorted(NOT_EVIDENCE):
        raise ContractError(
            "the not-evidence list drifted; skipped, cancelled, action_required and "
            "neutral are each the absence of a result, not a pass"
        )
    if manifest["simulator_states"] != sorted(SIMULATOR_STATES):
        raise ContractError("the simulator state list drifted from the implementation")

    if manifest["local_proxies_remote"] is not False:
        raise ContractError(
            "a local run never proxies a remote one; a green local run and a green "
            "hosted run are two observations of two different machines, and the "
            "interesting cases are the ones where they disagree"
        )
    if manifest["simulator_equals_hosted_runner"] is not False:
        raise ContractError(
            "a simulator is not a hosted runner; the image, the token permissions, the "
            "cache and artifact services and the billing all differ"
        )
    if manifest["stale_head_may_be_reused"] is not False:
        raise ContractError(
            "a run at an older SHA is a fact about older code; reusing it is the "
            "cheapest way to claim the current head was verified"
        )
    if manifest["skipped_is_pass"] is not False:
        raise ContractError(
            "a skipped job is not a pass. It is the state that reads as 'not a "
            "failure, so fine'"
        )
    if manifest["publication_owner"] != "HUMAN_OR_TRUSTED_OPERATOR":
        raise ContractError(
            "publication, workflow rerun, merge and billing recovery are Human-owned; "
            "this gate reports what was compared and what was not"
        )
    if manifest["live_simulator_state"] != "NOT_EXERCISED":
        raise ContractError(
            "no simulator has been exercised; nektos/act is an admission after exact "
            "version, image digest and license evidence"
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


def check_contracts(root: Path) -> int:
    validate_manifest(root)
    return len(sorted((root / CONTRACTS_REL).glob("*.json")))


def run_contract_selftest(root: Path) -> int:
    manifest = load_json(root / CONTRACTS_REL / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        ("schema identity", lambda m: m["schemas"][1].__setitem__("id", "https://x/y")),
        ("local made a proxy", lambda m: m.__setitem__("local_proxies_remote", True)),
        (
            "simulator made a runner",
            lambda m: m.__setitem__("simulator_equals_hosted_runner", True),
        ),
        (
            "stale head reused",
            lambda m: m.__setitem__("stale_head_may_be_reused", True),
        ),
        ("skipped made a pass", lambda m: m.__setitem__("skipped_is_pass", True)),
        (
            "publication owner moved",
            lambda m: m.__setitem__("publication_owner", "GATE"),
        ),
        (
            "live simulator claimed",
            lambda m: m.__setitem__("live_simulator_state", "PASS"),
        ),
        (
            "a GitHub-only surface dropped",
            lambda m: m["github_only_surfaces"].remove("BILLING"),
        ),
        (
            "a not-evidence conclusion dropped",
            lambda m: m["not_evidence_conclusions"].remove("CANCELLED"),
        ),
        (
            "a GitHub conclusion dropped",
            lambda m: m["github_conclusions"].remove("action_required"),
        ),
        ("a verdict dropped", lambda m: m["verdicts"].remove("PARTIAL")),
        (
            "a state dropped",
            lambda m: m["states"].remove("GITHUB_EXACT_HEAD_RUN_INGESTED"),
        ),
        (
            "states reordered",
            lambda m: m.__setitem__("states", list(reversed(m["states"]))),
        ),
        (
            "a simulator state dropped",
            lambda m: m["simulator_states"].remove("SIMULATOR_ABSENT"),
        ),
        ("interface version", lambda m: m.__setitem__("interface_version", "2.0.0")),
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
