#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "docs/traceability/issue-140-convergence.json"
QUEUE = ROOT / "docs/git/pdf-terminal-sequence.json"

EXPECTED_MERGES = {
    "BLIND-01": "0e27c9898925259b58c136e01fa4de175ad75231",
    "CONTEXT-FUNNEL": "9ec507f685c9f3d0fcf97238d036a22be92fddf5",
    "ADE-01": "d45c1bd8e9f1ba9c92c6926173efd59a4dfdcf33",
    "RETIRE-01": "ad0fdde3e46aa6ab6c59ced145bead7fa4fc72d3",
}

class ContractError(ValueError):
    pass


def require(value: bool, message: str) -> None:
    if not value:
        raise ContractError(message)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(receipt: dict, queue: dict, root: Path = ROOT) -> dict:
    require(receipt.get("schema_version") == "bettor-arena/issue-140-convergence/v1", "receipt schema drift")
    require(receipt.get("issue") == 140, "wrong convergence issue")
    current = queue.get("current", {})
    require(current.get("active_issue") == 140 and current.get("active_order") == 13, "machine queue is not #140/order13")
    item = next((x for x in queue.get("items", []) if x.get("order") == 13), None)
    require(isinstance(item, dict) and item.get("issues") == [140] and item.get("queue_state") == "ACTIVE", "stage 13 is not ACTIVE #140")
    q = receipt.get("queue", {})
    require(q.get("order") == 13 and q.get("state") == "ACTIVE", "receipt queue drift")
    require(q.get("advance_allowed") is False, "fixture/static convergence must not advance queue")

    predecessors = receipt.get("predecessors")
    require(isinstance(predecessors, list) and len(predecessors) == 4, "predecessor set drift")
    seen = {}
    for entry in predecessors:
        require(entry.get("state") == "PASS", f"{entry.get('id')}: predecessor not PASS")
        seen[entry.get("id")] = entry.get("merge_commit")
    require(seen == EXPECTED_MERGES, "predecessor merge subjects drift")

    architecture = receipt.get("architecture", {})
    require(architecture.get("code_graph_rag") == "RETIRED_FROM_CANONICAL_ROUTE", "retirement state drift")
    for key in ("blindspots_sqlite", "context_funnel", "parallel_agent_tech_lead"):
        require(architecture.get(key) == "IMPLEMENTED", f"{key}: convergence state drift")
    require(architecture.get("canonical_task_state_writer") == "LoopX reducer only", "task-state authority widened")
    require(architecture.get("skills_body_location") == "ed3c/skills-shared", "shared Skill ownership drift")
    require(architecture.get("consumer_repo_copies_skill_body") is False, "consumer copied Skill body")

    live = receipt.get("live_evidence", {})
    for key in (
        "grepai_canary",
        "serena_canary",
        "scip_lsp_live_execution",
        "tree_sitter_live_grammar_coverage",
        "git_town_executable_sync",
        "forgejo_exact_ancestry",
    ):
        require(live.get(key) == "NOT_EXERCISED", f"{key}: false live claim")

    admission = receipt.get("admission", {})
    require(admission.get("state") == "HUMAN_ADMIT_REQUIRED", "Human review boundary drift")
    require(admission.get("queue_advance") == "BLOCKED", "queue advance authority widened")
    require(admission.get("provider_activation") == "BLOCKED", "provider activation authority widened")
    require(admission.get("release_promotion") == "BLOCKED", "promotion authority widened")

    require(not (root / "docs/knowledge-providers/providers/code-graph-rag.json").exists(), "retired manifest resurrected")
    registry = load(root / "docs/knowledge-providers/registry.json")
    require(all(x.get("id") != "code-graph-rag" for x in registry.get("providers", [])), "retired registry route resurrected")
    require((root / "loop_wiki/code-truth-graph-v2/scripts/blindspots.py").is_file(), "Blindspots runtime missing")
    require((root / "loop_wiki/code-truth-graph-v2/scripts/context_funnel.py").is_file(), "context funnel missing")
    require((root / "loop_wiki/parallel-agent-tech-lead/scripts/plan.py").is_file(), "Tech Lead planner missing")
    require((root / ".arena/modules/parallel-agent-tech-lead/README.md").is_file(), "Tech Lead module route missing")
    return {"status": "PASS", "issue": 140, "queue": "ACTIVE/HUMAN_ADMIT_REQUIRED", "predecessors": sorted(seen)}


def selftest() -> dict:
    receipt = load(RECEIPT)
    queue = load(QUEUE)
    validate(receipt, queue)
    controls = []
    mutations = [
        ("premature-queue-advance", lambda r, q: r["queue"].__setitem__("advance_allowed", True)),
        ("false-live-provider", lambda r, q: r["live_evidence"].__setitem__("grepai_canary", "PASS")),
        ("retirement-state-laundered", lambda r, q: r["architecture"].__setitem__("code_graph_rag", "REJECTED")),
        ("human-admit-erased", lambda r, q: r["admission"].__setitem__("state", "PASS")),
        ("merge-subject-drift", lambda r, q: r["predecessors"][0].__setitem__("merge_commit", "0" * 40)),
        ("queue-subject-drift", lambda r, q: q["current"].__setitem__("active_issue", 70)),
    ]
    for name, mutate in mutations:
        r, q = copy.deepcopy(receipt), copy.deepcopy(queue)
        mutate(r, q)
        try:
            validate(r, q)
        except ContractError:
            controls.append(name)
        else:
            raise ContractError(f"planted control passed: {name}")
    return {"status": "PASS", "controls": controls}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    try:
        result = selftest() if args.selftest else validate(load(RECEIPT), load(QUEUE))
    except (ContractError, OSError, json.JSONDecodeError) as exc:
        print(f"issue-140-convergence FAIL: {exc}")
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
