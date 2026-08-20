#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
H40 = re.compile(r"^[0-9a-f]{40}$")
H64 = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_REPOSITORIES = {
    "ed3c/skills-shared",
    "ed3c/runtime-env",
    "ed3c/bettor-arena",
    "ed3c/agent-shield-monorepo",
    "ed3c/truth-verify-loop",
}
EXPECTED_GLOBAL_LIVE = {
    "runtime-env#73",
    "runtime-env#83",
    "agent-shield-monorepo#95",
    "agent-shield-monorepo#161",
    "agent-shield-monorepo#173",
    "bettor-arena#184",
    "bettor-arena#185",
    "bettor-arena#223",
    "bettor-arena#186",
    "truth-verify-loop#22",
    "bettor-arena#68",
}


class StatusError(AssertionError):
    pass


def refuse(code: str, detail: str = "") -> None:
    raise StatusError(f"{code}: {detail}" if detail else code)


def require_h40(value: object, code: str, detail: str) -> str:
    if not isinstance(value, str) or H40.fullmatch(value) is None:
        refuse(code, detail)
    return value


def require_h64(value: object, code: str, detail: str) -> str:
    if not isinstance(value, str) or H64.fullmatch(value) is None:
        refuse(code, detail)
    return value


def check(index: dict, readme: str, agents: str, review: str, queue: str) -> None:
    if index.get("schema") != "bettor.dual-agent-program-stack-index.v2":
        refuse("INDEX_SCHEMA_DRIFT")
    if index.get("owner_issue") != 234 or index.get("parent_issue") != 183:
        refuse("OWNER_ROUTE_DRIFT")

    previous = index.get("previous_trace")
    if previous != {
        "issue": 230,
        "pr": 231,
        "merge": "505176455d9fad6cbb262515af4a668170d732eb",
    }:
        refuse("PREVIOUS_TRACE_DRIFT")

    authority = index.get("authority", {})
    if authority.get("this_index_canonical_write") != "NONE":
        refuse("INDEX_AUTHORITY_WIDENING")
    if authority.get("task_writer") != "bettor-arena/loopx-ledger":
        refuse("TASK_WRITER_DRIFT")
    if authority.get("effect_writer") != "bettor-arena/dual-agent-effect-ledger":
        refuse("EFFECT_WRITER_DRIFT")
    if authority.get("provider_owner") != "agent-shield-monorepo":
        refuse("PROVIDER_OWNER_DRIFT")
    if authority.get("runtime_contract_owner") != "runtime-env":
        refuse("RUNTIME_OWNER_DRIFT")
    if authority.get("independent_verification_owner") != "truth-verify-loop":
        refuse("VERIFICATION_OWNER_DRIFT")
    if authority.get("human_release_owner") != "external-trusted-authority":
        refuse("HUMAN_RELEASE_OWNER_DRIFT")

    denominator = index.get("problem_denominator", {})
    if denominator.get("physical_end_to_end_issue") != "ed3c/bettor-arena#186":
        refuse("PHYSICAL_OWNER_DRIFT")
    if denominator.get("state") != "NOT_PHYSICALLY_CLOSED":
        refuse("FALSE_PHYSICAL_CLOSURE")

    repositories = index.get("repositories")
    if not isinstance(repositories, list):
        refuse("REPOSITORY_INDEX_MISSING")
    by_repo = {item.get("repository"): item for item in repositories if isinstance(item, dict)}
    if set(by_repo) != EXPECTED_REPOSITORIES:
        refuse("REPOSITORY_INDEX_DRIFT")

    skills = by_repo["ed3c/skills-shared"]
    if skills.get("state") != "DETERMINISTIC_METHOD_SUBJECT_BOUND":
        refuse("METHOD_STATE_DRIFT")
    skills_nodes = skills.get("nodes")
    if not isinstance(skills_nodes, list) or len(skills_nodes) != 1:
        refuse("METHOD_NODE_DRIFT")
    require_h40(skills_nodes[0].get("commit"), "METHOD_SUBJECT_MISSING", "commit")
    require_h40(skills_nodes[0].get("tree"), "METHOD_SUBJECT_MISSING", "tree")

    runtime = by_repo["ed3c/runtime-env"]
    if runtime.get("state") != "MERGED_DETERMINISTIC_RUNTIME_SUBTREE":
        refuse("RUNTIME_MERGE_STATE_DRIFT")
    if runtime.get("implementation_merge") != "92feed7c4e671dc63238155da9d4f394aac80d90":
        refuse("RUNTIME_MERGE_SUBJECT_DRIFT", "implementation")
    if runtime.get("trace_merge") != "baa4ce25d32a9fb4383ea8bc3530f9fd80be9ae7":
        refuse("RUNTIME_MERGE_SUBJECT_DRIFT", "trace")
    require_h64(runtime.get("contract_set"), "RUNTIME_CONTRACT_SET_DRIFT", "contract_set")
    if set(runtime.get("merged_prs", [])) != {69, 76, 77, 78, 79, 85, 86, 87, 104}:
        refuse("RUNTIME_MERGE_PATH_DRIFT")
    if set(runtime.get("closed_completed_issues", [])) != {57, 61, 70, 71, 72, 74, 75, 80, 81, 82, 84}:
        refuse("RUNTIME_CLOSURE_DRIFT")
    if set(runtime.get("parent_issues_keep_open", [])) != {58, 59}:
        refuse("RUNTIME_PARENT_CLOSURE_LAUNDERING")
    runtime_live = {item.get("issue"): item.get("state") for item in runtime.get("live_frontier", []) if isinstance(item, dict)}
    if runtime_live != {73: "NOT_EXERCISED", 83: "NOT_EXERCISED"}:
        refuse("RUNTIME_LIVE_STATE_DRIFT")

    bettor = by_repo["ed3c/bettor-arena"]
    if bettor.get("state") != "MERGED_DETERMINISTIC_WORKFLOW_EFFECT_SUBTREE":
        refuse("BETTOR_MERGE_STATE_DRIFT")
    if bettor.get("main_merge") != "74d1e75c61589dcd163c7412e1345f726781ffb4":
        refuse("BETTOR_MERGE_SUBJECT_DRIFT", "commit")
    if bettor.get("main_tree") != "0de94032a3227ad04dde52f138041294ef9cb810":
        refuse("BETTOR_MERGE_SUBJECT_DRIFT", "tree")
    if bettor.get("workflow_merge_path") != [232, 233, 202, 201]:
        refuse("WORKFLOW_MERGE_PATH_DRIFT")
    if bettor.get("effect_merge_path") != [229, 228, 225, 224, 216, 202, 201]:
        refuse("EFFECT_MERGE_PATH_DRIFT")
    if set(bettor.get("absorbed_leaf_prs", [])) != {209, 210, 211, 215, 226, 227}:
        refuse("ABSORBED_LEAF_DRIFT")
    if set(bettor.get("closed_workflow_issues", [])) != {199, 200, 203, 204, 205, 206, 207}:
        refuse("WORKFLOW_CLOSURE_DRIFT")
    if set(bettor.get("closed_effect_issues", [])) != {208, 217, 218, 219, 220, 221, 222}:
        refuse("EFFECT_CLOSURE_DRIFT")
    if set(bettor.get("parent_issues_keep_open", [])) != {184, 185}:
        refuse("BETTOR_PARENT_CLOSURE_LAUNDERING")
    if bettor.get("evidence_ceiling") != "COMPLETE_DETERMINISTIC_WORKFLOW_AND_EFFECT_SUBTREE_ONLY":
        refuse("BETTOR_EVIDENCE_CEILING_DRIFT")
    bettor_live = {item.get("issue"): item.get("state") for item in bettor.get("live_frontier", []) if isinstance(item, dict)}
    if bettor_live != {223: "HUMAN_REQUIRED", 186: "NOT_EXERCISED", 68: "NOT_PERFORMED"}:
        refuse("BETTOR_LIVE_STATE_DRIFT")

    shield = by_repo["ed3c/agent-shield-monorepo"]
    if shield.get("state") != "DETERMINISTIC_CANDIDATES_CURRENT_MAIN_RESTACK_REQUIRED":
        refuse("SHIELD_STATE_DRIFT")
    if shield.get("route_merge_plan") != [162, 166, 167] or shield.get("gvisor_merge_plan") != [174, 177, 178]:
        refuse("SHIELD_MERGE_PLAN_DRIFT")
    if set(shield.get("route_absorbed_leaf_prs", [])) != {163, 164, 165}:
        refuse("SHIELD_ROUTE_ABSORBED_DRIFT")
    if set(shield.get("gvisor_absorbed_leaf_prs", [])) != {175, 176}:
        refuse("SHIELD_GVISOR_ABSORBED_DRIFT")
    if shield.get("shared_candidate_pr") != 180:
        refuse("SHIELD_SHARED_CANDIDATE_DRIFT")
    shield_nodes = shield.get("nodes")
    if not isinstance(shield_nodes, list):
        refuse("SHIELD_NODE_SET_MISSING")
    by_pr = {item.get("pr"): item for item in shield_nodes if isinstance(item, dict)}
    if set(by_pr) != {162, 166, 167, 174, 177, 178, 180}:
        refuse("SHIELD_NODE_SET_DRIFT")
    for pr in (162, 166, 167, 180):
        require_h40(by_pr[pr].get("head"), "SHIELD_EXACT_CANDIDATE_MISSING", str(pr))
    if by_pr[180].get("state") != "HUMAN_REVIEW_PENDING_NON_PROMOTING":
        refuse("SHIELD_SHARED_CANDIDATE_PROMOTION")
    shield_live = {item.get("issue"): item.get("state") for item in shield.get("live_frontier", []) if isinstance(item, dict)}
    if shield_live != {95: "NOT_EXERCISED", 161: "HUMAN_REQUIRED", 173: "HUMAN_REQUIRED"}:
        refuse("SHIELD_LIVE_STATE_DRIFT")

    truth = by_repo["ed3c/truth-verify-loop"]
    if truth.get("state") != "MERGED_DETERMINISTIC_SUBTREE":
        refuse("TRUTH_MERGE_STATE_DRIFT")
    if truth.get("merge_path") != [29, 39, 44, 45]:
        refuse("TRUTH_MERGE_PATH_DRIFT")
    if truth.get("semantic_state") != "UNVERIFIABLE" or truth.get("live_state") != "NOT_EXERCISED":
        refuse("TECHNICAL_AS_SEMANTIC_OR_LIVE")
    if truth.get("parent_issue") != 22:
        refuse("TRUTH_PARENT_LOST")

    merge_frontier = index.get("global_merge_frontier")
    if not isinstance(merge_frontier, list) or len(merge_frontier) != 3:
        refuse("GLOBAL_MERGE_FRONTIER_DRIFT")
    if not all("agent-shield-monorepo" in item for item in merge_frontier):
        refuse("GLOBAL_MERGE_FRONTIER_DRIFT")

    if set(index.get("global_live_frontier", [])) != EXPECTED_GLOBAL_LIVE:
        refuse("LIVE_FRONTIER_DRIFT")
    if index.get("program_state") != "DETERMINISTIC_RUNTIME_WORKFLOW_EFFECT_TRUTH_MERGED_PROVIDER_AND_PHYSICAL_LOOP_OPEN":
        refuse("PROGRAM_STATE_PROMOTION")

    documents = {
        "README": (
            readme,
            [
                "MERGED_DETERMINISTIC_RUNTIME_SUBTREE",
                "MERGED_DETERMINISTIC_WORKFLOW_EFFECT_SUBTREE",
                "technical matrix PASS",
                "semantic closure UNVERIFIABLE",
                "Agent Shield current-main admission",
                "Local Handoff",
            ],
        ),
        "AGENTS": (
            agents,
            [
                "canonical_write=NONE",
                "A true child consumes named unmerged parent bytes.",
                "Do not self-approve",
                "Shadow stop conditions",
                "MERGED_DETERMINISTIC_SUBTREE",
                "Agent Shield deterministic families remain in current-main merge review",
            ],
        ),
        "MERGE_REVIEW": (
            review,
            [
                "Already admitted in this review stage",
                "ed3c/runtime-env",
                "ed3c/bettor-arena` Workflow + Effect",
                "Current candidate stacks requiring current-main restack and CI",
                "Must remain open",
            ],
        ),
        "QUEUE": (
            queue,
            [
                "LH-01",
                "LH-02",
                "LH-03",
                "LH-04",
                "LH-05",
                "LH-06",
                "LH-07",
                "LH-08",
                "LH-09",
                "Completion packet",
                "74d1e75c61589dcd163c7412e1345f726781ffb4",
                "baa4ce25d32a9fb4383ea8bc3530f9fd80be9ae7",
            ],
        ),
    }
    for name, (document, tokens) in documents.items():
        for token in tokens:
            if token not in document:
                refuse(f"{name}_INCOMPLETE", token)


class StatusTest(unittest.TestCase):
    def load(self) -> tuple[dict, str, str, str, str]:
        return (
            json.loads((ROOT / "stack-index.json").read_text()),
            (ROOT / "README.md").read_text(),
            (ROOT / "AGENTS.md").read_text(),
            (ROOT / "merge-review.md").read_text(),
            (ROOT / "local-handoff-queue.md").read_text(),
        )

    def assert_code(self, code: str, fn) -> None:
        with self.assertRaises(StatusError) as caught:
            fn()
        self.assertTrue(str(caught.exception).startswith(code))

    def test_current_snapshot_is_non_promoting(self) -> None:
        check(*self.load())

    def test_docs_cannot_close_physical_canary(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["problem_denominator"]["state"] = "PHYSICALLY_CLOSED"
        self.assert_code("FALSE_PHYSICAL_CLOSURE", lambda: check(changed, *docs))

    def test_index_cannot_become_writer(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["authority"]["this_index_canonical_write"] = "TASK_EFFECT_RELEASE"
        self.assert_code("INDEX_AUTHORITY_WIDENING", lambda: check(changed, *docs))

    def test_truth_matrix_cannot_self_promote_semantics(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        truth = next(item for item in changed["repositories"] if item["repository"] == "ed3c/truth-verify-loop")
        truth["semantic_state"] = "SUPPORTED"
        self.assert_code("TECHNICAL_AS_SEMANTIC_OR_LIVE", lambda: check(changed, *docs))

    def test_live_frontier_cannot_be_erased(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["global_live_frontier"].remove("bettor-arena#186")
        self.assert_code("LIVE_FRONTIER_DRIFT", lambda: check(changed, *docs))

    def test_agent_shield_candidate_needs_exact_head(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        shield = next(item for item in changed["repositories"] if item["repository"] == "ed3c/agent-shield-monorepo")
        next(item for item in shield["nodes"] if item["pr"] == 162)["head"] = "main"
        self.assert_code("SHIELD_EXACT_CANDIDATE_MISSING", lambda: check(changed, *docs))

    def test_runtime_parent_cannot_close_from_deterministic_merge(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        runtime = next(item for item in changed["repositories"] if item["repository"] == "ed3c/runtime-env")
        runtime["parent_issues_keep_open"] = []
        self.assert_code("RUNTIME_PARENT_CLOSURE_LAUNDERING", lambda: check(changed, *docs))

    def test_bettor_parent_cannot_close_from_deterministic_merge(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        bettor = next(item for item in changed["repositories"] if item["repository"] == "ed3c/bettor-arena")
        bettor["parent_issues_keep_open"] = []
        self.assert_code("BETTOR_PARENT_CLOSURE_LAUNDERING", lambda: check(changed, *docs))


if __name__ == "__main__":
    unittest.main()
