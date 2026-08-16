#!/usr/bin/env python3
"""Offline hard gate for Bettor's Agentic Tech Lead Skill binding."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

BINDING = Path(".skill-bindings/agentic-tech-lead-orchestration/binding.json")
README = BINDING.parent / "README.md"
ASSERTIONS = BINDING.parent / "assertions.md"
INDEX = Path(".skill-bindings/README.md")
WORKFLOW = Path(".github/workflows/agentic-tech-lead-binding.yml")
SUITE = Path("tests/agentic-tech-lead-binding/run-all.sh")
CHECKER = Path("scripts/gates/check_agentic_tech_lead_binding.py")
MANIFEST = Path("docs/knowledge-providers/providers/code-graph-rag.json")
REGISTRY = Path("docs/knowledge-providers/registry.json")
STATES = {
    "PASS", "FAIL", "ABSENT", "NOT_IMPLEMENTED",
    "NOT_EXERCISED", "SKIPPED_BY_POLICY",
}
ROLES = {
    "INTENT_ANCHOR": (
        "grepai", ".arena/modules/knowledge-providers",
        "knowledge-providers", "1.2.0", "NOT_EXERCISED",
        "CANDIDATE_ONLY",
    ),
    "DETERMINISTIC_GRAPH": (
        "scip-sqlite", ".arena/modules/code-truth-graph-v2",
        "code-truth-graph-v2", "1.0.0", "NOT_IMPLEMENTED",
        "EXACT_ONLY_WITH_SUBJECT_COVERAGE_READBACK",
    ),
    "STRUCTURAL_SLICER": (
        "tree-sitter", ".arena/modules/code-truth-graph-v2",
        "code-truth-graph-v2", "1.0.0", "NOT_IMPLEMENTED",
        "STRUCTURE_ONLY",
    ),
    "CONTEXT_ASSEMBLY": (
        "loopx-context-assembly", ".arena/modules/loopx-context-assembly",
        "loopx-context-assembly", "1.0.0", "NOT_EXERCISED",
        "PROMPT_IR_ONLY",
    ),
    "AGENT_EXECUTOR": (
        "serena", ".arena/modules/knowledge-providers",
        "knowledge-providers", "1.2.0", "NOT_EXERCISED",
        "BOUNDED_WORKER_ONLY",
    ),
    "VECTOR_CANDIDATE_STORE": (
        "lancedb", ".arena/modules/loopx-notes-retrieval",
        "loopx-notes-retrieval", "1.0.0", "NOT_IMPLEMENTED",
        "CANDIDATE_ONLY",
    ),
    "WORKER_FANOUT": (
        "loopx-worker-fleet", ".arena/modules/loopx-worker-fleet",
        "loopx-worker-fleet", "1.0.0", "NOT_EXERCISED",
        "LEASED_EXECUTION_ONLY",
    ),
    "STACK_DELIVERY": (
        "git-town", ".arena/modules/git-town-runtime",
        "git-town-runtime", "1.0.0", "ABSENT", "NO_EXECUTION",
    ),
}
HUMAN = {
    "provider activation", "semantic conflict admission",
    "remote publication", "merge", "promotion", "rollback",
}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SECRET = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)"
    r"\s*[:=]\s*[\"']?(sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9]{12,})"
)
USER_PATH = re.compile(r"/(?:Users|home)/[^/\s`]+/")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def digest(value: dict[str, Any]) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def exact(obj: dict[str, Any], key: str, expected: Any, errors: list[str]) -> None:
    if obj.get(key) != expected:
        errors.append(f"{key} must equal {expected!r}")


def validate_value(value: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    exact(value, "schema_version", "agentic-tech-lead-bettor-binding/v1", errors)
    exact(
        value, "source_proposal",
        {"title": "AI 编程新范式：并行 Agent 体验", "trust": "SOURCE_PROPOSAL"},
        errors,
    )

    consumer = value.get("consumer", {})
    if not isinstance(consumer, dict):
        return ["consumer must be an object"]
    expected_consumer = {
        "repository": "ed3c/bettor-arena",
        "base_commit": "a626899cc469afd8dba95e99fbffadeeec911f58",
        "base_tree": "f63aaf6960358603badd1bdd713f04fcdd2aedba",
        "active_issue": 92,
    }
    for key, expected in expected_consumer.items():
        exact(consumer, key, expected, errors)
    for key in ("base_commit", "base_tree"):
        if not SHA40.fullmatch(str(consumer.get(key, ""))):
            errors.append(f"consumer.{key} must be SHA-40")

    skill = value.get("skill", {})
    if not isinstance(skill, dict):
        return errors + ["skill must be an object"]
    expected_skill = {
        "name": "agentic-tech-lead-orchestration",
        "canonical_repository": "ed3c/skills-shared",
        "candidate_branch": "agent/agentic-tech-lead-controls-v1",
        "candidate_commit": "ee7aaa55ab5b779a813f78a266569d6b53ddc7b8",
        "candidate_tree": "674de1eafe1def98849b316c3df7664955d38caf",
        "candidate_state": "NOT_EXERCISED",
        "registry_classification": "ABSENT",
        "projection_state": "ABSENT",
        "copied_body": False,
    }
    for key, expected in expected_skill.items():
        exact(skill, key, expected, errors)
    for key in ("candidate_commit", "candidate_tree"):
        if not SHA40.fullmatch(str(skill.get(key, ""))):
            errors.append(f"skill.{key} must be SHA-40")
    for key in ("candidate_state", "registry_classification", "projection_state"):
        if skill.get(key) not in STATES:
            errors.append(f"skill.{key} state unsupported")

    orchestration = value.get("orchestration", {})
    expected_orchestration = {
        "default_mode": "STACK", "tournament_mode": "CONTRACT_ONLY",
        "max_workers": 3, "max_repairs_per_signature": 3,
        "one_writer_per_path": True, "path_disjoint_parallelism": True,
        "true_child_requires_parent_bytes": True,
        "immutable_acceptance_oracles": True,
    }
    for key, expected in expected_orchestration.items():
        exact(orchestration, key, expected, errors)

    intelligence = value.get("code_intelligence", {})
    expected_intelligence = {
        "intent_anchor": "grepai", "deterministic_graph": "scip-sqlite",
        "metadata_store": "sqlite", "structural_slicer": "tree-sitter",
        "vector_candidate_store": "lancedb",
        "historical_code_graph_rag_state": "REJECTED",
        "no_double_graph": True, "source_readback_required": True,
        "existing_reference_adapter": "python-ast",
        "existing_reference_adapter_is_scip": False,
    }
    for key, expected in expected_intelligence.items():
        exact(intelligence, key, expected, errors)

    modules = value.get("modules", [])
    if not isinstance(modules, list):
        return errors + ["modules must be an array"]
    by_role: dict[str, dict[str, Any]] = {}
    for item in modules:
        if not isinstance(item, dict) or not isinstance(item.get("role"), str):
            errors.append("module role missing")
            continue
        role = item["role"]
        if role in by_role:
            errors.append(f"duplicate role {role}")
        by_role[role] = item
        if item.get("binding_state") not in STATES:
            errors.append(f"{role}.binding_state unsupported")
        if item.get("runtime_state") not in STATES:
            errors.append(f"{role}.runtime_state unsupported")
        if item.get("provider") == "code-graph-rag":
            errors.append("active Code-Graph-RAG provider forbidden")
    if set(by_role) != set(ROLES):
        errors.append("module role set drifted")
    keys = (
        "provider", "owner", "module_id", "interface_version",
        "runtime_state", "authority",
    )
    for role, expected in ROLES.items():
        item = by_role.get(role, {})
        for key, wanted in zip(keys, expected):
            if item.get(key) != wanted:
                errors.append(f"{role}.{key} must equal {wanted!r}")
        if item.get("binding_state") != "PASS":
            errors.append(f"{role}.binding_state must equal 'PASS'")
    limitation = by_role.get("DETERMINISTIC_GRAPH", {}).get("limitation")
    if limitation != "The existing Python AST reference adapter is not SCIP.":
        errors.append("DETERMINISTIC_GRAPH limitation missing")

    automation = value.get("automation", {})
    for key in (
        "auto_restack", "auto_publish", "auto_resolve_conflicts",
        "auto_merge", "provider_state_write", "worker_state_write",
    ):
        if automation.get(key) is not False:
            errors.append(f"automation.{key} must be false")

    forbidden = value.get("forbidden", {})
    if forbidden.get("active_providers") != ["code-graph-rag"]:
        errors.append("forbidden.active_providers drifted")
    for key in (
        "double_graph", "test_assertion_mutation",
        "semantic_conflict_resolution", "force_push",
        "remote_publication", "merge", "promotion", "rollback",
    ):
        if forbidden.get(key) is not True:
            errors.append(f"forbidden.{key} must be true")
    if set(value.get("human_owned", [])) != HUMAN:
        errors.append("human_owned set drifted")
    if value.get("verification") != {
        "checker": CHECKER.as_posix(),
        "suite": SUITE.as_posix(),
        "workflow": WORKFLOW.as_posix(),
    }:
        errors.append("verification routes drifted")
    return errors


def validate_repo(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        binding = load(root / BINDING)
    except Exception as exc:
        return [str(exc)]
    errors.extend(validate_value(binding))

    for item in binding.get("modules", []):
        owner = root / item["owner"]
        manifest_path = owner / "module.json"
        if not manifest_path.is_file():
            errors.append(f"{manifest_path.relative_to(root)} ABSENT")
            continue
        manifest = load(manifest_path)
        if manifest.get("id") != item["module_id"]:
            errors.append(f"{manifest_path.relative_to(root)} id mismatch")
        if manifest.get("interface_version") != item["interface_version"]:
            errors.append(f"{manifest_path.relative_to(root)} version mismatch")

    try:
        manifest = load(root / MANIFEST)
        registry = load(root / REGISTRY)
    except Exception as exc:
        errors.append(str(exc))
    else:
        admission = manifest.get("admission", {})
        if manifest.get("provider_id") != "code-graph-rag":
            errors.append("historical provider identity drifted")
        if admission != {
            "state": "REJECTED", "runtime_state": "ABSENT", "live_claim": False
        }:
            errors.append("historical Code-Graph-RAG must be REJECTED/ABSENT")
        entries = [
            item for item in registry.get("providers", [])
            if isinstance(item, dict) and item.get("id") == "code-graph-rag"
        ]
        if len(entries) != 1 or entries[0].get("digest") != digest(manifest):
            errors.append("historical Code-Graph-RAG registry digest mismatch")

    for relative in (README, ASSERTIONS, INDEX, CHECKER, SUITE, WORKFLOW):
        if not (root / relative).is_file():
            errors.append(f"{relative} ABSENT")
    if (root / README).is_file():
        text = (root / README).read_text(encoding="utf-8")
        for heading in (
            "## Authority and source identity", "## State machine",
            "## Data flow", "## Domain module map",
            "## Evidence boundary", "## Verification",
        ):
            if heading not in text:
                errors.append(f"{README}: missing {heading}")
    if (root / ASSERTIONS).is_file():
        text = (root / ASSERTIONS).read_text(encoding="utf-8")
        for number in range(1, 13):
            ident = f"ATL-BIND-{number:03d}"
            if ident not in text:
                errors.append(f"{ASSERTIONS}: missing {ident}")
    if (root / INDEX).is_file() and (
        "agentic-tech-lead-orchestration/README.md"
        not in (root / INDEX).read_text(encoding="utf-8")
    ):
        errors.append(f"{INDEX}: route ABSENT")
    if (root / BINDING.parent / "SKILL.md").exists():
        errors.append("copied shared SKILL.md forbidden")
    for projection in (
        ".agents/skills/agentic-tech-lead-orchestration",
        ".claude/skills/agentic-tech-lead-orchestration",
    ):
        if (root / projection).exists():
            errors.append(f"{projection} must remain ABSENT")
    if (root / ".git-town.toml").exists():
        errors.append(".git-town.toml must remain ABSENT")
    if (root / WORKFLOW).is_file():
        workflow = (root / WORKFLOW).read_text(encoding="utf-8")
        if CHECKER.as_posix() not in workflow:
            errors.append("workflow checker route ABSENT")
        if "persist-credentials: false" not in workflow:
            errors.append("workflow must disable persisted credentials")
        if "contents: write" in workflow or "pull-requests: write" in workflow:
            errors.append("workflow write permission forbidden")

    for path in [root / BINDING.parent, root / INDEX, root / WORKFLOW]:
        files = list(path.rglob("*")) if path.is_dir() else [path]
        for file in files:
            if not file.is_file():
                continue
            text = file.read_text(encoding="utf-8")
            if SECRET.search(text):
                errors.append(f"{file.relative_to(root)} secret-shaped material")
            if USER_PATH.search(text):
                errors.append(f"{file.relative_to(root)} user path forbidden")
    return errors


def selftest(root: Path) -> list[str]:
    base = load(root / BINDING)
    failures: list[str] = []
    cases = [
        ("copied body", lambda x: x["skill"].__setitem__("copied_body", True),
         "copied_body"),
        ("candidate promoted", lambda x: x["skill"].__setitem__(
            "candidate_state", "PASS"), "candidate_state"),
        ("active old graph", lambda x: x["modules"][0].__setitem__(
            "provider", "code-graph-rag"), "Code-Graph-RAG"),
        ("AST mislabeled SCIP", lambda x: x["code_intelligence"].__setitem__(
            "existing_reference_adapter_is_scip", True),
         "existing_reference_adapter_is_scip"),
        ("SCIP invented", lambda x: x["modules"][1].__setitem__(
            "runtime_state", "PASS"), "DETERMINISTIC_GRAPH.runtime_state"),
        ("Git Town invented", lambda x: x["modules"][-1].__setitem__(
            "runtime_state", "NOT_EXERCISED"), "STACK_DELIVERY.runtime_state"),
        ("auto merge", lambda x: x["automation"].__setitem__(
            "auto_merge", True), "automation.auto_merge"),
        ("Human boundary", lambda x: x.__setitem__(
            "human_owned", [v for v in x["human_owned"] if v != "rollback"]),
         "human_owned"),
    ]
    if validate_value(base):
        failures.append(f"positive binding failed: {validate_value(base)}")
    for name, mutate, needle in cases:
        candidate = copy.deepcopy(base)
        mutate(candidate)
        observed = validate_value(candidate)
        if not any(needle in error for error in observed):
            failures.append(f"{name}: expected {needle!r}, got {observed!r}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    errors = selftest(args.root) if args.selftest else validate_repo(args.root)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print(
        "agentic-tech-lead binding selftest: PASS"
        if args.selftest else "agentic-tech-lead binding: PASS"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
