#!/usr/bin/env python3
"""Validate the Tech Lead + independent Shadow closure monitor."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs/architecture/tech-lead-shadow-monitor/closure-matrix.json"
QUEUE = ROOT / "docs/traceability/local-handoff-execution-queue.json"
DUPLICATE_QUEUE = ROOT / "docs/git/local-handoff-execution-queue.json"
PDF_QUEUE = ROOT / "docs/git/pdf-terminal-sequence.json"

SUBJECT_COMMIT = "4655b18a150716ad7a3a0edbe3201fd2927eef80"
SUBJECT_TREE = "849328ac84c770d5932a16b4a3a9f0946dff8dba"
ROLLBACK_COMMIT = "8c911b998fdf77d1abdfa4bb4153b0a7a5eaa9cf"
EXPECTED_PRS = {
    153: "0e27c9898925259b58c136e01fa4de175ad75231",
    155: "9ec507f685c9f3d0fcf97238d036a22be92fddf5",
    156: "d45c1bd8e9f1ba9c92c6926173efd59a4dfdcf33",
    157: "ad0fdde3e46aa6ab6c59ced145bead7fa4fc72d3",
    158: "e67a803ba6d12f8141a1bed3a26d9ec928931e35",
    159: "1970a2a6db3b743a2ad9204bcf506e80dbfd799b",
    169: "8c911b998fdf77d1abdfa4bb4153b0a7a5eaa9cf",
    154: SUBJECT_COMMIT,
}
EXPECTED_PROCESS = [
    ("issue-172", None, "ACTIVE"),
    ("issue-161", "issue-172", "BLOCKED_BY_PREDECESSOR"),
    ("issue-146", "issue-161", "BLOCKED_BY_PREDECESSOR"),
    ("issue-140", "issue-146", "BLOCKED_BY_PREDECESSOR"),
    ("issue-68", "issue-140", "FINAL_CONVERGENCE"),
]
EVIDENCE_STATES = {
    "PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED", "NOT_EXERCISED",
    "NOT_APPLICABLE", "NOT_REQUIRED_FOR_STATIC", "NOT_REQUIRED_FOR_FIX",
    "OBSERVED_DIVERGENCE", "NOT_RECONCILED", "HUMAN_ADMIT_REQUIRED",
    "DEFECT_CONFIRMED", "IMPLEMENTED", "BLOCKED",
}
FORBIDDEN_AUTOMATION = {
    "merge", "force_push", "issue_close", "queue_advance",
    "provider_activation", "semantic_conflict_resolution",
}


class InputError(Exception):
    pass


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InputError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError(f"{path}: root must be an object")
    return value


def validate(
    matrix: dict[str, Any],
    queue: dict[str, Any],
    pdf: dict[str, Any],
    duplicate_exists: bool = False,
) -> list[str]:
    errors: list[str] = []

    if matrix.get("schema_version") != "bettor-arena/tech-lead-shadow-closure/v1":
        errors.append("closure schema drifted")
    subject = matrix.get("subject", {})
    if (
        subject.get("repository"),
        subject.get("commit"),
        subject.get("tree"),
        subject.get("rollback_commit"),
    ) != ("ed3c/bettor-arena", SUBJECT_COMMIT, SUBJECT_TREE, ROLLBACK_COMMIT):
        errors.append("closure subject drifted")
    if subject.get("origin_relation") != "DIVERGED":
        errors.append("dual-origin divergence was falsely closed")

    roles = matrix.get("roles", {})
    tech = roles.get("tech_lead", {})
    shadow = roles.get("shadow_architect", {})
    if "convergence-owner" not in tech.get("owns", []):
        errors.append("Tech Lead convergence ownership missing")
    for forbidden in ("second-state-writer", "silent-builder-branch-edit"):
        if forbidden not in shadow.get("forbidden", []):
            errors.append("Shadow authority widened")

    if duplicate_exists:
        errors.append("two Local Handoff queue authorities exist")
    handoff = matrix.get("local_handoff", {})
    if handoff.get("canonical_path") != "docs/traceability/local-handoff-execution-queue.json":
        errors.append("canonical Local Handoff queue path drifted")
    if handoff.get("deprecated_duplicate_path") != "docs/git/local-handoff-execution-queue.json":
        errors.append("deprecated queue path not named")
    if handoff.get("current_active_issue") != 172:
        errors.append("Local Handoff active issue is not #172")

    if queue.get("schema_version") != "agentic-tech-lead/local-handoff-queue/v1":
        errors.append("Local Handoff schema drifted")
    qsubject = queue.get("subject", {})
    if (
        qsubject.get("repository"),
        qsubject.get("commit"),
        qsubject.get("tree"),
        qsubject.get("rollback_commit"),
    ) != ("ed3c/bettor-arena", SUBJECT_COMMIT, SUBJECT_TREE, ROLLBACK_COMMIT):
        errors.append("Local Handoff subject drifted")
    authority = set(queue.get("authority", {}).get("automation_forbidden", []))
    if not FORBIDDEN_AUTOMATION.issubset(authority):
        errors.append("Local Handoff automation authority widened")
    items = queue.get("items", [])
    active = [item for item in items if isinstance(item, dict) and item.get("state") == "ACTIVE"]
    if len(items) != 1 or len(active) != 1:
        errors.append("Local Handoff epoch must contain exactly one ACTIVE item")
    elif (
        active[0].get("id") != "dual-origin-reconciliation"
        or active[0].get("task_ref") != "ed3c/bettor-arena#172"
        or active[0].get("next") is not None
    ):
        errors.append("Local Handoff epoch is not the #172 reconciliation epoch")
    if queue.get("current") != {
        "active_item": "dual-origin-reconciliation",
        "state": "ACTIVE",
    }:
        errors.append("Local Handoff current pointer drifted")
    if active:
        item = active[0]
        if item.get("entry", {}).get("required_subject_commit") != SUBJECT_COMMIT:
            errors.append("Local Handoff item uses a stale subject")
        runtime = item.get("runtime_lane", {})
        if runtime.get("class") != "LOCAL_FORGE":
            errors.append("dual-origin reconciliation must execute in LOCAL_FORGE")
        if runtime.get("commands"):
            errors.append("unresolved dual-origin operation was guessed as an executable command")
        unresolved = runtime.get("unresolved_operations", [])
        if len(unresolved) != 1 or unresolved[0].get("required_output") != "CONCRETE_COMMAND_CONTRACT":
            errors.append("dual-origin command-resolution contract missing")
        if runtime.get("live_evidence_required") is not True:
            errors.append("dual-origin reconciliation must require live evidence")
        receipt = item.get("receipt", {})
        if "observed_divergence_to_reconciled" not in receipt.get("forbidden_promotions", []):
            errors.append("divergence false-promotion guard missing")
        if item.get("exit", {}).get("required_verdict") != "PASS":
            errors.append("Local Handoff exit does not require PASS receipt")

    current = pdf.get("current", {})
    if current.get("active_issue") != 140 or current.get("active_order") != 13:
        errors.append("PDF queue was advanced outside the order-13 admission")

    process = matrix.get("process_dag", [])
    observed_process = [
        (node.get("id"), node.get("predecessor"), node.get("state"))
        for node in process if isinstance(node, dict)
    ]
    if observed_process != EXPECTED_PROCESS:
        errors.append("process DAG drifted or skipped a predecessor")
    for node in process:
        if node.get("relation") != "PROCESS_DEPENDENCY" or node.get("git_parent") is not None:
            errors.append("process dependency was manufactured as Git ancestry")

    siblings = {node.get("id"): node for node in matrix.get("independent_siblings", [])}
    for sibling_id in ("issue-173", "issue-174", "issue-175"):
        if siblings.get(sibling_id, {}).get("relation") != "SIBLING":
            errors.append(f"{sibling_id} is not an independent sibling")
    if any(node.get("predecessor") for node in matrix.get("independent_siblings", [])):
        errors.append("independent control defect gained a false predecessor")

    pr_nodes = matrix.get("molecular_pr_index", [])
    seen_prs: set[int] = set()
    for node in pr_nodes:
        pr = node.get("pr")
        if pr in seen_prs:
            errors.append(f"duplicate PR index entry: {pr}")
        seen_prs.add(pr)
        if node.get("state") != "MERGED_TO_MAIN":
            errors.append(f"PR #{pr} not recorded as merged-to-main")
        if EXPECTED_PRS.get(pr) != node.get("merge_commit"):
            errors.append(f"PR #{pr} merge subject drifted")
        if node.get("relation") == "TRUE_CHILD":
            errors.append(f"PR #{pr} falsely represented as a true child")
    if seen_prs != set(EXPECTED_PRS):
        errors.append("molecular PR denominator is incomplete")

    directories = matrix.get("directory_owners", [])
    required_paths = {
        "docs/architecture/tech-lead-shadow-monitor/",
        "docs/traceability/local-handoff-execution-queue.json",
        "loop_wiki/code-truth-graph-v2/",
        "loop_wiki/parallel-agent-tech-lead/",
        "scripts/gates/",
        ".runtime-env/",
        "docs/git/pdf-terminal-sequence.json",
        ".arena/compositions/ + data/module-proof/",
    }
    if {entry.get("path") for entry in directories} != required_paths:
        errors.append("directory-to-State-Machine ownership map is incomplete")
    for entry in directories:
        for key in ("owner", "state_machine", "inputs", "outputs", "evidence_ceiling"):
            if not entry.get(key):
                errors.append(f"{entry.get('path')}: directory contract missing {key}")

    closure_items = {item.get("id"): item for item in matrix.get("closure_items", [])}
    required_closures = {
        "dual-origin",
        "blindspots-context-funnel",
        "parallel-tech-lead",
        "procedural-shadow-independent-live",
        "git-town-runtime",
        "controlled-language-deterministic",
        "controlled-language-heuristic-semantic",
        "production-termbase-and-safety-review",
        "confidential-external-processing",
        "intent-promotion",
        "production-memory-writeback",
        "workflow-receipt-status",
        "origin-projection-freshness",
        "final-release",
    }
    if set(closure_items) != required_closures:
        errors.append("real-problem closure denominator is incomplete")
    if closure_items.get("parallel-tech-lead", {}).get("live") != "NOT_EXERCISED":
        errors.append("physical Tech Lead run falsely promoted")
    if closure_items.get("procedural-shadow-independent-live", {}).get("live") != "NOT_EXERCISED":
        errors.append("independent Shadow live run falsely promoted")
    if closure_items.get("controlled-language-heuristic-semantic", {}).get("mechanism") != "NOT_IMPLEMENTED":
        errors.append("unimplemented controlled-language semantic lane falsely promoted")
    if closure_items.get("production-termbase-and-safety-review", {}).get("mechanism") != "ABSENT":
        errors.append("production termbase falsely claimed")
    if closure_items.get("workflow-receipt-status", {}).get("deterministic") != "FAIL":
        errors.append("receipt-status defect was laundered")
    if closure_items.get("origin-projection-freshness", {}).get("deterministic") != "FAIL":
        errors.append("origin freshness defect was laundered")
    if closure_items.get("final-release", {}).get("release") != "BLOCKED":
        errors.append("final release falsely promoted")
    for item_id, item in closure_items.items():
        for field in ("mechanism", "deterministic", "live", "human", "release"):
            value = item.get(field)
            if not isinstance(value, str) or not value:
                errors.append(f"{item_id}: missing closure lane {field}")

    proposal = matrix.get("source_proposals", [])
    if (
        len(proposal) != 1
        or proposal[0].get("authority") != "SOURCE_PROPOSAL"
        or "source-proposal-to-official-standard" not in proposal[0].get("forbidden_promotions", [])
    ):
        errors.append("source proposal authority widened")

    return errors


def selftest(
    matrix: dict[str, Any], queue: dict[str, Any], pdf: dict[str, Any]
) -> list[str]:
    failures: list[str] = []

    def case(name: str, mutate, needle: str, duplicate: bool = False) -> None:
        m, q, p = copy.deepcopy(matrix), copy.deepcopy(queue), copy.deepcopy(pdf)
        mutate(m, q, p)
        errors = validate(m, q, p, duplicate_exists=duplicate)
        if not any(needle.lower() in error.lower() for error in errors):
            failures.append(f"{name}: control did not turn red; errors={errors}")

    case("stale subject", lambda m, q, p: q["subject"].__setitem__("commit", "f" * 40), "subject drifted")
    case("two queue authorities", lambda m, q, p: None, "two Local Handoff", duplicate=True)
    case("two active items", lambda m, q, p: q["items"].append(copy.deepcopy(q["items"][0])), "exactly one ACTIVE")
    case("false physical Tech Lead", lambda m, q, p: next(x for x in m["closure_items"] if x["id"] == "parallel-tech-lead").__setitem__("live", "PASS"), "physical Tech Lead")
    case("false Shadow live", lambda m, q, p: next(x for x in m["closure_items"] if x["id"] == "procedural-shadow-independent-live").__setitem__("live", "PASS"), "Shadow live")
    case("false Human/final release", lambda m, q, p: next(x for x in m["closure_items"] if x["id"] == "final-release").__setitem__("release", "RELEASED"), "final release")
    case("queue skip", lambda m, q, p: m["process_dag"][2].__setitem__("predecessor", "issue-172"), "process DAG")
    case("fake Git child", lambda m, q, p: m["process_dag"][1].__setitem__("relation", "TRUE_CHILD"), "Git ancestry")
    case("sibling serialized", lambda m, q, p: m["independent_siblings"][1].__setitem__("predecessor", "issue-172"), "false predecessor")
    case("missing PR denominator", lambda m, q, p: m["molecular_pr_index"].pop(), "denominator")
    case("receipt defect green", lambda m, q, p: next(x for x in m["closure_items"] if x["id"] == "workflow-receipt-status").__setitem__("deterministic", "PASS"), "laundered")
    case("origin defect green", lambda m, q, p: next(x for x in m["closure_items"] if x["id"] == "origin-projection-freshness").__setitem__("deterministic", "PASS"), "laundered")
    case("official source promotion", lambda m, q, p: m["source_proposals"][0].__setitem__("authority", "OFFICIAL_STANDARD"), "authority widened")
    case("PDF queue advanced", lambda m, q, p: p["current"].__setitem__("active_order", 14), "order-13")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        matrix = load(root / MATRIX.relative_to(ROOT))
        queue = load(root / QUEUE.relative_to(ROOT))
        pdf = load(root / PDF_QUEUE.relative_to(ROOT))
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 64
    errors = (
        selftest(matrix, queue, pdf)
        if args.selftest
        else validate(
            matrix,
            queue,
            pdf,
            duplicate_exists=(root / DUPLICATE_QUEUE.relative_to(ROOT)).exists(),
        )
    )
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 2
    if args.selftest:
        print("SELFTEST GREEN: Tech Lead + Shadow closure controls (14 mutations)")
    else:
        print(
            "PASS: Tech Lead + Shadow closure monitor "
            f"(subject={SUBJECT_COMMIT}, active=#172, PRs={len(EXPECTED_PRS)})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
