#!/usr/bin/env python3
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent
H40 = re.compile(r"^[0-9a-f]{40}$")


class StatusError(AssertionError):
    pass


def refuse(code: str, detail: str = "") -> None:
    raise StatusError(f"{code}: {detail}" if detail else code)


def check(index: dict, readme: str, agents: str, review: str, queue: str) -> None:
    if index.get("schema") != "bettor.dual-agent-program-stack-index.v1":
        refuse("INDEX_SCHEMA_DRIFT")
    if index.get("owner_issue") != 230 or index.get("parent_issue") != 183:
        refuse("OWNER_ROUTE_DRIFT")

    authority = index.get("authority", {})
    if authority.get("this_index_canonical_write") != "NONE":
        refuse("INDEX_AUTHORITY_WIDENING")
    if authority.get("human_release_owner") != "external-trusted-authority":
        refuse("HUMAN_RELEASE_OWNER_DRIFT")

    denominator = index.get("problem_denominator", {})
    if denominator.get("physical_end_to_end_issue") != "ed3c/bettor-arena#186":
        refuse("PHYSICAL_OWNER_DRIFT")
    if denominator.get("state") != "NOT_PHYSICALLY_CLOSED":
        refuse("FALSE_PHYSICAL_CLOSURE")

    repos = index.get("repositories")
    if not isinstance(repos, list):
        refuse("REPOSITORY_INDEX_MISSING")
    by_repo = {item.get("repository"): item for item in repos if isinstance(item, dict)}
    expected_repos = {
        "ed3c/skills-shared",
        "ed3c/runtime-env",
        "ed3c/bettor-arena",
        "ed3c/agent-shield-monorepo",
        "ed3c/truth-verify-loop",
    }
    if set(by_repo) != expected_repos:
        refuse("REPOSITORY_INDEX_DRIFT")

    truth = by_repo["ed3c/truth-verify-loop"]
    if truth.get("state") != "MERGED_DETERMINISTIC_SUBTREE":
        refuse("TRUTH_MERGE_STATE_DRIFT")
    if truth.get("semantic_state") != "UNVERIFIABLE" or truth.get("live_state") != "NOT_EXERCISED":
        refuse("TECHNICAL_AS_SEMANTIC_OR_LIVE")
    if truth.get("parent_issue") != 22:
        refuse("TRUTH_PARENT_LOST")

    exact_states = {
        "DRAFT_CANDIDATE",
        "DRAFT_CONVERGENCE_CANDIDATE",
        "DRAFT_DOCS_CANDIDATE",
        "DETERMINISTIC_SUBJECT_BOUND",
    }
    for repo, payload in by_repo.items():
        for node in payload.get("nodes", []):
            state = str(node.get("state", ""))
            head = node.get("head") or node.get("commit")
            if state in exact_states and (not isinstance(head, str) or not H40.fullmatch(head)):
                refuse("EXACT_CANDIDATE_SUBJECT_MISSING", f"{repo}:{node.get('pr') or node.get('issue')}")
            if state == "MERGED" and payload.get("state") != "MERGED_DETERMINISTIC_SUBTREE":
                refuse("DRAFT_AS_MERGED")

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
    if set(index.get("global_live_frontier", [])) != expected_live:
        refuse("LIVE_FRONTIER_DRIFT")
    if index.get("program_state") != "DETERMINISTIC_IMPLEMENTATION_PARTIAL_MERGE_PHYSICAL_LOOP_OPEN":
        refuse("PROGRAM_STATE_PROMOTION")

    documents = {
        "README": (
            readme,
            [
                "technical matrix PASS",
                "SUPPORTED/REFUTED",
                "bettor-arena#186",
                "DRAFT_CANDIDATE",
                "NOT_EXERCISED",
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
                "technical verifier agreement",
                "semantic support/refutation",
            ],
        ),
        "MERGE_REVIEW": (
            review,
            [
                "Already admitted in this review stage",
                "Must remain open",
                "#176 and #188",
                "current-main restack",
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

    def test_exact_candidate_subject_is_required(self) -> None:
        index, *docs = self.load()
        changed = deepcopy(index)
        runtime = next(item for item in changed["repositories"] if item["repository"] == "ed3c/runtime-env")
        runtime["nodes"][0]["head"] = "main"
        self.assert_code("EXACT_CANDIDATE_SUBJECT_MISSING", lambda: check(changed, *docs))


if __name__ == "__main__":
    unittest.main()
