#!/usr/bin/env python3
"""Execution and residue verification. Success is asserted, never announced.

Every deletion here is followed by a look. `shutil.rmtree(..., ignore_errors=True)`
returns nothing and raises nothing, so a cleanup that prints PASS after calling it
is printing a hope. The residue scan covers four kinds because they fail
independently: a path can be gone while the process holding it is not, and a port
can be free while the mount is still there.

Disk exhaustion mid-run is `ResourceExhausted`, not a failure. The distinction
matters at exactly the moment it happens: someone reading "GC failed" goes to
debug the GC, and someone reading "the disk filled" goes to find space.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from rgc_common import (
    ContractError,
    ResourceExhausted,
    digest,
    iso_timestamp,
    non_empty_str,
)
from rgc_plan import tombstone, validate_plan

RESIDUE_KINDS = ("PATH", "PROCESS", "PORT", "MOUNT")


def scan_residue(
    root: Path,
    deleted: list[dict[str, Any]],
    live_processes: set[int],
    open_ports: set[int],
    mounts: set[str],
    claimed: dict[str, Any],
) -> list[dict[str, Any]]:
    """What is still there after the deletions. Asked of each kind separately."""
    residue: list[dict[str, Any]] = []

    for action in deleted:
        path = root / action["path"]
        if path.exists():
            residue.append(
                {
                    "kind": "PATH",
                    "id": action["resource_id"],
                    "detail": f"{action['path']} is still on disk after deletion",
                }
            )

    for pid in sorted(claimed.get("processes", [])):
        if pid in live_processes:
            residue.append(
                {
                    "kind": "PROCESS",
                    "id": str(pid),
                    "detail": (
                        f"process {pid} is still running; a path can be gone while "
                        "the process holding it is not"
                    ),
                }
            )
    for port in sorted(claimed.get("ports", [])):
        if port in open_ports:
            residue.append(
                {
                    "kind": "PORT",
                    "id": str(port),
                    "detail": f"port {port} is still bound",
                }
            )
    for mount in sorted(claimed.get("mounts", [])):
        if mount in mounts:
            residue.append(
                {"kind": "MOUNT", "id": mount, "detail": f"{mount} is still mounted"}
            )
    return sorted(residue, key=lambda entry: (entry["kind"], entry["id"]))


def execute(
    plan: dict[str, Any],
    root: Path,
    at: str,
    apply: bool = False,
    live_processes: set[int] | None = None,
    open_ports: set[int] | None = None,
    mounts: set[str] | None = None,
    claimed: dict[str, Any] | None = None,
    free_bytes: int | None = None,
) -> dict[str, Any]:
    """Run a plan and verify what it claims. Returns a receipt, never a verdict."""
    validate_plan(plan)
    iso_timestamp(at, "execute.at")

    deletions = [action for action in plan["actions"] if action["action"] == "DELETE"]
    before = _inventory_bytes(root, plan["actions"])

    if free_bytes is not None and free_bytes <= 0:
        # Typed, and raised before anything is touched. Reporting this as a GC
        # failure sends someone to debug code that was fine.
        raise ResourceExhausted(
            "no free disk before the run; a full disk is not a task that failed and "
            "not a gate that disagreed, and reporting it as either sends someone to "
            "debug the wrong thing"
        )

    removed, skipped, tombstones = [], [], []
    for action in deletions:
        path = root / action["path"]
        if not apply:
            skipped.append({"resource_id": action["resource_id"], "reason": "dry run"})
            continue
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            try:
                path.unlink()
            except OSError as exc:
                skipped.append(
                    {
                        "resource_id": action["resource_id"],
                        "reason": f"unlink failed: {exc}",
                    }
                )
                continue
        removed.append({"resource_id": action["resource_id"], "path": action["path"]})

    receipt_ref = digest({"plan": plan["root_id"], "at": at, "removed": removed})
    for action in deletions:
        if any(entry["resource_id"] == action["resource_id"] for entry in removed):
            tombstones.append(tombstone(action, receipt_ref, at))

    residue = (
        scan_residue(
            root,
            [
                a
                for a in deletions
                if any(r["resource_id"] == a["resource_id"] for r in removed)
            ],
            live_processes or set(),
            open_ports or set(),
            mounts or set(),
            claimed or {},
        )
        if apply
        else []
    )

    after = _inventory_bytes(root, plan["actions"])

    # The assertion, after the fact. Nothing above is trusted to have worked.
    if apply and residue:
        state = "RESIDUE_FOUND"
    elif apply:
        state = "CLEAN"
    else:
        state = "DRY_RUN"

    receipt = {
        "schema_version": "loopx/resource-gc-receipt/v1",
        "root_id": plan["root_id"],
        "authorized_by": plan["authorized_by"],
        "applied": apply,
        "removed": sorted(removed, key=lambda entry: entry["resource_id"]),
        "skipped": sorted(skipped, key=lambda entry: entry["resource_id"]),
        "kept": sorted(
            (
                {"resource_id": a["resource_id"], "reason": a["reason"]}
                for a in plan["actions"]
                if a["action"] == "KEEP"
            ),
            key=lambda entry: entry["resource_id"],
        ),
        "tombstones": sorted(tombstones, key=lambda entry: entry["resource_id"]),
        "residue": residue,
        "inventory_bytes_before": before,
        "inventory_bytes_after": after,
        "state": state,
        "recorded_at": at,
        "authority": "OBSERVATION_ONLY",
        "canonical_writer": "LOOPX_LEDGER_REDUCER",
    }
    receipt["receipt_digest"] = digest(
        {k: v for k, v in receipt.items() if k != "receipt_digest"}
    )
    return receipt


def _inventory_bytes(root: Path, actions: list[dict[str, Any]]) -> int:
    total = 0
    for action in actions:
        path = root / action["path"]
        if path.is_file():
            total += path.stat().st_size
        elif path.is_dir():
            total += sum(p.stat().st_size for p in path.rglob("*") if p.is_file())
    return total


def validate_receipt(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("receipt must be an object")
    if value.get("schema_version") != "loopx/resource-gc-receipt/v1":
        raise ContractError("receipt schema version drifted")
    if value.get("authority") != "OBSERVATION_ONLY":
        raise ContractError("a GC receipt observes; it does not decide")
    non_empty_str(value.get("authorized_by"), "receipt.authorized_by")

    if value.get("state") == "CLEAN" and value.get("residue"):
        raise ContractError(
            "the receipt reports CLEAN with residue recorded; a cleanup that prints "
            "success without looking is the failure this whole module is arranged "
            "around"
        )
    if value.get("applied") and value.get("state") == "DRY_RUN":
        raise ContractError("an applied run reported itself a dry run")

    for entry in value.get("removed", []):
        if not any(
            t["resource_id"] == entry["resource_id"]
            for t in value.get("tombstones", [])
        ):
            raise ContractError(
                f"{entry['resource_id']} was removed with no tombstone; the resource "
                "is gone and so is the record that it ever existed"
            )

    recomputed = digest({k: v for k, v in value.items() if k != "receipt_digest"})
    if value.get("receipt_digest") != recomputed:
        raise ContractError("receipt digest does not match its content")
    return value
