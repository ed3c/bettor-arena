#!/usr/bin/env python3
"""Fail closed on stale runtime-env bindings before the #146 physical canary."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs/traceability/issue-161-runtime-admission.json"
BINDING = ROOT / ".runtime-env/bindings/bettor-arena-local.json"
SHA40 = set("0123456789abcdef")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be object")
    return value


def is_sha40(value: object) -> bool:
    text = str(value)
    return len(text) == 40 and all(c in SHA40 for c in text)


def validate(packet: dict[str, Any], binding: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("schema_version") != "issue-161-runtime-admission/v1":
        errors.append("schema_version drifted")
    if packet.get("issue") != 161 or packet.get("parent_issue") != 146:
        errors.append("issue lineage drifted")

    consumer = packet.get("consumer_subject", {})
    if consumer.get("repository") != "ed3c/bettor-arena":
        errors.append("consumer repository drifted")
    for key in ("base_commit", "base_tree"):
        if not is_sha40(consumer.get(key)):
            errors.append(f"consumer_subject.{key} must be SHA-40")

    canonical = packet.get("canonical_subjects", {})
    skills = canonical.get("skills_shared", {})
    runtime = canonical.get("runtime_env", {})
    if skills.get("repository") != "ed3c/skills-shared" or not is_sha40(skills.get("commit")):
        errors.append("skills-shared exact subject invalid")
    if runtime.get("repository") != "ed3c/runtime-env" or not is_sha40(runtime.get("commit")):
        errors.append("runtime-env exact subject invalid")

    binding_source = binding.get("source", {}).get("commit")
    observed = packet.get("checked_in_binding", {}).get("observed_source_commit")
    if binding_source != observed:
        errors.append("packet observed binding source does not match checked-in binding")

    module_ids = {m.get("id") for m in binding.get("modules", []) if isinstance(m, dict)}
    required_modules = set(runtime.get("required_modules", []))
    exact_runtime = binding_source == runtime.get("commit")
    scheduler_bound = required_modules.issubset(module_ids)
    expected_state = "READY_FOR_LOCAL_CANARY" if exact_runtime and scheduler_bound else "BLOCKED_STALE_BINDING"
    if packet.get("checked_in_binding", {}).get("state") != expected_state:
        errors.append(f"checked-in binding state must be {expected_state}")
    if packet.get("admission", {}).get("scheduler_runtime") != expected_state:
        errors.append(f"scheduler runtime admission must be {expected_state}")

    admission = packet.get("admission", {})
    if admission.get("consumer_live_canary") != "NOT_EXERCISED":
        errors.append("consumer live canary falsely promoted")
    if admission.get("git_town_darwin_artifact") != "HUMAN_ADMIT_REQUIRED":
        errors.append("Git Town Darwin Human Admit erased")
    if admission.get("forgejo_service_activation") != "NOT_EXERCISED":
        errors.append("Forgejo activation falsely promoted")
    if admission.get("merge_or_ship_authority") is not False:
        errors.append("merge/ship authority must remain false")

    lanes = packet.get("evidence_lanes", {})
    for lane in (
        "bettor_worker_processes", "bettor_linked_worktrees", "bettor_checkpoint_resume",
        "bettor_stale_result_refusal", "bettor_budget_reconciliation", "grepai", "scip_lsp",
        "tree_sitter", "serena", "sqlite", "lancedb", "git_town", "forgejo", "github_exact_head",
    ):
        if lanes.get(lane) != "NOT_EXERCISED":
            errors.append(f"{lane} must remain NOT_EXERCISED before local canary")
    for lane in ("runtime_env_synthetic_scheduler", "runtime_env_synthetic_worktrees"):
        if lanes.get(lane) != "PASS":
            errors.append(f"{lane} must preserve observed synthetic PASS")

    forbidden = packet.get("forbidden", {})
    for key in (
        "static_fixture_as_consumer_pass", "synthetic_runtime_as_bettor_pass",
        "arbitrary_model_shell_command", "auto_admit_darwin_git_town_artifact",
        "auto_activate_forgejo", "auto_merge_ship_force_push",
    ):
        if forbidden.get(key) is not True:
            errors.append(f"forbidden control disabled: {key}")
    return errors


def selftest(packet: dict[str, Any], binding: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    cases = [
        ("fake ready", lambda p, b: p["admission"].__setitem__("scheduler_runtime", "READY_FOR_LOCAL_CANARY"), "scheduler runtime"),
        ("fake live", lambda p, b: p["evidence_lanes"].__setitem__("bettor_worker_processes", "PASS"), "bettor_worker_processes"),
        ("human admit erased", lambda p, b: p["admission"].__setitem__("git_town_darwin_artifact", "PASS"), "Human Admit"),
        ("binding observation drift", lambda p, b: p["checked_in_binding"].__setitem__("observed_source_commit", "0" * 40), "observed binding"),
        ("fake scheduler module", lambda p, b: b.setdefault("modules", []).append({"id": "multi-worker-scheduler"}), "BLOCKED_STALE_BINDING"),
        ("merge authority", lambda p, b: p["admission"].__setitem__("merge_or_ship_authority", True), "merge/ship"),
    ]
    for name, mutate, needle in cases:
        p = copy.deepcopy(packet)
        b = copy.deepcopy(binding)
        mutate(p, b)
        if not any(needle.lower() in error.lower() for error in validate(p, b)):
            failures.append(f"control did not turn red: {name}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    try:
        packet, binding = load(PACKET), load(BINDING)
    except Exception as exc:
        print(f"FAIL: {exc}")
        return 2
    errors = selftest(packet, binding) if args.selftest else validate(packet, binding)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    state = packet["admission"]["scheduler_runtime"]
    print(f"PASS: issue #161 runtime admission is fail-closed ({state})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
