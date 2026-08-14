"""Score validated provider observations without performing admission."""

from __future__ import annotations

from knowledge_provider_eval_common import require


def score(value: dict, packet: dict) -> dict:
    oid = packet["oid"]
    case = packet["case"]
    person = packet["person"]
    state = packet["state"]
    results = packet["results"]
    resources = value.get("resources", {})
    budgets = case["budgets"]
    for key in ("latency_ms", "context_bytes", "tool_calls", "result_count"):
        require(
            isinstance(resources.get(key), int) and resources[key] >= 0,
            f"{oid}: resource {key}",
        )
    require(resources["result_count"] == len(results), f"{oid}: result_count drift")
    require(
        resources["result_count"] <= budgets["max_results"], f"{oid}: result budget"
    )
    require(
        resources["context_bytes"] <= budgets["max_context_bytes"],
        f"{oid}: context budget",
    )
    require(
        resources["latency_ms"] <= budgets["max_latency_ms"], f"{oid}: latency budget"
    )
    require(resources["tool_calls"] <= budgets["max_tool_calls"], f"{oid}: tool budget")
    cleanup = value.get("cleanup", {})
    if state == "PASS" and case["hard_gates"]["cleanup_required"]:
        require(cleanup.get("status") == "PASS", f"{oid}: cleanup failed")
        require(cleanup.get("residue") == [], f"{oid}: cleanup residue")
    if case["family"] == "memory":
        policy = value.get("memory_policy", {})
        require(
            policy.get("conflict_preserved") is True, f"{oid}: memory conflict erased"
        )
        require(
            policy.get("current_authority_won") is True,
            f"{oid}: memory overrode authority",
        )
        require(
            policy.get("durable_write_performed") is False,
            f"{oid}: direct durable memory write",
        )
        require(policy.get("human_admit") is False, f"{oid}: provider Human Admit")
    else:
        require(value.get("memory_policy") is None, f"{oid}: unexpected memory policy")

    relevant = set(case["oracle"]["relevant_ids"])
    unknown = set(case["oracle"]["must_remain_unknown"])
    found = {
        item["id"]
        for item in results
        if item["verdict"] == "FOUND"
        and item["verification"] == "SOURCE_READBACK_CONFIRMED"
    }
    precision = len(found & relevant) / len(found) if found else 0.0
    recall = len(found & relevant) / len(relevant)
    verdicts = {item["id"]: item["verdict"] for item in results}
    unknown_preserved = all(verdicts.get(item) == "UNKNOWN" for item in unknown)
    hard = (
        state == "PASS"
        and precision >= case["hard_gates"]["min_verified_precision"]
        and recall >= case["hard_gates"]["min_verified_recall"]
        and not (found - relevant)
        and unknown_preserved
    )
    if value["fixture"]:
        recommendation = "FIXTURE_ONLY"
    elif state in {"ABSENT", "NOT_EXERCISED", "SKIPPED_BY_POLICY"}:
        recommendation = "NOT_EXERCISED"
    elif not hard:
        recommendation = "REJECTED"
    elif person["kind"] == "control":
        recommendation = case["eligible_recommendations"][-1]
    else:
        recommendation = case["eligible_recommendations"][0]
    return {
        "observation_id": oid,
        "case_id": value["case_id"],
        "family": case["family"],
        "participant_id": value["participant_id"],
        "participant_kind": person["kind"],
        "fixture": value["fixture"],
        "execution_state": state,
        "hard_gates_passed": hard,
        "metrics": {
            "verified_precision": round(precision, 6),
            "verified_recall": round(recall, 6),
            "false_positive_count": len(found - relevant),
            "unknown_preserved": unknown_preserved,
            "latency_ms": resources["latency_ms"],
            "context_bytes": resources["context_bytes"],
            "tool_calls": resources["tool_calls"],
            "result_count": resources["result_count"],
        },
        "recommendation": recommendation,
        "human_admit_required": True,
    }
