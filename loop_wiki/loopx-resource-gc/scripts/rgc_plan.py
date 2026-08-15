#!/usr/bin/env python3
"""Inventory, classification and the dry-run plan.

Selection is subtractive. Everything starts protected and has to earn its way
into the deletable set by passing each gate in turn, and every gate that stops a
resource records why. The reverse arrangement -- start deletable, remove the ones
that match a protection rule -- is how a resource nobody wrote a rule for ends up
selected, and the rule nobody wrote is always the one for the thing nobody
thought about.

`authorized_by` is checked against a list with one entry. An agent or a provider
cannot admit a destructive class here; not because the check is hard to bypass,
but because the failure it prevents is an agent deciding on its own that a
directory looked unused.
"""

from __future__ import annotations

from typing import Any

from rgc_common import (
    NEVER_DELETABLE,
    ContractError,
    classify,
    exact_object,
    non_empty_str,
    normalise_path,
    parse_time,
    require,
    sha256_ref,
)
from rgc_rebuild import admits_deletion

RESOURCE_KEYS = {
    "resource_id",
    "resource_class",
    "path",
    "bytes",
    "last_used_at",
    "lease_id",
    "dirty",
    "subject_commit",
    "blocked_evidence",
}

SETS = ("LIVE", "PROTECTED", "BLOCKED", "EXPIRED")

# The only authority that may admit a destructive class. A one-element list
# rather than a boolean, so the receipt records who rather than whether.
DESTRUCTIVE_AUTHORITIES = ("HUMAN",)


def validate_resource(value: Any, label: str) -> dict[str, Any]:
    resource = exact_object(value, RESOURCE_KEYS, label)
    non_empty_str(resource["resource_id"], f"{label}.resource_id")
    normalise_path(resource["path"], f"{label}.path")
    classify(resource["resource_class"], label)

    size = resource["bytes"]
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise ContractError(f"{label}.bytes must be a non-negative integer")
    if resource["last_used_at"] is not None:
        parse_time(resource["last_used_at"], f"{label}.last_used_at")
    if not isinstance(resource["dirty"], bool):
        raise ContractError(f"{label}.dirty must be a boolean")
    if not isinstance(resource["blocked_evidence"], bool):
        raise ContractError(f"{label}.blocked_evidence must be a boolean")
    if resource["subject_commit"] is not None:
        non_empty_str(resource["subject_commit"], f"{label}.subject_commit")
    if resource["lease_id"] is not None:
        non_empty_str(resource["lease_id"], f"{label}.lease_id")
    return resource


def derive_sets(
    resources: list[dict[str, Any]],
    held_leases: set[str],
    live_subjects: set[str],
    now: str,
    max_age_s: int,
) -> dict[str, list[str]]:
    """Partition the inventory. Every resource lands in exactly one set."""
    moment = parse_time(now, "now")
    sets: dict[str, list[str]] = {name: [] for name in SETS}
    for resource in resources:
        rid = resource["resource_id"]
        retention = classify(resource["resource_class"], rid)
        if resource["blocked_evidence"] or retention in NEVER_DELETABLE:
            sets["BLOCKED" if resource["blocked_evidence"] else "PROTECTED"].append(rid)
            continue
        if resource["lease_id"] in held_leases or resource["dirty"]:
            sets["LIVE"].append(rid)
            continue
        if resource["subject_commit"] in live_subjects:
            sets["PROTECTED"].append(rid)
            continue
        last_used = resource["last_used_at"]
        if last_used is None:
            # Never used, or the timestamp was lost. Not the same as old: an
            # unknown age treated as expired deletes on missing data.
            sets["PROTECTED"].append(rid)
            continue
        if (moment - parse_time(last_used, "last_used_at")).total_seconds() > max_age_s:
            sets["EXPIRED"].append(rid)
        else:
            sets["PROTECTED"].append(rid)

    total = sum(len(v) for v in sets.values())
    if total != len(resources):
        raise ContractError(
            f"{len(resources)} resources partitioned into {total} entries; a resource "
            "in two sets or none makes every later count wrong"
        )
    return {name: sorted(values) for name, values in sets.items()}


def build_plan(
    root_id: str,
    resources: list[dict[str, Any]],
    sets: dict[str, list[str]],
    proofs: dict[str, dict[str, Any]],
    admitted: list[str],
    authorized_by: str,
) -> dict[str, Any]:
    """Turn the expired set into actions, with every refusal recorded."""
    non_empty_str(root_id, "root_id")
    if authorized_by not in DESTRUCTIVE_AUTHORITIES:
        raise ContractError(
            f"destructive cleanup authorized by {authorized_by!r}; only "
            f"{list(DESTRUCTIVE_AUTHORITIES)} may admit a destructive class. An agent "
            "deciding on its own that a directory looked unused is the failure this "
            "check exists for"
        )

    by_id = {resource["resource_id"]: resource for resource in resources}
    admitted_set = set(admitted)
    unknown = sorted(admitted_set - set(by_id))
    if unknown:
        raise ContractError(
            f"admitted resources {unknown} are not in the inventory; admitting by a "
            "name nobody inventoried would delete whatever later takes that name"
        )

    # Everything starts protected. A resource reaches DELETE only by passing
    # every gate below, and each gate that stops it says so.
    actions = []
    for resource_id in sorted(by_id):
        resource = by_id[resource_id]
        retention = classify(resource["resource_class"], resource_id)

        if retention in NEVER_DELETABLE:
            actions.append(_keep(resource, "immutable evidence is never deletable"))
            continue
        if resource["blocked_evidence"]:
            actions.append(
                _keep(resource, "blocked conflict evidence must stay recoverable")
            )
            continue
        if resource_id in sets["LIVE"]:
            actions.append(_keep(resource, "leased or dirty"))
            continue
        if resource_id not in sets["EXPIRED"]:
            actions.append(_keep(resource, "not expired"))
            continue
        if resource_id not in admitted_set:
            actions.append(
                _keep(resource, "expired but not admitted by a Human", proposed=True)
            )
            continue

        # Admitted and expired. The last gate is the one that cannot be waived:
        # a mutable projection must have been rebuilt and matched.
        if retention == "MUTABLE_RECREATABLE":
            proof = proofs.get(resource_id)
            if proof is None:
                actions.append(
                    _keep(
                        resource,
                        "no rebuild proof; 'recreatable' is a claim about the future "
                        "and only a rebuild beside the original checks it",
                    )
                )
                continue
            if not admits_deletion(proof):
                actions.append(
                    _keep(
                        resource,
                        f"rebuild proof is {proof['state']}: {proof['reason']}",
                    )
                )
                continue
        actions.append(
            {
                "resource_id": resource_id,
                "path": resource["path"],
                "resource_class": resource["resource_class"],
                "retention": retention,
                "action": "DELETE",
                "reason": "expired, Human-admitted, and rebuild-proven where required",
                "proposed": False,
            }
        )

    deletions = [action for action in actions if action["action"] == "DELETE"]
    require(
        all(action["retention"] not in NEVER_DELETABLE for action in deletions),
        "a plan selected immutable evidence for deletion",
    )
    return {
        "schema_version": "loopx/resource-gc-plan/v1",
        "root_id": root_id,
        "authorized_by": authorized_by,
        "actions": actions,
        "delete_count": len(deletions),
        "keep_count": len(actions) - len(deletions),
        "bytes_reclaimable": sum(by_id[a["resource_id"]]["bytes"] for a in deletions),
        # A plan is a plan. Executing it is a separate call with its own flag.
        "state": "DRY_RUN",
    }


def _keep(
    resource: dict[str, Any], reason: str, proposed: bool = False
) -> dict[str, Any]:
    return {
        "resource_id": resource["resource_id"],
        "path": resource["path"],
        "resource_class": resource["resource_class"],
        "retention": classify(resource["resource_class"], resource["resource_id"]),
        "action": "KEEP",
        "reason": reason,
        "proposed": proposed,
    }


def validate_plan(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("a GC plan must be an object")
    if value.get("schema_version") != "loopx/resource-gc-plan/v1":
        raise ContractError("GC plan schema version drifted")
    if value.get("state") != "DRY_RUN":
        raise ContractError(
            "a GC plan is a dry run until executed; a plan that arrives in any other "
            "state has already done something"
        )
    for action in value.get("actions", []):
        if action["action"] not in {"DELETE", "KEEP"}:
            raise ContractError(f"unknown action {action['action']!r}")
        if action["action"] == "DELETE" and action["retention"] in NEVER_DELETABLE:
            raise ContractError(
                f"{action['resource_id']} is {action['retention']} and selected for "
                "deletion; deleting a ledger segment or a Human decision destroys the "
                "record of why everything else was allowed"
            )
    return value


def tombstone(action: dict[str, Any], receipt_ref: str, at: str) -> dict[str, Any]:
    """What is left behind after a deletion, so history survives the resource."""
    sha256_ref(receipt_ref, "tombstone.receipt_ref")
    return {
        "resource_id": action["resource_id"],
        "path": action["path"],
        "resource_class": action["resource_class"],
        "retention": action["retention"],
        "deleted_at": at,
        "receipt_ref": receipt_ref,
        "recoverable_from": (
            "REBUILD_PROVEN" if action["retention"] == "MUTABLE_RECREATABLE" else "NONE"
        ),
    }
