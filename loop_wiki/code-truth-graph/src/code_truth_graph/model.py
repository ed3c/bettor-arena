from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .util import stable_id

REACH_ORDER = {
    "TEXT": 0,
    "AST": 1,
    "SEMANTIC": 2,
    "STATIC": 3,
    "SANDBOX": 4,
    "DEPLOYED": 5,
    "PROD": 6,
    "AGENT": 7,
    "HUMAN": 8,
}

METHOD_TO_REACH = {
    "TEXT_SEARCH": "TEXT",
    "JAVA_AST": "AST",
    "TREE_SITTER": "AST",
    "LSP_DEFINITION": "SEMANTIC",
    "LSP_REFERENCE": "SEMANTIC",
    "LSP_CALL_HIERARCHY": "SEMANTIC",
    "STATIC_DATAFLOW": "STATIC",
    "STATIC_ROUTE": "STATIC",
    "JACOCO_LINE": "SANDBOX",
    "SANDBOX_EDGE_RECEIPT": "SANDBOX",
    "SANDBOX_STATE_RECEIPT": "SANDBOX",
    "DEPLOYMENT_RECEIPT": "DEPLOYED",
    "PROD_LOG": "PROD",
    "PROD_TRACE": "PROD",
    "PROD_STATE_RECEIPT": "PROD",
    "CLAUDE_SESSION": "AGENT",
    "CODEX_SESSION": "AGENT",
    "HUMAN_REVIEW": "HUMAN",
    "DOCUMENT": "TEXT",
}


@dataclass(frozen=True)
class Location:
    repo: str
    path: str
    start_line: int = 1
    end_line: int = 1
    symbol: str = ""
    sha: str = "UNKNOWN"

    def as_dict(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "symbol": self.symbol,
            "sha": self.sha,
        }


def new_graph(
    *, title: str, snapshot: dict[str, Any], scope: dict[str, Any]
) -> dict[str, Any]:
    return {
        "schema_version": "1.1.0",
        "title": title,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": snapshot,
        "scope": scope,
        "nodes": [],
        "edges": [],
        "evidence": [],
        "invariants": [],
        "invariant_events": [],
        "agent_sessions": [],
        "diagnostics": [],
        "communities": [],
        "closure": {},
    }


def _index(items: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def ensure_node(
    graph: dict[str, Any],
    *,
    node_id: str,
    kind: str,
    label: str,
    location: dict[str, Any] | None = None,
    critical: bool = False,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    by_id = _index(graph["nodes"])
    if node_id in by_id:
        node = by_id[node_id]
        node["critical"] = bool(node.get("critical") or critical)
        node.setdefault("metadata", {}).update(metadata or {})
        if location and not node.get("location"):
            node["location"] = location
        return node
    node = {
        "id": node_id,
        "kind": kind,
        "label": label,
        "critical": critical,
        "location": location,
        "metadata": metadata or {},
        "reach": [],
        "evidence_ids": [],
    }
    graph["nodes"].append(node)
    return node


def add_evidence(
    graph: dict[str, Any],
    *,
    method: str,
    status: str,
    source: str,
    summary: str,
    authority: str = "derived",
    environment_class: str = "source",
    details: dict[str, Any] | None = None,
    observed_at: str | None = None,
    evidence_id: str | None = None,
) -> str:
    evidence_id = evidence_id or stable_id(
        "ev", method, status, source, summary, observed_at or ""
    )
    by_id = _index(graph["evidence"])
    if evidence_id not in by_id:
        graph["evidence"].append(
            {
                "id": evidence_id,
                "method": method,
                "reach": METHOD_TO_REACH.get(method, "TEXT"),
                "status": status,
                "source": source,
                "summary": summary,
                "authority": authority,
                "environment_class": environment_class,
                "observed_at": observed_at,
                "details": details or {},
            }
        )
    return evidence_id


def attach_evidence_to_node(
    graph: dict[str, Any], node_id: str, evidence_id: str
) -> None:
    nodes = _index(graph["nodes"])
    evidence = _index(graph["evidence"])
    if node_id not in nodes or evidence_id not in evidence:
        return
    node = nodes[node_id]
    if evidence_id not in node["evidence_ids"]:
        node["evidence_ids"].append(evidence_id)
    reach = evidence[evidence_id]["reach"]
    if evidence[evidence_id]["status"] in {
        "observed",
        "possible",
        "covered",
        "documented",
    }:
        if reach not in node["reach"]:
            node["reach"].append(reach)
            node["reach"].sort(key=lambda value: REACH_ORDER.get(value, -1))


def ensure_edge(
    graph: dict[str, Any],
    *,
    source: str,
    target: str,
    kind: str,
    critical: bool = False,
    metadata: dict[str, Any] | None = None,
    edge_id: str | None = None,
) -> dict[str, Any]:
    edge_id = edge_id or stable_id("edge", source, target, kind)
    by_id = _index(graph["edges"])
    if edge_id in by_id:
        edge = by_id[edge_id]
        edge["critical"] = bool(edge.get("critical") or critical)
        edge.setdefault("metadata", {}).update(metadata or {})
        return edge
    edge = {
        "id": edge_id,
        "source": source,
        "target": target,
        "kind": kind,
        "critical": critical,
        "metadata": metadata or {},
        "reach": [],
        "evidence_ids": [],
    }
    graph["edges"].append(edge)
    return edge


def attach_evidence_to_edge(
    graph: dict[str, Any], edge_id: str, evidence_id: str
) -> None:
    edges = _index(graph["edges"])
    evidence = _index(graph["evidence"])
    if edge_id not in edges or evidence_id not in evidence:
        return
    edge = edges[edge_id]
    if evidence_id not in edge["evidence_ids"]:
        edge["evidence_ids"].append(evidence_id)
    item = evidence[evidence_id]
    if item["status"] in {"observed", "possible", "covered", "documented"}:
        reach = item["reach"]
        if reach not in edge["reach"]:
            edge["reach"].append(reach)
            edge["reach"].sort(key=lambda value: REACH_ORDER.get(value, -1))


def add_diagnostic(
    graph: dict[str, Any],
    *,
    code: str,
    severity: str,
    summary: str,
    details: dict[str, Any] | None = None,
) -> None:
    diagnostic_id = stable_id("diag", code, summary, len(graph["diagnostics"]))
    graph["diagnostics"].append(
        {
            "id": diagnostic_id,
            "code": code,
            "severity": severity,
            "summary": summary,
            "details": details or {},
        }
    )


def select_nodes(
    graph: dict[str, Any], selector: dict[str, Any]
) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for node in graph["nodes"]:
        location = node.get("location") or {}
        metadata = node.get("metadata") or {}
        conditions = {
            "id": node.get("id"),
            "kind": node.get("kind"),
            "label": node.get("label"),
            "path": location.get("path"),
            "symbol": location.get("symbol"),
            "qualified_name": metadata.get("qualified_name"),
            "payload_key": metadata.get("payload_key"),
        }
        ok = True
        for key, expected in selector.items():
            actual = conditions.get(key)
            if expected is None:
                continue
            if isinstance(expected, str) and expected.startswith("re:"):
                import re

                if actual is None or re.search(expected[3:], str(actual)) is None:
                    ok = False
                    break
            elif actual != expected:
                ok = False
                break
        if ok:
            matches.append(node)
    return matches


def select_one_node(
    graph: dict[str, Any], selector: dict[str, Any]
) -> dict[str, Any] | None:
    matches = select_nodes(graph, selector)
    return matches[0] if matches else None


def validate_graph(graph: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = [
        "schema_version",
        "nodes",
        "edges",
        "evidence",
        "invariants",
        "invariant_events",
    ]
    for key in required:
        if key not in graph:
            errors.append(f"missing top-level key: {key}")
    node_ids = [item.get("id") for item in graph.get("nodes", [])]
    edge_ids = [item.get("id") for item in graph.get("edges", [])]
    evidence_ids = [item.get("id") for item in graph.get("evidence", [])]
    for label, values in (
        ("node", node_ids),
        ("edge", edge_ids),
        ("evidence", evidence_ids),
    ):
        duplicates = sorted(
            {value for value in values if value and values.count(value) > 1}
        )
        if duplicates:
            errors.append(f"duplicate {label} ids: {duplicates}")
    node_set = set(node_ids)
    evidence_set = set(evidence_ids)
    for edge in graph.get("edges", []):
        if edge.get("source") not in node_set:
            errors.append(f"edge {edge.get('id')} source missing: {edge.get('source')}")
        if edge.get("target") not in node_set:
            errors.append(f"edge {edge.get('id')} target missing: {edge.get('target')}")
        for evidence_id in edge.get("evidence_ids", []):
            if evidence_id not in evidence_set:
                errors.append(f"edge {edge.get('id')} evidence missing: {evidence_id}")
    return errors


def highest_reach(values: Iterable[str]) -> str | None:
    present = list(values)
    return (
        max(present, key=lambda value: REACH_ORDER.get(value, -1)) if present else None
    )


def relative_location(
    path: Path, root: Path, repo: str, symbol: str = "", line: int = 1
) -> dict[str, Any]:
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        relative = path.resolve().as_posix()
    return Location(
        repo=repo, path=relative, start_line=line, end_line=line, symbol=symbol
    ).as_dict()
