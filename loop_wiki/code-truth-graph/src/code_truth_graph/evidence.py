from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from .model import (
    add_diagnostic,
    add_evidence,
    attach_evidence_to_edge,
    attach_evidence_to_node,
    ensure_edge,
    ensure_node,
    select_one_node,
)
from .util import read_json, stable_id


def add_manual_static(graph: dict[str, Any], entries: dict[str, Any]) -> dict[str, int]:
    nodes_added = 0
    edges_added = 0
    for item in entries.get("nodes", []):
        node = ensure_node(
            graph,
            node_id=item["id"],
            kind=item["kind"],
            label=item["label"],
            critical=bool(item.get("critical", False)),
            location=item.get("location"),
            metadata=item.get("metadata") or {},
        )
        evidence_id = add_evidence(
            graph,
            method=item.get("method", "DOCUMENT"),
            status=item.get("status", "documented"),
            source=item.get("source", "manifest"),
            summary=item.get("summary", "Manifest-declared node"),
            authority=item.get("authority", "declared"),
            environment_class=item.get("environment_class", "source"),
            details=item.get("details") or {},
            evidence_id=item.get("evidence_id"),
        )
        attach_evidence_to_node(graph, node["id"], evidence_id)
        nodes_added += 1
    for item in entries.get("edges", []):
        edge = ensure_edge(
            graph,
            source=item["source"],
            target=item["target"],
            kind=item["kind"],
            critical=bool(item.get("critical", False)),
            metadata=item.get("metadata") or {},
        )
        evidence_id = add_evidence(
            graph,
            method=item.get("method", "STATIC_ROUTE"),
            status=item.get("status", "possible"),
            source=item.get("source_ref", "manifest"),
            summary=item.get("summary", f"Declared {item['kind']} edge"),
            authority=item.get("authority", "declared"),
            environment_class=item.get("environment_class", "source"),
            details=item.get("details") or {},
            evidence_id=item.get("evidence_id"),
        )
        attach_evidence_to_edge(graph, edge["id"], evidence_id)
        edges_added += 1
    return {"nodes": nodes_added, "edges": edges_added}


def _sourcefile_candidates(package_name: str, source_name: str) -> list[str]:
    package_path = package_name.replace(".", "/")
    return [f"{package_path}/{source_name}".lstrip("/"), source_name]


def ingest_jacoco(
    graph: dict[str, Any], path: Path, *, environment_class: str = "synthetic"
) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    covered_lines: set[tuple[str, int]] = set()
    for package in root.findall("package"):
        package_name = package.get("name", "")
        for sourcefile in package.findall("sourcefile"):
            source_name = sourcefile.get("name", "")
            candidates = _sourcefile_candidates(package_name, source_name)
            for line in sourcefile.findall("line"):
                if int(line.get("ci", "0")) <= 0 and int(line.get("cb", "0")) <= 0:
                    continue
                number = int(line.get("nr", "0"))
                for candidate in candidates:
                    covered_lines.add((candidate, number))
    matched_nodes = 0
    evidence_id = add_evidence(
        graph,
        method="JACOCO_LINE",
        status="covered",
        source=str(path),
        summary=f"JaCoCo covered {len(covered_lines)} source-line identities",
        authority="runtime-tool",
        environment_class=environment_class,
        details={
            "critical_limit": "Line coverage lights nodes only; it never proves a specific edge executed.",
            "covered_line_count": len(covered_lines),
        },
    )
    for node in graph["nodes"]:
        location = node.get("location") or {}
        node_path = str(location.get("path", ""))
        start = int(location.get("start_line", 1))
        end = int(location.get("end_line", start))
        if any(
            node_path.endswith(candidate) and start <= line <= end
            for candidate, line in covered_lines
        ):
            attach_evidence_to_node(graph, node["id"], evidence_id)
            matched_nodes += 1
    add_diagnostic(
        graph,
        code="COVERAGE_IS_NODE_ONLY",
        severity="info",
        summary="Coverage was not promoted to edge execution evidence",
        details={"matched_nodes": matched_nodes, "covered_lines": len(covered_lines)},
    )
    return {
        "covered_lines": len(covered_lines),
        "matched_nodes": matched_nodes,
        "edges_lit": 0,
    }


def _resolve_selector(
    graph: dict[str, Any], selector: dict[str, Any], *, label: str
) -> dict[str, Any] | None:
    node = select_one_node(graph, selector)
    if node is None:
        add_diagnostic(
            graph,
            code="EVIDENCE_SELECTOR_UNRESOLVED",
            severity="warning",
            summary=f"Could not resolve {label} selector",
            details={"selector": selector},
        )
    return node


def ingest_receipt(graph: dict[str, Any], path: Path, *, lane: str) -> dict[str, Any]:
    receipt = read_json(path)
    if not isinstance(receipt, dict):
        raise ValueError(f"receipt must be an object: {path}")
    environment_class = str(receipt.get("environment_class", "unknown"))
    authority = str(receipt.get("authority", "fixture"))
    run_id = str(receipt.get("run_id", path.stem))
    observed_at = receipt.get("observed_at")
    method_prefix = "SANDBOX" if lane == "SANDBOX" else "PROD"
    node_method = f"{method_prefix}_STATE_RECEIPT"
    edge_method = f"{method_prefix}_EDGE_RECEIPT" if lane == "SANDBOX" else "PROD_TRACE"
    nodes_lit = 0
    edges_lit = 0

    for row in receipt.get("observed_nodes", []):
        selector = row.get("selector", row)
        node = _resolve_selector(graph, selector, label=f"{lane} node")
        if node is None:
            continue
        evidence_id = add_evidence(
            graph,
            method=node_method,
            status=str(row.get("status", "observed")),
            source=str(path),
            summary=str(row.get("summary", f"{lane} observed node {node['label']}")),
            authority=authority,
            environment_class=environment_class,
            observed_at=observed_at,
            details={"run_id": run_id, **(row.get("details") or {})},
            evidence_id=row.get("evidence_id"),
        )
        attach_evidence_to_node(graph, node["id"], evidence_id)
        nodes_lit += 1

    for row in receipt.get("observed_edges", []):
        source = _resolve_selector(graph, row["source"], label=f"{lane} edge source")
        target = _resolve_selector(graph, row["target"], label=f"{lane} edge target")
        if source is None or target is None:
            continue
        kind = str(row.get("kind", "RUNTIME_FLOW"))
        edge = ensure_edge(
            graph,
            source=source["id"],
            target=target["id"],
            kind=kind,
            critical=bool(row.get("critical", False)),
            metadata={"runtime_receipt": True, **(row.get("metadata") or {})},
        )
        evidence_id = add_evidence(
            graph,
            method=edge_method,
            status=str(row.get("status", "observed")),
            source=str(path),
            summary=str(
                row.get(
                    "summary", f"{lane} observed {source['label']} → {target['label']}"
                )
            ),
            authority=authority,
            environment_class=environment_class,
            observed_at=observed_at,
            details={"run_id": run_id, **(row.get("details") or {})},
            evidence_id=row.get("evidence_id"),
        )
        attach_evidence_to_edge(graph, edge["id"], evidence_id)
        edges_lit += 1

    for observation in receipt.get("observations", []):
        add_evidence(
            graph,
            method=node_method,
            status=str(observation.get("status", "observed")),
            source=str(path),
            summary=str(observation.get("summary", "Runtime observation")),
            authority=authority,
            environment_class=environment_class,
            observed_at=observed_at,
            details={"run_id": run_id, **(observation.get("details") or {})},
            evidence_id=observation.get("evidence_id"),
        )
    existing_events = {event.get("id") for event in graph.get("invariant_events", [])}
    for position, raw_event in enumerate(receipt.get("invariant_events", [])):
        event = dict(raw_event)
        event.setdefault(
            "id",
            stable_id(
                "receipt-invariant-event",
                run_id,
                position,
                event.get("invariant_id"),
                event.get("action"),
            ),
        )
        event.setdefault("at", observed_at)
        event.setdefault("source_receipt", str(path))
        if event["id"] not in existing_events:
            graph.setdefault("invariant_events", []).append(event)
            existing_events.add(event["id"])
    return {
        "run_id": run_id,
        "environment_class": environment_class,
        "nodes_lit": nodes_lit,
        "edges_lit": edges_lit,
    }


def ingest_log(
    graph: dict[str, Any],
    path: Path,
    *,
    anchors: list[dict[str, Any]],
    environment_class: str,
    authority: str,
) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    matches = 0
    for anchor in anchors:
        pattern = re.compile(anchor["pattern"], re.MULTILINE)
        found = list(pattern.finditer(text))
        if not found:
            add_diagnostic(
                graph,
                code="LOG_ANCHOR_NOT_OBSERVED",
                severity="info",
                summary=f"No match for log anchor {anchor.get('id', anchor['pattern'])}",
                details={
                    "pattern": anchor["pattern"],
                    "meaning": "Not observed does not establish absence; disclose traffic, sampling, and instrumentation.",
                },
            )
            continue
        target = _resolve_selector(graph, anchor["selector"], label="log anchor")
        if target is None:
            continue
        for match in found:
            line_number = text[: match.start()].count("\n") + 1
            evidence_id = add_evidence(
                graph,
                method="PROD_LOG",
                status="observed",
                source=f"{path}:{line_number}",
                summary=str(anchor.get("summary", match.group(0).strip())),
                authority=authority,
                environment_class=environment_class,
                details={
                    "anchor_id": anchor.get("id"),
                    "matched_text": match.group(0).strip(),
                    "unique_emitter_required": True,
                },
            )
            attach_evidence_to_node(graph, target["id"], evidence_id)
            matches += 1
    return {"matches": matches, "anchors": len(anchors)}


def mark_critical_path(
    graph: dict[str, Any], selectors: list[dict[str, Any]]
) -> dict[str, Any]:
    marked_nodes = 0
    marked_edges = 0
    selected_ids: list[str] = []
    for selector in selectors:
        node = select_one_node(graph, selector)
        if node is None:
            continue
        node["critical"] = True
        selected_ids.append(node["id"])
        marked_nodes += 1
    selected_set = set(selected_ids)
    for edge in graph["edges"]:
        if edge["source"] in selected_set and edge["target"] in selected_set:
            edge["critical"] = True
            marked_edges += 1
    return {"nodes": marked_nodes, "edges": marked_edges, "node_ids": selected_ids}


def compute_static_paths(
    graph: dict[str, Any],
    source_selector: dict[str, Any],
    target_selector: dict[str, Any],
) -> list[list[str]]:
    source = select_one_node(graph, source_selector)
    target = select_one_node(graph, target_selector)
    if source is None or target is None:
        return []
    adjacency: dict[str, list[str]] = {}
    for edge in graph["edges"]:
        if not any(
            reach in edge.get("reach", []) for reach in {"AST", "SEMANTIC", "STATIC"}
        ):
            continue
        adjacency.setdefault(edge["source"], []).append(edge["target"])
    paths: list[list[str]] = []
    stack: list[tuple[str, list[str]]] = [(source["id"], [source["id"]])]
    while stack and len(paths) < 20:
        current, path = stack.pop()
        if current == target["id"]:
            paths.append(path)
            continue
        if len(path) > 16:
            continue
        for neighbour in adjacency.get(current, []):
            if neighbour not in path:
                stack.append((neighbour, path + [neighbour]))
    return paths


def add_selector_bindings(
    graph: dict[str, Any],
    entries: list[dict[str, Any]],
    *,
    attach_endpoint_evidence: bool = False,
) -> dict[str, Any]:
    """Add declared semantic bridges after AST/LSP extraction, resolving endpoints by selectors.

    This is useful when a product build is incomplete: the bridge is explicit evidence with its own
    authority and never masquerades as a compiler-resolved relation.
    """
    added = 0
    blocked: list[dict[str, Any]] = []
    for item in entries:
        source = select_one_node(graph, item.get("source_selector", {}))
        target = select_one_node(graph, item.get("target_selector", {}))
        if source is None or target is None:
            blocked.append(item)
            add_diagnostic(
                graph,
                code="POST_STATIC_BINDING_UNRESOLVED",
                severity="warning",
                summary=f"Could not resolve declared binding {item.get('kind', 'RELATED_TO')}",
                details={
                    "source_selector": item.get("source_selector"),
                    "target_selector": item.get("target_selector"),
                    "meaning": "The edge is UNKNOWN; the missing selector is not proof that the relation is absent.",
                },
            )
            continue
        edge = ensure_edge(
            graph,
            source=source["id"],
            target=target["id"],
            kind=item.get("kind", "RELATED_TO"),
            critical=bool(item.get("critical", False)),
            metadata=item.get("metadata") or {},
        )
        evidence_id = add_evidence(
            graph,
            method=item.get("method", "STATIC_ROUTE"),
            status=item.get("status", "possible"),
            source=item.get("source_ref", "manifest post-static binding"),
            summary=item.get("summary", "Declared post-static binding"),
            authority=item.get("authority", "declared"),
            environment_class=item.get("environment_class", "source"),
            details=item.get("details") or {},
            evidence_id=item.get("evidence_id"),
        )
        attach_evidence_to_edge(graph, edge["id"], evidence_id)
        if attach_endpoint_evidence:
            attach_evidence_to_node(graph, source["id"], evidence_id)
            attach_evidence_to_node(graph, target["id"], evidence_id)
        added += 1
    return {"added": added, "blocked": len(blocked), "blocked_entries": blocked}
