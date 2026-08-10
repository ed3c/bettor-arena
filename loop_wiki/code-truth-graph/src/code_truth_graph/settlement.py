from __future__ import annotations

from collections import defaultdict
from typing import Any

from .model import REACH_ORDER

POSITIVE_ACTIONS = {"ASSERTED", "REASSERTED", "SURVIVED", "SETTLED"}
NEGATIVE_ACTIONS = {"REFUTED", "SCOPE_NARROWED", "INVALIDATED"}


def _evidence_index(graph: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in graph.get("evidence", [])}


def evaluate_invariant(
    graph: dict[str, Any],
    invariant: dict[str, Any],
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    evidence = _evidence_index(graph)
    ordered_all = sorted(
        events,
        key=lambda event: (int(event.get("sequence", 0)), str(event.get("at", ""))),
    )
    invalid_event_ids: list[str] = []
    ordered: list[dict[str, Any]] = []
    for event in ordered_all:
        ids = list(event.get("evidence_ids", []))
        complete = bool(ids) and all(evidence_id in evidence for evidence_id in ids)
        if complete:
            ordered.append(event)
        else:
            invalid_event_ids.append(str(event.get("id")))
    last_refutation_index = -1
    for index, event in enumerate(ordered):
        if event.get("action") in NEGATIVE_ACTIONS:
            last_refutation_index = index
    survivors = [
        event
        for event in ordered[last_refutation_index + 1 :]
        if event.get("action") in POSITIVE_ACTIONS
    ]
    reach_classes: set[str] = set()
    independence_groups: set[str] = set()
    production_run_ids: set[str] = set()
    real_authority = False
    for event in survivors:
        if event.get("reach"):
            reach_classes.add(str(event["reach"]))
        if event.get("independence_group"):
            independence_groups.add(str(event["independence_group"]))
        for evidence_id in event.get("evidence_ids", []):
            item = evidence.get(evidence_id)
            if not item:
                continue
            reach_classes.add(str(item.get("reach", "TEXT")))
            group = item.get("details", {}).get("independence_group")
            if group:
                independence_groups.add(str(group))
            if item.get("reach") == "PROD":
                run_id = item.get("details", {}).get("run_id")
                if run_id:
                    production_run_ids.add(str(run_id))
            if item.get("environment_class") in {
                "production",
                "real_device",
                "staging_real",
            } and item.get("authority") not in {"fixture", "synthetic"}:
                real_authority = True
    policy = invariant.get("settlement_policy") or {}
    min_reaches = int(policy.get("min_independent_reaches", 2))
    min_groups = int(policy.get("min_independence_groups", 2))
    require_prod = bool(policy.get("require_prod", invariant.get("critical", False)))
    min_prod_runs = int(
        policy.get("min_prod_runs", 2 if invariant.get("repeat_sensitive") else 1)
    )
    has_later_refutation = bool(
        ordered and ordered[-1].get("action") in NEGATIVE_ACTIONS
    )
    requirements = {
        "no_latest_refutation": not has_later_refutation,
        "reach_classes": len(reach_classes) >= min_reaches,
        "independence_groups": len(independence_groups) >= min_groups,
        "prod_present": (not require_prod) or ("PROD" in reach_classes),
        "prod_repetition": (not require_prod)
        or len(production_run_ids) >= min_prod_runs,
        "real_authority": (not require_prod) or real_authority,
    }
    settled = all(requirements.values())
    if settled:
        status = "SETTLED"
    elif has_later_refutation:
        status = "REFUTED"
    elif survivors:
        status = "UNSETTLED"
    else:
        status = "UNCHALLENGED"
    if status == "UNSETTLED" and any(
        evidence.get(eid, {}).get("environment_class") == "synthetic"
        for event in survivors
        for eid in event.get("evidence_ids", [])
    ):
        status = "DEMO_ONLY"
    return {
        "status": status,
        "settled": settled,
        "requirements": requirements,
        "reach_classes": sorted(
            reach_classes, key=lambda value: REACH_ORDER.get(value, -1)
        ),
        "independence_groups": sorted(independence_groups),
        "production_run_ids": sorted(production_run_ids),
        "last_refutation_sequence": ordered[last_refutation_index].get("sequence")
        if last_refutation_index >= 0
        else None,
        "surviving_event_ids": [event["id"] for event in survivors],
        "invalid_event_ids": invalid_event_ids,
        "critical_rule": "Critical invariants require real PROD evidence; synthetic fixtures can demonstrate the system but cannot settle product truth.",
    }


def evaluate_all(graph: dict[str, Any]) -> dict[str, Any]:
    events_by_invariant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in graph.get("invariant_events", []):
        events_by_invariant[str(event["invariant_id"])].append(event)
    status_counts: dict[str, int] = defaultdict(int)
    for invariant in graph.get("invariants", []):
        result = evaluate_invariant(
            graph, invariant, events_by_invariant.get(invariant["id"], [])
        )
        invariant["settlement"] = result
        invariant["current_status"] = result["status"]
        status_counts[result["status"]] += 1
    graph["closure"]["invariants"] = dict(sorted(status_counts.items()))
    return {"status_counts": dict(status_counts)}


def add_invariants_and_events(
    graph: dict[str, Any],
    *,
    invariants: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> None:
    existing_invariants = {item["id"] for item in graph["invariants"]}
    for invariant in invariants:
        if invariant["id"] not in existing_invariants:
            graph["invariants"].append(invariant)
            existing_invariants.add(invariant["id"])
    existing_events = {item["id"] for item in graph["invariant_events"]}
    for event in events:
        if event["id"] not in existing_events:
            graph["invariant_events"].append(event)
            existing_events.add(event["id"])
