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

EXPECTED_NODES = {
    "DA-WF-C": (199, 201, "56cb74650bda20adfe84cc522977419158437f53", "3b2f1a351296f87f6570a182b2d72b46be181bac", 32263925774),
    "DA-WF-K": (200, 202, "7821e81f15d64ff3119d9bdb9278fc725e5aa398", "60d486041b36608d5d03e33b2eb8944c9899b50b", 32264598907),
    "DA-WF-R": (203, 209, "37376884bebc7403fab52dc0b2bff8ab5bb61060", "19b0008b218c10385fc4e5d9a6556464b55f526c", 32265868475),
    "DA-WF-H": (204, 210, "460d8419d579c7dba50800c790af2dce053fbb23", "5ec3a7bda1c2bbd294943324ce01c55557b9fdba", 32266054386),
    "DA-WF-COMP": (205, 211, "e425ec026c4792b94cf8b2214b4179260e2f1834", "4a50ff3a58785eb50363304725641e8b3a0e003e", 32266218555),
    "DA-WF-E": (206, 232, "bf99eacaa848683a89d327e4c7899a452f2bbd99", "bdfd5080e8c4b2b0a3e84e4fc2d59d4bfc73c8b3", 32343897103),
}


class DocsError(ValueError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def refuse(code: str, detail: str = "") -> None:
    raise DocsError(code, detail)


def h40(value: object, code: str, detail: str) -> str:
    if not isinstance(value, str) or H40.fullmatch(value) is None:
        refuse(code, detail)
    return value


def verify(index: dict, readme: str, agents: str) -> None:
    if index.get("schema") != "bettor.dual-agent-workflow-stack-index.v1":
        refuse("STACK_SCHEMA_DRIFT")
    if index.get("parent_issue") != 184 or index.get("docs_issue") != 207 or index.get("docs_pr") != 233:
        refuse("DOCS_ROUTE_DRIFT")
    if index.get("docs_subject_state") != "CANDIDATE_SUBJECT_PENDING":
        refuse("DOCS_SELF_PROMOTION")

    runtime = index.get("runtime_contract")
    if not isinstance(runtime, dict) or runtime.get("repository") != "ed3c/runtime-env":
        refuse("RUNTIME_BINDING_DRIFT")
    h40(runtime.get("source_head"), "RUNTIME_BINDING_DRIFT", "head")
    h40(runtime.get("source_tree"), "RUNTIME_BINDING_DRIFT", "tree")
    contract_set = runtime.get("contract_set")
    if not isinstance(contract_set, str) or H64.fullmatch(contract_set) is None:
        refuse("RUNTIME_BINDING_DRIFT", "contract_set")

    candidate = index.get("current_candidate")
    if not isinstance(candidate, dict):
        refuse("CURRENT_CANDIDATE_MISSING")
    if candidate.get("repository") != "ed3c/bettor-arena" or candidate.get("branch") != "feat/200-dual-agent-workflow-replay":
        refuse("CURRENT_CANDIDATE_DRIFT")
    if candidate.get("commit") != "602134eb5f04b62776b7c1a787d6d8366e9f31af" or candidate.get("tree") != "bdfd5080e8c4b2b0a3e84e4fc2d59d4bfc73c8b3":
        refuse("CURRENT_CANDIDATE_DRIFT")
    if candidate.get("state") != "DETERMINISTIC_WORKFLOW_EFFECT_SUBTREE_CANDIDATE":
        refuse("CURRENT_CANDIDATE_PROMOTION")
    runs = candidate.get("runs")
    if not isinstance(runs, dict) or any(not isinstance(value, int) for value in runs.values()):
        refuse("CURRENT_RUN_RECEIPTS_MISSING")

    nodes = index.get("nodes")
    if not isinstance(nodes, list) or len(nodes) != len(EXPECTED_NODES):
        refuse("NODE_SET_DRIFT")
    by_atom = {item.get("atom"): item for item in nodes if isinstance(item, dict)}
    if set(by_atom) != set(EXPECTED_NODES):
        refuse("NODE_SET_DRIFT")
    for atom, expected in EXPECTED_NODES.items():
        issue, pr, head, tree, run = expected
        node = by_atom[atom]
        if (node.get("issue"), node.get("pr"), node.get("head"), node.get("tree"), node.get("targeted_run")) != expected:
            refuse("EXACT_NODE_DRIFT", atom)
        h40(head, "EXACT_NODE_DRIFT", f"{atom}.head")
        h40(tree, "EXACT_NODE_DRIFT", f"{atom}.tree")

    effect = index.get("effect_integration")
    if not isinstance(effect, dict):
        refuse("EFFECT_BOUNDARY_MISSING")
    if effect.get("canonical_writer") != "dual-agent-effect-ledger" or effect.get("workflow_interface") != "EFFECT_ADMISSION_REQUEST":
        refuse("EFFECT_AUTHORITY_DRIFT")
    if effect.get("state") != "COMPLETE_DETERMINISTIC_EFFECT_PLANE_INTEGRATED" or effect.get("live_state") != "NOT_EXERCISED":
        refuse("EFFECT_LIVE_PROMOTION")

    authority = index.get("authority", {})
    if authority.get("workflow_canonical_write") != "NONE":
        refuse("WORKFLOW_WRITER_WIDENING")
    if authority.get("task_writer") != "loop_wiki/loopx-ledger":
        refuse("TASK_WRITER_DRIFT")
    if authority.get("effect_writer") != "loop_wiki/dual-agent-effect-ledger":
        refuse("EFFECT_WRITER_DRIFT")
    if authority.get("provider_owner") != "ed3c/agent-shield-monorepo" or authority.get("verification_owner") != "ed3c/truth-verify-loop":
        refuse("CROSS_PLANE_AUTHORITY_DRIFT")
    if authority.get("human_admission") != "EXTERNAL" or authority.get("release") != "EXTERNAL":
        refuse("HUMAN_RELEASE_AUTHORITY_DRIFT")

    merge = index.get("merge_plan")
    if not isinstance(merge, dict):
        refuse("MERGE_PLAN_MISSING")
    if merge.get("minimal_path") != [233, 202, 201]:
        refuse("MERGE_PLAN_DRIFT")
    if set(merge.get("absorbed_leaf_prs", [])) != {209, 210, 211, 215, 232}:
        refuse("ABSORBED_LEAF_DRIFT")
    if set(merge.get("issues_ready_to_close_after_main", [])) != {199, 200, 203, 204, 205, 206, 207}:
        refuse("ISSUE_CLOSURE_DRIFT")
    if set(merge.get("parent_keep_open", [])) != {184, 185} or set(merge.get("live_keep_open", [])) != {223, 186, 68}:
        refuse("PARENT_OR_LIVE_CLOSURE_LAUNDERING")

    failures = index.get("retained_failures")
    if not isinstance(failures, list) or not any(item.get("pr") == 215 and item.get("successor_pr") == 232 for item in failures if isinstance(item, dict)):
        refuse("FAILURE_HISTORY_ERASED")

    live = index.get("live_frontier")
    if not isinstance(live, dict):
        refuse("LIVE_FRONTIER_MISSING")
    allowed = {"NOT_EXERCISED", "NOT_PERFORMED"}
    if any(value not in allowed for value in live.values()):
        refuse("LIVE_STATE_PROMOTION")
    if live.get("release") != "NOT_PERFORMED":
        refuse("RELEASE_PROMOTION")

    handoff = index.get("local_handoff")
    if not isinstance(handoff, dict) or handoff.get("id") != "LH-WF-001" or handoff.get("owner") != "ed3c/bettor-arena#184":
        refuse("HANDOFF_ROUTE_DRIFT")
    if handoff.get("state") != "HANDOFF_READY_NOT_EXERCISED":
        refuse("HANDOFF_SELF_PROMOTION")
    exact_base = handoff.get("exact_base")
    if not isinstance(exact_base, dict) or exact_base.get("commit") != candidate.get("commit") or exact_base.get("tree") != candidate.get("tree"):
        refuse("HANDOFF_BASE_DRIFT")
    for field in ("idempotency", "timeout", "receipt", "rollback", "verifier"):
        if not isinstance(handoff.get(field), str) or not handoff[field].strip():
            refuse("HANDOFF_PACKET_INCOMPLETE", field)

    if index.get("evidence_ceiling") != "COMPLETE_DETERMINISTIC_WORKFLOW_AND_EFFECT_SUBTREE_ONLY":
        refuse("EVIDENCE_CEILING_DRIFT")

    readme_tokens = (
        "## Directory → State Machine → DAG owner",
        "## Workflow State Machine",
        "## Process DAG",
        "## Git Stack and merge chain",
        "## Deterministic data flow",
        "## Local Handoff Execution Queue",
        "technical matrix PASS      != physical local→cloud→local PASS",
        "LH-WF-001",
    )
    for token in readme_tokens:
        if token not in readme:
            refuse("README_ROUTE_INCOMPLETE", token)

    agents_tokens = (
        "A true child consumes named unmerged parent bytes.",
        "## Evidence non-substitution laws",
        "## Shadow stop conditions",
        "Do not self-approve.",
        "LH-WF-001",
        "workflow COMPLETED            != effect commit",
        "canonical_write=NONE",
    )
    for token in agents_tokens:
        if token not in agents:
            refuse("AGENTS_ROUTE_INCOMPLETE", token)


class WorkflowDocsTest(unittest.TestCase):
    def load(self) -> tuple[dict, str, str]:
        return (
            json.loads((ROOT / "stack-index.json").read_text()),
            (ROOT / "README.md").read_text(),
            (ROOT / "AGENTS.md").read_text(),
        )

    def assert_code(self, code: str, fn) -> None:
        with self.assertRaises(DocsError) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)

    def test_current_trace_is_exact_and_non_promoting(self) -> None:
        verify(*self.load())

    def test_docs_cannot_become_writer(self) -> None:
        index, readme, agents = self.load()
        changed = deepcopy(index)
        changed["authority"]["workflow_canonical_write"] = "TASK_AND_EFFECT"
        self.assert_code("WORKFLOW_WRITER_WIDENING", lambda: verify(changed, readme, agents))

    def test_live_state_cannot_promote(self) -> None:
        index, readme, agents = self.load()
        changed = deepcopy(index)
        changed["live_frontier"]["durable_engine"] = "PASS"
        self.assert_code("LIVE_STATE_PROMOTION", lambda: verify(changed, readme, agents))

    def test_parent_cannot_close_from_deterministic_children(self) -> None:
        index, readme, agents = self.load()
        changed = deepcopy(index)
        changed["merge_plan"]["parent_keep_open"].remove(184)
        self.assert_code("PARENT_OR_LIVE_CLOSURE_LAUNDERING", lambda: verify(changed, readme, agents))

    def test_handoff_cannot_self_promote(self) -> None:
        index, readme, agents = self.load()
        changed = deepcopy(index)
        changed["local_handoff"]["state"] = "LIVE_PASS"
        self.assert_code("HANDOFF_SELF_PROMOTION", lambda: verify(changed, readme, agents))

    def test_failure_history_cannot_be_erased(self) -> None:
        index, readme, agents = self.load()
        changed = deepcopy(index)
        changed["retained_failures"] = []
        self.assert_code("FAILURE_HISTORY_ERASED", lambda: verify(changed, readme, agents))


if __name__ == "__main__":
    unittest.main()
