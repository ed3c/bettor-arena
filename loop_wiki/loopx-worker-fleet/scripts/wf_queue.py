#!/usr/bin/env python3
"""The queue, its dependency graph, and a scheduler that produces the same plan twice.

Determinism is the property that makes the rest of this module testable. A
scheduler that iterates a set, or breaks ties by wall clock, produces a
different plan on every run and no collision control can then distinguish "this
schedule is wrong" from "this schedule is different". Ordering here is by
(priority, order, task_id) and nothing else.

Backpressure is a refusal, not a queue-behind-the-queue. Admitting more work
than the fleet can hold and letting it wait consumes leases while it waits, and
the leases are what the waiting work is waiting for.
"""

from __future__ import annotations

from typing import Any

from wf_common import (
    ContractError,
    exact_object,
    non_empty_str,
    positive_int,
    require,
    SHA40,
)

ITEM_KEYS = {
    "task_id",
    "order",
    "priority",
    "subject",
    "depends_on",
    "requested_lease",
    "budgets",
    "cache_scope",
}

SUBJECT_KEYS = {"repository", "commit", "issue"}

BUDGET_KEYS = {
    "cpu_slots",
    "memory_mb",
    "disk_mb",
    "max_processes",
    "max_output_bytes",
    "timeout_ms",
}

FLEET_KEYS = {
    "schema_version",
    "max_parallelism",
    "cpu_slots_total",
    "memory_mb_total",
    "disk_mb_total",
    "owner_checkout",
    "items",
}


def validate_subject(value: Any, label: str) -> dict[str, Any]:
    subject = exact_object(value, SUBJECT_KEYS, label)
    non_empty_str(subject["repository"], f"{label}.repository")
    if SHA40.fullmatch(str(subject["commit"])) is None:
        raise ContractError(f"{label}.commit must be a full 40-hex sha")
    positive_int(subject["issue"], f"{label}.issue")
    return subject


def validate_budgets(value: Any, label: str) -> dict[str, Any]:
    budgets = exact_object(value, BUDGET_KEYS, label)
    for field in BUDGET_KEYS:
        positive_int(budgets[field], f"{label}.{field}")
    return budgets


def validate_item(value: Any, label: str) -> dict[str, Any]:
    item = exact_object(value, ITEM_KEYS, label)
    non_empty_str(item["task_id"], f"{label}.task_id")
    non_empty_str(item["cache_scope"], f"{label}.cache_scope")
    for field in ("order", "priority"):
        value_ = item[field]
        if not isinstance(value_, int) or isinstance(value_, bool) or value_ < 0:
            raise ContractError(f"{label}.{field} must be a non-negative integer")
    validate_subject(item["subject"], f"{label}.subject")
    validate_budgets(item["budgets"], f"{label}.budgets")

    depends = item["depends_on"]
    if not isinstance(depends, list) or depends != sorted(depends):
        raise ContractError(f"{label}.depends_on must be a sorted list")
    if item["task_id"] in depends:
        raise ContractError(f"{label} depends on itself")
    non_empty_str(item["requested_lease"], f"{label}.requested_lease")
    return item


def validate_fleet(value: Any) -> dict[str, Any]:
    fleet = exact_object(value, FLEET_KEYS, "fleet")
    require(
        fleet["schema_version"] == "loopx/worker-fleet-queue/v1",
        "fleet queue schema version drifted",
    )
    for field in (
        "max_parallelism",
        "cpu_slots_total",
        "memory_mb_total",
        "disk_mb_total",
    ):
        positive_int(fleet[field], f"fleet.{field}")
    non_empty_str(fleet["owner_checkout"], "fleet.owner_checkout")

    items = fleet["items"]
    if not isinstance(items, list) or not items:
        raise ContractError("fleet.items must be a non-empty list")

    seen: set[str] = set()
    for index, value_ in enumerate(items):
        item = validate_item(value_, f"items[{index}]")
        if item["task_id"] in seen:
            raise ContractError(f"duplicate task_id {item['task_id']!r}")
        seen.add(item["task_id"])

    for item in items:
        for dependency in item["depends_on"]:
            if dependency not in seen:
                raise ContractError(
                    f"{item['task_id']} depends on {dependency!r}, which is not in the "
                    "queue; a dependency on nothing is satisfied by nothing and the "
                    "task would dispatch immediately"
                )
        # A task that asks for more than the fleet has never becomes ready, and
        # it would sit in the queue looking merely unlucky.
        budgets = item["budgets"]
        for field, total in (
            ("cpu_slots", "cpu_slots_total"),
            ("memory_mb", "memory_mb_total"),
            ("disk_mb", "disk_mb_total"),
        ):
            if budgets[field] > fleet[total]:
                raise ContractError(
                    f"{item['task_id']} requests {budgets[field]} {field} but the "
                    f"fleet has {fleet[total]}; this task can never become ready and "
                    "would wait forever looking merely unlucky"
                )

    detect_cycles(items)
    return fleet


def detect_cycles(items: list[dict[str, Any]]) -> None:
    """Refuse a dependency cycle, naming the cycle rather than just its existence."""
    graph = {item["task_id"]: list(item["depends_on"]) for item in items}
    state: dict[str, int] = {}
    stack: list[str] = []

    def walk(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for dependency in graph.get(node, []):
            if state.get(dependency) == 1:
                cycle = stack[stack.index(dependency) :] + [dependency]
                raise ContractError(
                    f"dependency cycle: {' -> '.join(cycle)}; every task in it waits "
                    "for another task in it, so none becomes ready and the queue "
                    "stalls without any single item looking wrong"
                )
            if state.get(dependency) is None:
                walk(dependency)
        state[node] = 2
        stack.pop()

    for task_id in sorted(graph):
        if state.get(task_id) is None:
            walk(task_id)


def ready(items: list[dict[str, Any]], completed: set[str]) -> list[dict[str, Any]]:
    """Items whose dependencies are all complete, in the scheduler's fixed order."""
    return sorted(
        (item for item in items if set(item["depends_on"]) <= completed),
        key=lambda item: (-item["priority"], item["order"], item["task_id"]),
    )


def schedule(
    fleet: dict[str, Any], completed: set[str], running: list[dict[str, Any]]
) -> dict[str, Any]:
    """One deterministic scheduling decision. Same inputs, same plan, every time."""
    used = {
        "cpu_slots": sum(item["budgets"]["cpu_slots"] for item in running),
        "memory_mb": sum(item["budgets"]["memory_mb"] for item in running),
        "disk_mb": sum(item["budgets"]["disk_mb"] for item in running),
    }
    free_slots = fleet["max_parallelism"] - len(running)

    dispatch: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []
    for item in ready(fleet["items"], completed):
        if item["task_id"] in completed or any(
            r["task_id"] == item["task_id"] for r in running
        ):
            continue
        reasons = []
        if len(dispatch) >= free_slots:
            reasons.append("max_parallelism")
        for field, total in (
            ("cpu_slots", "cpu_slots_total"),
            ("memory_mb", "memory_mb_total"),
            ("disk_mb", "disk_mb_total"),
        ):
            projected = used[field] + sum(d["budgets"][field] for d in dispatch)
            if projected + item["budgets"][field] > fleet[total]:
                reasons.append(field)
        if reasons:
            # Deferred with the reason, not silently dropped. A backpressure
            # decision nobody recorded looks exactly like a scheduler bug.
            deferred.append(
                {"task_id": item["task_id"], "reasons": sorted(set(reasons))}
            )
            continue
        dispatch.append(item)

    blocked = sorted(
        {
            item["task_id"]
            for item in fleet["items"]
            if item["task_id"] not in completed
            and not set(item["depends_on"]) <= completed
        }
    )
    return {
        "dispatch": [item["task_id"] for item in dispatch],
        "deferred": sorted(deferred, key=lambda entry: entry["task_id"]),
        "blocked_by_dependency": blocked,
        "slots_in_use": len(running) + len(dispatch),
        "max_parallelism": fleet["max_parallelism"],
    }
