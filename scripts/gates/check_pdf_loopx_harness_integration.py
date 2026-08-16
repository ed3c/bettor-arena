#!/usr/bin/env python3
"""Validate the LoopX Harness PDF → bettor-arena modular integration contract.

This verifier is intentionally repository-contained and zero-network. It checks
that the PDF is treated as a requirement/hypothesis source, that every admitted
claim maps to current modules, paths, state machines, and deterministic gates,
and that README/AGENTS routing agrees with the machine-readable contract.

Exit codes:
  0  checked-clean / expected self-test result
  2  contract or repository integration disagreement
 64  invalid invocation, missing root, or unreadable input
"""

from __future__ import annotations
import argparse
import copy
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Callable

EXIT_OK, EXIT_CHECK_FAILED, EXIT_FATAL = 0, 2, 64
SCHEMA_ID = "bettor-arena/pdf-loopx-harness-integration/v1"
SOURCE_TITLE = "LLM 泛化：模型權重與 Harness"
SOURCE_PAGES = 41
SHA40 = re.compile(r"^[0-9a-f]{40}$")
REQ_ID = re.compile(r"^LX-[0-9]{2}$")
DIR_ID = re.compile(r"^DIR-[A-Z0-9-]+$")
NODE_ID = re.compile(r"^[A-Z][A-Z0-9_-]*$")
REPO_ID = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ALLOWED_STATES = {
    "IMPLEMENTED",
    "PARTIAL",
    "NOT_IMPLEMENTED",
    "NOT_EXERCISED",
    "NOT_ADOPTED",
    "BLOCKED",
}
ALLOWED_STACK_STATES = {
    "MERGED_TO_MAIN",
    "OPEN_DIVERGED_SUPERSEDED_CANDIDATE",
    "OPEN_RED_EXACT_HEAD",
    "OPEN_DRAFT",
    "OPEN",
    "BRANCH_BEFORE_PR",
    "CLOSED_SUPERSEDED",
}
ALLOWED_COMMANDS = {"python3", "sh", "bun"}
FORBIDDEN_ARG_TOKENS = {"-c", "--command", "shell=true", "shell=True"}
SHELL_METACHARS = ("&&", "||", "$(", "`", "\n", "\r", ";", "|", ">", "<")
REQUIRED_REQUIREMENTS = {f"LX-{index:02d}" for index in range(1, 16)}
REQUIRED_PROMOTIONS = {
    "PDF prose or diagram -> runtime PASS",
    "provider installation or configuration -> provider health PASS",
    "fixture-only evaluator PASS -> live provider superiority",
    "Worker/model prose -> hard-gate verdict",
    "merged child PR -> bytes present on main without convergence",
    "LangGraph checkpoint -> canonical LoopX authority",
    "raw chain-of-thought -> durable episodic memory",
    "force_skip string -> automated admission or exception authority",
}
EXTERNAL_OWNERS = {
    "human/source",
    "automated-admission-controller",
    "skills-shared",
    "runtime-env",
    "host/provider",
    "human",
}


class ContractError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"ABSENT: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"UNREADABLE_JSON: {path}: {exc}") from exc


def safe_relative(value: str) -> bool:
    if not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and all(part not in {"", "."} for part in path.parts)
    )


def unique_strings(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    require(isinstance(value, list), f"{label}: array required")
    require(allow_empty or bool(value), f"{label}: must not be empty")
    require(
        all(isinstance(item, str) and item for item in value),
        f"{label}: strings required",
    )
    require(len(value) == len(set(value)), f"{label}: duplicate value")
    return value


def load_modules(root: Path) -> dict[str, dict[str, Any]]:
    modules = {}
    for path in sorted((root / ".arena/modules").glob("*/module.json")):
        value = load_json(path)
        mid = value.get("id")
        require(isinstance(mid, str) and mid, f"{path}: module id")
        require(mid not in modules, f"duplicate module id: {mid}")
        modules[mid] = value
    require(modules, "module catalog is empty")
    return modules


def validate_command(root: Path, argv: Any, label: str, *, check_files: bool) -> None:
    require(isinstance(argv, list) and len(argv) >= 2, f"{label}: typed argv required")
    require(
        all(isinstance(item, str) and item for item in argv),
        f"{label}: string argv required",
    )
    require(
        argv[0] in ALLOWED_COMMANDS, f"{label}: executable not allowlisted: {argv[0]}"
    )
    for item in argv[1:]:
        require(item not in FORBIDDEN_ARG_TOKENS, f"{label}: raw shell surface: {item}")
        require(
            not any(token in item for token in SHELL_METACHARS),
            f"{label}: shell metacharacter: {item}",
        )
    if check_files:
        for item in argv[1:]:
            if item.startswith(("scripts/", "proof_workflow/", "loopctl/", "tests/")):
                require((root / item).exists(), f"{label}: gate path absent: {item}")


def validate_requirements(
    root: Path,
    requirements: Any,
    modules: dict[str, dict[str, Any]],
    *,
    check_files: bool,
) -> None:
    require(
        isinstance(requirements, list) and requirements, "requirements: non-empty array"
    )
    seen = set()
    fields = {
        "id",
        "pdf_pages",
        "requirement",
        "owner_modules",
        "state_machines",
        "paths",
        "deterministic_gates",
        "status",
        "blockers",
        "corrections",
    }
    for item in requirements:
        require(
            isinstance(item, dict) and set(item) == fields,
            f"requirement fields drift: {item.get('id')}",
        )
        rid = item["id"]
        require(
            isinstance(rid, str) and REQ_ID.fullmatch(rid),
            f"invalid requirement id: {rid}",
        )
        require(rid not in seen, f"duplicate requirement id: {rid}")
        seen.add(rid)
        pages = item["pdf_pages"]
        require(
            isinstance(pages, list)
            and pages
            and all(
                isinstance(page, int) and 1 <= page <= SOURCE_PAGES for page in pages
            ),
            f"{rid}: invalid PDF page",
        )
        require(
            pages == sorted(set(pages)), f"{rid}: PDF pages must be unique and sorted"
        )
        require(
            isinstance(item["requirement"], str) and len(item["requirement"]) >= 12,
            f"{rid}: requirement text too short",
        )
        for owner in unique_strings(item["owner_modules"], f"{rid}.owner_modules"):
            require(owner in modules, f"{rid}: unknown owner module: {owner}")
        unique_strings(item["state_machines"], f"{rid}.state_machines")
        paths = unique_strings(item["paths"], f"{rid}.paths", allow_empty=True)
        for relative in paths:
            require(safe_relative(relative), f"{rid}: unsafe path: {relative}")
            require(
                not check_files or (root / relative).exists(),
                f"{rid}: path absent: {relative}",
            )
        gates = item["deterministic_gates"]
        require(isinstance(gates, list), f"{rid}.deterministic_gates: array required")
        for index, argv in enumerate(gates):
            validate_command(
                root, argv, f"{rid}.gate[{index}]", check_files=check_files
            )
        status = item["status"]
        require(status in ALLOWED_STATES, f"{rid}: invalid state: {status}")
        blockers = unique_strings(item["blockers"], f"{rid}.blockers", allow_empty=True)
        unique_strings(item["corrections"], f"{rid}.corrections")
        if status == "IMPLEMENTED":
            require(paths, f"{rid}: IMPLEMENTED requires current paths")
            require(gates, f"{rid}: IMPLEMENTED requires a deterministic gate")
            require(not blockers, f"{rid}: IMPLEMENTED cannot retain blockers")
        else:
            require(blockers, f"{rid}: non-IMPLEMENTED state requires blockers")
    require(
        seen == REQUIRED_REQUIREMENTS, f"requirement coverage drift: {sorted(seen)}"
    )


def validate_directories(
    root: Path, entries: Any, modules: dict[str, dict[str, Any]], *, check_files: bool
) -> None:
    require(
        isinstance(entries, list) and entries,
        "directory_state_machines: non-empty array",
    )
    ids = set()
    paths = set()
    fields = {
        "id",
        "path",
        "owner_module",
        "state_machine",
        "inputs",
        "outputs",
        "evidence",
        "status",
    }
    for item in entries:
        require(
            isinstance(item, dict) and set(item) == fields,
            f"directory fields drift: {item.get('id')}",
        )
        did = item["id"]
        path = item["path"]
        require(
            isinstance(did, str) and DIR_ID.fullmatch(did),
            f"invalid directory id: {did}",
        )
        require(did not in ids, f"duplicate directory id: {did}")
        ids.add(did)
        require(isinstance(path, str) and safe_relative(path), f"{did}: unsafe path")
        require(path not in paths, f"duplicate directory path: {path}")
        paths.add(path)
        require(
            not check_files or (root / path).exists(), f"{did}: path absent: {path}"
        )
        require(item["owner_module"] in modules, f"{did}: unknown owner module")
        require(
            isinstance(item["state_machine"], str)
            and "->" in item["state_machine"]
            and len(item["state_machine"]) >= 10,
            f"{did}: state transition chain required",
        )
        unique_strings(item["inputs"], f"{did}.inputs")
        unique_strings(item["outputs"], f"{did}.outputs")
        unique_strings(item["evidence"], f"{did}.evidence")
        require(item["status"] in ALLOWED_STATES, f"{did}: invalid state")


def detect_cycle(nodes: set[str], edges: list[dict[str, Any]]) -> None:
    graph = {node: [] for node in nodes}
    indegree = {node: 0 for node in nodes}
    for edge in edges:
        if edge["feedback"]:
            continue
        graph[edge["from"]].append(edge["to"])
        indegree[edge["to"]] += 1
    queue = [node for node, degree in indegree.items() if degree == 0]
    visited = 0
    while queue:
        node = queue.pop()
        visited += 1
        for target in graph[node]:
            indegree[target] -= 1
            if indegree[target] == 0:
                queue.append(target)
    require(visited == len(nodes), "data flow contains an unlabelled cycle")


def validate_flow(value: Any, modules: dict[str, dict[str, Any]]) -> None:
    require(
        isinstance(value, dict) and set(value) == {"nodes", "edges"}, "data_flow fields"
    )
    nodes_raw = value["nodes"]
    edges = value["edges"]
    require(isinstance(nodes_raw, list) and len(nodes_raw) >= 2, "data_flow.nodes")
    node_ids = set()
    for node in nodes_raw:
        require(
            isinstance(node, dict) and set(node) == {"id", "kind", "owner", "artifact"},
            "data flow node fields",
        )
        nid = node["id"]
        require(
            isinstance(nid, str) and NODE_ID.fullmatch(nid), f"invalid node id: {nid}"
        )
        require(nid not in node_ids, f"duplicate node id: {nid}")
        node_ids.add(nid)
        require(
            node["owner"] in modules or node["owner"] in EXTERNAL_OWNERS,
            f"{nid}: unknown data-flow owner: {node['owner']}",
        )
    require(isinstance(edges, list) and edges, "data_flow.edges")
    pairs = set()
    feedback_count = 0
    for edge in edges:
        require(
            isinstance(edge, dict) and set(edge) == {"from", "to", "type", "feedback"},
            "data flow edge fields",
        )
        require(
            edge["from"] in node_ids and edge["to"] in node_ids, "broken data-flow edge"
        )
        require(edge["from"] != edge["to"], "self edge forbidden")
        require(isinstance(edge["type"], str) and edge["type"], "edge type")
        require(isinstance(edge["feedback"], bool), "edge feedback flag")
        key = (edge["from"], edge["to"], edge["type"])
        require(key not in pairs, f"duplicate data-flow edge: {key}")
        pairs.add(key)
        feedback_count += int(edge["feedback"])
    require(feedback_count <= 1, "only one explicit memory feedback edge is admitted")
    detect_cycle(node_ids, edges)


def validate_stack(value: Any) -> None:
    require(
        isinstance(value, dict)
        and set(value) == {"snapshot_only", "authority", "entries"},
        "stack_snapshot fields",
    )
    require(
        value["snapshot_only"] is True,
        "stack snapshot must be explicitly non-authoritative",
    )
    require(
        isinstance(value["authority"], str)
        and "GitHub base/head" in value["authority"]
        and "exact-head" in value["authority"],
        "stack authority marker",
    )
    prs = set()
    heads = set()
    current = False
    for item in value["entries"]:
        require(
            isinstance(item, dict)
            and set(item) == {"pr", "role", "base", "head", "state", "on_main"},
            "stack entry fields",
        )
        pr = item["pr"]
        require(isinstance(pr, int) and pr >= 0, "stack PR number")
        require(pr not in prs, f"duplicate stack PR: {pr}")
        prs.add(pr)
        require(item["head"] not in heads, f"duplicate stack head: {item['head']}")
        heads.add(item["head"])
        require(item["state"] in ALLOWED_STACK_STATES, f"PR #{pr}: state")
        require(isinstance(item["on_main"], bool), f"PR #{pr}: on_main")
        if item["on_main"]:
            require(
                item["state"] == "MERGED_TO_MAIN", f"PR #{pr}: on_main state mismatch"
            )
        if item["head"] == "feat/pdf-loopx-modular-verifier-v1":
            current = True
            require(
                item["state"] in {"BRANCH_BEFORE_PR", "OPEN"},
                "current workstream state",
            )
    require(
        {43, 51, 53, 56, 57, 58} <= prs,
        f"stack snapshot missing PRs: {sorted({43, 51, 53, 56, 57, 58} - prs)}",
    )
    require(current, "stack snapshot missing current LoopX workstream")


def validate_documents(root: Path, markers: Any, *, check_files: bool) -> None:
    require(
        isinstance(markers, dict) and len(markers) >= 4, "required_document_markers"
    )
    for relative, expected in markers.items():
        require(
            isinstance(relative, str) and safe_relative(relative),
            f"unsafe document path: {relative}",
        )
        expected_markers = unique_strings(expected, f"markers[{relative}]")
        if check_files:
            path = root / relative
            require(path.is_file(), f"required document absent: {relative}")
            text = path.read_text(encoding="utf-8")
            for marker in expected_markers:
                require(marker in text, f"{relative}: missing marker: {marker}")


def validate_mechanisms(
    root: Path, modules: dict[str, dict[str, Any]], *, check_files: bool
) -> None:
    if not check_files:
        return
    runner = (
        root / ".agents/skills/harness-wiki/scripts/run_portable_skill.py"
    ).read_text(encoding="utf-8")
    require(
        "never accepts a raw" in runner, "portable runner raw-shell boundary missing"
    )
    require(
        "never writes LoopX" in runner,
        "portable runner state-authority boundary missing",
    )
    require("shell=True" not in runner, "portable runner contains shell=True")
    runtime = modules["agent-runtime-integration"]
    require(
        "portable_skill_execution" in runtime.get("components", {}),
        "agent-runtime module missing portable_skill_execution",
    )
    require(
        "skill-execution.runner/v1" in runtime.get("provides", []),
        "agent-runtime module missing runner capability",
    )
    require(
        "arena.stateless-mcp/v1" in modules["loop-runtime"].get("provides", []),
        "loop-runtime missing stateless MCP capability",
    )
    proof = modules["proof-kernel"].get("proof", {})
    require(proof.get("control"), "proof-kernel control is absent")
    require(proof.get("mutation"), "proof-kernel mutation instrument is absent")
    commands = load_json(root / "loopctl/contract.json").get("commands", [])
    require(
        any(item.get("loop") == "skill-execution" for item in commands),
        "loopctl public contract missing skill-execution",
    )


def validate_contract(root: Path, value: Any, *, check_files: bool = True) -> None:
    top = {
        "schema",
        "source",
        "audit_subject",
        "verdict",
        "requirements",
        "directory_state_machines",
        "data_flow",
        "stack_snapshot",
        "forbidden_promotions",
        "required_document_markers",
    }
    require(isinstance(value, dict) and set(value) == top, "top-level fields drifted")
    require(value["schema"] == SCHEMA_ID, f"schema must be {SCHEMA_ID}")
    source = value["source"]
    require(
        isinstance(source, dict)
        and set(source)
        == {"title", "page_count", "source_class", "locator", "authority"},
        "source fields",
    )
    require(source["title"] == SOURCE_TITLE, "source title drift")
    require(source["page_count"] == SOURCE_PAGES, "source page count drift")
    require(
        source["source_class"] == "REQUIREMENT_HYPOTHESIS", "source authority class"
    )
    require(
        "never repository or runtime evidence" in source["authority"],
        "source authority boundary",
    )
    subject = value["audit_subject"]
    require(
        isinstance(subject, dict) and set(subject) == {"repository", "commit", "tree"},
        "audit_subject fields",
    )
    require(
        REPO_ID.fullmatch(str(subject["repository"])) is not None, "audit repository"
    )
    require(SHA40.fullmatch(str(subject["commit"])) is not None, "audit commit")
    require(SHA40.fullmatch(str(subject["tree"])) is not None, "audit tree")
    verdict = value["verdict"]
    require(
        isinstance(verdict, dict)
        and set(verdict) == {"state", "summary", "full_physical_integration"},
        "verdict fields",
    )
    require(verdict["state"] in ALLOWED_STATES, "verdict state")
    require(
        isinstance(verdict["summary"], str) and len(verdict["summary"]) >= 80,
        "verdict summary",
    )
    require(
        verdict["full_physical_integration"]
        in {"PASS", "FAIL", "NOT_EXERCISED", "ABSENT"},
        "physical integration state",
    )
    require(
        verdict["full_physical_integration"] != "PASS",
        "physical integration cannot be PASS without live receipts",
    )
    modules = (
        load_modules(root)
        if check_files
        else {
            module: {"id": module}
            for module in {
                "arena-core",
                "loop-runtime",
                "proof-kernel",
                "agent-runtime-integration",
                "module-catalog",
                "knowledge-providers",
                "environment-contracts",
                "openwiki",
                "perfect-seed-factory",
                "code-truth-graph",
            }
        }
    )
    validate_requirements(root, value["requirements"], modules, check_files=check_files)
    validate_directories(
        root, value["directory_state_machines"], modules, check_files=check_files
    )
    validate_flow(value["data_flow"], modules)
    validate_stack(value["stack_snapshot"])
    promotions = unique_strings(value["forbidden_promotions"], "forbidden_promotions")
    require(
        set(promotions) == REQUIRED_PROMOTIONS, "forbidden-promotion coverage drift"
    )
    validate_documents(
        root, value["required_document_markers"], check_files=check_files
    )
    validate_mechanisms(root, modules, check_files=check_files)
    if check_files:
        require(
            load_json(
                root / "docs/architecture/pdf-loopx-harness.integration.schema.json"
            ).get("$id")
            == SCHEMA_ID,
            "JSON Schema id does not match integration manifest",
        )


def expect_failure(
    root: Path,
    value: dict[str, Any],
    mutation: Callable[[dict[str, Any]], None],
    text: str,
    name: str,
) -> None:
    candidate = copy.deepcopy(value)
    mutation(candidate)
    try:
        validate_contract(root, candidate, check_files=False)
    except ContractError as exc:
        require(text in str(exc), f"{name}: wrong failure: {exc}")
        return
    raise ContractError(f"{name}: mutation unexpectedly passed")


def selftest(root: Path, value: dict[str, Any]) -> dict[str, Any]:
    validate_contract(root, value, check_files=True)
    mutations = [
        (
            "duplicate-requirement",
            "duplicate requirement id",
            lambda x: x["requirements"].__setitem__(
                1, copy.deepcopy(x["requirements"][0])
            ),
        ),
        (
            "invalid-status",
            "invalid state",
            lambda x: x["requirements"][0].__setitem__("status", "DONE"),
        ),
        (
            "invalid-page",
            "invalid PDF page",
            lambda x: x["requirements"][0].__setitem__("pdf_pages", [0]),
        ),
        (
            "unknown-owner",
            "unknown owner module",
            lambda x: x["requirements"][0]["owner_modules"].__setitem__(0, "unknown"),
        ),
        (
            "path-traversal",
            "unsafe path",
            lambda x: x["requirements"][0]["paths"].__setitem__(0, "../secret"),
        ),
        (
            "raw-shell",
            "raw shell surface",
            lambda x: x["requirements"][0]["deterministic_gates"].__setitem__(
                0, ["sh", "-c", "pytest"]
            ),
        ),
        (
            "implemented-without-gate",
            "IMPLEMENTED requires a deterministic gate",
            lambda x: x["requirements"][1].__setitem__("deterministic_gates", []),
        ),
        (
            "partial-without-blocker",
            "non-IMPLEMENTED state requires blockers",
            lambda x: x["requirements"][0].__setitem__("blockers", []),
        ),
        (
            "broken-edge",
            "broken data-flow edge",
            lambda x: x["data_flow"]["edges"][0].__setitem__("to", "ABSENT_NODE"),
        ),
        (
            "unlabelled-cycle",
            "unlabelled cycle",
            lambda x: x["data_flow"]["edges"].append(
                {
                    "from": "AUTOMATION",
                    "to": "SOURCE",
                    "type": "cycle",
                    "feedback": False,
                }
            ),
        ),
        (
            "stack-on-main-drift",
            "on_main state mismatch",
            lambda x: x["stack_snapshot"]["entries"][0].__setitem__("state", "OPEN"),
        ),
        (
            "promotion-loss",
            "forbidden-promotion coverage drift",
            lambda x: x["forbidden_promotions"].pop(),
        ),
        (
            "physical-false-pass",
            "physical integration cannot be PASS",
            lambda x: x["verdict"].__setitem__("full_physical_integration", "PASS"),
        ),
    ]
    for name, text, mutation in mutations:
        expect_failure(root, value, mutation, text, name)
    return {"status": "PASS", "positive": 1, "mutations": len(mutations)}


def default_root() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_pdf_loopx_harness_integration.py")
    parser.add_argument("--root", type=Path, default=default_root())
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("docs/architecture/pdf-loopx-harness.integration.json"),
    )
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    manifest_path = (
        args.manifest if args.manifest.is_absolute() else root / args.manifest
    )
    try:
        require(root.is_dir(), f"repository root absent: {root}")
        value = load_json(manifest_path)
        result = selftest(root, value) if args.selftest else None
        if result is None:
            validate_contract(root, value, check_files=True)
            result = {
                "status": "PASS",
                "requirements": len(value["requirements"]),
                "directories": len(value["directory_state_machines"]),
                "verdict": value["verdict"]["state"],
                "physical": value["verdict"]["full_physical_integration"],
            }
    except ContractError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        print(
            json.dumps(payload, ensure_ascii=False, sort_keys=True)
            if args.json
            else f"PDF-LOOPX-INTEGRATION RED: {exc}",
            file=sys.stdout if args.json else sys.stderr,
        )
        return EXIT_CHECK_FAILED
    except (OSError, RuntimeError) as exc:
        payload = {"status": "FATAL", "error": str(exc)}
        print(
            json.dumps(payload, ensure_ascii=False, sort_keys=True)
            if args.json
            else f"PDF-LOOPX-INTEGRATION FATAL: {exc}",
            file=sys.stdout if args.json else sys.stderr,
        )
        return EXIT_FATAL
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    elif args.selftest:
        print(
            f"SELFTEST GREEN: LoopX PDF integration ({result['positive']} positive, {result['mutations']} mutations)"
        )
    else:
        print(
            f"PASS LoopX PDF modular integration contract: {result['requirements']} requirements, {result['directories']} directories, verdict={result['verdict']}, physical={result['physical']}"
        )
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
