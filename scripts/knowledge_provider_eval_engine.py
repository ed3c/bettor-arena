"""Assemble exact provider/control observations into a non-admitting report."""
from __future__ import annotations

from pathlib import Path

from knowledge_provider_eval_common import load, require
from knowledge_provider_eval_cases import load_cases
from knowledge_provider_eval_metrics import score
from knowledge_provider_eval_packet import validate_packet
from knowledge_provider_eval_registry import load_participants, provider_digests


def evaluate(root: Path, path: Path) -> dict:
    manifests = provider_digests(root)
    people = load_participants(root, manifests)
    suite = load_cases(root, people)
    values = load(path)
    require(isinstance(values, list) and values, "observations array")
    ids, pairs, checked = set(), set(), []
    for value in values:
        oid = value.get("observation_id")
        pair = (value.get("case_id"), value.get("participant_id"))
        require(oid not in ids, f"duplicate observation: {oid}")
        require(pair not in pairs, f"duplicate pair: {pair}")
        ids.add(oid)
        pairs.add(pair)
        checked.append(score(value, validate_packet(value, suite, people)))
    fixture_only = all(item["fixture"] for item in checked)
    return {
        "schema_version": "knowledge-provider-eval-report/v1",
        "suite": {
            "case_count": len(suite),
            "participant_count": len(people),
            "observation_count": len(checked),
            "families": ["graph", "memory", "semantic", "symbol"],
        },
        "evidence_scope": "FIXTURE_ONLY" if fixture_only else "SUBJECT_BOUND_OBSERVATIONS",
        "status": "PASS" if all(item["hard_gates_passed"] for item in checked) else "FAIL",
        "observations": sorted(
            checked,
            key=lambda item: (item["family"], item["case_id"], item["participant_id"]),
        ),
        "admission": {
            "automatic_admission": False,
            "human_admit_required": True,
            "winner": None,
            "reason": (
                "Fixture observations test the evaluator only."
                if fixture_only
                else "Recommendations are candidates; no provider is admitted automatically."
            ),
        },
    }
