#!/usr/bin/env python3
"""Fail-closed Phase-0 gate for issue #146 physical golden-run readiness."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = ROOT / "docs/traceability/issue-146-golden-readiness.json"
QUEUE = ROOT / "docs/git/pdf-terminal-sequence.json"
BINDING = ROOT / ".skill-bindings/agentic-tech-lead-orchestration/binding.json"
RETIRED_MANIFEST = ROOT / "docs/knowledge-providers/providers/code-graph-rag.json"
REQUIRED_ROUTES = [
    ROOT / "loop_wiki/parallel-agent-tech-lead/scripts/plan.py",
    ROOT / "loop_wiki/parallel-agent-tech-lead/tests/run-all.sh",
    ROOT / "loop_wiki/code-truth-graph-v2/tests/run-all.sh",
    ROOT / "tests/agentic-tech-lead-binding/run-all.sh",
    ROOT / "scripts/gates/check_issue_140_convergence.py",
]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def validate(receipt: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if receipt.get("schema_version") != "issue-146-golden-readiness/v1":
        errors.append("schema_version drifted")
    if receipt.get("issue") != 146 or receipt.get("parent_issue") != 140:
        errors.append("issue lineage drifted")
    subject = receipt.get("subject", {})
    if subject.get("repository") != "ed3c/bettor-arena":
        errors.append("repository subject drifted")
    for key in ("commit", "tree"):
        value = str(subject.get(key, ""))
        if len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
            errors.append(f"subject.{key} must be SHA-40")
    selected = receipt.get("selected_slice", {})
    if selected.get("topology") != "COOPERATIVE":
        errors.append("Phase-0 topology must remain COOPERATIVE")
    if selected.get("topology_execution_state") != "NOT_EXERCISED":
        errors.append("physical topology must remain NOT_EXERCISED")
    if (
        selected.get("interface_owner")
        != ".skill-bindings/agentic-tech-lead-orchestration/binding.json"
    ):
        errors.append("single interface owner drifted")

    packets = receipt.get("planned_packets", [])
    if not isinstance(packets, list) or len(packets) != 2:
        errors.append("expected exactly two planned packets")
    else:
        writable: set[str] = set()
        for packet in packets:
            for path in packet.get("allowed_paths", []):
                if path in writable:
                    errors.append(f"overlapping planned writer: {path}")
                writable.add(path)

    forbidden = receipt.get("forbidden", {})
    placeholder = forbidden.get("placeholder_command")
    commands = receipt.get("command_matrix", [])
    if not commands:
        errors.append("command matrix empty")
    for command in commands:
        argv = command.get("argv", [])
        if (
            not isinstance(argv, list)
            or not argv
            or not all(isinstance(x, str) and x for x in argv)
        ):
            errors.append("command argv invalid")
            continue
        if placeholder in argv or any(placeholder in x for x in argv):
            errors.append("placeholder command survived into execution matrix")
        if command.get("cwd") != ".":
            errors.append("command cwd must be repository root")
        timeout = command.get("timeout_seconds")
        budget = command.get("output_budget_bytes")
        if not isinstance(timeout, int) or timeout <= 0 or timeout > 300:
            errors.append("command timeout unbounded")
        if not isinstance(budget, int) or budget <= 0 or budget > 2_097_152:
            errors.append("command output budget unbounded")

    lanes = receipt.get("tool_lanes", {})
    for lane in (
        "grepai",
        "scip_lsp",
        "tree_sitter",
        "serena",
        "lancedb",
        "git_town",
        "forgejo",
    ):
        if lanes.get(lane) != "NOT_EXERCISED":
            errors.append(f"{lane} must remain NOT_EXERCISED in Phase 0")
    admission = receipt.get("admission", {})
    if admission.get("physical_golden_run") != "NOT_EXERCISED":
        errors.append("physical golden run falsely promoted")
    if admission.get("parent_issue_140") != "HUMAN_ADMIT_REQUIRED":
        errors.append("parent Human Admit erased")
    if admission.get("queue_advance") != "BLOCKED":
        errors.append("queue advanced prematurely")

    stale_root = root / str(forbidden.get("stale_runtime_root", ""))
    if stale_root.exists():
        errors.append("stale duplicate .agentic runtime must remain absent")
    if (root / "docs/knowledge-providers/providers/code-graph-rag.json").exists():
        errors.append("retired Code-Graph-RAG manifest resurrected")
    for route in REQUIRED_ROUTES:
        if not route.is_file():
            errors.append(f"canonical route absent: {route.relative_to(root)}")

    try:
        queue = load(root / "docs/git/pdf-terminal-sequence.json")
    except Exception as exc:
        errors.append(str(exc))
    else:
        current = queue.get("current", {})
        if current.get("active_issue") != 140 or current.get("active_order") != 13:
            errors.append("parent queue subject advanced or drifted")

    try:
        binding = load(
            root / ".skill-bindings/agentic-tech-lead-orchestration/binding.json"
        )
    except Exception as exc:
        errors.append(str(exc))
    else:
        roles = {
            x.get("role"): x for x in binding.get("modules", []) if isinstance(x, dict)
        }
        for role in ("DETERMINISTIC_GRAPH", "STRUCTURAL_SLICER"):
            if roles.get(role, {}).get("runtime_state") != "NOT_EXERCISED":
                errors.append(
                    f"{role} must distinguish implemented contract from unexercised live runtime"
                )
    return errors


def selftest(base: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    cases = [
        (
            "placeholder",
            lambda x: x["command_matrix"][0].__setitem__(
                "argv", ["sh", "REPLACE_WITH_REPOSITORY_TEST_COMMAND"]
            ),
            "placeholder",
        ),
        (
            "fake live",
            lambda x: x["tool_lanes"].__setitem__("grepai", "PASS"),
            "grepai",
        ),
        (
            "queue laundering",
            lambda x: x["admission"].__setitem__("queue_advance", "PASS"),
            "queue",
        ),
        (
            "human admit erased",
            lambda x: x["admission"].__setitem__("parent_issue_140", "PASS"),
            "Human Admit",
        ),
        (
            "fake physical fanout",
            lambda x: x["selected_slice"].__setitem__(
                "topology_execution_state", "PASS"
            ),
            "NOT_EXERCISED",
        ),
        (
            "writer collision",
            lambda x: x["planned_packets"][1]["allowed_paths"].append(
                x["planned_packets"][0]["allowed_paths"][0]
            ),
            "overlapping",
        ),
    ]
    for name, mutate, needle in cases:
        candidate = copy.deepcopy(base)
        mutate(candidate)
        errors = validate(candidate)
        if not any(needle.lower() in error.lower() for error in errors):
            failures.append(f"control did not turn red: {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    try:
        receipt = load(RECEIPT)
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 2
    errors = selftest(receipt) if args.selftest else validate(receipt)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: issue #146 Phase-0 golden-run readiness is fail-closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
