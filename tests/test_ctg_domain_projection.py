#!/usr/bin/env python3
"""Exercise the v1.1 domain projection without importing an ix-private runtime."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from code_truth_graph.cli import (
    ContractError,
    ingest_redacted_availability,
    resolve_profile_invariants,
)
from code_truth_graph.model import ensure_node, new_graph
from code_truth_graph.settlement import add_invariants_and_events, evaluate_all


def receipt(raw_content_embedded: bool = False) -> dict[str, object]:
    return {
        "schema_version": "ix-ctg-redacted-evidence@1.1.0",
        "policy_id": "fixture-policy",
        "policy_sha256": "1" * 64,
        "observation_id": "obs-projection",
        "source_count": 2,
        "sources": [
            {
                "source_class": "synthetic_sandbox",
                "source_sha256": "2" * 64,
                "observed_at": "2026-08-09T00:00:00Z",
                "authority": "fixture",
                "run_id": "sandbox-1",
                "evidence_ids": ["ev-sandbox"],
            },
            {
                "source_class": "synthetic_fixture",
                "source_sha256": "3" * 64,
                "observed_at": "2026-08-09T00:01:00Z",
                "authority": "fixture",
                "run_id": "prod-1",
                "evidence_ids": ["ev-prod"],
            },
        ],
        "derived_environment_class": "synthetic_sandbox",
        "derived_authority": "ix-redaction-boundary",
        "observed_at": "2026-08-09T00:00:00Z",
        "raw_content_embedded": raw_content_embedded,
    }


def definitions() -> list[dict[str, object]]:
    return [
        {
            "id": "GF-TEST",
            "statement": "synthetic evidence cannot settle production truth",
            "critical": True,
            "repeat_sensitive": False,
            "subject_selectors": [],
            "settlement_policy": {
                "min_independent_reaches": 2,
                "min_independence_groups": 2,
                "require_prod": True,
                "min_prod_runs": 1,
            },
            "events": [
                {
                    "sequence": 1,
                    "action": "SURVIVED",
                    "reach": "SANDBOX",
                    "independence_group": "sandbox-group",
                    "evidence_ids": ["ev-sandbox"],
                    "note": "sandbox observation",
                },
                {
                    "sequence": 2,
                    "action": "SETTLED",
                    "reach": "PROD",
                    "independence_group": "prod-group",
                    "evidence_ids": ["ev-prod"],
                    "note": "synthetic production-shaped observation",
                    "affected_edge_selectors": [
                        {
                            "source": {"id": "payload:test"},
                            "target": {"id": "store:test"},
                            "kind": "WRITES_TO",
                        }
                    ],
                },
            ],
        }
    ]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ctg-domain-projection-") as raw_tmp:
        bundle = Path(raw_tmp)
        evidence_dir = bundle / "evidence"
        evidence_dir.mkdir()
        receipt_path = evidence_dir / "redacted.json"
        receipt_path.write_text(json.dumps(receipt()) + "\n", encoding="utf-8")
        graph = new_graph(title="projection", snapshot={}, scope={})
        ensure_node(graph, node_id="payload:test", kind="payload", label="payload")
        ensure_node(graph, node_id="store:test", kind="store", label="store")
        rows = definitions()
        ingest_redacted_availability(
            graph,
            bundle=bundle,
            evidence_records=[{"artifact_ref": "evidence/redacted.json"}],
            definitions=rows,
        )
        invariants, events = resolve_profile_invariants(graph, rows)
        add_invariants_and_events(graph, invariants=invariants, events=events)
        evaluate_all(graph)
        invariant = graph["invariants"][0]
        assert invariant["current_status"] == "DEMO_ONLY", invariant
        assert invariant["settlement"]["reach_classes"] == ["SANDBOX", "PROD"]
        assert invariant["settlement"]["production_run_ids"] == ["prod-1"]
        assert graph["edges"][0]["kind"] == "WRITES_TO", graph["edges"]
        assert graph["edges"][0]["evidence_ids"] == ["ev-prod"], graph["edges"]

        receipt_path.write_text(
            json.dumps(receipt(raw_content_embedded=True)) + "\n", encoding="utf-8"
        )
        try:
            ingest_redacted_availability(
                new_graph(title="hollow", snapshot={}, scope={}),
                bundle=bundle,
                evidence_records=[{"artifact_ref": "evidence/redacted.json"}],
                definitions=rows,
            )
        except ContractError as exc:
            assert "raw content" in str(exc), exc
        else:
            raise AssertionError("raw-content receipt was accepted")
    print("CTG DOMAIN PROJECTION TEST GREEN")


if __name__ == "__main__":
    main()
