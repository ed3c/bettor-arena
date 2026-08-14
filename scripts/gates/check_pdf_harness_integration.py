#!/usr/bin/env python3
"""Validate the PDF Harness integration audit, directory map, and Stack index.

This is an offline documentation/control-plane gate. It does not launch an LLM,
a provider, a worker, or a network request.

Exit codes:
  0: audit contracts agree with the exact checked-out tree
  2: a checked invariant disagrees
 64: invalid invocation or unreadable input
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Callable

OK = 0
CHECK_FAILED = 2
FATAL = 64

MATRIX = Path("docs/architecture/pdf-harness-integration.matrix.json")
AUDIT = Path("docs/architecture/PDF_HARNESS_INTEGRATION_AUDIT.md")
DIRECTORY_MAP = Path("docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md")
STACK_INDEX = Path("docs/traceability/STACK_PR_INDEX.md")
REQUIREMENTS = Path(".arena/compositions/bettor-arena.requirements.json")
LOCK = Path(".arena/locks/bettor-arena.lock.json")
RELEASE = Path("data/module-proof/release-receipt.json")
ENTRYPOINTS = Path("docs/architecture/agent-entrypoints.contract.json")
README_COVERAGE = Path("docs/architecture/readme-coverage.contract.json")
MACRO_CONTEXT = Path(".arena/contexts/macro.json")
SHARED_SKILLS = Path(".agents/shared-skills.requirements.json")

ALLOWED_STATES = {
    "PASS",
    "FAIL",
    "ABSENT",
    "IMPLEMENTED",
    "NOT_IMPLEMENTED",
    "NOT_EXERCISED",
    "SKIPPED_BY_POLICY",
}


class AuditError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def read_json(root: Path, path: Path) -> Any:
    try:
        return json.loads((root / path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise AuditError(f"ABSENT: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"UNREADABLE_JSON: {path}: {exc}") from exc


def read_text(root: Path, path: Path) -> str:
    try:
        return (root / path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise AuditError(f"ABSENT: {path}") from exc
    except OSError as exc:
        raise AuditError(f"UNREADABLE_TEXT: {path}: {exc}") from exc


def module_ids(value: Any, label: str) -> set[str]:
    require(isinstance(value, dict), f"{label}: object required")
    modules = value.get("modules")
    require(isinstance(modules, list) and modules, f"{label}: modules missing")
    result: set[str] = set()
    for entry in modules:
        require(isinstance(entry, dict), f"{label}: module entry must be object")
        module_id = entry.get("id")
        require(isinstance(module_id, str) and module_id, f"{label}: module id missing")
        require(module_id not in result, f"{label}: duplicate module id: {module_id}")
        result.add(module_id)
    return result


def component_by_id(matrix: dict[str, Any], component_id: str) -> dict[str, Any]:
    for component in matrix.get("components", []):
        if component.get("id") == component_id:
            return component
    raise AuditError(f"matrix component missing: {component_id}")


def validate_matrix_shape(matrix: Any) -> dict[str, Any]:
    require(isinstance(matrix, dict), "matrix must be an object")
    require(
        matrix.get("schema") == "bettor-arena/pdf-harness-integration-matrix/v1",
        "matrix schema drift",
    )
    source = matrix.get("source")
    require(isinstance(source, dict), "matrix source missing")
    require(source.get("kind") == "ATTACHED_PDF_SOURCE_PROPOSAL", "PDF source kind")
    require(source.get("authority") == "SOURCE_PROPOSAL_ONLY", "PDF authority")
    require(source.get("pages") == 41, "PDF page count must remain 41")
    require(source.get("repository_copy") == "ABSENT", "repository copy state")

    assessment = matrix.get("assessment")
    require(isinstance(assessment, dict), "assessment missing")
    require(
        assessment.get("full_pdf_target") == "NOT_IMPLEMENTED",
        "full PDF target overclaimed",
    )
    require(
        assessment.get("modular_foundation") == "IMPLEMENTED",
        "modular foundation state",
    )
    require(
        isinstance(assessment.get("claim"), str) and assessment["claim"],
        "assessment claim",
    )

    components = matrix.get("components")
    require(isinstance(components, list) and components, "components missing")
    seen: set[str] = set()
    for component in components:
        require(isinstance(component, dict), "component must be object")
        component_id = component.get("id")
        state = component.get("state")
        require(isinstance(component_id, str) and component_id, "component id")
        require(component_id not in seen, f"duplicate component: {component_id}")
        seen.add(component_id)
        require(state in ALLOWED_STATES, f"{component_id}: invalid state {state!r}")
        require(
            isinstance(component.get("owner"), str), f"{component_id}: owner missing"
        )
        require(
            isinstance(component.get("pdf_pages"), str),
            f"{component_id}: PDF page locator",
        )

    required_ids = {
        "module-control-plane",
        "hard-gates-and-evidence",
        "host-owned-skill-execution",
        "context-capsules-and-driver-projections",
        "openwiki-static-knowledge-compilation",
        "code-truth-graph",
        "knowledge-provider-contracts",
        "runtime-contract-projection",
        "loopx-objective-todos-gates-evidence-quota-kernel",
        "langgraph-strategy-and-hitl",
        "externalized-episodic-memory",
        "heterogeneous-worker-live-matrix",
        "serena-grepai-live-provider-canaries",
        "code-graph-rag-and-mem0-runtime",
        "herdr-tmux-worker-fleet",
        "cloud-local-execution-fabric",
        "langfuse-opentelemetry-observability",
        "harness-console",
    }
    require(
        required_ids <= seen,
        f"matrix missing components: {sorted(required_ids - seen)}",
    )
    return matrix


def validate_component_paths(root: Path, matrix: dict[str, Any]) -> None:
    for component in matrix["components"]:
        component_id = component["id"]
        state = component["state"]
        evidence_paths = component.get("evidence_paths", [])
        absent_paths = component.get("expected_absent_paths", [])
        require(isinstance(evidence_paths, list), f"{component_id}: evidence_paths")
        require(
            isinstance(absent_paths, list), f"{component_id}: expected_absent_paths"
        )

        if state == "IMPLEMENTED":
            require(
                evidence_paths, f"{component_id}: IMPLEMENTED without evidence paths"
            )
            for raw in evidence_paths:
                path = Path(raw)
                require(
                    (root / path).exists(),
                    f"{component_id}: implemented path absent: {path}",
                )
        elif state == "NOT_EXERCISED":
            require(
                evidence_paths, f"{component_id}: NOT_EXERCISED without mechanism paths"
            )
            for raw in evidence_paths:
                path = Path(raw)
                require(
                    (root / path).exists(),
                    f"{component_id}: mechanism path absent: {path}",
                )
        elif state in {"NOT_IMPLEMENTED", "ABSENT"}:
            require(
                absent_paths,
                f"{component_id}: non-implemented state without absence probes",
            )
            for raw in absent_paths:
                path = Path(raw)
                require(
                    not (root / path).exists(),
                    f"{component_id}: expected absent path exists: {path}",
                )


def validate_module_sets(requirements: Any, lock: Any, release: Any) -> set[str]:
    desired = module_ids(requirements, "requirements")
    locked = module_ids(lock, "composition lock")
    released = module_ids(release, "release receipt")
    require(
        desired == locked,
        f"module-set drift: requirements={sorted(desired)} lock={sorted(locked)}",
    )
    require(
        locked == released,
        f"module-set drift: lock={sorted(locked)} release={sorted(released)}",
    )
    return desired


def validate_module_files(root: Path, modules: set[str]) -> None:
    for module_id in sorted(modules):
        manifest = root / ".arena/modules" / module_id / "module.json"
        readme = root / ".arena/modules" / module_id / "README.md"
        require(
            manifest.is_file(), f"module manifest absent: {manifest.relative_to(root)}"
        )
        require(readme.is_file(), f"module README absent: {readme.relative_to(root)}")
        value = read_json(root, manifest.relative_to(root))
        require(value.get("id") == module_id, f"module manifest id drift: {module_id}")
        require(
            isinstance(value.get("interface_version"), str),
            f"{module_id}: interface_version",
        )


def require_markers(text: str, label: str, markers: list[str]) -> None:
    for marker in markers:
        require(marker in text, f"{label}: missing marker: {marker}")


def validate_readme_text(readme: str, modules: set[str]) -> None:
    require_markers(
        readme,
        "README.md",
        [
            "PDF Harness Integration verdict",
            "Directory → State Machine ownership",
            "Missing LoopX control flow",
            "Molecular Stack PR index",
            "PASS ≠ FAIL ≠ ABSENT ≠ NOT_IMPLEMENTED ≠ NOT_EXERCISED",
        ],
    )
    for module_id in modules:
        require(
            f"`{module_id}`" in readme, f"README.md: module not indexed: {module_id}"
        )


def validate_stack_text(stack: str, matrix: dict[str, Any]) -> None:
    require_markers(
        stack,
        str(STACK_INDEX),
        [
            "Git Town status",
            "Four-repository documentation convergence",
            "Modular platform implementation spine",
            "Skill, host execution and provider spine",
            "Open terminal leaves required by the PDF target",
            "#56",
            "#53",
            "#24",
            "integration/pdf-harness-convergence-v1",
        ],
    )
    tokens = matrix.get("required_stack_tokens")
    require(isinstance(tokens, list) and tokens, "required_stack_tokens missing")
    for token in tokens:
        require(token in stack, f"Stack index missing token: {token}")


def validate_git_town(
    root: Path, matrix: dict[str, Any], shared_skills: dict[str, Any]
) -> None:
    state = matrix.get("git_town")
    require(isinstance(state, dict), "git_town matrix section missing")
    paths = state.get("configuration_paths")
    require(isinstance(paths, list) and paths, "git_town configuration paths")
    present = [path for path in paths if (root / path).exists()]
    expected_state = state.get("repository_config")
    if expected_state == "ABSENT":
        require(
            not present, f"Git Town config appeared without matrix update: {present}"
        )
    else:
        require(bool(present), "Git Town claimed configured but no config exists")

    shared = shared_skills.get("shared", [])
    require(isinstance(shared, list), "shared Skill list")
    selected = "git-town-stacked-pr-worker" in shared
    expected_skill = state.get("selected_shared_skill")
    if expected_skill == "ABSENT":
        require(
            not selected, "git-town-stacked-pr-worker selected without matrix update"
        )
    else:
        require(selected, "Git Town Skill claimed but not selected")
    require(
        state.get("molecular_delivery_policy") == "IMPLEMENTED",
        "molecular delivery policy",
    )


def validate_docs(root: Path, matrix: dict[str, Any], modules: set[str]) -> None:
    routes = matrix.get("required_document_routes")
    require(isinstance(routes, list) and routes, "required_document_routes missing")
    for raw in routes:
        require((root / raw).is_file(), f"required PDF route absent: {raw}")

    readme = read_text(root, Path("README.md"))
    agents = read_text(root, Path("AGENTS.md"))
    claude = read_text(root, Path("CLAUDE.md"))
    audit = read_text(root, AUDIT)
    directory_map = read_text(root, DIRECTORY_MAP)
    stack = read_text(root, STACK_INDEX)

    validate_readme_text(readme, modules)
    require_markers(
        agents,
        "AGENTS.md",
        [
            "PDF Harness verification protocol",
            str(AUDIT),
            str(DIRECTORY_MAP),
            str(STACK_INDEX),
            "scripts/gates/check_pdf_harness_integration.py",
            "strategy graph proposes",
            "LoopX reducer alone commits",
        ],
    )
    require_markers(
        claude,
        "CLAUDE.md",
        [str(AUDIT), str(DIRECTORY_MAP), str(STACK_INDEX), "Claude Code 不得"],
    )
    require_markers(
        audit,
        str(AUDIT),
        [
            "Bettor has modularly integrated a large part",
            "Exact drift found at audit start",
            "Rejected source shortcuts",
            "Required state-machine leaves",
            "complete PDF architecture",
        ],
    )
    require_markers(
        directory_map,
        str(DIRECTORY_MAP),
        [
            "Directory → State Machine ownership map",
            "Missing LoopX state machine",
            "strategy graph proposes",
            "LoopX reducer alone commits",
        ],
    )
    validate_stack_text(stack, matrix)


def validate_contract_routes(root: Path) -> None:
    entrypoints = read_json(root, ENTRYPOINTS)
    canonical = entrypoints.get("canonical_documents", [])
    require(str(AUDIT) in canonical, "agent entrypoints omit PDF audit")
    require(str(DIRECTORY_MAP) in canonical, "agent entrypoints omit directory map")
    require(str(STACK_INDEX) in canonical, "agent entrypoints omit Stack index")

    for filename in ("AGENTS.md", "CLAUDE.md"):
        config = entrypoints.get("entrypoints", {}).get(filename)
        require(isinstance(config, dict), f"entrypoint contract missing: {filename}")
        content = read_text(root, Path(filename))
        for marker in config.get("required_markers", []):
            require(
                marker in content, f"{filename}: entrypoint marker missing: {marker}"
            )

    coverage = read_json(root, README_COVERAGE)
    required_readmes = coverage.get("required_readmes", [])
    require(
        isinstance(required_readmes, list) and required_readmes, "README coverage list"
    )
    for raw in required_readmes:
        require((root / raw).is_file(), f"README coverage path absent: {raw}")
    markers = coverage.get("required_markers", {})
    for raw, values in markers.items():
        text = read_text(root, Path(raw))
        for marker in values:
            require(marker in text, f"{raw}: README contract marker missing: {marker}")

    macro = read_json(root, MACRO_CONTEXT)
    common = macro.get("common", [])
    require(str(AUDIT) in common, "macro context omits PDF audit")
    require(str(DIRECTORY_MAP) in common, "macro context omits directory map")
    require(str(STACK_INDEX) in common, "macro context omits Stack index")
    for raw in common:
        require((root / raw).is_file(), f"macro context path absent: {raw}")


def validate_repository(root: Path) -> dict[str, Any]:
    matrix = validate_matrix_shape(read_json(root, MATRIX))
    requirements = read_json(root, REQUIREMENTS)
    lock = read_json(root, LOCK)
    release = read_json(root, RELEASE)
    shared_skills = read_json(root, SHARED_SKILLS)

    modules = validate_module_sets(requirements, lock, release)
    validate_module_files(root, modules)
    validate_component_paths(root, matrix)
    validate_git_town(root, matrix, shared_skills)
    validate_docs(root, matrix, modules)
    validate_contract_routes(root)

    return {
        "status": "PASS",
        "source_authority": matrix["source"]["authority"],
        "pdf_pages": matrix["source"]["pages"],
        "full_pdf_target": matrix["assessment"]["full_pdf_target"],
        "modular_foundation": matrix["assessment"]["modular_foundation"],
        "module_count": len(modules),
        "component_count": len(matrix["components"]),
        "git_town": matrix["git_town"]["repository_config"],
    }


def expect_failure(name: str, action: Callable[[], None], expected: str) -> None:
    try:
        action()
    except AuditError as exc:
        require(expected in str(exc), f"{name}: wrong failure: {exc}")
        return
    raise AuditError(f"{name}: mutation unexpectedly passed")


def run_selftest(root: Path) -> dict[str, Any]:
    matrix = validate_matrix_shape(read_json(root, MATRIX))
    requirements = read_json(root, REQUIREMENTS)
    lock = read_json(root, LOCK)
    release = read_json(root, RELEASE)
    shared_skills = read_json(root, SHARED_SKILLS)
    modules = module_ids(requirements, "requirements")
    readme = read_text(root, Path("README.md"))
    stack = read_text(root, STACK_INDEX)

    outcomes: list[str] = []

    bad_lock = copy.deepcopy(lock)
    bad_lock["modules"] = bad_lock["modules"][:-1]
    expect_failure(
        "module-set-drift",
        lambda: validate_module_sets(requirements, bad_lock, release),
        "module-set drift",
    )
    outcomes.append("module-set-drift")

    false_loopx = copy.deepcopy(matrix)
    component_by_id(false_loopx, "loopx-objective-todos-gates-evidence-quota-kernel")[
        "state"
    ] = "IMPLEMENTED"
    expect_failure(
        "false-loopx-implemented",
        lambda: validate_component_paths(root, false_loopx),
        "IMPLEMENTED without evidence paths",
    )
    outcomes.append("false-loopx-implemented")

    expect_failure(
        "readme-map-missing",
        lambda: validate_readme_text(
            readme.replace(
                "Directory → State Machine ownership", "Directory map removed"
            ),
            modules,
        ),
        "Directory → State Machine ownership",
    )
    outcomes.append("readme-map-missing")

    expect_failure(
        "stack-leaf-missing",
        lambda: validate_stack_text(stack.replace("#56", "#XX"), matrix),
        "#56",
    )
    outcomes.append("stack-leaf-missing")

    false_git_town = copy.deepcopy(matrix)
    false_git_town["git_town"]["repository_config"] = "IMPLEMENTED"
    expect_failure(
        "false-git-town-config",
        lambda: validate_git_town(root, false_git_town, shared_skills),
        "no config exists",
    )
    outcomes.append("false-git-town-config")

    return {"status": "PASS", "mutations": outcomes}


def find_root(explicit: str | None) -> Path:
    root = Path(explicit).resolve() if explicit else Path(__file__).resolve().parents[2]
    require((root / "AGENTS.md").is_file(), f"repository root not found: {root}")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        root = find_root(args.root)
        result = run_selftest(root) if args.selftest else validate_repository(root)
    except AuditError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(f"pdf-harness-integration FAIL: {exc}", file=sys.stderr)
        return CHECK_FAILED
    except (OSError, RuntimeError) as exc:
        payload = {"status": "FATAL", "error": str(exc)}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(f"pdf-harness-integration FATAL: {exc}", file=sys.stderr)
        return FATAL

    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif args.selftest:
        print(
            f"pdf-harness-integration selftest PASS: {len(result['mutations'])} mutations"
        )
    else:
        print(
            "pdf-harness-integration PASS: "
            f"{result['component_count']} components, {result['module_count']} modules, "
            f"foundation={result['modular_foundation']}, full_target={result['full_pdf_target']}, "
            f"git_town={result['git_town']}"
        )
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
