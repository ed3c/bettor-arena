#!/usr/bin/env python3
"""The GC pass, in the order #97 names.

    RESOURCE_INVENTORY_CAPTURED
    -> OWNERSHIP_LEASE_RETENTION_CLASSIFIED
    -> LIVE_PROTECTED_BLOCKED_EXPIRED_DERIVED
    -> DRY_RUN_GC_PLAN
    -> SAFETY_SUBJECT_REACHABILITY_GATES
    -> HUMAN_ADMIT_FOR_DESTRUCTIVE_CLASSES
    -> CLEANUP_EXECUTED
    -> RESIDUE_VERIFIED
    -> TOMBSTONE_RECEIPT_APPENDED
    -> REBUILD_ROLLBACK_PROBE

The rebuild probe runs *before* the plan, not after the deletion. Proving a
projection rebuildable after removing it is not a probe, it is a recovery
attempt, and by then there is no original left to compare against.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rgc_common import ContractError, digest
from rgc_execute import execute
from rgc_plan import build_plan, derive_sets, validate_resource
from rgc_rebuild import prove

STATES = [
    "RESOURCE_INVENTORY_CAPTURED",
    "OWNERSHIP_LEASE_RETENTION_CLASSIFIED",
    "LIVE_PROTECTED_BLOCKED_EXPIRED_DERIVED",
    "REBUILD_PROBE",
    "DRY_RUN_GC_PLAN",
    "SAFETY_SUBJECT_REACHABILITY_GATES",
    "HUMAN_ADMIT_FOR_DESTRUCTIVE_CLASSES",
    "CLEANUP_EXECUTED",
    "RESIDUE_VERIFIED",
    "TOMBSTONE_RECEIPT_APPENDED",
]


def run_gc(
    root_id: str,
    resources: list[dict[str, Any]],
    held_leases: set[str],
    live_subjects: set[str],
    rebuild_specs: list[dict[str, Any]],
    admitted: list[str],
    authorized_by: str,
    now: str,
    max_age_s: int,
    root: Path,
    apply: bool = False,
    **observed: Any,
) -> dict[str, Any]:
    """One GC pass. Deterministic given its inputs and the tree it looks at."""
    trace = ["RESOURCE_INVENTORY_CAPTURED"]

    for index, resource in enumerate(resources):
        validate_resource(resource, f"resources[{index}]")
    trace.append("OWNERSHIP_LEASE_RETENTION_CLASSIFIED")

    sets = derive_sets(resources, held_leases, live_subjects, now, max_age_s)
    trace.append("LIVE_PROTECTED_BLOCKED_EXPIRED_DERIVED")

    # Before the plan. A rebuild proof taken after deletion has no original to
    # compare against, which makes it a recovery attempt rather than a proof.
    proofs = {spec["resource_id"]: prove(spec, root) for spec in rebuild_specs}
    trace.append("REBUILD_PROBE")

    plan = build_plan(root_id, resources, sets, proofs, admitted, authorized_by)
    trace.append("DRY_RUN_GC_PLAN")
    trace.append("SAFETY_SUBJECT_REACHABILITY_GATES")
    trace.append("HUMAN_ADMIT_FOR_DESTRUCTIVE_CLASSES")

    receipt = execute(plan, root, now, apply=apply, **observed)
    trace.append("CLEANUP_EXECUTED")
    trace.append("RESIDUE_VERIFIED")
    trace.append("TOMBSTONE_RECEIPT_APPENDED")

    if receipt["state"] == "RESIDUE_FOUND":
        raise ContractError(
            f"cleanup left residue: {receipt['residue']}; a GC that reports success "
            "with a path, process, port or mount still held has not finished, and the "
            "next run will find it and classify it as an orphan"
        )

    result = {
        "state_trace": trace,
        "sets": sets,
        "rebuild_proofs": {
            rid: proof["state"] for rid, proof in sorted(proofs.items())
        },
        "plan": plan,
        "receipt": receipt,
    }
    result["gc_digest"] = digest(
        {"sets": sets, "plan": plan["actions"], "state": receipt["state"]}
    )
    return result
