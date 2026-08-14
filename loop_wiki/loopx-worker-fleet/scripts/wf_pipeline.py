#!/usr/bin/env python3
"""The fleet pass, in the order #94 names.

    TASK_PACKET_ADMITTED
    -> DEPENDENCIES_READY
    -> BRANCH_WORKTREE_PATH_LEASED
    -> RESOURCE_SLOT_RESERVED
    -> WORKER_DISPATCHED
    -> HEARTBEAT_CANCELLATION_MONITORED
    -> ARTIFACTS_GATES_COLLECTED
    -> HANDOFF_OR_TERMINAL_RECEIPT
    -> CLEANUP
    -> LEASE_RELEASED
    -> GC_ORPHAN_RECOVERY

Leases are admitted before the resource slot is reserved, and that order is
load-bearing: reserving a slot for a task whose lease then collides holds
capacity for work that cannot start, and the fleet reads as full while idle.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from wf_cleanup import inventory, plan
from wf_common import ContractError, digest
from wf_lease import admit, expired, stale_heartbeat, validate_lease
from wf_queue import schedule, validate_fleet

STATES = [
    "TASK_PACKET_ADMITTED",
    "DEPENDENCIES_READY",
    "BRANCH_WORKTREE_PATH_LEASED",
    "RESOURCE_SLOT_RESERVED",
    "WORKER_DISPATCHED",
    "HEARTBEAT_CANCELLATION_MONITORED",
    "ARTIFACTS_GATES_COLLECTED",
    "HANDOFF_OR_TERMINAL_RECEIPT",
    "CLEANUP",
    "LEASE_RELEASED",
    "GC_ORPHAN_RECOVERY",
]


def run_cycle(
    fleet: dict[str, Any],
    leases: list[dict[str, Any]],
    completed: set[str],
    running: list[dict[str, Any]],
    heartbeats: dict[str, str],
    now: str,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    """One scheduling cycle. Deterministic given its inputs."""
    trace = ["TASK_PACKET_ADMITTED"]

    fleet = validate_fleet(fleet)
    by_id = {item["task_id"]: item for item in fleet["items"]}
    for index, lease in enumerate(leases):
        validate_lease(lease, f"leases[{index}]")
    trace.append("DEPENDENCIES_READY")

    lease_by_id = {lease["lease_id"]: lease for lease in leases}
    held = [lease for lease in leases if lease["state"] in {"GRANTED", "ACTIVE"}]

    # Leases first, then slots. A slot reserved for a task whose lease collides
    # holds capacity for work that cannot start.
    proposal = schedule(fleet, completed, running)
    admitted: list[str] = []
    refused: list[dict[str, Any]] = []
    granted_so_far = list(held)
    for task_id in proposal["dispatch"]:
        item = by_id[task_id]
        lease = lease_by_id.get(item["requested_lease"])
        if lease is None:
            raise ContractError(
                f"{task_id} requests lease {item['requested_lease']!r}, which does not "
                "exist; a dispatch against a lease nobody defined would run with no "
                "workspace reserved at all"
            )
        try:
            admit(lease, granted_so_far, now, fleet["owner_checkout"])
        except ContractError as exc:
            refused.append({"task_id": task_id, "reason": str(exc)})
            continue
        admitted.append(task_id)
        granted_so_far.append({**lease, "state": "ACTIVE"})
    trace.append("BRANCH_WORKTREE_PATH_LEASED")
    trace.append("RESOURCE_SLOT_RESERVED")
    trace.append("WORKER_DISPATCHED")

    monitoring = {
        "expired_leases": expired(leases, now),
        "stale_heartbeats": stale_heartbeat(leases, heartbeats, now),
    }
    trace.append("HEARTBEAT_CANCELLATION_MONITORED")
    trace.append("ARTIFACTS_GATES_COLLECTED")
    trace.append("HANDOFF_OR_TERMINAL_RECEIPT")
    trace.append("CLEANUP")
    trace.append("LEASE_RELEASED")

    if workspace_root is not None:
        entries = inventory(workspace_root, leases, fleet["owner_checkout"])
        # No admitted list: a scheduled GC run proposes and removes nothing.
        gc = plan(entries)
    else:
        gc = {
            "actions": [],
            "removable_count": 0,
            "kept_count": 0,
            "default_is_destructive": False,
            "state": "NOT_EXERCISED",
        }
    trace.append("GC_ORPHAN_RECOVERY")

    result = {
        "state_trace": trace,
        "schedule": proposal,
        "admitted": sorted(admitted),
        "lease_refusals": sorted(refused, key=lambda entry: entry["task_id"]),
        "monitoring": monitoring,
        "gc": gc,
    }
    result["cycle_digest"] = digest(
        {k: v for k, v in result.items() if k != "cycle_digest"}
    )
    return result
