#!/usr/bin/env python3
"""Compile an exact-subject Blindspots ledger into a bounded context plan.

The compiler is read-only with respect to source and SQLite. It validates the
repository commit/tree, re-reads every promoted source path from that commit,
and emits a bounded context plan. Analyzer/provider candidates without source
readback remain candidates and cannot become graph facts or absence proof.

Exit codes: 0 PASS, 2 deterministic refusal, 64 invalid input, 70 mechanism error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
from collections import deque
from pathlib import Path, PurePosixPath
from typing import Any

OK, REFUSED, INVALID, MECHANISM = 0, 2, 64, 70
REQUEST_SCHEMA = "bettor-arena/context-funnel-request/v1"
RESULT_SCHEMA = "bettor-arena/context-funnel-result/v1"
LENSES = {"source", "grepai", "scip-lsp", "tree-sitter", "test", "runtime"}


class Refusal(ValueError):
    pass


class Invalid(ValueError):
    pass


def require(condition: bool, message: str, *, invalid: bool = False) -> None:
    if condition:
        return
    if invalid:
        raise Invalid(message)
    raise Refusal(message)


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Invalid(f"ABSENT: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise Invalid(f"UNREADABLE_JSON: {path}: {exc}") from exc


def safe_path(value: str) -> str:
    path = PurePosixPath(value.replace("\\", "/"))
    require(bool(value) and not path.is_absolute() and ".." not in path.parts, f"unsafe source path: {value}")
    return str(path)


def validate_request(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict), "request must be an object", invalid=True)
    require(value.get("schema") == REQUEST_SCHEMA, "request schema drift", invalid=True)
    subject = value.get("subject")
    require(isinstance(subject, dict), "subject missing", invalid=True)
    require(set(subject) == {"repository", "commit", "tree"}, "subject key drift", invalid=True)
    require(isinstance(subject["repository"], str) and "/" in subject["repository"], "subject.repository invalid", invalid=True)
    for key in ("commit", "tree"):
        token = subject.get(key)
        require(isinstance(token, str) and len(token) == 40 and all(ch in "0123456789abcdef" for ch in token), f"subject.{key} invalid", invalid=True)
    language = value.get("language")
    require(isinstance(language, str) and language, "language missing", invalid=True)
    targets = value.get("targets")
    require(isinstance(targets, list) and targets and all(isinstance(item, str) and item for item in targets), "targets invalid", invalid=True)
    require(len(targets) == len(set(targets)), "duplicate target", invalid=True)
    lenses = value.get("required_lenses")
    require(isinstance(lenses, list) and lenses and set(lenses) <= LENSES and len(lenses) == len(set(lenses)), "required_lenses invalid", invalid=True)
    limits = value.get("limits")
    require(isinstance(limits, dict), "limits missing", invalid=True)
    expected = {"max_depth", "max_nodes", "max_paths", "max_output_bytes"}
    require(set(limits) == expected, "limits key drift", invalid=True)
    bounds = {
        "max_depth": (0, 8),
        "max_nodes": (1, 512),
        "max_paths": (1, 512),
        "max_output_bytes": (512, 1_048_576),
    }
    for key, (minimum, maximum) in bounds.items():
        number = limits[key]
        require(isinstance(number, int) and not isinstance(number, bool) and minimum <= number <= maximum, f"limits.{key} out of bounds", invalid=True)
    return value


def run_git(repo: Path, *args: str) -> bytes:
    try:
        completed = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=False)
    except OSError as exc:
        raise RuntimeError(str(exc)) from exc
    if completed.returncode != 0:
        raise Refusal(f"git {' '.join(args)} failed")
    return completed.stdout


def verify_repo_subject(repo: Path, subject: dict[str, str]) -> None:
    require(repo.is_dir(), "repository path absent", invalid=True)
    commit = run_git(repo, "rev-parse", f"{subject['commit']}^{{commit}}").decode().strip()
    tree = run_git(repo, "rev-parse", f"{subject['commit']}^{{tree}}").decode().strip()
    require(commit == subject["commit"], "repository commit mismatch")
    require(tree == subject["tree"], "repository tree mismatch")


def connect(path: Path) -> sqlite3.Connection:
    require(path.is_file(), f"ABSENT: {path}", invalid=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def read_db(db_path: Path, language: str) -> tuple[dict[str, str], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    with connect(db_path) as db:
        subject_rows = {row["key"]: row["value"] for row in db.execute("SELECT key,value FROM meta WHERE key IN ('repository','commit','tree')")}
        require(set(subject_rows) == {"repository", "commit", "tree"}, "database subject missing")
        observations = [dict(row) for row in db.execute("SELECT * FROM observations WHERE language=? ORDER BY observation_id", (language,))]
        coverage = {row["lens"]: dict(row) for row in db.execute("SELECT lens,language,state,freshness,tool_identity FROM coverage WHERE language=? ORDER BY lens", (language,))}
    return subject_rows, observations, coverage


def source_bytes(repo: Path, commit: str, path: str) -> bytes:
    return run_git(repo, "show", f"{commit}:{safe_path(path)}")


def validate_readback(repo: Path, subject: dict[str, str], observations: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    facts: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    failures: list[str] = []
    cache: dict[str, str] = {}
    for row in observations:
        path = safe_path(str(row["path"]))
        if path not in cache:
            try:
                cache[path] = sha256_bytes(source_bytes(repo, subject["commit"], path))
            except Refusal:
                failures.append(f"missing-source:{path}")
                cache[path] = ""
        current = cache[path]
        if current and current != row["source_sha256"]:
            failures.append(f"source-drift:{path}")
            continue
        if row["relation"] == "CANDIDATE":
            candidates.append(row)
            continue
        if row["readback"] != "CONFIRMED":
            failures.append(f"unread-back:{row['observation_id']}")
            continue
        facts.append(row)
    return facts, candidates, sorted(set(failures))


def bounded_traversal(targets: list[str], facts: list[dict[str, Any]], max_depth: int, max_nodes: int) -> tuple[list[str], list[dict[str, Any]]]:
    adjacency: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for row in facts:
        source, target = str(row["source"]), str(row["target"])
        adjacency.setdefault(source, []).append((target, row))
        adjacency.setdefault(target, []).append((source, row))
    queue = deque((target, 0) for target in targets)
    seen: set[str] = set()
    selected: dict[str, dict[str, Any]] = {}
    while queue:
        node, depth = queue.popleft()
        if node in seen:
            continue
        require(len(seen) < max_nodes, "max_nodes exceeded")
        seen.add(node)
        if depth >= max_depth:
            continue
        for neighbor, row in sorted(adjacency.get(node, []), key=lambda item: (item[0], item[1]["observation_id"])):
            selected[row["observation_id"]] = row
            if neighbor not in seen:
                queue.append((neighbor, depth + 1))
    return sorted(seen), [selected[key] for key in sorted(selected)]


def compile_plan(repo: Path, db_path: Path, request: dict[str, Any]) -> dict[str, Any]:
    validate_request(request)
    subject = request["subject"]
    verify_repo_subject(repo, subject)
    db_subject, observations, coverage = read_db(db_path, request["language"])
    require(db_subject == subject, "database/request subject mismatch")

    missing_lenses: list[str] = []
    for lens in request["required_lenses"]:
        item = coverage.get(lens)
        if item is None or item["state"] != "COMPLETE" or item["freshness"] != "FRESH":
            missing_lenses.append(lens)

    facts, candidates, readback_failures = validate_readback(repo, subject, observations)
    nodes, traversed = bounded_traversal(
        request["targets"],
        facts,
        request["limits"]["max_depth"],
        request["limits"]["max_nodes"],
    )
    require(len(traversed) <= request["limits"]["max_paths"], "max_paths exceeded")

    target_set = set(request["targets"])
    target_paths = sorted({row["path"] for row in facts if row["source"] in target_set or row["target"] in target_set})
    dependency_signatures = [
        {"source": row["source"], "target": row["target"], "relation": row["relation"], "lens": row["lens"], "path": row["path"], "evidence_id": row["observation_id"]}
        for row in traversed
    ]
    downstream_callsites = [item for item in dependency_signatures if item["target"] in target_set]
    test_paths = sorted({row["path"] for row in traversed if row["lens"] == "test" or PurePosixPath(row["path"]).name.startswith("test_") or "/tests/" in f"/{row['path']}"})
    candidate_anchors = [
        {"source": row["source"], "target": row["target"], "lens": row["lens"], "path": row["path"], "readback": row["readback"], "evidence_id": row["observation_id"]}
        for row in candidates
        if row["source"] in nodes or row["target"] in nodes or row["source"] in target_set or row["target"] in target_set
    ]

    if missing_lenses or readback_failures or not target_paths:
        state = "UNKNOWN"
    else:
        state = "PASS"
    result: dict[str, Any] = {
        "schema": RESULT_SCHEMA,
        "state": state,
        "subject": subject,
        "language": request["language"],
        "targets": request["targets"],
        "coverage": {
            "required_lenses": request["required_lenses"],
            "missing_or_unfresh_lenses": sorted(missing_lenses),
            "readback_failures": readback_failures,
        },
        "bounded_traversal": {
            "max_depth": request["limits"]["max_depth"],
            "max_nodes": request["limits"]["max_nodes"],
            "visited_nodes": nodes,
            "relation_count": len(dependency_signatures),
        },
        "context_plan": {
            "target_full_source": target_paths,
            "dependency_signatures": dependency_signatures,
            "downstream_callsites": downstream_callsites,
            "tests": test_paths,
            "candidate_anchors": candidate_anchors,
        },
        "authority": {
            "sqlite": "REBUILDABLE_PROJECTION",
            "candidate_anchors": "CANDIDATE_ONLY",
            "source_readback": "REQUIRED_FOR_FACTS",
            "advances_state": False,
        },
    }
    result["content_sha256"] = sha256_bytes(canonical(result))
    require(len(canonical(result)) <= request["limits"]["max_output_bytes"], "max_output_bytes exceeded")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("compile",))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = compile_plan(args.repo, args.db, load_json(args.request))
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return OK if result["state"] == "PASS" else REFUSED
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return REFUSED
    except Invalid as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return INVALID
    except (OSError, sqlite3.Error, RuntimeError) as exc:
        print(f"MECHANISM_ERROR: {exc}", file=sys.stderr)
        return MECHANISM


if __name__ == "__main__":
    raise SystemExit(main())
