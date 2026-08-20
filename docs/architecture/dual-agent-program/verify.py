#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
H40 = re.compile(r"^[0-9a-f]{40}$")


class ProgramStatusError(AssertionError):
    pass


def refuse(code: str, detail: str = "") -> None:
    raise ProgramStatusError(f"{code}: {detail}" if detail else code)


def verify(index: dict, readme: str, agents: str, review: str, queue: str) -> None:
    if index.get("schema") != "bettor.dual-agent-program-stack-index.v1":
        refuse("INDEX_SCHEMA_DRIFT")
    if index.get("owner_issue") != 230 or index.get("parent_issue") != 183:
        refuse("OWNER_ROUTE_DRIFT")
    authority = index.get("authority", {})
    if authority.get("this_index_canonical_write") != "NONE":
        refuse("STATUS_INDEX_WRITER_WIDENING")
    if authority.get("human_release_owner") != "external-trusted-authority":
        refuse("HUMAN_RELEASE_OWNER_DRIFT")

    problem = index.get("problem_denominator", {})
    if problem.get("physical_end_to_end_issue") != "ed3c/bettor-arena#186":
        refuse("PHYSICAL_OWNER_DRIFT")
    if problem.get("state") != "NOT_PHYSICALLY_CLOSED":
        refuse("FALSE_PHYSICAL_CLOSURE")

    repositories = index.get("repositories")
    if not isinstance(repositories, list):
        refuse("REPOSITORY_INDEX_MISSING")
    by_repo = {item.get("repository"): item for item in repositories if isinstance(item, dict)}
    required = {
        "ed3c/skills-shared",
        "ed3c/runtime-env",
        "ed3c/bettor-arena",
        "ed3c/agent-shield-monorepo",
        "ed3c/truth-verify-loop",
    }
    if set(by_repo) != required:
        refuse("REPOSITORY_INDEX_DRIFT")

    truth = by_repo["ed3c/truth-verify-loop"]
    if truth.get("state") != "MERGED_DETERMINISTIC_SUBTREE":
        refuse("MERGED_TRUTH_STATE_DRIFT")
    if truth.get("semantic_state") != "UNVERIFIABLE" or truth.get("live_state") != "NOT_EXERCISED":
        refuse("TECHNICAL_AS_SEMANTIC_OR_LIVE")
    if truth.get("parent_issue") != 22:
        refuse("TRUTH_PARENT_CLOSED_OR_LOST")

    for repo, payload in by_repo.items():
        for node in payload.get("nodes", []):
            state = str(node.get("state", ""))
            head = node.get("head") or node.get("commit")
            if state in {"DRAFT_CANDIDATE", "DRAFT_CONVERGENCE_CANDIDATE", "DRAFT_DOCS_CANDIDATE", "DETERMINISTIC_SUBJECT_BOUND"}:
                if not isinstance(head, str) or not H40.fullmatch(head):
                    refuse("EXACT_CANDIDATE_SUBJECT_MISSING", f"{repo}:{node}")
            if state.startswith("DRAFT") and state == "MERGED":
                refuse("DRAFT_AS_MERGED")

    live = set(index.get("global_live_frontier", []))
    expected_live = {
        "runtime-env#73",
        "runtime-env#83",
        "agent-shield-monorepo#95",
        "agent-shield-monorepo#161",
        "agent-shield-monorepo#173",
        "bettor-arena#223",
        "bettor-arena#186",
        "truth-verify-loop#22",
        "bettor-arena#68",
    }
    if live != expected_live:
        refuse("LIVE_FRONTIER_DRIFT")
    if index.get("program_state") != "DETERMINISTIC_IMPLEMENTATION_PARTIAL_MERGE_PHYSICAL_LOOP_OPEN":
        refuse("PROGRAM_STATE_PROMOTION")

    tokens = {
        "README": [
            "Technical matrix PASS       != SUPPORTED/REFUTED",
            "truth-verify-loop",
            "bettor-arena#186",
            "DRAFT_CANDIDATE",
            "NOT_EXERCISED",
            "Local Handoff",
        ],
        "AGENTS": [
            "canonical_write=NONE",
            "A true child consumes named unmerged parent bytes.",
            "Do not self-approve",
            "Shadow stop conditions",
            "Technical verifier PASS cannot emit SUPPORTED/REFUTED by itself.",
        ],
        "MERGE_REVIEW": [
            "Already admitted in this review stage",
            "Must remain open",
            "#176 and #188",
            "current-main restack",
        ],
        "QUEUE": [
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
        ],
    }
    documents = {"README": readme, "AGENTS": agents, "MERGE_REVIEW": review, "QUEUE": queue}
    for name, required_tokens in tokens.items():
        for token in required_tokens:
            if token not in documents[name]:
                refuse(f"{name}_INCOMPLETE", token)


class ProgramStatusTest(unittest.TestCase):
    def load(self) -> tuple[dict, str, str, str, str]:
        return (
            json.loads((ROOT / "stack-index.json").read_text()),
            (ROOT / "README.md").read_text(),
            (ROOT / "AGENTS.md").read_text(),
            (ROOT / "merge-review.md").read_text(),
            (ROOT / "local-handoff-queue.md").read_text(),
        )

    def assert_code(self, code: str, fn) -> None:
        with self.assertRaises(ProgramStatusError) as caught:
            fn()
        self.assertTrue(str(caught.exception).startswith(code))

    def test_current_status_is_exact_and_non_promoting(self) -> None:
        verify(*self.load())

    def test_index_cannot_write_program_state(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["authority"]["this_index_canonical_write"] = "TASK_EFFECT_RELEASE"
        self.assert_code("STATUS_INDEX_WRITER_WIDENING", lambda: verify(changed, *docs))

    def test_physical_canary_cannot_be_closed_by_docs(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["problem_denominator"]["state"] = "PHYSICALLY_CLOSED"
        self.assert_code("FALSE_PHYSICAL_CLOSURE", lambda: verify(changed, *docs))

    def test_technical_truth_cannot_become_semantic_truth(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        truth = next(item for item in changed["repositories"] if item["repository"] == "ed3c/truth-verify-loop")
        truth["semantic_state"] = "SUPPORTED"
        self.assert_code("TECHNICAL_AS_SEMANTIC_OR_LIVE", lambda: verify(changed, *docs))

    def test_live_frontier_cannot_be_dropped(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        changed["global_live_frontier"].remove("bettor-arena#186")
        self.assert_code("LIVE_FRONTIER_DRIFT", lambda: verify(changed, *docs))

    def test_exact_candidate_subject_is_required(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        runtime = next(item for item in changed["repositories"] if item["repository"] == "ed3c/runtime-env")
        runtime["nodes"][0]["head"] = "main"
        self.assert_code("EXACT_CANDIDATE_SUBJECT_MISSING", lambda: verify(changed, *docs))


if __name__ == "__main__":
    unittest.main()
