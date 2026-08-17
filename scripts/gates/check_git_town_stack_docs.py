#!/usr/bin/env python3
"""Validate current molecular/process/external-evidence Stack snapshot.

This gate never executes Git Town. Exit 0/2/64.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "docs/git/stack-prs.index.json"
SCHEMA_PATH = ROOT / "docs/git/stack-prs.index.schema.json"
MONITOR = ROOT / "docs/architecture/tech-lead-shadow-monitor/README.md"
DOC_INDEX = ROOT / "docs/INDEX.md"
QUEUE = ROOT / "docs/traceability/local-handoff-execution-queue.json"

MAIN = "4655b18a150716ad7a3a0edbe3201fd2927eef80"
TREE = "849328ac84c770d5932a16b4a3a9f0946dff8dba"
SHARED_COMMIT = "86a02a8a79651696b77f5af2c0976939bed5bc84"
SHARED_BLOB = "714f1b0e3abb6d569f59c0eef18c09318d0886cf"
EXPECTED_MERGES = {
    153: "0e27c9898925259b58c136e01fa4de175ad75231",
    155: "9ec507f685c9f3d0fcf97238d036a22be92fddf5",
    156: "d45c1bd8e9f1ba9c92c6926173efd59a4dfdcf33",
    157: "ad0fdde3e46aa6ab6c59ced145bead7fa4fc72d3",
    158: "e67a803ba6d12f8141a1bed3a26d9ec928931e35",
    159: "1970a2a6db3b743a2ad9204bcf506e80dbfd799b",
    169: "8c911b998fdf77d1abdfa4bb4153b0a7a5eaa9cf",
    154: MAIN,
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class Fatal(Exception):
    pass


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Fatal(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise Fatal(f"{path}: object required")
    return value


def nodes(index: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        node
        for stack in index.get("stacks", [])
        if isinstance(stack, dict)
        for node in stack.get("nodes", [])
        if isinstance(node, dict)
    ]


def validate(
    index: dict[str, Any],
    schema: dict[str, Any],
    monitor_text: str,
    docs_text: str,
    queue: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if index.get("schema") != "bettor-arena/stack-pr-index/v3":
        errors.append("Stack schema drifted")
    if schema.get("properties", {}).get("schema", {}).get("const") != index.get("schema"):
        errors.append("Stack schema document disagrees with index")
    repo = index.get("repository", {})
    if (
        repo.get("full_name"),
        repo.get("repository_id"),
        repo.get("default_branch"),
        repo.get("observed_main_sha"),
        repo.get("observed_main_tree"),
    ) != ("ed3c/bettor-arena", 1330387399, "main", MAIN, TREE):
        errors.append("repository/main exact subject drifted")
    if repo.get("origin_relation") != "DIVERGED" or repo.get("origin_issue") != 172:
        errors.append("dual-origin divergence was hidden")
    shared = index.get("shared_skill", {})
    if (
        shared.get("repository"),
        shared.get("commit"),
        shared.get("blob"),
        shared.get("path"),
    ) != (
        "ed3c/skills-shared",
        SHARED_COMMIT,
        SHARED_BLOB,
        "skills/git-town-stacked-pr-worker/SKILL.md",
    ):
        errors.append("shared Git Town method identity drifted")
    git_town = index.get("git_town", {})
    if (
        git_town.get("method_state"),
        git_town.get("binary_state"),
        git_town.get("configuration_state"),
        git_town.get("live_no_push_sync_state"),
        git_town.get("publication_state"),
    ) != (
        "IMPLEMENTED",
        "ABSENT",
        "ABSENT",
        "NOT_EXERCISED",
        "NOT_EXERCISED",
    ):
        errors.append("Git Town runtime falsely promoted")
    if index.get("program") != {
        "issue": 61,
        "active_order": 13,
        "active_issue": 140,
        "convergence_issue": 68,
    }:
        errors.append("PDF program pointer drifted")
    if index.get("current_process") != {
        "active": "issue-172",
        "queue_path": "docs/traceability/local-handoff-execution-queue.json",
    }:
        errors.append("current process does not point to #172 canonical queue")

    all_nodes = nodes(index)
    ids = [node.get("id") for node in all_nodes]
    if len(ids) != len(set(ids)):
        errors.append("duplicate Stack node id")
    issue_owners: dict[int, list[str]] = {}
    pr_owners: dict[int, list[str]] = {}
    for node in all_nodes:
        issue = node.get("issue")
        pr = node.get("pr")
        if isinstance(issue, int):
            issue_owners.setdefault(issue, []).append(str(node.get("id")))
        if isinstance(pr, int):
            pr_owners.setdefault(pr, []).append(str(node.get("id")))
        for field in ("head_sha", "merge_commit_sha"):
            value = node.get(field)
            if value is not None and not SHA40.fullmatch(str(value)):
                errors.append(f"{node.get('id')}: invalid {field}")
        if not SHA40.fullmatch(str(node.get("rollback_subject"))):
            errors.append(f"{node.get('id')}: invalid rollback subject")
        for path in node.get("path_roots", []):
            if Path(path).is_absolute() or ".." in Path(path).parts:
                errors.append(f"{node.get('id')}: unsafe path root")
    if any(len(owners) > 1 for owners in pr_owners.values()):
        errors.append("duplicate PR ownership")

    pr_nodes = {node.get("pr"): node for node in all_nodes if isinstance(node.get("pr"), int)}
    for pr, merge in EXPECTED_MERGES.items():
        node = pr_nodes.get(pr)
        if not node:
            errors.append(f"PR #{pr} missing from denominator")
            continue
        if (
            node.get("merge_commit_sha"),
            node.get("state"),
            node.get("main_presence"),
        ) != (merge, "MERGED_TO_MAIN", "ON_MAIN"):
            errors.append(f"PR #{pr} merge/main state drifted")
        if node.get("relation") == "TRUE_CHILD":
            errors.append(f"PR #{pr} falsely serialized as true child")

    historical = pr_nodes.get(81)
    if (
        not historical
        or historical.get("relation") != "HISTORICAL"
        or historical.get("state") != "SUPERSEDED_HISTORICAL"
        or historical.get("main_presence") != "NOT_ON_MAIN"
    ):
        errors.append("PR #81 stale writer was not demoted to historical")

    issue_nodes = {node.get("issue"): node for node in all_nodes if node.get("kind") == "ISSUE_ONLY"}
    if (
        issue_nodes.get(172, {}).get("state") != "ACTIVE"
        or issue_nodes.get(172, {}).get("relation") != "PROCESS_DEPENDENCY"
    ):
        errors.append("#172 is not the active process dependency")
    for issue in (161, 146, 140):
        node = issue_nodes.get(issue, {})
        if node.get("state") != "BLOCKED_BY_PREDECESSOR" or node.get("relation") != "PROCESS_DEPENDENCY":
            errors.append(f"#{issue} predecessor block drifted")
    if issue_nodes.get(68, {}).get("state") != "FINAL_CONVERGENCE":
        errors.append("#68 is not final convergence")
    for issue in (173, 174, 175):
        if issue_nodes.get(issue, {}).get("relation") != "SIBLING":
            errors.append(f"#{issue} is not a path-disjoint sibling")

    conflicts = {item.get("id"): item for item in index.get("conflicts", [])}
    if conflicts.get("pr-81-stale-writer", {}).get("state") != "SUPERSEDED_HISTORICAL":
        errors.append("PR #81 writer conflict is not resolved historically")
    if conflicts.get("dual-local-handoff-queues", {}).get("state") != "RESOLVED_IN_CANDIDATE":
        errors.append("duplicate Local Handoff authority not resolved in candidate")

    if queue.get("current", {}).get("active_item") != "dual-origin-reconciliation":
        errors.append("Stack index and Local Handoff queue disagree")
    if "Molecular implementation and evidence index" not in monitor_text:
        errors.append("human molecular index missing")
    if "Current process DAG" not in monitor_text:
        errors.append("human process DAG missing")
    if "tech-lead-shadow-monitor/README.md" not in docs_text:
        errors.append("documentation index does not route to closure monitor")

    return errors


def selftest(
    index: dict[str, Any],
    schema: dict[str, Any],
    monitor: str,
    docs: str,
    queue: dict[str, Any],
) -> list[str]:
    failures: list[str] = []

    def case(name: str, mutate, needle: str) -> None:
        i, s, m, d, q = (
            copy.deepcopy(index),
            copy.deepcopy(schema),
            monitor,
            docs,
            copy.deepcopy(queue),
        )
        mutated = mutate(i, s, m, d, q)
        if isinstance(mutated, tuple):
            i, s, m, d, q = mutated
        errors = validate(i, s, m, d, q)
        if not any(needle.lower() in error.lower() for error in errors):
            failures.append(f"{name}: control did not turn red; errors={errors}")

    case("stale main", lambda i,s,m,d,q: (i["repository"].__setitem__("observed_main_sha","0"*40) or (i,s,m,d,q)), "subject drifted")
    case("Git Town false live", lambda i,s,m,d,q: (i["git_town"].__setitem__("live_no_push_sync_state","PASS") or (i,s,m,d,q)), "falsely promoted")
    case("missing PR", lambda i,s,m,d,q: (i["stacks"][0]["nodes"].pop() or (i,s,m,d,q)), "missing from denominator")
    case("fake true child", lambda i,s,m,d,q: (i["stacks"][0]["nodes"][0].__setitem__("relation","TRUE_CHILD") or (i,s,m,d,q)), "falsely serialized")
    case("PR81 active again", lambda i,s,m,d,q: (i["stacks"][3]["nodes"][0].__setitem__("state","OPEN") or (i,s,m,d,q)), "stale writer")
    case("172 complete without receipt", lambda i,s,m,d,q: (i["stacks"][1]["nodes"][0].__setitem__("state","MERGED_TO_MAIN") or (i,s,m,d,q)), "active process")
    case("174 serialized", lambda i,s,m,d,q: (i["stacks"][2]["nodes"][1].__setitem__("relation","TRUE_CHILD") or (i,s,m,d,q)), "not a path-disjoint sibling")
    case("duplicate queue unresolved", lambda i,s,m,d,q: (i["conflicts"][1].__setitem__("state","BLOCKED") or (i,s,m,d,q)), "not resolved")
    case("queue disagreement", lambda i,s,m,d,q: (q["current"].__setitem__("active_item","bettor-runtime-rebind") or (i,s,m,d,q)), "disagree")
    case("human index missing", lambda i,s,m,d,q: (i,s,m.replace("Molecular implementation and evidence index","gone"),d,q), "human molecular")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        index = load(root / INDEX.relative_to(ROOT))
        schema = load(root / SCHEMA_PATH.relative_to(ROOT))
        monitor = (root / MONITOR.relative_to(ROOT)).read_text(encoding="utf-8")
        docs = (root / DOC_INDEX.relative_to(ROOT)).read_text(encoding="utf-8")
        queue = load(root / QUEUE.relative_to(ROOT))
    except (Fatal, OSError) as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 64
    errors = (
        selftest(index, schema, monitor, docs, queue)
        if args.selftest
        else validate(index, schema, monitor, docs, queue)
    )
    if errors:
        for error in errors:
            print(f"GIT-TOWN-STACK-RED: {error}", file=sys.stderr)
        return 2
    if args.selftest:
        print("SELFTEST GREEN: current Stack snapshot controls (10 mutations)")
    else:
        print(
            "PASS: molecular/process Stack snapshot "
            f"(main={MAIN}, active=#172, merged_prs={len(EXPECTED_MERGES)})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
