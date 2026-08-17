#!/usr/bin/env python3
"""Validate bettor-arena's zero-context Local Handoff Execution Queue."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "docs/git/local-handoff-execution-queue.json"
RUNTIME_PACKET = ROOT / "docs/traceability/issue-161-runtime-admission.json"
PDF_QUEUE = ROOT / "docs/git/pdf-terminal-sequence.json"
SHA40 = set("0123456789abcdef")
SHARED_COMMIT = "dbcfdb4df76609822893aeb595e5f8ada8483435"
FORBIDDEN = {"merge", "force_push", "issue_close", "queue_advance", "provider_activation", "semantic_conflict_resolution"}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def sha40(value: object) -> bool:
    text = str(value)
    return len(text) == 40 and all(ch in SHA40 for ch in text)


def validate(queue: dict[str, Any], runtime: dict[str, Any], pdf: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if queue.get("schema_version") != "agentic-tech-lead/local-handoff-queue/v1":
        errors.append("schema drifted")
    shared = queue.get("shared_contract", {})
    if shared.get("repository") != "ed3c/skills-shared" or shared.get("commit") != SHARED_COMMIT or shared.get("admission_state") != "MERGED_TO_MAIN":
        errors.append("shared handoff contract pin drifted")
    subject = queue.get("subject", {})
    for key in ("commit", "tree", "rollback_commit"):
        if not sha40(subject.get(key)):
            errors.append(f"subject.{key} must be SHA-40")
    if subject.get("repository") != "ed3c/bettor-arena":
        errors.append("consumer repository drifted")
    runtime_consumer = runtime.get("consumer_subject", {})
    if subject.get("commit") != runtime_consumer.get("base_commit") or subject.get("tree") != runtime_consumer.get("base_tree"):
        errors.append("handoff subject does not match #161 runtime admission subject")
    authority = set(queue.get("authority", {}).get("automation_forbidden", []))
    if not FORBIDDEN.issubset(authority):
        errors.append("handoff automation authority widened")
    if pdf.get("current", {}).get("active_issue") != 140 or pdf.get("current", {}).get("active_order") != 13:
        errors.append("PDF queue must remain #140/order 13")

    items = queue.get("items", [])
    active = [item for item in items if item.get("state") == "ACTIVE"]
    if len(active) != 1 or active[0].get("id") != "issue-161-runtime-rebind-and-canary-admission":
        errors.append("#161 must be the single ACTIVE local handoff item")
    expected = [
        ("issue-161-runtime-rebind-and-canary-admission", "bettor-arena#161", "ACTIVE", None),
        ("issue-146-physical-tech-lead-golden-run", "bettor-arena#146", "BLOCKED_BY_PREDECESSOR", "issue-161-runtime-rebind-and-canary-admission"),
        ("issue-140-terminal-human-admission", "bettor-arena#140", "BLOCKED_BY_PREDECESSOR", "issue-146-physical-tech-lead-golden-run"),
    ]
    if len(items) != len(expected):
        errors.append("handoff queue item count drifted")
        return errors
    for item, (item_id, task_ref, state, predecessor) in zip(items, expected):
        if (item.get("id"), item.get("task_ref"), item.get("state")) != (item_id, task_ref, state):
            errors.append(f"{item_id}: identity/state drifted")
        entry = item.get("entry", {})
        if entry.get("predecessor") != predecessor:
            errors.append(f"{item_id}: predecessor drifted")
        if entry.get("required_subject_commit") != subject.get("commit"):
            errors.append(f"{item_id}: stale required subject")
        lane = item.get("runtime_lane", {})
        commands = lane.get("commands", [])
        unresolved = lane.get("unresolved_operations", [])
        if not commands and not unresolved:
            errors.append(f"{item_id}: no executable or resolvable runtime lane")
        for command in commands:
            argv = command.get("argv", []) if isinstance(command, dict) else []
            if not argv or any(str(arg).startswith("LOCAL_") or "REPLACE_WITH_" in str(arg) or "PLACEHOLDER" in str(arg) for arg in argv):
                errors.append(f"{item_id}: fake/placeholder command survived")
            if not command.get("cwd") or int(command.get("timeout_seconds", 0) or 0) <= 0:
                errors.append(f"{item_id}: command bounds missing")
        for operation in unresolved:
            if operation.get("required_output") != "CONCRETE_COMMAND_CONTRACT" or not operation.get("resolver_source"):
                errors.append(f"{item_id}: unresolved operation contract invalid")
        if unresolved and item.get("state") == "COMPLETE":
            errors.append(f"{item_id}: unresolved operation cannot be COMPLETE")
        receipt = item.get("receipt", {})
        if not receipt.get("path") or not receipt.get("schema") or not receipt.get("forbidden_promotions"):
            errors.append(f"{item_id}: receipt/evidence ceiling missing")
        exit_contract = item.get("exit", {})
        if exit_contract.get("requires_receipt") is not True or exit_contract.get("required_verdict") != "PASS":
            errors.append(f"{item_id}: exit must require PASS receipt")
    return errors


def selftest(queue: dict[str, Any], runtime: dict[str, Any], pdf: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    cases = [
        ("shared pin", lambda q, r, p: q["shared_contract"].__setitem__("commit", "0" * 40), "shared handoff"),
        ("subject drift", lambda q, r, p: q["subject"].__setitem__("commit", "f" * 40), "runtime admission subject"),
        ("two active", lambda q, r, p: q["items"][1].__setitem__("state", "ACTIVE"), "single ACTIVE"),
        ("fake command", lambda q, r, p: q["items"][0]["runtime_lane"]["commands"][0].__setitem__("argv", ["LOCAL_FAKE"]), "fake/placeholder"),
        ("unresolved complete", lambda q, r, p: q["items"][0].__setitem__("state", "COMPLETE"), "unresolved operation cannot be COMPLETE"),
        ("queue advance", lambda q, r, p: p["current"].__setitem__("active_issue", 70), "#140/order 13"),
        ("authority widen", lambda q, r, p: q["authority"].__setitem__("automation_forbidden", ["merge"]), "authority widened"),
    ]
    for name, mutate, needle in cases:
        q, r, p = copy.deepcopy(queue), copy.deepcopy(runtime), copy.deepcopy(pdf)
        mutate(q, r, p)
        errors = validate(q, r, p)
        if not any(needle.lower() in error.lower() for error in errors):
            failures.append(f"control did not turn red: {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    try:
        queue, runtime, pdf = load(QUEUE), load(RUNTIME_PACKET), load(PDF_QUEUE)
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 2
    errors = selftest(queue, runtime, pdf) if args.selftest else validate(queue, runtime, pdf)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: bettor Local Handoff Execution Queue is fail-closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
