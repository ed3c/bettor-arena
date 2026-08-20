#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
H40 = re.compile(r"^[0-9a-f]{40}$")


class WorkflowDocsError(AssertionError):
    pass


def refuse(code: str, detail: str = "") -> None:
    raise WorkflowDocsError(f"{code}: {detail}" if detail else code)


def verify(index: dict, agents: str, status: str, review: str, queue: str) -> None:
    if index.get("schema") != "bettor.dual-agent-workflow-stack-index.v1":
        refuse("INDEX_SCHEMA_DRIFT")
    if index.get("parent_issue") != 184 or index.get("docs_issue") != 207:
        refuse("OWNER_ROUTE_DRIFT")
    authority = index.get("authority", {})
    if authority.get("this_index_canonical_write") != "NONE":
        refuse("DOCS_AUTHORITY_WIDENING")
    if authority.get("task_writer") != "loop_wiki/loopx-ledger":
        refuse("TASK_WRITER_DRIFT")
    if authority.get("effect_owner") != "loop_wiki/dual-agent-effect-ledger":
        refuse("EFFECT_OWNER_DRIFT")
    for key in ("provider_owner", "runtime_owner", "truth_owner"):
        if not str(authority.get(key, "")).startswith("external:"):
            refuse("EXTERNAL_OWNER_DRIFT", key)

    expected = {
        ("DA-WF-C", 199, 201, "MERGED_DETERMINISTIC"),
        ("DA-WF-K", 200, 202, "MERGED_DETERMINISTIC"),
        ("DA-WF-R", 203, 209, "ABSORBED_BY_215"),
        ("DA-WF-H", 204, 210, "ABSORBED_BY_215"),
        ("DA-WF-COMP", 205, 211, "ABSORBED_BY_215"),
        ("DA-WF-E", 206, 215, "MERGED_DETERMINISTIC_CONVERGENCE"),
    }
    nodes = index.get("merged_nodes")
    observed = {
        (item.get("atom"), item.get("issue"), item.get("pr"), item.get("state"))
        for item in nodes
        if isinstance(item, dict)
    } if isinstance(nodes, list) else set()
    if observed != expected:
        refuse("NODE_SET_DRIFT")
    for node in nodes:
        if not H40.fullmatch(str(node.get("candidate_head", ""))):
            refuse("EXACT_HEAD_MISSING", str(node.get("atom")))
        if not H40.fullmatch(str(node.get("candidate_tree", ""))):
            refuse("EXACT_TREE_MISSING", str(node.get("atom")))
        if not isinstance(node.get("prior_exact_head_ci"), int):
            refuse("CI_RECEIPT_MISSING", str(node.get("atom")))

    if index.get("closed_completed_issues") != [199, 200, 203, 204, 205, 206]:
        refuse("ISSUE_CLOSURE_DRIFT")
    if index.get("closed_absorbed_prs") != [209, 210, 211]:
        refuse("ABSORBED_PR_DRIFT")
    if index.get("documentation_convergence", {}).get("state") != "CURRENT_MAIN_DOCS_CANDIDATE":
        refuse("DOCS_SELF_PROMOTION")
    parent = index.get("parent_state", {})
    if parent.get("issue") != 184 or parent.get("state") != "OPEN":
        refuse("PARENT_CLOSURE_LAUNDERING")

    live = index.get("live_frontier", {})
    expected_live = {
        "durable_engine": "NOT_EXERCISED",
        "physical_transport": "NOT_EXERCISED",
        "live_identity": "NOT_EXERCISED",
        "live_human": "NOT_EXERCISED",
        "provider_execution": "NOT_EXERCISED",
        "external_effect": "NOT_EXERCISED",
        "user_result": "NOT_EXERCISED",
        "physical_canary_issue": 186,
        "human": "NOT_PERFORMED",
        "release": "NOT_PERFORMED",
    }
    if live != expected_live:
        refuse("LIVE_FRONTIER_DRIFT")
    if index.get("evidence_ceiling") != "COMPLETE_DETERMINISTIC_WORKFLOW_REPLAY_MATRIX_ONLY":
        refuse("EVIDENCE_CEILING_DRIFT")

    required = {
        "AGENTS": (agents, [
            "canonical_write=NONE",
            "A true child consumes named unmerged parent bytes.",
            "Do not self-approve.",
            "Shadow stop conditions",
            "workflow COMPLETED            != effect commit",
        ]),
        "STATUS": (status, [
            "MERGED_DETERMINISTIC",
            "NOT_EXERCISED",
            "PR #215",
            "COMPLETE_DETERMINISTIC_WORKFLOW_REPLAY_MATRIX_ONLY",
        ]),
        "REVIEW": (review, [
            "Issues closed as completed",
            "Must remain open",
            "#184",
            "#209/#210/#211",
        ]),
        "QUEUE": (queue, [
            "LH-W01", "LH-W02", "LH-W03", "LH-W04",
            "LH-W05", "LH-W06", "LH-W07", "LH-W08",
            "Completion packet",
        ]),
    }
    for name, (document, tokens) in required.items():
        for token in tokens:
            if token not in document:
                refuse(f"{name}_INCOMPLETE", token)


class WorkflowDocsTest(unittest.TestCase):
    def load(self) -> tuple[dict, str, str, str, str]:
        return (
            json.loads((ROOT / "stack-index.json").read_text()),
            (ROOT / "AGENTS.md").read_text(),
            (ROOT / "current-main-status.md").read_text(),
            (ROOT / "merge-review.md").read_text(),
            (ROOT / "local-handoff-queue.md").read_text(),
        )

    def assert_code(self, code: str, fn) -> None:
        with self.assertRaises(WorkflowDocsError) as caught:
            fn()
        self.assertTrue(str(caught.exception).startswith(code))

    def test_current_snapshot(self) -> None:
        verify(*self.load())

    def test_docs_cannot_become_writer(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["authority"]["this_index_canonical_write"] = "TASK_EFFECT"
        self.assert_code("DOCS_AUTHORITY_WIDENING", lambda: verify(changed, *docs))

    def test_parent_cannot_be_laundered_closed(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["parent_state"]["state"] = "CLOSED"
        self.assert_code("PARENT_CLOSURE_LAUNDERING", lambda: verify(changed, *docs))

    def test_live_frontier_cannot_be_promoted(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["live_frontier"]["durable_engine"] = "PASS"
        self.assert_code("LIVE_FRONTIER_DRIFT", lambda: verify(changed, *docs))

    def test_exact_subject_cannot_be_mutable(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["merged_nodes"][0]["candidate_head"] = "main"
        self.assert_code("EXACT_HEAD_MISSING", lambda: verify(changed, *docs))


if __name__ == "__main__":
    unittest.main()
