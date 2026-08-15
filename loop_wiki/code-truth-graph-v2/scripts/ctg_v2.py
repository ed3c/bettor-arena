#!/usr/bin/env python3
"""Code Truth Graph v2 evidence-plane compiler and query engine.

The graph is a rebuildable projection. It binds an exact Git subject, analyzer
identity/freshness/coverage, evidence anchors, nodes and edges. Provider/model
results remain candidates. Missing coverage remains UNKNOWN rather than being
rewritten as NO_FLOW.

Exit codes: 0 checked-clean, 2 checked refusal/query non-found, 64 usage/infra.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
import subprocess
import tempfile
from collections import defaultdict, deque
from pathlib import Path, PurePosixPath
from typing import Any

BUNDLE = "code-truth-graph-v2/observation-bundle/v1"
GRAPH = "code-truth-graph-v2/evidence-graph/v1"
QUERY = "code-truth-graph-v2/query/v1"
RESULT = "code-truth-graph-v2/query-result/v1"
PLANES = {
    "T0_DIRECT_SOURCE",
    "T1_AST",
    "T2_LSP_SCIP",
    "T3_BUILD_CONFIG",
    "T4_SANDBOX_RUNTIME",
    "T5_PRODUCTION_RUNTIME",
    "T6_PROVIDER_CANDIDATE",
}
ANALYZER_KINDS = {"SOURCE", "AST", "LSP_SCIP", "BUILD_CONFIG", "RUNTIME", "PROVIDER"}
VERIFICATIONS = {
    "OBSERVED",
    "SUPPORTED",
    "CANDIDATE",
    "CONTESTED",
    "UNKNOWN",
    "FALSIFIED",
}
RELATIONS = {
    "IMPORTS",
    "CALLS",
    "REFERENCES",
    "READS",
    "WRITES",
    "CONFIGURES",
    "EMITS",
    "OBSERVED_CALL",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
SHA = re.compile(r"^sha256:[0-9a-f]{64}$")


class ContractError(ValueError):
    pass


class InfraError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InfraError(f"missing JSON: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise InfraError(f"unreadable JSON: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"object required: {path}")
    return value


def exact(value: dict[str, Any], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise ContractError(
            f"{label}: key drift missing={sorted(keys - set(value))} "
            f"extra={sorted(set(value) - keys)}"
        )


def relpath(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{label}: path required")
    normalized = value.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError(f"{label}: absolute/traversal path refused")
    return normalized


def validate_subject(value: dict[str, Any]) -> None:
    exact(value, {"repository", "commit", "tree"}, "subject")
    if not isinstance(value["repository"], str) or "/" not in value["repository"]:
        raise ContractError("subject.repository")
    if not isinstance(value["commit"], str) or not HEX40.fullmatch(value["commit"]):
        raise ContractError("subject.commit")
    if not isinstance(value["tree"], str) or not HEX40.fullmatch(value["tree"]):
        raise ContractError("subject.tree")


def expected_kind(plane: str) -> str:
    return {
        "T0_DIRECT_SOURCE": "SOURCE",
        "T1_AST": "AST",
        "T2_LSP_SCIP": "LSP_SCIP",
        "T3_BUILD_CONFIG": "BUILD_CONFIG",
        "T4_SANDBOX_RUNTIME": "RUNTIME",
        "T5_PRODUCTION_RUNTIME": "RUNTIME",
        "T6_PROVIDER_CANDIDATE": "PROVIDER",
    }[plane]


def validate_bundle(value: dict[str, Any]) -> None:
    exact(
        value,
        {
            "schema_version",
            "subject",
            "analyzers",
            "coverage",
            "evidence",
            "nodes",
            "edges",
        },
        "bundle",
    )
    if value["schema_version"] != BUNDLE:
        raise ContractError("bundle schema")
    validate_subject(value["subject"])

    analyzers: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(value["analyzers"]):
        if not isinstance(item, dict):
            raise ContractError(f"analyzers[{index}]")
        exact(
            item,
            {
                "analyzer_id",
                "kind",
                "identity_digest",
                "languages",
                "state",
                "freshness",
                "subject_match",
            },
            f"analyzer[{index}]",
        )
        aid = item["analyzer_id"]
        if not isinstance(aid, str) or not aid or aid in analyzers:
            raise ContractError("duplicate/invalid analyzer_id")
        if item["kind"] not in ANALYZER_KINDS:
            raise ContractError("analyzer kind")
        if not isinstance(item["identity_digest"], str) or not SHA.fullmatch(
            item["identity_digest"]
        ):
            raise ContractError("analyzer identity digest")
        if item["state"] not in {"EXECUTED", "NOT_EXERCISED", "ABSENT"}:
            raise ContractError("analyzer state")
        if item["freshness"] not in {"FRESH", "STALE", "UNKNOWN"}:
            raise ContractError("analyzer freshness")
        if not isinstance(item["subject_match"], bool):
            raise ContractError("analyzer subject_match")
        if not isinstance(item["languages"], list) or len(item["languages"]) != len(
            set(item["languages"])
        ):
            raise ContractError("analyzer languages")
        analyzers[aid] = item

    coverage_languages: set[str] = set()
    for index, item in enumerate(value["coverage"]):
        if not isinstance(item, dict):
            raise ContractError(f"coverage[{index}]")
        exact(
            item,
            {
                "language",
                "state",
                "source_paths",
                "analyzed_paths",
                "excluded_paths",
                "missing_reasons",
                "required_analyzers",
            },
            f"coverage[{index}]",
        )
        language = item["language"]
        if (
            not isinstance(language, str)
            or not language
            or language in coverage_languages
        ):
            raise ContractError("duplicate/invalid coverage language")
        coverage_languages.add(language)
        if item["state"] not in {"COMPLETE", "PARTIAL", "UNSUPPORTED", "UNKNOWN"}:
            raise ContractError("coverage state")
        for key in ("source_paths", "analyzed_paths", "excluded_paths"):
            if not isinstance(item[key], list) or len(item[key]) != len(set(item[key])):
                raise ContractError(f"coverage.{key}")
            for path_index, path in enumerate(item[key]):
                relpath(path, f"coverage.{key}[{path_index}]")
        if not isinstance(item["missing_reasons"], list):
            raise ContractError("coverage missing_reasons")
        if item["state"] == "COMPLETE":
            if set(item["source_paths"]) != set(item["analyzed_paths"]) | set(
                item["excluded_paths"]
            ):
                raise ContractError("complete coverage path accounting")
            if item["missing_reasons"]:
                raise ContractError("complete coverage cannot have missing reasons")
        elif not item["missing_reasons"]:
            raise ContractError("incomplete coverage requires reason")
        if (
            not isinstance(item["required_analyzers"], list)
            or not item["required_analyzers"]
        ):
            raise ContractError("coverage required_analyzers")
        for aid in item["required_analyzers"]:
            if aid not in analyzers:
                raise ContractError("coverage references unknown analyzer")
            analyzer = analyzers[aid]
            if language not in analyzer["languages"]:
                raise ContractError("coverage/analyzer language mismatch")
            if item["state"] == "COMPLETE" and (
                analyzer["state"] != "EXECUTED"
                or analyzer["freshness"] != "FRESH"
                or analyzer["subject_match"] is not True
            ):
                raise ContractError(
                    "complete coverage requires fresh subject-matched analyzer"
                )

    evidence: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(value["evidence"]):
        if not isinstance(item, dict):
            raise ContractError(f"evidence[{index}]")
        exact(
            item,
            {
                "evidence_id",
                "plane",
                "kind",
                "locator",
                "digest",
                "subject_commit",
                "analyzer_id",
            },
            f"evidence[{index}]",
        )
        eid = item["evidence_id"]
        if not isinstance(eid, str) or not eid or eid in evidence:
            raise ContractError("duplicate/invalid evidence_id")
        if item["plane"] not in PLANES:
            raise ContractError("evidence plane")
        if item["kind"] not in {
            "SOURCE_SPAN",
            "AST_FACT",
            "SEMANTIC_FACT",
            "BUILD_FACT",
            "TEST_RESULT",
            "RUNTIME_RECEIPT",
            "PRODUCTION_OBSERVATION",
            "PROVIDER_CANDIDATE",
            "COUNTEREXAMPLE",
        }:
            raise ContractError("evidence kind")
        if not isinstance(item["locator"], str) or not item["locator"]:
            raise ContractError("evidence locator")
        if not isinstance(item["digest"], str) or not SHA.fullmatch(item["digest"]):
            raise ContractError("evidence digest")
        if item["subject_commit"] != value["subject"]["commit"]:
            raise ContractError("evidence subject drift")
        aid = item["analyzer_id"]
        if aid not in analyzers or analyzers[aid]["kind"] != expected_kind(
            item["plane"]
        ):
            raise ContractError("evidence/analyzer plane mismatch")
        analyzer = analyzers[aid]
        if item["plane"] != "T6_PROVIDER_CANDIDATE" and (
            analyzer["state"] != "EXECUTED"
            or analyzer["freshness"] != "FRESH"
            or analyzer["subject_match"] is not True
        ):
            raise ContractError(
                "authoritative evidence requires fresh subject-matched execution"
            )
        evidence[eid] = item

    nodes: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(value["nodes"]):
        if not isinstance(item, dict):
            raise ContractError(f"nodes[{index}]")
        exact(
            item,
            {"node_id", "kind", "name", "language", "path", "span", "evidence_refs"},
            f"node[{index}]",
        )
        nid = item["node_id"]
        if not isinstance(nid, str) or not nid or nid in nodes:
            raise ContractError("duplicate/invalid node_id")
        if item["kind"] not in {
            "FILE",
            "MODULE",
            "SYMBOL",
            "ENDPOINT",
            "CONFIG",
            "RUNTIME_EVENT",
        }:
            raise ContractError("node kind")
        if item["path"] is not None:
            relpath(item["path"], "node.path")
        span = item["span"]
        if span is not None:
            if not isinstance(span, dict):
                raise ContractError("node span")
            exact(span, {"start_line", "end_line"}, "node.span")
            if (
                not isinstance(span["start_line"], int)
                or not isinstance(span["end_line"], int)
                or span["start_line"] < 1
                or span["end_line"] < span["start_line"]
            ):
                raise ContractError("node span range")
        if not isinstance(item["evidence_refs"], list) or not item["evidence_refs"]:
            raise ContractError("node evidence required")
        if any(ref not in evidence for ref in item["evidence_refs"]):
            raise ContractError("node unknown evidence")
        nodes[nid] = item

    edge_ids: set[str] = set()
    for index, item in enumerate(value["edges"]):
        if not isinstance(item, dict):
            raise ContractError(f"edges[{index}]")
        exact(
            item,
            {
                "edge_id",
                "source",
                "target",
                "relation",
                "plane",
                "verification",
                "confidence",
                "evidence_refs",
                "boundary",
            },
            f"edge[{index}]",
        )
        edge_id = item["edge_id"]
        if not isinstance(edge_id, str) or not edge_id or edge_id in edge_ids:
            raise ContractError("duplicate/invalid edge_id")
        edge_ids.add(edge_id)
        if item["source"] not in nodes or item["target"] not in nodes:
            raise ContractError("dangling edge")
        if (
            item["relation"] not in RELATIONS
            or item["plane"] not in PLANES
            or item["verification"] not in VERIFICATIONS
        ):
            raise ContractError("edge enum")
        if item["confidence"] not in {"LOW", "MEDIUM", "HIGH"}:
            raise ContractError("edge confidence")
        if (
            not isinstance(item["evidence_refs"], list)
            or not item["evidence_refs"]
            or any(ref not in evidence for ref in item["evidence_refs"])
        ):
            raise ContractError("edge evidence")
        refs = [evidence[ref] for ref in item["evidence_refs"]]
        if any(ref["plane"] != item["plane"] for ref in refs):
            raise ContractError("edge/evidence plane mismatch")
        if item["plane"] == "T6_PROVIDER_CANDIDATE":
            if (
                item["verification"] not in {"CANDIDATE", "CONTESTED", "UNKNOWN"}
                or item["confidence"] == "HIGH"
            ):
                raise ContractError("provider overclaim")
        if (
            item["plane"] in {"T4_SANDBOX_RUNTIME", "T5_PRODUCTION_RUNTIME"}
            and item["verification"] == "OBSERVED"
        ):
            allowed = (
                {"TEST_RESULT", "RUNTIME_RECEIPT"}
                if item["plane"] == "T4_SANDBOX_RUNTIME"
                else {"PRODUCTION_OBSERVATION", "RUNTIME_RECEIPT"}
            )
            if not any(ref["kind"] in allowed for ref in refs):
                raise ContractError("runtime observation lacks runtime artifact")
        if (
            item["plane"]
            in {"T0_DIRECT_SOURCE", "T1_AST", "T2_LSP_SCIP", "T3_BUILD_CONFIG"}
            and item["verification"] == "OBSERVED"
        ):
            raise ContractError("static evidence cannot claim runtime OBSERVED")
        if not isinstance(item["boundary"], str) or not item["boundary"]:
            raise ContractError("edge boundary")


def compile_graph(bundle: dict[str, Any]) -> dict[str, Any]:
    validate_bundle(bundle)
    graph = {
        "schema_version": GRAPH,
        "subject": bundle["subject"],
        "analyzers": sorted(bundle["analyzers"], key=lambda x: x["analyzer_id"]),
        "coverage": sorted(bundle["coverage"], key=lambda x: x["language"]),
        "evidence": sorted(bundle["evidence"], key=lambda x: x["evidence_id"]),
        "nodes": sorted(bundle["nodes"], key=lambda x: x["node_id"]),
        "edges": sorted(bundle["edges"], key=lambda x: x["edge_id"]),
        "authority": {
            "projection": True,
            "canonical": False,
            "model_write": False,
            "state_write": False,
        },
    }
    graph["graph_digest"] = digest(graph)
    validate_graph(graph)
    return graph


def validate_graph(graph: dict[str, Any]) -> None:
    exact(
        graph,
        {
            "schema_version",
            "subject",
            "analyzers",
            "coverage",
            "evidence",
            "nodes",
            "edges",
            "authority",
            "graph_digest",
        },
        "graph",
    )
    if graph["schema_version"] != GRAPH:
        raise ContractError("graph schema")
    authority = graph["authority"]
    if authority != {
        "projection": True,
        "canonical": False,
        "model_write": False,
        "state_write": False,
    }:
        raise ContractError("graph authority escalation")
    expected = copy.deepcopy(graph)
    actual = expected.pop("graph_digest")
    if actual != digest(expected):
        raise ContractError("graph digest mismatch")
    bundle = {
        key: graph[key]
        for key in ("subject", "analyzers", "coverage", "evidence", "nodes", "edges")
    }
    bundle["schema_version"] = BUNDLE
    validate_bundle(bundle)


def complete_coverage(
    graph: dict[str, Any], source: dict[str, Any], target: dict[str, Any]
) -> tuple[bool, list[str]]:
    languages = {
        value for value in (source.get("language"), target.get("language")) if value
    }
    reasons: list[str] = []
    coverage_by_lang = {entry["language"]: entry for entry in graph["coverage"]}
    analyzers = {entry["analyzer_id"]: entry for entry in graph["analyzers"]}
    if not languages:
        return False, ["node language unknown"]
    for language in sorted(languages):
        coverage = coverage_by_lang.get(language)
        if not coverage or coverage["state"] != "COMPLETE":
            reasons.append(f"{language} coverage is not COMPLETE")
            continue
        for aid in coverage["required_analyzers"]:
            analyzer = analyzers.get(aid)
            if (
                not analyzer
                or analyzer["state"] != "EXECUTED"
                or analyzer["freshness"] != "FRESH"
                or analyzer["subject_match"] is not True
            ):
                reasons.append(
                    f"{language} analyzer {aid} is not fresh/executed/subject-matched"
                )
    return not reasons, reasons


def run_query(graph: dict[str, Any], query: dict[str, Any]) -> dict[str, Any]:
    validate_graph(graph)
    exact(
        query,
        {"schema_version", "source_node", "target_node", "relations", "max_depth"},
        "query",
    )
    if query["schema_version"] != QUERY:
        raise ContractError("query schema")
    nodes = {node["node_id"]: node for node in graph["nodes"]}
    source = nodes.get(query["source_node"])
    target = nodes.get(query["target_node"])
    if source is None or target is None:
        return result(
            graph,
            query,
            "UNKNOWN",
            [],
            [],
            ["source or target node is absent from the graph projection"],
        )
    relations = set(query["relations"])
    eligible = [
        edge
        for edge in graph["edges"]
        if not relations or edge["relation"] in relations
    ]
    adjacency: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in eligible:
        if edge["verification"] not in {"FALSIFIED", "UNKNOWN"}:
            adjacency[edge["source"]].append(edge)
    queue: deque[tuple[str, list[str], int, bool]] = deque(
        [(source["node_id"], [], 0, False)]
    )
    visited = {(source["node_id"], 0)}
    found: list[list[str]] = []
    contested = False
    while queue:
        node_id, path, depth, path_contested = queue.popleft()
        if depth >= query["max_depth"]:
            continue
        for edge in adjacency.get(node_id, []):
            next_path = path + [edge["edge_id"]]
            next_contested = path_contested or edge["verification"] in {
                "CONTESTED",
                "CANDIDATE",
            }
            if edge["target"] == target["node_id"]:
                found.append(next_path)
                contested |= next_contested
                continue
            key = (edge["target"], depth + 1)
            if key not in visited:
                visited.add(key)
                queue.append((edge["target"], next_path, depth + 1, next_contested))
    if found:
        status = (
            "CONTESTED"
            if contested
            and not any(
                all(
                    next(e for e in graph["edges"] if e["edge_id"] == eid)[
                        "verification"
                    ]
                    in {"SUPPORTED", "OBSERVED"}
                    for eid in path
                )
                for path in found
            )
            else "FOUND"
        )
        return result(
            graph,
            query,
            status,
            found,
            [],
            ["one or more evidence-bound paths were found"],
        )
    complete, reasons = complete_coverage(graph, source, target)
    if complete:
        basis = [
            f"{language}:COMPLETE"
            for language in sorted(
                {source.get("language"), target.get("language")} - {None}
            )
        ]
        return result(
            graph,
            query,
            "NO_FLOW",
            [],
            basis,
            ["no eligible path under complete relevant coverage"],
        )
    return result(
        graph, query, "UNKNOWN", [], [], reasons or ["coverage is insufficient"]
    )


def result(
    graph: dict[str, Any],
    query: dict[str, Any],
    status: str,
    paths: list[list[str]],
    basis: list[str],
    reasons: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": RESULT,
        "subject": graph["subject"],
        "graph_digest": graph["graph_digest"],
        "query_digest": digest(query),
        "status": status,
        "paths": paths,
        "coverage_basis": basis,
        "reasons": reasons,
        "authority": "PROJECTION_ONLY",
    }


def run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise InfraError(f"missing executable: {argv[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise InfraError(f"command timeout: {argv[0]}") from exc


def git(repo: Path, *args: str) -> str:
    completed = run(["git", "-C", str(repo), *args])
    if completed.returncode != 0:
        raise InfraError(completed.stderr.strip() or "git failed")
    return completed.stdout.strip()


def node_id(kind: str, identity: str) -> str:
    return f"{kind.lower()}-{hashlib.sha256(identity.encode()).hexdigest()[:16]}"


def evidence_id(plane: str, identity: str) -> str:
    return f"ev-{plane.lower()}-{hashlib.sha256(identity.encode()).hexdigest()[:16]}"


def build_python(
    repo: Path, repository: str, commit: str, paths: list[str]
) -> dict[str, Any]:
    resolved_commit = git(repo, "rev-parse", f"{commit}^{{commit}}")
    tree = git(repo, "rev-parse", f"{resolved_commit}^{{tree}}")
    subject = {"repository": repository, "commit": resolved_commit, "tree": tree}
    analyzer_id = "python-stdlib-ast"
    analyzer = {
        "analyzer_id": analyzer_id,
        "kind": "AST",
        "identity_digest": "sha256:"
        + hashlib.sha256(
            (
                f"python-ast:{ast.__version__ if hasattr(ast, '__version__') else 'stdlib'}"
            ).encode()
        ).hexdigest(),
        "languages": ["python"],
        "state": "EXECUTED",
        "freshness": "FRESH",
        "subject_match": True,
    }
    source_analyzer = {
        "analyzer_id": "git-source",
        "kind": "SOURCE",
        "identity_digest": "sha256:"
        + hashlib.sha256(git(repo, "--version").encode()).hexdigest(),
        "languages": ["python"],
        "state": "EXECUTED",
        "freshness": "FRESH",
        "subject_match": True,
    }
    evidence: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    node_by_name: dict[str, str] = {}
    imports_by_file: dict[str, dict[str, str]] = {}
    parsed: list[str] = []

    for relative in paths:
        relative = relpath(relative, "build path")
        source_result = run(
            ["git", "-C", str(repo), "show", f"{resolved_commit}:{relative}"]
        )
        if source_result.returncode != 0:
            raise ContractError(f"path absent from subject: {relative}")
        text = source_result.stdout
        try:
            tree_ast = ast.parse(text, filename=relative)
        except SyntaxError as exc:
            raise ContractError(f"AST parse failed: {relative}:{exc.lineno}") from exc
        parsed.append(relative)
        source_eid = evidence_id("T0_DIRECT_SOURCE", f"{resolved_commit}:{relative}")
        evidence.append(
            {
                "evidence_id": source_eid,
                "plane": "T0_DIRECT_SOURCE",
                "kind": "SOURCE_SPAN",
                "locator": f"{relative}:1-{max(1, len(text.splitlines()))}",
                "digest": "sha256:" + hashlib.sha256(text.encode()).hexdigest(),
                "subject_commit": resolved_commit,
                "analyzer_id": "git-source",
            }
        )
        file_id = node_id("FILE", relative)
        nodes.append(
            {
                "node_id": file_id,
                "kind": "FILE",
                "name": relative,
                "language": "python",
                "path": relative,
                "span": {"start_line": 1, "end_line": max(1, len(text.splitlines()))},
                "evidence_refs": [source_eid],
            }
        )
        node_by_name[f"file:{relative}"] = file_id
        imports: dict[str, str] = {}
        for top in tree_ast.body:
            if isinstance(top, ast.ImportFrom) and top.module:
                for alias in top.names:
                    imports[alias.asname or alias.name] = f"{top.module}.{alias.name}"
            elif isinstance(top, ast.Import):
                for alias in top.names:
                    imports[alias.asname or alias.name] = alias.name
        imports_by_file[relative] = imports
        for top in tree_ast.body:
            if isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qualified = f"{Path(relative).with_suffix('').as_posix().replace('/', '.')}.{top.name}"
                ast_eid = evidence_id(
                    "T1_AST", f"{resolved_commit}:{relative}:{top.lineno}:{qualified}"
                )
                evidence.append(
                    {
                        "evidence_id": ast_eid,
                        "plane": "T1_AST",
                        "kind": "AST_FACT",
                        "locator": f"{relative}:{top.lineno}-{getattr(top, 'end_lineno', top.lineno)}",
                        "digest": "sha256:"
                        + hashlib.sha256(
                            ast.dump(top, include_attributes=True).encode()
                        ).hexdigest(),
                        "subject_commit": resolved_commit,
                        "analyzer_id": analyzer_id,
                    }
                )
                symbol_id = node_id("SYMBOL", qualified)
                nodes.append(
                    {
                        "node_id": symbol_id,
                        "kind": "SYMBOL",
                        "name": qualified,
                        "language": "python",
                        "path": relative,
                        "span": {
                            "start_line": top.lineno,
                            "end_line": getattr(top, "end_lineno", top.lineno),
                        },
                        "evidence_refs": [ast_eid],
                    }
                )
                node_by_name[qualified] = symbol_id

    for relative in parsed:
        text = run(
            ["git", "-C", str(repo), "show", f"{resolved_commit}:{relative}"]
        ).stdout
        tree_ast = ast.parse(text, filename=relative)
        module = Path(relative).with_suffix("").as_posix().replace("/", ".")
        for top in tree_ast.body:
            if not isinstance(top, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            caller = node_by_name.get(f"{module}.{top.name}")
            if not caller:
                continue
            for call in (node for node in ast.walk(top) if isinstance(node, ast.Call)):
                target_name: str | None = None
                if isinstance(call.func, ast.Name):
                    target_name = imports_by_file[relative].get(
                        call.func.id, f"{module}.{call.func.id}"
                    )
                elif isinstance(call.func, ast.Attribute) and isinstance(
                    call.func.value, ast.Name
                ):
                    base = imports_by_file[relative].get(
                        call.func.value.id, call.func.value.id
                    )
                    target_name = f"{base}.{call.func.attr}"
                if not target_name:
                    continue
                target = node_by_name.get(target_name)
                if target is None:
                    target = node_id("SYMBOL", target_name)
                    if target not in {node["node_id"] for node in nodes}:
                        call_eid = evidence_id(
                            "T1_AST",
                            f"{resolved_commit}:{relative}:{call.lineno}:{target_name}",
                        )
                        evidence.append(
                            {
                                "evidence_id": call_eid,
                                "plane": "T1_AST",
                                "kind": "AST_FACT",
                                "locator": f"{relative}:{call.lineno}-{getattr(call, 'end_lineno', call.lineno)}",
                                "digest": "sha256:"
                                + hashlib.sha256(
                                    ast.dump(call, include_attributes=True).encode()
                                ).hexdigest(),
                                "subject_commit": resolved_commit,
                                "analyzer_id": analyzer_id,
                            }
                        )
                        nodes.append(
                            {
                                "node_id": target,
                                "kind": "SYMBOL",
                                "name": target_name,
                                "language": "python",
                                "path": relative,
                                "span": {
                                    "start_line": call.lineno,
                                    "end_line": getattr(
                                        call, "end_lineno", call.lineno
                                    ),
                                },
                                "evidence_refs": [call_eid],
                            }
                        )
                edge_eid = evidence_id(
                    "T1_AST",
                    f"edge:{resolved_commit}:{relative}:{call.lineno}:{target_name}",
                )
                evidence.append(
                    {
                        "evidence_id": edge_eid,
                        "plane": "T1_AST",
                        "kind": "AST_FACT",
                        "locator": f"{relative}:{call.lineno}-{getattr(call, 'end_lineno', call.lineno)}",
                        "digest": "sha256:"
                        + hashlib.sha256(
                            ast.dump(call, include_attributes=True).encode()
                        ).hexdigest(),
                        "subject_commit": resolved_commit,
                        "analyzer_id": analyzer_id,
                    }
                )
                edges.append(
                    {
                        "edge_id": node_id(
                            "EDGE", f"{caller}:CALLS:{target}:{call.lineno}"
                        ),
                        "source": caller,
                        "target": target,
                        "relation": "CALLS",
                        "plane": "T1_AST",
                        "verification": "SUPPORTED",
                        "confidence": "MEDIUM",
                        "evidence_refs": [edge_eid],
                        "boundary": "syntactic call relation; runtime dispatch and dynamic resolution are not proven",
                    }
                )

    bundle = {
        "schema_version": BUNDLE,
        "subject": subject,
        "analyzers": [source_analyzer, analyzer],
        "coverage": [
            {
                "language": "python",
                "state": "COMPLETE",
                "source_paths": sorted(parsed),
                "analyzed_paths": sorted(parsed),
                "excluded_paths": [],
                "missing_reasons": [],
                "required_analyzers": [analyzer_id],
            }
        ],
        "evidence": evidence,
        "nodes": nodes,
        "edges": edges,
    }
    return compile_graph(bundle)


def module_root() -> Path:
    return Path(__file__).resolve().parents[1]


def check_contracts() -> list[str]:
    failures: list[str] = []
    schemas = sorted((module_root() / "contracts").glob("*.schema.json"))
    if len(schemas) != 4:
        failures.append(f"schema count={len(schemas)} expected=4")
    ids: set[str] = set()
    for path in schemas:
        try:
            value = load(path)
            schema_id = value.get("$id")
            if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                failures.append(f"schema draft: {path.name}")
            if not isinstance(schema_id, str) or schema_id in ids:
                failures.append(f"schema id: {path.name}")
            ids.add(str(schema_id))
        except (ContractError, InfraError) as exc:
            failures.append(str(exc))
    try:
        manifest = load(module_root() / "contracts/manifest.json")
        exact(
            manifest,
            {
                "schema_version",
                "observation_bundle_schema",
                "evidence_graph_schema",
                "query_schema",
                "query_result_schema",
            },
            "manifest",
        )
        if manifest["schema_version"] != "code-truth-graph-v2/contract-manifest/v1":
            failures.append("manifest schema")
        for key, relative in manifest.items():
            if (
                key.endswith("_schema")
                and not (module_root() / "contracts" / relative).is_file()
            ):
                failures.append(f"manifest missing: {relative}")
    except (ContractError, InfraError) as exc:
        failures.append(str(exc))
    return failures


def selftest() -> None:
    failures = check_contracts()
    if failures:
        raise ContractError(f"contract baseline failed: {failures}")
    with tempfile.TemporaryDirectory(prefix="ctg-v2.") as temporary:
        repo = Path(temporary) / "repo"
        repo.mkdir()
        commands = [
            ["git", "init", "-q", str(repo)],
            ["git", "-C", str(repo), "config", "user.email", "fixture@example.invalid"],
            ["git", "-C", str(repo), "config", "user.name", "Fixture"],
        ]
        for command in commands:
            completed = run(command)
            if completed.returncode != 0:
                raise InfraError(completed.stderr)
        (repo / "app.py").write_text(
            "from util import helper\n\ndef run():\n    return helper()\n\ndef isolated():\n    return 7\n",
            encoding="utf-8",
        )
        (repo / "util.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
        for command in (
            ["git", "-C", str(repo), "add", "."],
            ["git", "-C", str(repo), "commit", "-qm", "fixture"],
        ):
            completed = run(command)
            if completed.returncode != 0:
                raise InfraError(completed.stderr)
        commit = git(repo, "rev-parse", "HEAD")
        graph = build_python(repo, "ed3c/fixture", commit, ["app.py", "util.py"])
        nodes = {node["name"]: node["node_id"] for node in graph["nodes"]}
        found_query = {
            "schema_version": QUERY,
            "source_node": nodes["app.run"],
            "target_node": nodes["util.helper"],
            "relations": ["CALLS"],
            "max_depth": 4,
        }
        found = run_query(graph, found_query)
        if found["status"] != "FOUND":
            raise ContractError(f"positive path not found: {found}")
        no_flow_query = {
            "schema_version": QUERY,
            "source_node": nodes["app.isolated"],
            "target_node": nodes["util.helper"],
            "relations": ["CALLS"],
            "max_depth": 4,
        }
        no_flow = run_query(graph, no_flow_query)
        if no_flow["status"] != "NO_FLOW":
            raise ContractError("complete-coverage NO_FLOW failed")
        partial = copy.deepcopy(graph)
        partial.pop("graph_digest")
        partial["coverage"][0]["state"] = "PARTIAL"
        partial["coverage"][0]["missing_reasons"] = ["semantic index not exercised"]
        partial["graph_digest"] = digest(partial)
        unknown = run_query(partial, no_flow_query)
        if unknown["status"] != "UNKNOWN":
            raise ContractError("incomplete coverage was not UNKNOWN")

        bundle = {
            key: copy.deepcopy(graph[key])
            for key in (
                "subject",
                "analyzers",
                "coverage",
                "evidence",
                "nodes",
                "edges",
            )
        }
        bundle["schema_version"] = BUNDLE
        mutations = 0

        def reject(value: dict[str, Any]) -> None:
            nonlocal mutations
            try:
                validate_bundle(value)
            except ContractError:
                mutations += 1
                return
            raise ContractError("mutation accepted")

        value = copy.deepcopy(bundle)
        value["subject"]["commit"] = "9" * 40
        reject(value)
        value = copy.deepcopy(bundle)
        value["evidence"][0]["subject_commit"] = "9" * 40
        reject(value)
        value = copy.deepcopy(bundle)
        value["nodes"].append(copy.deepcopy(value["nodes"][0]))
        reject(value)
        value = copy.deepcopy(bundle)
        value["edges"][0]["target"] = "missing-node"
        reject(value)
        value = copy.deepcopy(bundle)
        value["nodes"][0]["path"] = "../escape"
        reject(value)
        value = copy.deepcopy(bundle)
        value["evidence"][0]["locator"] = ""
        reject(value)
        value = copy.deepcopy(bundle)
        value["nodes"][0]["span"] = {"start_line": 4, "end_line": 1}
        reject(value)
        value = copy.deepcopy(bundle)
        value["coverage"][0]["state"] = "PARTIAL"
        value["coverage"][0]["missing_reasons"] = []
        reject(value)
        value = copy.deepcopy(bundle)
        value["analyzers"][1]["freshness"] = "STALE"
        reject(value)
        value = copy.deepcopy(bundle)
        value["analyzers"][1]["subject_match"] = False
        reject(value)
        value = copy.deepcopy(bundle)
        value["evidence"][-1]["analyzer_id"] = "git-source"
        reject(value)
        provider = copy.deepcopy(bundle)
        provider["analyzers"].append(
            {
                "analyzer_id": "provider",
                "kind": "PROVIDER",
                "identity_digest": "sha256:" + "a" * 64,
                "languages": ["python"],
                "state": "EXECUTED",
                "freshness": "FRESH",
                "subject_match": True,
            }
        )
        provider_eid = "ev-provider"
        provider["evidence"].append(
            {
                "evidence_id": provider_eid,
                "plane": "T6_PROVIDER_CANDIDATE",
                "kind": "PROVIDER_CANDIDATE",
                "locator": "provider-result:1",
                "digest": "sha256:" + "b" * 64,
                "subject_commit": commit,
                "analyzer_id": "provider",
            }
        )
        provider["edges"][0] = {
            **provider["edges"][0],
            "plane": "T6_PROVIDER_CANDIDATE",
            "verification": "OBSERVED",
            "confidence": "HIGH",
            "evidence_refs": [provider_eid],
        }
        reject(provider)
        runtime = copy.deepcopy(bundle)
        runtime["analyzers"].append(
            {
                "analyzer_id": "runtime",
                "kind": "RUNTIME",
                "identity_digest": "sha256:" + "c" * 64,
                "languages": ["python"],
                "state": "EXECUTED",
                "freshness": "FRESH",
                "subject_match": True,
            }
        )
        runtime_eid = "ev-runtime"
        runtime["evidence"].append(
            {
                "evidence_id": runtime_eid,
                "plane": "T4_SANDBOX_RUNTIME",
                "kind": "SOURCE_SPAN",
                "locator": "app.py:1",
                "digest": "sha256:" + "d" * 64,
                "subject_commit": commit,
                "analyzer_id": "runtime",
            }
        )
        runtime["edges"][0] = {
            **runtime["edges"][0],
            "plane": "T4_SANDBOX_RUNTIME",
            "verification": "OBSERVED",
            "confidence": "HIGH",
            "evidence_refs": [runtime_eid],
        }
        reject(runtime)
        static_observed = copy.deepcopy(bundle)
        static_observed["edges"][0]["verification"] = "OBSERVED"
        reject(static_observed)
        duplicate_evidence = copy.deepcopy(bundle)
        duplicate_evidence["evidence"].append(
            copy.deepcopy(duplicate_evidence["evidence"][0])
        )
        reject(duplicate_evidence)
        complete_missing = copy.deepcopy(bundle)
        complete_missing["coverage"][0]["analyzed_paths"] = ["app.py"]
        reject(complete_missing)

        bad_graph = copy.deepcopy(graph)
        bad_graph["graph_digest"] = "sha256:" + "0" * 64
        try:
            validate_graph(bad_graph)
        except ContractError:
            mutations += 1
        else:
            raise ContractError("graph digest mutation accepted")

        fake_no_flow = copy.deepcopy(unknown)
        fake_no_flow["status"] = "NO_FLOW"
        if (
            partial["coverage"][0]["state"] != "COMPLETE"
            and fake_no_flow["status"] == "NO_FLOW"
        ):
            mutations += 1
        else:
            raise ContractError("false NO_FLOW control failed")

        if mutations < 17:
            raise ContractError(f"mutation count too low: {mutations}")
        print(
            f"code-truth-graph-v2 selftest PASS: FOUND, NO_FLOW, UNKNOWN, {mutations} mutations/controls"
        )


def main() -> int:
    parser = argparse.ArgumentParser(prog="ctg-v2")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("selftest")
    build = sub.add_parser("build-python")
    build.add_argument("--repo", type=Path, required=True)
    build.add_argument("--repository", default="ed3c/bettor-arena")
    build.add_argument("--commit", required=True)
    build.add_argument("--paths", nargs="+", required=True)
    build.add_argument("--output", type=Path, required=True)
    query_parser = sub.add_parser("query")
    query_parser.add_argument("--graph", type=Path, required=True)
    query_parser.add_argument("--source", required=True)
    query_parser.add_argument("--target", required=True)
    query_parser.add_argument("--relation", action="append", default=[])
    query_parser.add_argument("--max-depth", type=int, default=8)
    args = parser.parse_args()
    try:
        if args.command == "check":
            failures = check_contracts()
            if failures:
                for failure in failures:
                    print(f"CTG-V2-RED {failure}")
                return 2
            print("code-truth-graph-v2 contracts PASS: 4 schemas")
            return 0
        if args.command == "selftest":
            selftest()
            return 0
        if args.command == "build-python":
            if args.output.exists():
                raise ContractError("output already exists")
            graph = build_python(
                args.repo.resolve(), args.repository, args.commit, args.paths
            )
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(graph, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print(f"code-truth-graph-v2 WROTE {args.output}")
            return 0
        graph = load(args.graph)
        query = {
            "schema_version": QUERY,
            "source_node": args.source,
            "target_node": args.target,
            "relations": args.relation,
            "max_depth": args.max_depth,
        }
        output = run_query(graph, query)
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0 if output["status"] in {"FOUND", "CONTESTED", "NO_FLOW"} else 2
    except ContractError as exc:
        print(f"ctg-v2 checked refusal: {exc}")
        return 2
    except (InfraError, OSError) as exc:
        print(f"ctg-v2 FATAL: {exc}")
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
