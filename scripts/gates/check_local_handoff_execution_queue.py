#!/usr/bin/env python3
"""Validate Bettor's single-authority Local Handoff Execution Queue."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "docs/traceability/local-handoff-execution-queue.json"
DUPLICATE = ROOT / "docs/git/local-handoff-execution-queue.json"
MATRIX = ROOT / "docs/architecture/tech-lead-shadow-monitor/closure-matrix.json"
PDF_QUEUE = ROOT / "docs/git/pdf-terminal-sequence.json"

SUBJECT = "4655b18a150716ad7a3a0edbe3201fd2927eef80"
TREE = "849328ac84c770d5932a16b4a3a9f0946dff8dba"
ROLLBACK = "8c911b998fdf77d1abdfa4bb4153b0a7a5eaa9cf"
FORBIDDEN = {
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
        raise InputError(f"{path}: object required")
    return value


def validate(
    queue: dict[str, Any],
    matrix: dict[str, Any],
    pdf: dict[str, Any],
    duplicate_exists: bool,
) -> list[str]:
    errors: list[str] = []
    if duplicate_exists:
        errors.append("duplicate Local Handoff queue authority exists")
    if queue.get("schema_version") != "agentic-tech-lead/local-handoff-queue/v1":
        errors.append("queue schema drifted")
    subject = queue.get("subject", {})
    if (
        subject.get("repository"),
        subject.get("commit"),
        subject.get("tree"),
        subject.get("rollback_commit"),
    ) != ("ed3c/bettor-arena", SUBJECT, TREE, ROLLBACK):
        errors.append("queue exact subject drifted")
    if not FORBIDDEN.issubset(
        set(queue.get("authority", {}).get("automation_forbidden", []))
    ):
        errors.append("queue automation authority widened")
    if queue.get("current") != {
        "active_item": "dual-origin-reconciliation",
        "state": "ACTIVE",
    }:
        errors.append("current item is not #172 dual-origin reconciliation")
    items = queue.get("items", [])
    active = [item for item in items if item.get("state") == "ACTIVE"]
    if len(items) != 1 or len(active) != 1:
        errors.append("one-item epoch requires exactly one ACTIVE item")
        return errors
    item = active[0]
    if (
        item.get("id"),
        item.get("task_ref"),
        item.get("next"),
    ) != ("dual-origin-reconciliation", "ed3c/bettor-arena#172", None):
        errors.append("queue item identity or epoch boundary drifted")
    entry = item.get("entry", {})
    if entry.get("predecessor") is not None:
        errors.append("#172 gained a false predecessor")
    if entry.get("required_subject_commit") != SUBJECT:
        errors.append("#172 required subject is stale")
    lane = item.get("runtime_lane", {})
    if lane.get("class") != "LOCAL_FORGE":
        errors.append("#172 runtime lane is not LOCAL_FORGE")
    if lane.get("commands"):
        errors.append("unresolved host command was guessed")
    unresolved = lane.get("unresolved_operations", [])
    if (
        len(unresolved) != 1
        or unresolved[0].get("required_output") != "CONCRETE_COMMAND_CONTRACT"
        or not unresolved[0].get("resolver_source")
    ):
        errors.append("concrete command-resolution contract missing")
    if lane.get("live_evidence_required") is not True:
        errors.append("#172 live evidence requirement missing")
    receipt = item.get("receipt", {})
    if not receipt.get("path") or not receipt.get("schema"):
        errors.append("durable receipt contract missing")
    guards = set(receipt.get("forbidden_promotions", []))
    for required in (
        "observed_divergence_to_reconciled",
        "blind_merge_or_pull_to_semantic_resolution",
        "documentation_pass_to_live_receipt",
    ):
        if required not in guards:
            errors.append("Local Handoff evidence promotion guard missing")
    exit_contract = item.get("exit", {})
    if (
        exit_contract.get("requires_receipt") is not True
        or exit_contract.get("required_verdict") != "PASS"
        or exit_contract.get("cleanup_required") is not True
    ):
        errors.append("#172 exit does not require PASS + cleanup")
    if (
        matrix.get("local_handoff", {}).get("canonical_path")
        != "docs/traceability/local-handoff-execution-queue.json"
        or matrix.get("local_handoff", {}).get("current_active_issue") != 172
    ):
        errors.append("closure matrix disagrees with Local Handoff authority")
    if (
        pdf.get("current", {}).get("active_issue") != 140
        or pdf.get("current", {}).get("active_order") != 13
    ):
        errors.append("Local Handoff falsely advanced the PDF queue")
    return errors


def selftest(queue: dict[str, Any], matrix: dict[str, Any], pdf: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    def case(name: str, mutate, needle: str, duplicate: bool = False) -> None:
        q, m, p = copy.deepcopy(queue), copy.deepcopy(matrix), copy.deepcopy(pdf)
        mutate(q, m, p)
        errors = validate(q, m, p, duplicate)
        if not any(needle.lower() in error.lower() for error in errors):
            failures.append(f"{name}: control did not turn red; errors={errors}")

    case("duplicate queue", lambda q, m, p: None, "duplicate", True)
    case("stale subject", lambda q, m, p: q["subject"].__setitem__("commit", "f"*40), "subject drifted")
    case("two active", lambda q, m, p: q["items"].append(copy.deepcopy(q["items"][0])), "exactly one ACTIVE")
    case("wrong active", lambda q, m, p: q["items"][0].__setitem__("task_ref", "ed3c/bettor-arena#161"), "identity")
    case("guessed command", lambda q, m, p: q["items"][0]["runtime_lane"].__setitem__("commands", [{"argv":["git","pull"],"cwd":".","timeout_seconds":60}]), "guessed")
    case("no unresolved contract", lambda q, m, p: q["items"][0]["runtime_lane"].__setitem__("unresolved_operations", []), "command-resolution")
    case("no live requirement", lambda q, m, p: q["items"][0]["runtime_lane"].__setitem__("live_evidence_required", False), "live evidence")
    case("missing promotion guard", lambda q, m, p: q["items"][0]["receipt"].__setitem__("forbidden_promotions", []), "promotion guard")
    case("cleanup disabled", lambda q, m, p: q["items"][0]["exit"].__setitem__("cleanup_required", False), "PASS + cleanup")
    case("matrix disagreement", lambda q, m, p: m["local_handoff"].__setitem__("current_active_issue", 161), "disagrees")
    case("queue advance", lambda q, m, p: p["current"].__setitem__("active_order", 14), "advanced")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        queue = load(root / QUEUE.relative_to(ROOT))
        matrix = load(root / MATRIX.relative_to(ROOT))
        pdf = load(root / PDF_QUEUE.relative_to(ROOT))
    except InputError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 64
    errors = (
        selftest(queue, matrix, pdf)
        if args.selftest
        else validate(
            queue,
            matrix,
            pdf,
            (root / DUPLICATE.relative_to(ROOT)).exists(),
        )
    )
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 2
    if args.selftest:
        print("SELFTEST GREEN: Bettor Local Handoff controls (11 mutations)")
    else:
        print(f"PASS: one Local Handoff authority (active=#172, subject={SUBJECT})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
