#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "loop_wiki/parallel-agent-tech-lead/scripts/plan.py"
spec = importlib.util.spec_from_file_location("bettor_tech_lead_plan", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

BASE_COMMIT = "1" * 40
BASE_TREE = "2" * 40
CONTEXT = "3" * 64
FUNNEL_DIGEST = "4" * 64


def worker(
    worker_id: str,
    role: str,
    path: str,
    *,
    deps: list[str] | None = None,
    focus: str | None = None,
) -> dict:
    item = {
        "id": worker_id,
        "branch": f"feat/fixture-{worker_id.lower()}",
        "role": role,
        "parent": "main",
        "depends_on": list(deps or []),
        "writable_paths": [path],
        "read_only_paths": ["contracts/immutable/**"],
        "context_digest": CONTEXT,
        "token_budget": 5000,
        "timeout_seconds": 300,
        "process_budget": 2,
        "output_byte_budget": 65536,
    }
    if focus:
        item["focus"] = focus
    if role == "child":
        item["consumes_contracts"] = ["fixture.contract/v1"]
    return item


def convergence(deps: list[str]) -> dict:
    return worker("CONV", "convergence", "generated/convergence/**", deps=deps)


def plan(mode: str) -> dict:
    if mode == "TOURNAMENT":
        leaves = [
            worker("A", "competitor", "src/feature/**", focus="minimal-diff"),
            worker("B", "competitor", "src/feature/**", focus="architecture-types"),
        ]
    elif mode == "COOPERATIVE":
        leaves = [
            worker("A", "sibling", "src/a/**"),
            worker("B", "sibling", "src/b/**"),
        ]
    elif mode == "SERIAL_STACK":
        leaves = [
            worker("A", "sibling", "src/a/**"),
            worker("B", "child", "src/a/**", deps=["A"]),
        ]
    elif mode == "HYBRID":
        leaves = [
            worker("A", "competitor", "src/feature/**", focus="minimal-diff"),
            worker("B", "competitor", "src/feature/**", focus="performance-security"),
            worker("C", "sibling", "src/docs/**"),
        ]
    else:
        raise AssertionError(mode)
    ids = [item["id"] for item in leaves]
    return {
        "schema": "bettor-arena/tech-lead-plan/v1",
        "upstream_contract": {
            "repository": "ed3c/skills-shared",
            "commit": "82a59bc9d253d9d77ea8bbdc493dd3689b423f52",
            "schema_path": "skills/git-town-stacked-pr-worker/references/FAN_OUT_CONTRACT.schema.json",
            "schema_blob": "e00bbb99fdb1a8888ff6fd03ce792254319e2697",
        },
        "repository": "ed3c/bettor-arena",
        "mode": mode,
        "base": {
            "branch": "main",
            "commit": BASE_COMMIT,
            "tree": BASE_TREE,
            "immutable": True,
        },
        "context": {
            "digest": CONTEXT,
            "providers": [
                {"name": "grepai", "required": False, "state": "NOT_EXERCISED"},
                {"name": "scip-lsp", "required": False, "state": "NOT_EXERCISED"},
                {"name": "tree-sitter", "required": False, "state": "NOT_EXERCISED"},
                {"name": "sqlite", "required": True, "state": "PASS"},
                {"name": "code-graph-rag", "required": False, "state": "REJECTED"},
            ],
            "compiler_truth_funnel": {
                "state": "PASS",
                "receipt": "loop_wiki/parallel-agent-tech-lead/tests/fixtures/context-funnel-pass.json",
                "digest": FUNNEL_DIGEST,
            },
        },
        "budgets": {
            "max_workers": 6,
            "max_tokens_per_worker": 8000,
            "max_wall_clock_seconds": 600,
            "max_retries_per_worker": 2,
            "max_processes_per_worker": 4,
            "max_output_bytes_per_worker": 131072,
            "circuit_breakers": [
                "same-failure-signature-three-times",
                "context-subject-drift",
                "lease-conflict",
            ],
        },
        "acceptance": {
            "immutable_paths": ["contracts/immutable/**", "tests/acceptance/**"],
            "oracles": ["repository-native-tests", "independent-blindspots-readback"],
        },
        "workers": [*leaves, convergence(ids)],
        "human_owned_operations": [
            "semantic_conflict_resolution",
            "winner_admission",
            "merge_or_ship",
            "release_promotion",
            "rollback",
        ],
        "automation": {
            "auto_publish": False,
            "auto_merge": False,
            "auto_resolve_semantic_conflicts": False,
            "auto_promote": False,
        },
    }


def expect_refusal(name: str, value: dict, marker: str, controls: list[str]) -> None:
    try:
        module.validate(value)
    except module.Refusal as exc:
        assert marker in str(exc), (name, exc)
        controls.append(name)
        return
    raise AssertionError(f"{name}: mutation passed")


def main() -> int:
    for mode in ("TOURNAMENT", "COOPERATIVE", "SERIAL_STACK", "HYBRID"):
        value = plan(mode)
        result = module.validate(copy.deepcopy(value))
        assert result["status"] == "PASS" and result["mode"] == mode
        receipt = module.compile_receipt(copy.deepcopy(value))
        assert receipt["status"] == "PASS"
        assert receipt["execution_state"] == "NOT_EXERCISED"
        assert receipt["git_town_state"] == "NOT_EXERCISED"
        assert receipt["forgejo_state"] == "NOT_EXERCISED"
        assert receipt["publication_state"] == "NOT_EXERCISED"
        assert len(receipt["worker_packets"]) == len(value["workers"])

    controls: list[str] = []

    value = plan("COOPERATIVE")
    value["base"]["immutable"] = False
    expect_refusal("mutable-base", value, "MUTABLE_BASE", controls)

    value = plan("COOPERATIVE")
    value["workers"][0]["context_digest"] = "9" * 64
    expect_refusal(
        "context-digest-mismatch", value, "CONTEXT_DIGEST_MISMATCH", controls
    )

    value = plan("COOPERATIVE")
    value["workers"][1]["writable_paths"] = ["src/a/sub/**"]
    expect_refusal("parallel-path-overlap", value, "PATH_OVERLAP", controls)

    value = plan("SERIAL_STACK")
    value["workers"][1].pop("consumes_contracts")
    expect_refusal("fake-linear-child", value, "FAKE_LINEAR_CHILD", controls)

    value = plan("COOPERATIVE")
    value["workers"][0]["writable_paths"] = ["tests/acceptance/**"]
    expect_refusal(
        "acceptance-test-mutation", value, "ACCEPTANCE_TEST_MUTATED", controls
    )

    value = plan("COOPERATIVE")
    value["workers"][0]["token_budget"] = 999999
    expect_refusal("worker-budget-overflow", value, "WORKER_BUDGET_OVERFLOW", controls)

    value = plan("COOPERATIVE")
    value["automation"]["auto_merge"] = True
    expect_refusal(
        "auto-merge-authority", value, "AUTOMATION_AUTHORITY_ESCALATION", controls
    )

    value = plan("COOPERATIVE")
    value["context"]["providers"][-1]["required"] = True
    expect_refusal(
        "retired-provider-required", value, "FORBIDDEN_CONTEXT_PROVIDER", controls
    )

    value = plan("TOURNAMENT")
    value["workers"][1]["focus"] = value["workers"][0]["focus"]
    expect_refusal(
        "duplicate-competitor-focus", value, "MISSING_BRANCH_FOCUS", controls
    )

    value = plan("COOPERATIVE")
    value["workers"][-1]["depends_on"] = ["A"]
    expect_refusal("premature-convergence", value, "PREMATURE_CONVERGENCE", controls)

    value = plan("COOPERATIVE")
    value["mode"] = "SERIAL_STACK"
    expect_refusal("mode-mismatch", value, "MODE_MISMATCH", controls)

    value = plan("SERIAL_STACK")
    value["workers"][0]["depends_on"] = ["B"]
    expect_refusal("dag-cycle", value, "DAG_CYCLE", controls)

    assert len(controls) == 12
    print(
        json.dumps({"status": "PASS", "modes": 4, "controls": controls}, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
