#!/usr/bin/env python3
"""Positive properties plus one planted control per named failure in #94.

Each control mutates the good fixtures in exactly one place and asserts the
cycle refuses, matching on the substring its own rule raises.

Two controls check a *result* rather than a refusal: a tmux session reported as
a Worker verdict and a Herdr exit code reported as a gate verdict both have to
produce a receipt that still says NONE, because refusing them outright would
also throw away a legitimate operator projection.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

from wf_common import ContractError, paths_overlap
from wf_lease import admit, conflicts
from wf_pipeline import run_cycle
from wf_receipt import build_receipt, validate_receipt

NAMES = ("fleet-queue", "leases", "heartbeats", "observations")

CLEAN = {
    "workspace_removed": True,
    "process_group_empty": True,
    "ports_released": True,
    "mounts_released": True,
}


def load_inputs(root: Path) -> dict[str, Any]:
    good = root / "tests/fixtures/good"
    return {
        name: json.loads((good / f"{name}.json").read_text(encoding="utf-8"))
        for name in NAMES
    }


def _cycle(inputs: dict[str, Any], now: str = "2026-08-15T10:30:00Z") -> dict[str, Any]:
    return run_cycle(
        inputs["fleet-queue"],
        inputs["leases"],
        set(inputs.get("_completed", [])),
        inputs.get("_running", []),
        inputs["heartbeats"],
        now,
    )


def _lease(inputs: dict[str, Any], lease_id: str) -> dict[str, Any]:
    for lease in inputs["leases"]:
        if lease["lease_id"] == lease_id:
            return lease
    raise KeyError(lease_id)


def _item(inputs: dict[str, Any], task_id: str) -> dict[str, Any]:
    for item in inputs["fleet-queue"]["items"]:
        if item["task_id"] == task_id:
            return item
    raise KeyError(task_id)


# --- controls -----------------------------------------------------------------


def _two_workers_one_lease(inputs: dict[str, Any]) -> None:
    _item(inputs, "task-lsp-pool")["requested_lease"] = "lease-gc"


def _worker_in_the_owner_checkout(inputs: dict[str, Any]) -> None:
    _lease(inputs, "lease-gc")["worktree_path"] = "checkouts/owner-live/scratch"


def _overlapping_sibling_paths(inputs: dict[str, Any]) -> None:
    _lease(inputs, "lease-lsp")["path_globs"] = sorted(
        ["loop_wiki/loopx-resource-gc/scripts/**"]
    )


def _same_branch_two_leases(inputs: dict[str, Any]) -> None:
    _lease(inputs, "lease-lsp")["branch"] = "feat/loopx-resource-gc"


def _same_worktree_two_leases(inputs: dict[str, Any]) -> None:
    _lease(inputs, "lease-lsp")["worktree_path"] = "workspaces/resource-gc"


def _expired_lease_continues(inputs: dict[str, Any]) -> None:
    _lease(inputs, "lease-gc")["expires_at"] = "2026-08-15T10:15:00Z"


def _lease_that_expires_when_granted(inputs: dict[str, Any]) -> None:
    _lease(inputs, "lease-gc")["expires_at"] = _lease(inputs, "lease-gc")["granted_at"]


def _heartbeat_longer_than_lease(inputs: dict[str, Any]) -> None:
    _lease(inputs, "lease-gc")["heartbeat_interval_s"] = 99999


def _self_overlapping_lease(inputs: dict[str, Any]) -> None:
    _lease(inputs, "lease-gc")["path_globs"] = sorted(
        ["loop_wiki/loopx-resource-gc/**", "loop_wiki/loopx-resource-gc/scripts/**"]
    )


def _path_traversal_in_a_lease(inputs: dict[str, Any]) -> None:
    _lease(inputs, "lease-gc")["path_globs"] = sorted(["loop_wiki/../../escape/**"])


def _dependency_cycle(inputs: dict[str, Any]) -> None:
    _item(inputs, "task-resource-gc")["depends_on"] = ["task-mem0"]


def _dependency_on_nothing(inputs: dict[str, Any]) -> None:
    _item(inputs, "task-lsp-pool")["depends_on"] = ["task-that-does-not-exist"]


def _task_larger_than_the_fleet(inputs: dict[str, Any]) -> None:
    _item(inputs, "task-mem0")["budgets"]["memory_mb"] = 999999


def _dispatch_against_an_absent_lease(inputs: dict[str, Any]) -> None:
    _item(inputs, "task-resource-gc")["requested_lease"] = "lease-nobody-defined"


def _task_depends_on_itself(inputs: dict[str, Any]) -> None:
    _item(inputs, "task-lsp-pool")["depends_on"] = ["task-lsp-pool"]


def _tmux_state_with_a_verdict_word(inputs: dict[str, Any]) -> None:
    inputs["observations"]["tmux"]["state"] = "PASS"


CONTROLS: list[tuple[str, Callable[[dict[str, Any]], None], str]] = [
    ("two-workers-one-lease", _two_workers_one_lease, "already held"),
    (
        "worker-in-the-owner-live-checkout",
        _worker_in_the_owner_checkout,
        "while they are in it",
    ),
    ("overlapping-sibling-paths", _overlapping_sibling_paths, "overlapping paths"),
    ("two-leases-one-branch", _same_branch_two_leases, "same branch"),
    ("two-leases-one-worktree", _same_worktree_two_leases, "same worktree"),
    ("expired-lease-continues", _expired_lease_continues, "believes is"),
    ("lease-expires-when-granted", _lease_that_expires_when_granted, "cannot be held"),
    (
        "heartbeat-longer-than-the-lease",
        _heartbeat_longer_than_lease,
        "detected by nothing",
    ),
    ("self-overlapping-lease", _self_overlapping_lease, "overlaps itself"),
    ("path-traversal-in-a-lease", _path_traversal_in_a_lease, "climb out of itself"),
    ("queue-dependency-cycle", _dependency_cycle, "dependency cycle"),
    (
        "dependency-on-a-task-not-in-the-queue",
        _dependency_on_nothing,
        "satisfied by nothing",
    ),
    ("task-larger-than-the-fleet", _task_larger_than_the_fleet, "never become ready"),
    (
        "dispatch-against-an-absent-lease",
        _dispatch_against_an_absent_lease,
        "no workspace reserved",
    ),
    ("task-depends-on-itself", _task_depends_on_itself, "depends on itself"),
    (
        "tmux-state-with-a-verdict-word",
        _tmux_state_with_a_verdict_word,
        "survives that process failing",
    ),
]


def run_selftest(root: Path) -> tuple[int, int]:
    base = load_inputs(root)
    positives = 0

    result = _cycle(copy.deepcopy(base))
    if result["state_trace"][-1] != "GC_ORPHAN_RECOVERY":
        raise ContractError("the cycle did not reach orphan recovery")
    if sorted(result["admitted"]) != ["task-lsp-pool", "task-resource-gc"]:
        raise ContractError(f"unexpected admissions: {result['admitted']}")
    if result["lease_refusals"]:
        raise ContractError(
            f"the clean cycle refused leases: {result['lease_refusals']}"
        )
    positives += 1

    # Determinism. A scheduler that iterates a set produces a different plan on
    # every run, and then no collision control can distinguish "wrong" from
    # "different".
    again = _cycle(copy.deepcopy(base))
    if again["cycle_digest"] != result["cycle_digest"]:
        raise ContractError("two identical cycles produced different plans")
    positives += 1

    # Backpressure defers with a reason rather than dropping.
    squeezed = copy.deepcopy(base)
    squeezed["fleet-queue"]["max_parallelism"] = 1
    tight = _cycle(squeezed)
    if tight["schedule"]["dispatch"] != ["task-resource-gc"]:
        raise ContractError(f"backpressure dispatched {tight['schedule']['dispatch']}")
    if [d["task_id"] for d in tight["schedule"]["deferred"]] != ["task-lsp-pool"]:
        raise ContractError("the deferred task was dropped rather than recorded")
    if "max_parallelism" not in tight["schedule"]["deferred"][0]["reasons"]:
        raise ContractError("the deferral did not name its reason")
    positives += 1

    # Dependencies gate readiness, and completing one releases exactly one.
    advanced = copy.deepcopy(base)
    advanced["_completed"] = ["task-resource-gc", "task-lsp-pool"]
    after = _cycle(advanced)
    if after["schedule"]["dispatch"] != ["task-decision-memory"]:
        raise ContractError(
            f"dependency release dispatched {after['schedule']['dispatch']}"
        )
    positives += 1

    # The path rule, both directions. Siblings sharing a prefix must not collide.
    if paths_overlap("loop_wiki/ab", "loop_wiki/a"):
        raise ContractError(
            "loop_wiki/ab was read as inside loop_wiki/a; a string prefix test would "
            "refuse leases that were never in conflict"
        )
    if not paths_overlap("loop_wiki/a/b", "loop_wiki/a"):
        raise ContractError("a nested path was not detected as overlapping")
    positives += 1

    # Every conflict is reported, not just the first.
    left = _lease(base, "lease-gc")
    right = copy.deepcopy(left)
    right["lease_id"] = "lease-clone"
    reasons = conflicts(left, right)
    if len(reasons) < 3:
        raise ContractError(
            f"a fully colliding pair reported {len(reasons)} reason(s); fixing a "
            "collision one reason at a time is a loop of re-runs"
        )
    positives += 1

    # Stale heartbeat and expiry are separate findings. The lease is set ACTIVE
    # first: a REQUESTED lease has no Worker yet, so silence from it is not a
    # crashed Worker and monitoring it would report every queued task as dead.
    silent = copy.deepcopy(base)
    _lease(silent, "lease-gc")["state"] = "ACTIVE"
    silent["heartbeats"]["lease-gc"] = "2026-08-15T10:00:00Z"
    monitored = _cycle(silent)["monitoring"]
    stale_ids = [row["lease_id"] for row in monitored["stale_heartbeats"]]
    if "lease-gc" not in stale_ids:
        raise ContractError("a Worker silent for ten intervals was not reported stale")
    if monitored["expired_leases"]:
        raise ContractError(
            "a stale heartbeat was also reported as expired; recovering them the same "
            "way kills slow work"
        )
    positives += 1

    # A receipt records adapter observations without promoting them.
    receipt = build_receipt(
        "task-resource-gc",
        {**_lease(base, "lease-gc"), "state": "ACTIVE"},
        "COMPLETED",
        0,
        [
            {
                "gate_id": "selftest",
                "state": "PASS",
                "receipt_ref": "sha256:" + "ab" * 32,
            }
        ],
        [],
        CLEAN,
        base["observations"],
        "2026-08-15T11:00:00Z",
    )
    validate_receipt(receipt)
    if receipt["observations"]["tmux"]["task_evidence"] != "NONE":
        raise ContractError("a tmux projection claimed to be task evidence")
    if receipt["observations"]["herdr"]["state"] != "NOT_EXERCISED":
        raise ContractError(
            "Herdr was admitted without an exact binary digest, config digest and "
            "canary receipt"
        )
    positives += 1

    # Herdr exiting zero still yields no gate evidence.
    exercised = copy.deepcopy(base)
    exercised["observations"]["herdr"] = {
        "binary_digest": "sha256:" + "11" * 32,
        "config_digest": "sha256:" + "22" * 32,
        "canary_receipt": "canary-001",
        "exit_code": 0,
    }
    admitted_receipt = build_receipt(
        "task-resource-gc",
        {**_lease(base, "lease-gc"), "state": "ACTIVE"},
        "COMPLETED",
        0,
        [
            {
                "gate_id": "selftest",
                "state": "PASS",
                "receipt_ref": "sha256:" + "ab" * 32,
            }
        ],
        [],
        CLEAN,
        exercised["observations"],
        "2026-08-15T11:00:00Z",
    )
    validate_receipt(admitted_receipt)
    herdr = admitted_receipt["observations"]["herdr"]
    if herdr["state"] != "ADAPTER_ADMITTED":
        raise ContractError("an exercised Herdr canary was not admitted as an adapter")
    if herdr["gate_evidence"] != "NONE":
        raise ContractError(
            "Herdr exiting zero was recorded as gate evidence; the exit code "
            "describes the adapter's run, not the workload's gates"
        )
    positives += 1

    failures = []
    for name, mutate, needle in CONTROLS:
        inputs = copy.deepcopy(base)
        mutate(inputs)
        try:
            cycle = _cycle(inputs)
            # Lease collisions surface as refusals inside the cycle rather than
            # as exceptions, because one task colliding must not stop the fleet.
            refusals = " ".join(row["reason"] for row in cycle["lease_refusals"])
            if needle in refusals:
                continue
            if name == "tmux-state-with-a-verdict-word":
                build_receipt(
                    "task-resource-gc",
                    {**_lease(inputs, "lease-gc"), "state": "ACTIVE"},
                    "COMPLETED",
                    0,
                    [
                        {
                            "gate_id": "s",
                            "state": "PASS",
                            "receipt_ref": "sha256:" + "ab" * 32,
                        }
                    ],
                    [],
                    CLEAN,
                    inputs["observations"],
                    "2026-08-15T11:00:00Z",
                )
            failures.append(f"{name} was accepted")
        except ContractError as exc:
            if needle not in str(exc):
                failures.append(
                    f"{name} was refused, but for the wrong reason: expected a message "
                    f"containing {needle!r}, got {exc}"
                )
        except Exception as exc:  # noqa: BLE001
            failures.append(
                f"{name} raised {type(exc).__name__}: {exc} -- that is a broken "
                "control, not a refusal; nothing was measured"
            )

    # A cleanup that says PASS while descendants run must be refused.
    try:
        build_receipt(
            "task-resource-gc",
            {**_lease(base, "lease-gc"), "state": "ACTIVE"},
            "TIMED_OUT",
            None,
            [{"gate_id": "s", "state": "FAIL", "receipt_ref": "sha256:" + "ab" * 32}],
            [],
            {**CLEAN, "process_group_empty": False},
            base["observations"],
            "2026-08-15T11:00:00Z",
        )
    except ContractError as exc:
        if "no free CPU" not in str(exc):
            failures.append(
                f"orphaned-descendants control refused for the wrong reason: {exc}"
            )
    else:
        failures.append("a receipt with running descendants was accepted")

    # And a completed task whose only positive signal is a tmux session.
    try:
        build_receipt(
            "task-resource-gc",
            {**_lease(base, "lease-gc"), "state": "ACTIVE"},
            "COMPLETED",
            0,
            [],
            [],
            CLEAN,
            base["observations"],
            "2026-08-15T11:00:00Z",
        )
    except ContractError as exc:
        if "still open" not in str(exc):
            failures.append(
                f"tmux-as-completion control refused for the wrong reason: {exc}"
            )
    else:
        failures.append(
            "a COMPLETED receipt with no gates and a live session was accepted"
        )

    # An admitted lease cannot be admitted twice.
    try:
        held = [{**_lease(base, "lease-gc"), "state": "ACTIVE"}]
        admit(
            _lease(base, "lease-gc"),
            held,
            "2026-08-15T10:30:00Z",
            "checkouts/owner-live",
        )
    except ContractError as exc:
        if "already held" not in str(exc):
            failures.append(
                f"double-admission control refused for the wrong reason: {exc}"
            )
    else:
        failures.append("a lease was admitted while already held")

    if failures:
        raise ContractError(
            "planted controls did not behave:\n  " + "\n  ".join(failures)
        )
    return positives, len(CONTROLS) + 3
