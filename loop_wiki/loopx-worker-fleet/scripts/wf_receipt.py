#!/usr/bin/env python3
"""Terminal receipts. What a Worker observed, and what it is not allowed to conclude.

A fleet receipt records a dispatch and its collected artifacts. It does not
record whether the task passed: the gates the task ran do that, and this module
copies their verdicts through without adding to them. `gate_authority` says so
on every receipt, next to the numbers, because the place a reader forms the
wrong impression is the place the correction has to be.

`worker_state` is derived from the process, never from an adapter. A tmux
session and a Herdr exit code are recorded on the receipt as observations, and
the constructor refuses to build a receipt whose worker state was taken from
either.
"""

from __future__ import annotations

from typing import Any

from wf_adapter import herdr_admission, tmux_projection
from wf_common import (
    ContractError,
    digest,
    exact_object,
    iso_timestamp,
    non_empty_str,
)

RECEIPT_SCHEMA = "loopx/worker-fleet-receipt/v1"

WORKER_STATES = (
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    "TIMED_OUT",
    "LOST_HEARTBEAT",
)

# Terminal states in which cleanup must have run. A Worker that ended and left
# its workspace behind is the orphan the GC will later find and be unable to
# classify.
REQUIRE_CLEANUP = set(WORKER_STATES)

CLEANUP_KEYS = {
    "workspace_removed",
    "process_group_empty",
    "ports_released",
    "mounts_released",
}


def build_receipt(
    task_id: str,
    lease: dict[str, Any],
    worker_state: str,
    exit_code: int | None,
    gates: list[dict[str, Any]],
    artifacts: list[dict[str, Any]],
    cleanup: dict[str, Any],
    observations: dict[str, Any],
    at: str,
) -> dict[str, Any]:
    non_empty_str(task_id, "task_id")
    iso_timestamp(at, "receipt.at")
    if worker_state not in WORKER_STATES:
        raise ContractError(f"worker_state must be one of {list(WORKER_STATES)}")

    cleanup = exact_object(cleanup, CLEANUP_KEYS, "cleanup")
    for field in CLEANUP_KEYS:
        if not isinstance(cleanup[field], bool):
            raise ContractError(f"cleanup.{field} must be a boolean")
    if worker_state in REQUIRE_CLEANUP and not cleanup["process_group_empty"]:
        raise ContractError(
            f"task {task_id} reached {worker_state} with descendants still running; "
            "a timeout that kills the Worker and leaves its children shows up later "
            "as a machine with no free CPU while the fleet says the task ended"
        )
    if worker_state in REQUIRE_CLEANUP and not cleanup["workspace_removed"]:
        raise ContractError(
            f"task {task_id} reached {worker_state} without removing its workspace; "
            "the GC will find it later and have to guess what it was"
        )

    for index, gate in enumerate(gates):
        exact_object(gate, {"gate_id", "state", "receipt_ref"}, f"gates[{index}]")
        if gate["state"] not in {"PASS", "FAIL", "NOT_EXERCISED", "SKIPPED_BY_POLICY"}:
            raise ContractError(f"gates[{index}].state is not a known evidence state")
        non_empty_str(gate["gate_id"], f"gates[{index}].gate_id")

    # Observations are kept and never promoted. Building the receipt validates
    # them through the adapter module, which has no verdict vocabulary at all.
    tmux = observations.get("tmux")
    herdr = observations.get("herdr")
    projection = tmux_projection(tmux) if tmux is not None else None
    admission = herdr_admission(herdr) if herdr is not None else None

    if projection is not None and worker_state == "COMPLETED":
        # The specific bad inference, refused where it would be made: a live
        # session is not a completed task, and this is the line that stops
        # someone reading one as the other.
        if not gates:
            raise ContractError(
                f"task {task_id} is COMPLETED with no gate results, and the only "
                "positive signal on this receipt is a tmux session. A session is a "
                "terminal that is still open; it survives the process failing"
            )

    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "task_id": task_id,
        "lease_id": lease["lease_id"],
        "worker_id": lease["worker_id"],
        "branch": lease["branch"],
        "worktree_path": lease["worktree_path"],
        "worker_state": worker_state,
        "exit_code": exit_code,
        "gates": sorted(gates, key=lambda gate: gate["gate_id"]),
        "artifacts": sorted(artifacts, key=lambda artifact: artifact["path"]),
        "cleanup": cleanup,
        "observations": {
            "tmux": projection,
            "herdr": admission,
        },
        "recorded_at": at,
        # The two sentences this module exists to keep true.
        "gate_authority": "GATES_ONLY_NOT_THIS_FLEET",
        "canonical_writer": "LOOPX_LEDGER_REDUCER",
        "authority": "OBSERVATION_ONLY",
    }
    receipt["receipt_digest"] = digest(
        {k: v for k, v in receipt.items() if k != "receipt_digest"}
    )
    return receipt


def validate_receipt(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("receipt must be an object")
    if value.get("schema_version") != RECEIPT_SCHEMA:
        raise ContractError("receipt schema version drifted")
    if value.get("authority") != "OBSERVATION_ONLY":
        raise ContractError(
            "a fleet receipt observes; it does not decide. Any other authority would "
            "mean the fleet wrote a verdict the gates did not reach"
        )
    if value.get("gate_authority") != "GATES_ONLY_NOT_THIS_FLEET":
        raise ContractError("gate authority drifted from the gates")
    if value.get("canonical_writer") != "LOOPX_LEDGER_REDUCER":
        raise ContractError("canonical writer drifted from the reducer")

    observations = value.get("observations", {})
    for name in ("tmux", "herdr"):
        observation = observations.get(name)
        if observation is None:
            continue
        if observation.get("authority") not in {
            "OPERATOR_PROJECTION_ONLY",
            "ADAPTER_ONLY",
        }:
            raise ContractError(
                f"observations.{name} claims authority {observation.get('authority')!r}; "
                "adapters observe and nothing else"
            )
        evidence = observation.get("task_evidence", observation.get("gate_evidence"))
        if evidence != "NONE":
            raise ContractError(
                f"observations.{name} claims to be evidence about the task; a session "
                "being present and an adapter exiting zero are facts about adapters"
            )

    recomputed = digest({k: v for k, v in value.items() if k != "receipt_digest"})
    if value.get("receipt_digest") != recomputed:
        raise ContractError("receipt digest does not match its content")
    return value
