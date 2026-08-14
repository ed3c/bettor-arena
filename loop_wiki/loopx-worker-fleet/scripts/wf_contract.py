#!/usr/bin/env python3
"""Schema identity, digest and fixture checks for the fleet contracts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from wf_adapter import ADMISSION_STATES, TMUX_STATES
from wf_cleanup import AUTO_DISPOSITION, DISPOSITIONS
from wf_common import ContractError, InputError, load_json
from wf_lease import HOLDING_STATES, LEASE_STATES, validate_lease
from wf_queue import validate_fleet

MANIFEST_KEYS = {
    "schema_version",
    "interface_version",
    "requires_capabilities",
    "lease_states",
    "holding_states",
    "tmux_states",
    "adapter_admission_states",
    "gc_dispositions",
    "gc_auto_disposition",
    "gc_default_is_destructive",
    "adapter_may_write_gate_verdict",
    "adapter_may_write_canonical_state",
    "schemas",
}

SCHEMA_VERSIONS = {
    "fleet-queue.schema.json": "loopx/worker-fleet-queue/v1",
    "lease.schema.json": "loopx/worker-fleet-lease/v1",
    "receipt.schema.json": "loopx/worker-fleet-receipt/v1",
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

    if manifest["schema_version"] != "loopx/worker-fleet-contract-manifest/v1":
        raise ContractError("manifest schema version drifted")
    if manifest["interface_version"] != "1.0.0":
        raise ContractError("manifest interface version drifted")
    if manifest["requires_capabilities"] != [
        "arena.proof-kernel/v1",
        "loopx.contracts/v1",
        "loopx.ledger/v1",
        "loopx.runtime-fabric/v1",
        "loopx.worker-gateway/v1",
    ]:
        raise ContractError("manifest capability dependencies drifted")

    if manifest["lease_states"] != sorted(LEASE_STATES):
        raise ContractError("lease states drifted from the implementation")
    if manifest["holding_states"] != sorted(HOLDING_STATES):
        raise ContractError("holding states drifted from the implementation")
    if manifest["tmux_states"] != sorted(TMUX_STATES):
        raise ContractError("tmux states drifted from the implementation")
    if manifest["adapter_admission_states"] != sorted(ADMISSION_STATES):
        raise ContractError("adapter admission states drifted")
    if manifest["gc_dispositions"] != sorted(DISPOSITIONS):
        raise ContractError("GC dispositions drifted from the implementation")
    if manifest["gc_auto_disposition"] != AUTO_DISPOSITION:
        raise ContractError("the auto-removable disposition drifted")

    # A tmux state list containing a verdict word is the failure this module is
    # arranged around, checked here as well as at the projection boundary.
    for state in manifest["tmux_states"]:
        if state in {"PASS", "FAIL", "OK", "COMPLETE", "SUCCESS"}:
            raise ContractError(
                f"tmux state {state!r} is a verdict word; a session is a terminal "
                "that is still open, and giving it a verdict vocabulary is how a "
                "live session becomes a passing task"
            )

    if manifest["gc_default_is_destructive"] is not False:
        raise ContractError(
            "gc_default_is_destructive may not be true; a scheduled orphan sweep that "
            "removes by default will eventually remove the one workspace that mattered"
        )
    if manifest["adapter_may_write_gate_verdict"] is not False:
        raise ContractError(
            "an adapter may not write a gate verdict; tmux and Herdr observe, and the "
            "gates the task ran decide"
        )
    if manifest["adapter_may_write_canonical_state"] is not False:
        raise ContractError(
            "an adapter may not write canonical task state; LoopX owns it, and a "
            "queue adapter that writes it becomes a second source of truth"
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
    validate_fleet(load_json(good / "fleet-queue.json"))
    for index, lease in enumerate(load_json(good / "leases.json")):
        validate_lease(lease, f"leases[{index}]")
    return len(sorted(good.glob("*.json")))


def check_contracts(root: Path) -> tuple[int, int]:
    validate_manifest(root)
    return len(SCHEMA_VERSIONS), validate_fixtures(root)


def run_contract_selftest(root: Path) -> int:
    manifest = load_json(root / "contracts" / "manifest.json")
    mutations = [
        ("schema digest", lambda m: m["schemas"][0].__setitem__("sha256", "0" * 64)),
        (
            "tmux gains a verdict word",
            lambda m: m.__setitem__("tmux_states", sorted([*TMUX_STATES, "PASS"])),
        ),
        (
            "gc default made destructive",
            lambda m: m.__setitem__("gc_default_is_destructive", True),
        ),
        (
            "adapter allowed to write a gate verdict",
            lambda m: m.__setitem__("adapter_may_write_gate_verdict", True),
        ),
        (
            "adapter allowed to write canonical state",
            lambda m: m.__setitem__("adapter_may_write_canonical_state", True),
        ),
        (
            "holding states widened",
            lambda m: m.__setitem__(
                "holding_states", sorted([*HOLDING_STATES, "RELEASED"])
            ),
        ),
        (
            "keep dispositions dropped",
            lambda m: m.__setitem__("gc_dispositions", ["AUTO_REMOVABLE"]),
        ),
        (
            "auto disposition widened",
            lambda m: m.__setitem__("gc_auto_disposition", "PROPOSED_REQUIRES_HUMAN"),
        ),
        (
            "requested lease state dropped",
            lambda m: m.__setitem__(
                "lease_states", sorted(set(LEASE_STATES) - {"REQUESTED"})
            ),
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
