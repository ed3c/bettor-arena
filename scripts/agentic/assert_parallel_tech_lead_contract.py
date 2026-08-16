#!/usr/bin/env python3
"""Assert this repository's Parallel Tech Lead adoption layer. Zero network.

The shared fan-out and DAG contracts live in skills-shared and are reached
through `.agents/skills` symlinks, which exist on a developer host and not on a
GitHub Actions runner. A consumer gate that executed the shared checker would
pass locally and fail in CI for an environment reason, so this asserts only what
can be decided from this repository's own files and records which shared
contract each artifact targets.

The rule this exists for is ACCEPTANCE_COMMAND_NOT_REAL. #146 asked for template
assertions to be replaced, because the staged bundle shipped
`REPLACE_WITH_REPOSITORY_TEST_COMMAND` and a contract whose oracle is a
placeholder passes every check while proving nothing.

Exit codes: 0 pass, 2 assertion failed, 64 unusable input, 70 evaluator defect.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
LAYER = REPO / ".agentic" / "parallel-tech-lead"
CONFIG = LAYER / "config.json"
PLAN = LAYER / "plan.example.json"
REQUIREMENTS = REPO / ".agents" / "shared-skills.requirements.json"

SHA40 = re.compile(r"^[0-9a-f]{40}$")
PLACEHOLDER = re.compile(r"REPLACE_WITH[A-Z_]*|TODO_BEFORE_USE|<FILL[^>]*>")
REQUIRED_HUMAN = {
    "semantic_conflict_resolution",
    "winner_admission",
    "merge_or_ship",
    "release_promotion",
}


class Refused(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def refuse(code: str, detail: str) -> None:
    raise Refused(code, detail)


def lease_overlap(left: str, right: str) -> bool:
    a = left.split("*", 1)[0].rstrip("/")
    b = right.split("*", 1)[0].rstrip("/")
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def check_no_placeholders(config: dict[str, Any], plan: dict[str, Any]) -> None:
    """A contract whose oracle is a placeholder passes everything and proves nothing.

    Scope is the two machine-readable bodies and not the prose beside them. The
    README and the architecture note both quote `REPLACE_WITH_REPOSITORY_TEST_COMMAND`
    on purpose, to say what this layer replaced; scanning them would make the
    checker refuse its own history. The contract is what executes, so the
    contract is what is scanned.
    """
    for name, body in (("config.json", config), ("plan.example.json", plan)):
        found = PLACEHOLDER.findall(json.dumps(body))
        if found:
            refuse(
                "PLACEHOLDER_IN_CONTRACT",
                f"{name} still carries {sorted(set(found))}; #146 exists because the "
                f"staged bundle shipped exactly this",
            )


def check_acceptance_is_real(config: dict[str, Any], repo: Path) -> None:
    """The acceptance command must name a file this repository actually has."""
    owned = config.get("repository_owned") or {}
    argv = owned.get("acceptance_command")
    if not isinstance(argv, list) or len(argv) < 2:
        refuse(
            "ACCEPTANCE_COMMAND_NOT_REAL",
            "repository_owned.acceptance_command must be an argv array",
        )
    target = next(
        (part for part in argv[1:] if "/" in part or part.endswith(".sh")), None
    )
    if target is None:
        refuse(
            "ACCEPTANCE_COMMAND_NOT_REAL",
            f"acceptance_command {argv} names no file in this repository",
        )
    if not (repo / target).is_file():
        refuse(
            "ACCEPTANCE_COMMAND_NOT_REAL",
            f"acceptance_command points at {target}, which does not exist here",
        )


def check_binding_claims(config: dict[str, Any], requirements: dict[str, Any]) -> None:
    """A `bound_here: true` claim is checked against the requirements file, not trusted."""
    declared = set(requirements.get("shared") or []) | set(
        requirements.get("repo_owned") or []
    )
    for target in config.get("targets_shared_contracts") or []:
        skill = target.get("skill")
        if not skill:
            refuse("CONTRACT_TARGET_MALFORMED", "a shared contract target has no skill")
        claimed = target.get("bound_here")
        if claimed is None:
            refuse(
                "CONTRACT_TARGET_MALFORMED",
                f"{skill} does not state whether it is bound here",
            )
        if claimed and skill not in declared:
            refuse(
                "SHARED_CONTRACT_UNBOUND_BUT_CLAIMED",
                f"{skill} is claimed bound but is absent from "
                f".agents/shared-skills.requirements.json",
            )
        if not claimed and not str(target.get("bound_note", "")).strip():
            refuse(
                "CONTRACT_TARGET_MALFORMED",
                f"{skill} is recorded unbound with no note saying what would bind it",
            )


def check_base_exists(plan: dict[str, Any], repo: Path) -> None:
    """A plan against a base this repository does not have is a plan about another tree."""
    base = plan.get("base") or {}
    for field in ("commit_sha", "tree_sha"):
        value = base.get(field)
        if not isinstance(value, str) or not SHA40.fullmatch(value):
            refuse(
                "BASE_NOT_IN_REPOSITORY",
                f"base.{field} must be a 40-character lowercase SHA",
            )
    if base.get("immutable") is not True:
        refuse("BASE_NOT_IN_REPOSITORY", "base.immutable must be true")
    result = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", base["commit_sha"] + "^{commit}"],
        capture_output=True,
    )
    if result.returncode != 0:
        refuse(
            "BASE_NOT_IN_REPOSITORY",
            f"base commit {base['commit_sha'][:12]} is not a commit in this repository",
        )


def check_leases(plan: dict[str, Any], config: dict[str, Any]) -> None:
    workers = plan.get("workers") or []
    if not workers:
        refuse("PLAN_MALFORMED", "the plan declares no Worker")

    by_id = {w["id"]: w for w in workers}

    def ancestors(worker_id: str, seen: set[str] | None = None) -> set[str]:
        seen = seen or set()
        for dependency in by_id[worker_id].get("depends_on") or []:
            if dependency not in seen:
                seen.add(dependency)
                ancestors(dependency, seen)
        return seen

    order = sorted(by_id)
    for index, left in enumerate(order):
        for right in order[index + 1 :]:
            if right in ancestors(left) or left in ancestors(right):
                continue
            if (
                by_id[left].get("role") == "competitor"
                and by_id[right].get("role") == "competitor"
            ):
                continue
            for left_path in by_id[left].get("writable_paths") or []:
                for right_path in by_id[right].get("writable_paths") or []:
                    if lease_overlap(left_path, right_path):
                        refuse(
                            "LEASE_OVERLAP",
                            f"{left} and {right} run concurrently and both write "
                            f"{left_path} / {right_path}",
                        )

    immutable = list(
        (config.get("repository_owned") or {}).get("immutable_paths") or []
    )
    immutable += list((plan.get("acceptance") or {}).get("immutable_paths") or [])
    for worker in workers:
        for lease in worker.get("writable_paths") or []:
            for protected in immutable:
                if lease_overlap(lease, protected):
                    refuse(
                        "ACCEPTANCE_PATH_WRITABLE",
                        f"{worker['id']} leases {lease}, which reaches the immutable "
                        f"path {protected}",
                    )


def check_convergence(plan: dict[str, Any]) -> None:
    workers = {w["id"]: w for w in plan.get("workers") or []}
    convergence = plan.get("convergence")
    declared = [w for w in workers.values() if w.get("role") == "convergence"]
    if convergence is None:
        if declared:
            refuse(
                "CONVERGENCE_MISSING_INPUT",
                f"{declared[0]['id']} holds the convergence role with no owner declared",
            )
        return
    owner = convergence.get("owner_worker_id")
    if owner not in workers:
        refuse(
            "CONVERGENCE_MISSING_INPUT", f"convergence owner {owner} is not a Worker"
        )
    missing = [
        i
        for i in convergence.get("inputs") or []
        if i not in (workers[owner].get("depends_on") or [])
    ]
    if missing:
        refuse(
            "CONVERGENCE_MISSING_INPUT",
            f"{owner} converges {missing} without depending on them, so it could start "
            f"before they exist",
        )


def check_human_boundary(plan: dict[str, Any], config: dict[str, Any]) -> None:
    for name, body in (("plan", plan), ("config", config)):
        declared = set(body.get("human_owned_operations") or [])
        missing = sorted(REQUIRED_HUMAN - declared)
        if missing:
            refuse("HUMAN_OPERATION_DROPPED", f"{name} drops {missing}")
    if plan.get("semantic_conflict_resolution") == "automatic":
        refuse(
            "HUMAN_OPERATION_DROPPED", "semantic_conflict_resolution must stay human"
        )
    if (plan.get("ranking") or {}).get("winner_admission") == "automatic":
        refuse("HUMAN_OPERATION_DROPPED", "winner_admission must stay human")


def validate(
    config: dict[str, Any],
    plan: dict[str, Any],
    requirements: dict[str, Any],
    repo: Path,
) -> None:
    check_no_placeholders(config, plan)
    check_acceptance_is_real(config, repo)
    check_binding_claims(config, requirements)
    check_base_exists(plan, repo)
    check_leases(plan, config)
    check_convergence(plan)
    check_human_boundary(plan, config)


def selftest(
    config: dict[str, Any],
    plan: dict[str, Any],
    requirements: dict[str, Any],
    repo: Path,
) -> int:
    try:
        validate(config, plan, requirements, repo)
    except Refused as failure:
        print(
            f"SELFTEST RED: committed layer already refused -- {failure}",
            file=sys.stderr,
        )
        return 2

    def mutate(
        target: str, fn: Any
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        trio = {
            "config": copy.deepcopy(config),
            "plan": copy.deepcopy(plan),
            "requirements": copy.deepcopy(requirements),
        }
        fn(trio[target])
        return trio["config"], trio["plan"], trio["requirements"]

    controls = [
        (
            "template-placeholder-returns",
            "PLACEHOLDER_IN_CONTRACT",
            mutate(
                "config",
                lambda d: d["repository_owned"].update(
                    {
                        "acceptance_command": [
                            "sh",
                            "REPLACE_WITH_REPOSITORY_TEST_COMMAND",
                        ]
                    }
                ),
            ),
        ),
        (
            "acceptance-command-not-a-file",
            "ACCEPTANCE_COMMAND_NOT_REAL",
            mutate(
                "config",
                lambda d: d["repository_owned"].update(
                    {"acceptance_command": ["sh", "scripts/gates/does_not_exist.sh"]}
                ),
            ),
        ),
        (
            "binding-claimed-but-absent",
            "SHARED_CONTRACT_UNBOUND_BUT_CLAIMED",
            mutate(
                "config",
                lambda d: d["targets_shared_contracts"][0].update({"bound_here": True}),
            ),
        ),
        (
            "base-not-a-commit-here",
            "BASE_NOT_IN_REPOSITORY",
            mutate("plan", lambda d: d["base"].update({"commit_sha": "0" * 40})),
        ),
        (
            "mutable-base",
            "BASE_NOT_IN_REPOSITORY",
            mutate("plan", lambda d: d["base"].update({"immutable": False})),
        ),
        (
            "siblings-share-a-path",
            "LEASE_OVERLAP",
            mutate(
                "plan",
                lambda d: d["workers"][1].update(
                    {"writable_paths": d["workers"][0]["writable_paths"]}
                ),
            ),
        ),
        (
            "worker-leases-the-gate",
            "ACCEPTANCE_PATH_WRITABLE",
            mutate(
                "plan",
                lambda d: d["workers"][0]["writable_paths"].append(
                    "scripts/gates/verify_modular_contracts.sh"
                ),
            ),
        ),
        (
            "convergence-without-dependency",
            "CONVERGENCE_MISSING_INPUT",
            mutate("plan", lambda d: d["workers"][2].update({"depends_on": []})),
        ),
        (
            "human-merge-dropped",
            "HUMAN_OPERATION_DROPPED",
            mutate(
                "plan",
                lambda d: d.update({"human_owned_operations": ["winner_admission"]}),
            ),
        ),
        (
            "automatic-winner",
            "HUMAN_OPERATION_DROPPED",
            mutate(
                "plan", lambda d: d["ranking"].update({"winner_admission": "automatic"})
            ),
        ),
    ]

    failed = 0
    for name, code, trio in controls:
        try:
            validate(trio[0], trio[1], trio[2], repo)
        except Refused as failure:
            if failure.code == code:
                print(f"REFUSED {code} ({name})")
                continue
            print(
                f"CONTROL FAILED {name}: expected {code}, got {failure.code}",
                file=sys.stderr,
            )
            failed += 1
            continue
        print(
            f"CONTROL FAILED {name}: expected {code}, nothing was refused",
            file=sys.stderr,
        )
        failed += 1

    if failed:
        return 2
    print(
        f"SELFTEST GREEN: committed layer admitted; {len(controls)} planted defects refused"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "mode", nargs="?", default="check", choices=["check", "selftest"]
    )
    args = parser.parse_args(argv)

    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        plan = json.loads(PLAN.read_text(encoding="utf-8"))
        requirements = json.loads(REQUIREMENTS.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"USAGE: {error}", file=sys.stderr)
        return 64
    except json.JSONDecodeError as error:
        print(f"USAGE: unparseable input: {error}", file=sys.stderr)
        return 64

    if args.mode == "selftest":
        return selftest(config, plan, requirements, REPO)

    try:
        validate(config, plan, requirements, REPO)
    except Refused as failure:
        print(
            f"PARALLEL TECH LEAD REFUSED {failure.code}: {failure.detail}",
            file=sys.stderr,
        )
        return 2
    except Exception as error:
        print(f"EVALUATOR FAILURE: {error!r}", file=sys.stderr)
        return 70

    bound = sum(1 for t in config["targets_shared_contracts"] if t.get("bound_here"))
    print(
        f"PARALLEL TECH LEAD CONTRACT PASS: {len(plan['workers'])} Worker(s), "
        f"acceptance {' '.join(config['repository_owned']['acceptance_command'])}, "
        f"{bound}/{len(config['targets_shared_contracts'])} shared contracts bound here"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
