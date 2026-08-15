#!/usr/bin/env python3
"""Manifest identity, digests and vocabulary for the benchmark contracts.

The manifest states the things that, if they drifted, would turn this into the
thing it was built against: a source proposal counted as evidence, a failure
dropped from a count, or a local number read as a guarantee. Each has a mutation.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from bm_claim import ORIGINS
from bm_common import (
    CACHE_STATES,
    FAMILIES,
    LOCALES,
    STATES,
    TRIAL_OUTCOMES,
    VERDICTS,
    ContractError,
    InputError,
    load_json,
)
from bm_report import MIN_OK_TRIALS

CONTRACTS_REL = "loop_wiki/loopx-benchmark/contracts"

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "states",
    "verdicts",
    "trial_outcomes",
    "case_families",
    "cache_states",
    "locales",
    "claim_origins",
    "min_ok_trials",
    "failures_retained",
    "source_proposal_is_evidence",
    "gate_may_promote_claim",
    "local_result_is_a_guarantee",
    "promotion_owner",
    "live_hardware_matrix_state",
    "schemas",
}

SCHEMA_VERSIONS = {
    "benchmark-report.schema.json": "loopx/benchmark-report/v1",
    "claim-verdict.schema.json": "loopx/benchmark-claim-verdict/v1",
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

    if manifest["schema_version"] != "loopx/benchmark-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")

    if manifest["states"] != STATES:
        raise ContractError("the state sequence drifted from the implementation")
    if manifest["verdicts"] != list(VERDICTS):
        raise ContractError(
            "the verdict ladder drifted; it is ordered because CLAIM_UNVERIFIED is where "
            "everything starts and nothing climbs on its own"
        )
    if manifest["trial_outcomes"] != sorted(TRIAL_OUTCOMES):
        raise ContractError(
            "the trial outcome list drifted; FAILED, TIMEOUT and OOM are exactly the "
            "ones that get dropped before a mean is taken"
        )
    if manifest["case_families"] != sorted(FAMILIES):
        raise ContractError("the case family list drifted from the implementation")
    if manifest["cache_states"] != sorted(CACHE_STATES):
        raise ContractError("the cache state list drifted from the implementation")
    if manifest["locales"] != sorted(LOCALES):
        raise ContractError("the locale list drifted from the implementation")
    if manifest["claim_origins"] != sorted(ORIGINS):
        raise ContractError("the claim origin list drifted from the implementation")
    if manifest["min_ok_trials"] != MIN_OK_TRIALS:
        raise ContractError(
            "the successful-trial floor drifted; below it a percentile is a single "
            "observation with a percentile's name on it"
        )

    if manifest["failures_retained"] is not True:
        raise ContractError(
            "every trial is retained, including the ones that failed. A mean over the "
            "runs that finished is a different statistic wearing the same name"
        )
    if manifest["source_proposal_is_evidence"] is not False:
        raise ContractError(
            "a number in a source proposal was measured somewhere, on hardware nobody "
            "here has, with software nobody here pinned. It is a hypothesis with a "
            "decimal point"
        )
    if manifest["gate_may_promote_claim"] is not False:
        raise ContractError("claim promotion is Human Admit; no gate writes a verdict")
    if manifest["local_result_is_a_guarantee"] is not False:
        raise ContractError(
            "a LOCAL number is a fact about one machine with its own page cache, its own "
            "thermal headroom and its own idle neighbours; a VPS has none of those"
        )
    if manifest["promotion_owner"] != "HUMAN_ADMIT":
        raise ContractError("claim promotion ownership drifted")
    if manifest["live_hardware_matrix_state"] != "NOT_EXERCISED":
        raise ContractError(
            "no live hardware matrix has been run; the six-host and local/cloud families "
            "need machines this repository does not have"
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
    return len(SCHEMA_VERSIONS), len(sorted((root / CONTRACTS_REL).glob("*.json")))


def run_contract_selftest(root: Path) -> int:
    manifest = load_json(root / CONTRACTS_REL / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        ("schema identity", lambda m: m["schemas"][1].__setitem__("id", "https://x/y")),
        (
            "failures no longer retained",
            lambda m: m.__setitem__("failures_retained", False),
        ),
        (
            "source proposal made evidence",
            lambda m: m.__setitem__("source_proposal_is_evidence", True),
        ),
        (
            "gate promotes a claim",
            lambda m: m.__setitem__("gate_may_promote_claim", True),
        ),
        (
            "local made a guarantee",
            lambda m: m.__setitem__("local_result_is_a_guarantee", True),
        ),
        ("promotion owner moved", lambda m: m.__setitem__("promotion_owner", "GATE")),
        (
            "live hardware matrix claimed",
            lambda m: m.__setitem__("live_hardware_matrix_state", "PASS"),
        ),
        ("the trial floor lowered", lambda m: m.__setitem__("min_ok_trials", 1)),
        ("a failure outcome dropped", lambda m: m["trial_outcomes"].remove("TIMEOUT")),
        ("the OOM outcome dropped", lambda m: m["trial_outcomes"].remove("OOM")),
        ("a verdict dropped", lambda m: m["verdicts"].remove("PROFILE_OBSERVED")),
        (
            "the ladder reordered",
            lambda m: m.__setitem__("verdicts", list(reversed(m["verdicts"]))),
        ),
        (
            "a case family dropped",
            lambda m: m["case_families"].remove("local_cloud_same_workload"),
        ),
        ("the synthetic locale dropped", lambda m: m["locales"].remove("SYNTHETIC")),
        ("a cache state dropped", lambda m: m["cache_states"].remove("WARM")),
        (
            "a claim origin dropped",
            lambda m: m["claim_origins"].remove("SOURCE_PROPOSAL"),
        ),
        ("a state dropped", lambda m: m["states"].remove("FAILURES_RETAINED")),
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
