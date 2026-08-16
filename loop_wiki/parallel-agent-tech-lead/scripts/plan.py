#!/usr/bin/env python3
"""Validate and compile Bettor Tech Lead fan-out plans.

This is a consumer-side instance compiler. The canonical generic fan-out law
stays in ed3c/skills-shared; this file binds one immutable upstream contract and
adds Bettor repository invariants. It never creates branches/worktrees, launches
Agents, calls Git Town, publishes, merges, or resolves semantic conflicts.

Exit codes: 0 PASS, 2 deterministic refusal, 64 invalid input, 70 mechanism error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
from typing import Any

OK, REFUSED, INVALID, MECHANISM = 0, 2, 64, 70
SCHEMA = "bettor-arena/tech-lead-plan/v1"
UPSTREAM_REPO = "ed3c/skills-shared"
UPSTREAM_COMMIT = "82a59bc9d253d9d77ea8bbdc493dd3689b423f52"
UPSTREAM_SCHEMA = "skills/git-town-stacked-pr-worker/references/FAN_OUT_CONTRACT.schema.json"
UPSTREAM_SCHEMA_BLOB = "e00bbb99fdb1a8888ff6fd03ce792254319e2697"
MODES = {"TOURNAMENT", "COOPERATIVE", "SERIAL_STACK", "HYBRID"}
ROLES = {"competitor", "sibling", "child", "convergence"}
FOCUSES = {"minimal-diff", "architecture-types", "defensive-boundaries", "performance-security"}
REQUIRED_HUMAN = {"semantic_conflict_resolution", "winner_admission", "merge_or_ship", "release_promotion"}
FORBIDDEN_REQUIRED_PROVIDERS = {"code-graph-rag", "code_graph_rag", "codegraphrag"}


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


def is_sha(value: Any, size: int) -> bool:
    return isinstance(value, str) and len(value) == size and all(ch in "0123456789abcdef" for ch in value)


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Invalid(f"ABSENT: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise Invalid(f"UNREADABLE_JSON: {path}: {exc}") from exc


def safe_path(value: Any) -> str:
    require(isinstance(value, str) and value, "path must be non-empty", invalid=True)
    path = PurePosixPath(value.replace("\\", "/"))
    require(not path.is_absolute() and ".." not in path.parts, f"unsafe path: {value}", invalid=True)
    return str(path)


def path_overlap(left: str, right: str) -> bool:
    a = left.split("*", 1)[0].rstrip("/")
    b = right.split("*", 1)[0].rstrip("/")
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def infer_mode(workers: list[dict[str, Any]]) -> str:
    has_competitors = any(worker.get("role") == "competitor" for worker in workers)
    has_non_competitor_parallel = any(worker.get("role") == "sibling" for worker in workers)
    has_dependency = any(worker.get("depends_on") for worker in workers if worker.get("role") != "convergence")
    if has_competitors and (has_non_competitor_parallel or has_dependency):
        return "HYBRID"
    if has_competitors:
        return "TOURNAMENT"
    if has_dependency or any(worker.get("role") == "child" for worker in workers):
        return "SERIAL_STACK"
    return "COOPERATIVE"


def ancestors(worker_id: str, workers: dict[str, dict[str, Any]], seen: set[str] | None = None) -> set[str]:
    out = set() if seen is None else seen
    for dependency in workers[worker_id].get("depends_on", []):
        if dependency not in out:
            out.add(dependency)
            ancestors(dependency, workers, out)
    return out


def validate(plan: Any) -> dict[str, Any]:
    require(isinstance(plan, dict), "plan must be object", invalid=True)
    require(plan.get("schema") == SCHEMA, "plan schema drift", invalid=True)
    require(plan.get("repository") == "ed3c/bettor-arena", "repository drift")
    upstream = plan.get("upstream_contract")
    require(isinstance(upstream, dict), "upstream_contract missing", invalid=True)
    require(upstream.get("repository") == UPSTREAM_REPO, "upstream repository drift")
    require(upstream.get("commit") == UPSTREAM_COMMIT, "upstream fan-out contract commit drift")
    require(upstream.get("schema_path") == UPSTREAM_SCHEMA, "upstream fan-out schema path drift")
    require(upstream.get("schema_blob") == UPSTREAM_SCHEMA_BLOB, "upstream fan-out schema blob drift")

    base = plan.get("base")
    require(isinstance(base, dict), "base missing", invalid=True)
    require(base.get("immutable") is True, "MUTABLE_BASE")
    require(is_sha(base.get("commit"), 40) and is_sha(base.get("tree"), 40), "base commit/tree invalid", invalid=True)

    context = plan.get("context")
    require(isinstance(context, dict), "context missing", invalid=True)
    require(is_sha(context.get("digest"), 64), "context digest invalid", invalid=True)
    funnel = context.get("compiler_truth_funnel")
    require(isinstance(funnel, dict), "compiler_truth_funnel missing", invalid=True)
    require(funnel.get("state") == "PASS", "CONTEXT_FUNNEL_NOT_PASS")
    require(isinstance(funnel.get("receipt"), str) and funnel["receipt"], "CONTEXT_FUNNEL_STATE_LAUNDERED")
    require(is_sha(funnel.get("digest"), 64), "context funnel digest invalid", invalid=True)
    for provider in context.get("providers", []):
        require(isinstance(provider, dict), "provider entry invalid", invalid=True)
        name = str(provider.get("name", "")).strip().lower()
        if name in FORBIDDEN_REQUIRED_PROVIDERS and provider.get("required") is True:
            raise Refusal("FORBIDDEN_CONTEXT_PROVIDER")

    budgets = plan.get("budgets")
    require(isinstance(budgets, dict), "budgets missing", invalid=True)
    for key in ("max_workers", "max_tokens_per_worker", "max_wall_clock_seconds", "max_retries_per_worker", "max_processes_per_worker", "max_output_bytes_per_worker"):
        value = budgets.get(key)
        require(isinstance(value, int) and not isinstance(value, bool) and value >= 0, f"budgets.{key} invalid", invalid=True)
    require(budgets["max_workers"] > 0 and budgets["max_tokens_per_worker"] > 0 and budgets["max_wall_clock_seconds"] > 0 and budgets["max_processes_per_worker"] > 0 and budgets["max_output_bytes_per_worker"] > 0, "zero worker budget")
    require(isinstance(budgets.get("circuit_breakers"), list) and budgets["circuit_breakers"], "circuit_breakers missing", invalid=True)

    acceptance = plan.get("acceptance")
    require(isinstance(acceptance, dict), "acceptance missing", invalid=True)
    immutable = acceptance.get("immutable_paths")
    oracles = acceptance.get("oracles")
    require(isinstance(immutable, list) and immutable, "immutable acceptance paths missing", invalid=True)
    require(isinstance(oracles, list) and len(oracles) >= 2, "at least two acceptance oracles required", invalid=True)
    immutable = [safe_path(path) for path in immutable]

    worker_list = plan.get("workers")
    require(isinstance(worker_list, list) and worker_list, "workers missing", invalid=True)
    require(len(worker_list) <= budgets["max_workers"], "WORKER_BUDGET_OVERFLOW")
    workers: dict[str, dict[str, Any]] = {}
    branches: set[str] = set()
    for index, worker in enumerate(worker_list):
        require(isinstance(worker, dict), f"workers[{index}] invalid", invalid=True)
        worker_id = worker.get("id")
        require(isinstance(worker_id, str) and worker_id and worker_id not in workers, "worker id invalid/duplicate", invalid=True)
        workers[worker_id] = worker
        require(worker.get("role") in ROLES, f"{worker_id}: role invalid", invalid=True)
        branch = worker.get("branch")
        require(isinstance(branch, str) and branch and branch not in branches, f"{worker_id}: branch invalid/duplicate", invalid=True)
        branches.add(branch)
        require(worker.get("parent") == base.get("branch") or worker.get("parent") in branches or isinstance(worker.get("parent"), str), f"{worker_id}: parent missing", invalid=True)
        deps = worker.get("depends_on")
        require(isinstance(deps, list), f"{worker_id}: depends_on invalid", invalid=True)
        writable = worker.get("writable_paths")
        require(isinstance(writable, list) and writable, f"{worker_id}: writable_paths missing", invalid=True)
        worker["writable_paths"] = [safe_path(path) for path in writable]
        read_only = worker.get("read_only_paths", [])
        require(isinstance(read_only, list), f"{worker_id}: read_only_paths invalid", invalid=True)
        worker["read_only_paths"] = [safe_path(path) for path in read_only]
        require(worker.get("context_digest") == context["digest"], f"{worker_id}: CONTEXT_DIGEST_MISMATCH")
        require(isinstance(worker.get("token_budget"), int) and 0 < worker["token_budget"] <= budgets["max_tokens_per_worker"], f"{worker_id}: WORKER_BUDGET_OVERFLOW")
        require(isinstance(worker.get("timeout_seconds"), int) and 0 < worker["timeout_seconds"] <= budgets["max_wall_clock_seconds"], f"{worker_id}: timeout overflow")
        require(isinstance(worker.get("process_budget"), int) and 0 < worker["process_budget"] <= budgets["max_processes_per_worker"], f"{worker_id}: process overflow")
        require(isinstance(worker.get("output_byte_budget"), int) and 0 < worker["output_byte_budget"] <= budgets["max_output_bytes_per_worker"], f"{worker_id}: output overflow")
        for lease in worker["writable_paths"]:
            for protected in immutable:
                require(not path_overlap(lease, protected), f"{worker_id}: ACCEPTANCE_TEST_MUTATED")

    for worker in worker_list:
        for dependency in worker["depends_on"]:
            require(dependency in workers and dependency != worker["id"], f"{worker['id']}: UNDECLARED_DEPENDENCY")
        require(worker["id"] not in ancestors(worker["id"], workers), "DAG_CYCLE")
        if worker["role"] == "child":
            require(worker["depends_on"], f"{worker['id']}: child lacks dependency")
            require(worker.get("consumes_contracts") or worker.get("consumes_paths"), f"{worker['id']}: FAKE_LINEAR_CHILD")
        if worker["role"] == "sibling":
            require(not worker["depends_on"], f"{worker['id']}: sibling has dependency")

    competitor_focus: set[str] = set()
    competitors = [worker for worker in worker_list if worker["role"] == "competitor"]
    for worker in competitors:
        require(not worker["depends_on"], f"{worker['id']}: competitor dependency")
        require(worker.get("focus") in FOCUSES and worker["focus"] not in competitor_focus, f"{worker['id']}: MISSING_BRANCH_FOCUS")
        competitor_focus.add(worker["focus"])

    for left_index, left in enumerate(worker_list):
        for right in worker_list[left_index + 1:]:
            if right["id"] in ancestors(left["id"], workers) or left["id"] in ancestors(right["id"], workers):
                continue
            if left["role"] == right["role"] == "competitor":
                continue
            for left_path in left["writable_paths"]:
                for right_path in right["writable_paths"]:
                    require(not path_overlap(left_path, right_path), f"PATH_OVERLAP: {left['id']} / {right['id']}")

    inferred = infer_mode(worker_list)
    require(plan.get("mode") in MODES, "mode invalid", invalid=True)
    require(plan["mode"] == inferred, f"MODE_MISMATCH: declared {plan['mode']} inferred {inferred}")

    convergence = [worker for worker in worker_list if worker["role"] == "convergence"]
    require(len(convergence) <= 1, "CONVERGENCE_OWNER_AMBIGUOUS")
    if convergence:
        conv = convergence[0]
        leaves = {worker["id"] for worker in worker_list if worker["role"] != "convergence"}
        require(leaves <= set(conv["depends_on"]), "PREMATURE_CONVERGENCE")

    human = set(plan.get("human_owned_operations") or [])
    require(REQUIRED_HUMAN <= human, "AUTOMATIC_SEMANTIC_RESOLUTION")
    authority = plan.get("automation", {})
    require(isinstance(authority, dict), "automation missing", invalid=True)
    for key in ("auto_publish", "auto_merge", "auto_resolve_semantic_conflicts", "auto_promote"):
        require(authority.get(key) is False, f"AUTOMATION_AUTHORITY_ESCALATION: {key}")

    return {"status": "PASS", "mode": inferred, "workers": len(worker_list), "context_digest": context["digest"], "upstream_commit": UPSTREAM_COMMIT}


def compile_receipt(plan: dict[str, Any]) -> dict[str, Any]:
    summary = validate(plan)
    packets = []
    for worker in sorted(plan["workers"], key=lambda item: item["id"]):
        packets.append({
            "worker_id": worker["id"],
            "branch": worker["branch"],
            "role": worker["role"],
            "depends_on": sorted(worker["depends_on"]),
            "writable_paths": sorted(worker["writable_paths"]),
            "read_only_paths": sorted(worker.get("read_only_paths", [])),
            "context_digest": worker["context_digest"],
            "budgets": {
                "tokens": worker["token_budget"],
                "timeout_seconds": worker["timeout_seconds"],
                "processes": worker["process_budget"],
                "output_bytes": worker["output_byte_budget"],
            },
            "authority": "LEASED_WORKER_ONLY",
        })
    receipt = {
        "schema": "bettor-arena/tech-lead-plan-receipt/v1",
        "status": "PASS",
        "plan_sha256": digest(plan),
        "mode": summary["mode"],
        "base": plan["base"],
        "context_digest": plan["context"]["digest"],
        "upstream_contract": plan["upstream_contract"],
        "worker_packets": packets,
        "execution_state": "NOT_EXERCISED",
        "git_town_state": "NOT_EXERCISED",
        "forgejo_state": "NOT_EXERCISED",
        "publication_state": "NOT_EXERCISED",
    }
    receipt["content_sha256"] = digest(receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("validate", "compile"))
    parser.add_argument("plan", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        plan = load(args.plan)
        output = validate(plan) if args.command == "validate" else compile_receipt(plan)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(output, ensure_ascii=False, sort_keys=True))
        return OK
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return REFUSED
    except Invalid as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return INVALID
    except OSError as exc:
        print(f"MECHANISM_ERROR: {exc}", file=sys.stderr)
        return MECHANISM


if __name__ == "__main__":
    raise SystemExit(main())
