"""Validate one normalized provider/control observation packet."""
from __future__ import annotations

from typing import Any

from knowledge_provider_eval_common import (
    AUTH_FALSE, IDENT, common_safety, require, validate_subject,
)


def authority(value: Any, label: str) -> None:
    require(isinstance(value, dict) and value.get("candidate_only") is True, f"{label}: candidate authority")
    for key in AUTH_FALSE:
        require(value.get(key) is False, f"{label}: authority escalation: {key}")


def validate_packet(value: Any, suite: dict[str, dict], people: dict[str, dict]) -> dict:
    oid = value.get("observation_id")
    cid = value.get("case_id")
    pid = value.get("participant_id")
    require(value.get("schema_version") == "knowledge-provider-eval-observation/v1", "observation schema")
    allowed = {
        "schema_version", "observation_id", "case_id", "participant_id",
        "participant_identity_digest", "provider_manifest_digest", "subject",
        "query_digest", "fixture", "execution", "index", "results",
        "authority", "resources", "cleanup", "memory_policy",
    }
    require(set(value) <= allowed, f"{oid}: unexpected observation keys")
    require(isinstance(oid, str) and IDENT.fullmatch(oid), "observation id")
    require(cid in suite and pid in people, f"{oid}: unknown case or participant")
    case = suite[cid]
    person = people[pid]
    require(pid in case["participants"], f"{oid}: participant not in case")
    require(value.get("participant_identity_digest") == person["identity_digest"], f"{oid}: participant identity drift")
    if person["kind"] == "provider":
        require(value.get("provider_manifest_digest") == person["manifest_digest"], f"{oid}: provider manifest drift")
    else:
        require(value.get("provider_manifest_digest") is None, f"{oid}: control manifest")
    require(value.get("subject") == case["subject"], f"{oid}: subject drift")
    validate_subject(value.get("subject"), f"{oid}.subject")
    require(value.get("query_digest") == case["query_digest"], f"{oid}: query digest mismatch")
    require(isinstance(value.get("fixture"), bool), f"{oid}: fixture")

    execution = value.get("execution", {})
    state = execution.get("state")
    executed = execution.get("executed")
    require(state in {"PASS", "FAIL", "ABSENT", "NOT_EXERCISED", "SKIPPED_BY_POLICY"}, f"{oid}: state")
    require(isinstance(executed, bool), f"{oid}: executed")
    if state == "PASS":
        require(executed is True, f"{oid}: false PASS")
    if state in {"ABSENT", "NOT_EXERCISED", "SKIPPED_BY_POLICY"}:
        require(executed is False, f"{oid}: non-run executed")

    index = value.get("index", {})
    require(index.get("state") in {"FRESH", "STALE", "UNKNOWN", "NOT_APPLICABLE"}, f"{oid}: index")
    require(isinstance(index.get("subject_match"), bool), f"{oid}: index subject")
    if state == "PASS" and case["hard_gates"]["fresh_index_required"]:
        require(index.get("state") == "FRESH", f"{oid}: stale index")
        require(index.get("subject_match") is True, f"{oid}: index subject drift")

    results = value.get("results", [])
    require(isinstance(results, list), f"{oid}: results")
    ids, ranks = set(), set()
    for item in results:
        rid = item.get("id")
        rank = item.get("rank")
        require(isinstance(rid, str) and IDENT.fullmatch(rid), f"{oid}: result id")
        require(rid not in ids and isinstance(rank, int) and rank > 0 and rank not in ranks, f"{oid}: duplicate result")
        ids.add(rid); ranks.add(rank)
        verdict = item.get("verdict")
        verification = item.get("verification")
        require(verdict in {"FOUND", "NO_FLOW", "UNKNOWN"}, f"{oid}: verdict")
        require(verification in {"SOURCE_READBACK_CONFIRMED", "CANDIDATE_ONLY", "UNRESOLVED"}, f"{oid}: verification")
        if verdict == "FOUND" and case["hard_gates"]["source_readback_required"]:
            require(verification == "SOURCE_READBACK_CONFIRMED" and item.get("source_refs"), f"{oid}: FOUND without source readback")
        if verdict == "NO_FLOW":
            require(rid not in case["oracle"]["must_remain_unknown"], f"{oid}: coverage gap collapsed to NO_FLOW")
    authority(value.get("authority"), oid)
    common_safety(value)
    return {"oid": oid, "case": case, "person": person, "state": state, "results": results}
