#!/usr/bin/env python3
"""Plan fail-closed reconciliation for GitHub issue close events.

This program never mutates GitHub. It returns one of:
- REOPEN_REQUIRED: repository authority proves the closed issue remains incomplete;
- NO_ACTION: the issue is not protected by current repository authority.

Contract errors fail with exit 2 and must result in no remote mutation.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = ROOT / "docs/git/pdf-terminal-sequence.json"
GUARD_PATH = ROOT / "docs/git/issue-state-guard.json"


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be object")
    return data


def nested_get(data: dict[str, Any], path: list[str]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            raise KeyError(".".join(path))
        current = current[key]
    return current


def queue_active_items(queue: dict[str, Any]) -> list[dict[str, Any]]:
    items = queue.get("items")
    if not isinstance(items, list):
        raise ValueError("queue.items must be list")
    return [item for item in items if isinstance(item, dict) and item.get("queue_state") == "ACTIVE"]


def validate_contract(queue: dict[str, Any], guard: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if guard.get("schema_version") != "issue-state-guard/v1":
        errors.append("guard schema drifted")

    current = queue.get("current")
    if not isinstance(current, dict):
        errors.append("queue.current missing")
        return errors
    active_issue = current.get("active_issue")
    active_order = current.get("active_order")
    if not isinstance(active_issue, int) or not isinstance(active_order, int):
        errors.append("queue current active issue/order invalid")

    active = queue_active_items(queue)
    if len(active) != 1:
        errors.append(f"expected exactly one ACTIVE queue item, got {len(active)}")
    elif active[0].get("order") != active_order or active_issue not in active[0].get("issues", []):
        errors.append("queue.current does not match ACTIVE item")

    anchor = guard.get("queue_anchor", {})
    if anchor.get("active_issue") != active_issue or anchor.get("active_order") != active_order:
        errors.append("guard queue anchor is stale")

    forbidden = guard.get("forbidden_actions")
    if not isinstance(forbidden, list) or "close_issue" not in forbidden or "advance_queue" not in forbidden:
        errors.append("forbidden action ceiling weakened")

    protected = guard.get("protected_incomplete_issues")
    if not isinstance(protected, list):
        errors.append("protected_incomplete_issues must be list")
        return errors
    seen: set[int] = set()
    for item in protected:
        if not isinstance(item, dict) or not isinstance(item.get("issue"), int):
            errors.append("protected issue entry invalid")
            continue
        issue = item["issue"]
        if issue in seen:
            errors.append(f"duplicate protected issue {issue}")
        seen.add(issue)
        receipt_path = root / str(item.get("receipt", ""))
        if not receipt_path.is_file():
            errors.append(f"protected issue {issue} receipt absent")
            continue
        try:
            receipt = load_json(receipt_path)
            state_path = item.get("required_state_path")
            if not isinstance(state_path, list) or not all(isinstance(x, str) and x for x in state_path):
                errors.append(f"protected issue {issue} state path invalid")
                continue
            observed = nested_get(receipt, state_path)
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            errors.append(f"protected issue {issue} receipt invalid: {exc}")
            continue
        if observed != item.get("required_state_value"):
            errors.append(f"protected issue {issue} guard state is stale: {observed!r}")
    return errors


def plan(issue: int, event: str, queue: dict[str, Any], guard: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    errors = validate_contract(queue, guard, root)
    if errors:
        raise ValueError("; ".join(errors))
    if event != "closed":
        raise ValueError("only closed events are accepted")

    current = queue["current"]
    if issue == current["active_issue"]:
        return {
            "decision": "REOPEN_REQUIRED",
            "issue": issue,
            "reason": f"issue is machine-active queue terminal order {current['active_order']}",
            "active_issue": current["active_issue"],
            "active_order": current["active_order"],
        }

    for protected in guard["protected_incomplete_issues"]:
        if protected["issue"] == issue:
            return {
                "decision": "REOPEN_REQUIRED",
                "issue": issue,
                "reason": protected["reason"],
                "active_issue": current["active_issue"],
                "active_order": current["active_order"],
            }

    return {
        "decision": "NO_ACTION",
        "issue": issue,
        "reason": "issue is neither current ACTIVE terminal nor tracked incomplete execution issue",
        "active_issue": current["active_issue"],
        "active_order": current["active_order"],
    }


def run_selftest(queue: dict[str, Any], guard: dict[str, Any]) -> list[str]:
    failures: list[str] = []

    for issue in (140, 146):
        try:
            result = plan(issue, "closed", queue, guard)
        except Exception as exc:  # pragma: no cover - reported below
            failures.append(f"expected reopen for {issue}: {exc}")
        else:
            if result["decision"] != "REOPEN_REQUIRED":
                failures.append(f"expected reopen for {issue}, got {result['decision']}")

    try:
        unrelated = plan(999999, "closed", queue, guard)
    except Exception as exc:
        failures.append(f"unrelated issue control failed: {exc}")
    else:
        if unrelated["decision"] != "NO_ACTION":
            failures.append("unrelated closed issue must be NO_ACTION")

    mutations: list[tuple[str, Any, str]] = []

    def two_active(q: dict[str, Any], g: dict[str, Any]) -> None:
        for item in q["items"]:
            if item.get("order") == 14:
                item["queue_state"] = "ACTIVE"
                return

    mutations.append(("two active", two_active, "exactly one ACTIVE"))

    def stale_anchor(q: dict[str, Any], g: dict[str, Any]) -> None:
        g["queue_anchor"]["active_order"] = 12

    mutations.append(("stale anchor", stale_anchor, "anchor is stale"))

    def fake_completion(q: dict[str, Any], g: dict[str, Any]) -> None:
        g["protected_incomplete_issues"][0]["required_state_value"] = "PASS"

    mutations.append(("fake completion", fake_completion, "guard state is stale"))

    def weaken_ceiling(q: dict[str, Any], g: dict[str, Any]) -> None:
        g["forbidden_actions"].remove("close_issue")

    mutations.append(("weaken ceiling", weaken_ceiling, "ceiling weakened"))

    for name, mutate, needle in mutations:
        q = copy.deepcopy(queue)
        g = copy.deepcopy(guard)
        mutate(q, g)
        errors = validate_contract(q, g)
        if not any(needle.lower() in err.lower() for err in errors):
            failures.append(f"control did not turn red: {name}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["plan", "check", "selftest"])
    parser.add_argument("--issue", type=int)
    parser.add_argument("--event", default="closed")
    args = parser.parse_args()

    try:
        queue = load_json(QUEUE_PATH)
        guard = load_json(GUARD_PATH)
        if args.command == "selftest":
            failures = run_selftest(queue, guard)
            if failures:
                for failure in failures:
                    print(f"FAIL: {failure}")
                return 1
            print("PASS: issue-state guard planted controls")
            return 0
        if args.command == "check":
            errors = validate_contract(queue, guard)
            if errors:
                for error in errors:
                    print(f"FAIL: {error}")
                return 2
            print("PASS: issue-state guard contract")
            return 0
        if args.issue is None:
            parser.error("--issue is required for plan")
        result = plan(args.issue, args.event, queue, guard)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
