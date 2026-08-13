"""Validate exact provider-evaluation cases and their hard-gate contracts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from knowledge_provider_eval_common import (
    EVALS, FAMILIES, IDENT, common_safety, digest, load, require,
    validate_subject,
)


def validate_case(value: Any, people: dict[str, dict]) -> None:
    cid = value.get("id")
    family = value.get("family")
    require(value.get("schema_version") == "knowledge-provider-eval-case/v1", "case schema")
    require(isinstance(cid, str) and IDENT.fullmatch(cid), "case id")
    require(family in FAMILIES, f"{cid}: family")
    validate_subject(value.get("subject"), f"{cid}.subject")
    query = value.get("query")
    require(isinstance(query, dict) and digest(query) == value.get("query_digest"), f"{cid}: query digest")
    pids = value.get("participants", [])
    require(len(pids) >= 2 and len(pids) == len(set(pids)), f"{cid}: participants")
    require(any(people.get(pid, {}).get("kind") == "control" for pid in pids), f"{cid}: control")
    require(any(people.get(pid, {}).get("kind") == "provider" for pid in pids), f"{cid}: provider")
    for pid in pids:
        require(pid in people and family in people[pid]["families"], f"{cid}: participant {pid}")
    oracle = value.get("oracle", {})
    relevant = oracle.get("relevant_ids", [])
    unknown = oracle.get("must_remain_unknown", [])
    require(relevant and len(relevant) == len(set(relevant)), f"{cid}: relevant ids")
    require(len(unknown) == len(set(unknown)) and not (set(relevant) & set(unknown)), f"{cid}: unknown ids")
    gates = value.get("hard_gates", {})
    budgets = value.get("budgets", {})
    for key in {
        "source_readback_required", "fresh_index_required", "candidate_only",
        "no_authority_escalation", "cleanup_required",
    }:
        require(isinstance(gates.get(key), bool), f"{cid}: gate {key}")
    for key in {"min_verified_precision", "min_verified_recall"}:
        require(isinstance(gates.get(key), (int, float)) and 0 <= gates[key] <= 1, f"{cid}: {key}")
    for key in {"max_results", "max_context_bytes", "max_latency_ms", "max_tool_calls"}:
        require(isinstance(budgets.get(key), int) and budgets[key] > 0, f"{cid}: budget {key}")
    recommendations = value.get("eligible_recommendations", [])
    require(recommendations and len(recommendations) == len(set(recommendations)), f"{cid}: recommendations")
    if family == "memory":
        policy = value.get("memory_policy", {})
        require(policy.get("preserve_conflict") is True, f"{cid}: preserve conflict")
        require(policy.get("current_authority_wins") is True, f"{cid}: current authority")
        require(policy.get("durable_write_requires_human_admit") is True, f"{cid}: memory admit")
    common_safety(value)


def load_cases(root: Path, people: dict[str, dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for path in sorted((root / EVALS / "cases").glob("*.json")):
        value = load(path)
        validate_case(value, people)
        require(value["id"] not in result, f"duplicate case: {value['id']}")
        result[value["id"]] = value
    require({item["family"] for item in result.values()} == FAMILIES, "family coverage")
    return result
