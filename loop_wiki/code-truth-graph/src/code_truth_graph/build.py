from __future__ import annotations

import glob
from pathlib import Path
from typing import Any

from .evidence import (
    add_manual_static,
    add_selector_bindings,
    compute_static_paths,
    ingest_jacoco,
    ingest_log,
    ingest_receipt,
    mark_critical_path,
)
from .graphrag import compute_communities, export_graphrag
from .java_ast import extract_java_records, ingest_java_ast
from .model import (
    add_diagnostic,
    ensure_edge,
    ensure_node,
    new_graph,
    select_one_node,
    validate_graph,
)
from .render import render_html
from .sessions import compute_agent_coverage, ingest_session, parse_session
from .settlement import add_invariants_and_events, evaluate_all
from .util import (
    expand_env,
    read_json,
    resolve_path,
    sha256_file,
    stable_id,
    write_json,
)


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = expand_env(read_json(path))
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    manifest_path = path.resolve()
    declared_base = manifest.get("path_base")
    base = (
        Path(str(declared_base)).expanduser().resolve()
        if declared_base
        else manifest_path.parent
    )
    if declared_base and not Path(str(declared_base)).is_absolute():
        raise ValueError("path_base must be absolute when supplied")
    manifest["_manifest_path"] = str(manifest_path)
    manifest["_base_dir"] = str(base)
    return manifest


def _paths_from_globs(root: Path, patterns: list[str]) -> list[Path]:
    values: set[Path] = set()
    for pattern in patterns:
        absolute = pattern if Path(pattern).is_absolute() else str(root / pattern)
        for match in glob.glob(absolute, recursive=True):
            path = Path(match)
            if path.is_file():
                values.add(path.resolve())
    return sorted(values)


def _edge_for_selector(
    graph: dict[str, Any], selector: dict[str, Any]
) -> dict[str, Any] | None:
    source = select_one_node(graph, selector.get("source", {}))
    target = select_one_node(graph, selector.get("target", {}))
    if source is None or target is None:
        return None
    kind = selector.get("kind")
    for edge in graph["edges"]:
        if (
            edge["source"] == source["id"]
            and edge["target"] == target["id"]
            and (kind is None or edge["kind"] == kind)
        ):
            return edge
    return None


def _resolve_invariant_links(
    graph: dict[str, Any], definitions: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    invariants: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    evidence_ids = {item["id"] for item in graph["evidence"]}
    for definition in definitions:
        invariant = {key: value for key, value in definition.items() if key != "events"}
        subject_ids: list[str] = []
        for selector in definition.get("subject_selectors", []):
            node = select_one_node(graph, selector)
            if node:
                node["critical"] = bool(
                    definition.get("critical", False) or node.get("critical")
                )
                subject_ids.append(node["id"])
        invariant["subject_ids"] = sorted(
            set(invariant.get("subject_ids", []) + subject_ids)
        )
        invariant.pop("subject_selectors", None)
        ensure_node(
            graph,
            node_id=f"invariant:{invariant['id']}",
            kind="business_invariant",
            label=invariant["id"],
            critical=bool(invariant.get("critical", False)),
            metadata={"description": invariant.get("statement", ""), "visual_stage": 7},
        )
        for subject_id in invariant["subject_ids"]:
            ensure_edge(
                graph,
                source=subject_id,
                target=f"invariant:{invariant['id']}",
                kind="AFFECTS_INVARIANT",
                critical=bool(invariant.get("critical", False)),
            )
        invariants.append(invariant)
        for raw_event in definition.get("events", []):
            event = dict(raw_event)
            event.setdefault(
                "id",
                stable_id(
                    "inv-event",
                    invariant["id"],
                    event.get("sequence"),
                    event.get("action"),
                    event.get("note"),
                ),
            )
            event["invariant_id"] = invariant["id"]
            affected: list[str] = []
            for edge_selector in event.pop("affected_edge_selectors", []):
                edge = _edge_for_selector(graph, edge_selector)
                if edge:
                    affected.append(edge["id"])
                else:
                    add_diagnostic(
                        graph,
                        code="INVARIANT_EDGE_SELECTOR_UNRESOLVED",
                        severity="warning",
                        summary=f"Could not resolve edge selector for {invariant['id']} T{event.get('sequence')}",
                        details={"selector": edge_selector},
                    )
            event["affected_edge_ids"] = affected
            missing = [
                evidence_id
                for evidence_id in event.get("evidence_ids", [])
                if evidence_id not in evidence_ids
            ]
            if missing:
                add_diagnostic(
                    graph,
                    code="INVARIANT_EVIDENCE_MISSING",
                    severity="warning",
                    summary=f"Invariant event references missing evidence: {missing}",
                    details={"event_id": event["id"]},
                )
            events.append(event)
    return invariants, events


def _critical_edge_metrics(graph: dict[str, Any]) -> dict[str, Any]:
    critical = [edge for edge in graph["edges"] if edge.get("critical")]
    static_only = [
        edge
        for edge in critical
        if any(
            reach in edge.get("reach", []) for reach in {"AST", "SEMANTIC", "STATIC"}
        )
        and not any(reach in edge.get("reach", []) for reach in {"SANDBOX", "PROD"})
    ]
    unknown = [edge for edge in critical if not edge.get("reach")]
    prod = [edge for edge in critical if "PROD" in edge.get("reach", [])]
    return {
        "critical_edges": len(critical),
        "static_only_critical_edges": len(static_only),
        "production_observed_critical_edges": len(prod),
        "unknown_critical_edges": len(unknown),
        "static_only_edge_ids": [edge["id"] for edge in static_only],
    }


def build_graph(
    manifest_path: Path, *, output_dir: Path | None = None
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    base = Path(manifest["_base_dir"])
    artifacts = dict(manifest.get("artifacts") or {})
    html_name = str(artifacts.get("html", "report.html"))
    if Path(html_name).name != html_name or not html_name.endswith(".html"):
        raise ValueError("artifacts.html must be one relative .html filename")
    output_dir = (
        output_dir
        or resolve_path(base, manifest.get("output_dir"))
        or (base / "../build").resolve()
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    snapshot = dict(manifest.get("snapshot") or {})
    scope = dict(manifest.get("scope") or {})
    graph = new_graph(title=manifest["title"], snapshot=snapshot, scope=scope)
    if snapshot.get("generated_at"):
        graph["generated_at"] = snapshot["generated_at"]
    graph["manifest"] = {
        "path": str(manifest_path.resolve()),
        "sha256": sha256_file(manifest_path),
        "slice_id": manifest.get("slice_id"),
    }

    stage_report: dict[str, Any] = {}
    stage_report["manual_static"] = add_manual_static(
        graph, manifest.get("manual_static") or {}
    )

    static = manifest.get("static") or {}
    source_root = resolve_path(base, static.get("root"))
    if not static:
        stage_report["static"] = {
            "status": "NOT_REQUESTED",
            "reason": "No static source extraction requested",
        }
    elif source_root and source_root.is_dir():
        source_files = _paths_from_globs(
            source_root, static.get("source_globs", ["**/*.java"])
        )
        if source_files:
            records = extract_java_records(
                root=source_root,
                source_files=source_files,
                tool_source=(
                    Path(__file__).resolve().parents[2]
                    / "tools/java/CodeGraphAstExtractor.java"
                ),
                build_dir=output_dir / "java-extractor",
                classpath=str(static.get("classpath", "")),
            )
            stage_report["static"] = ingest_java_ast(
                graph,
                root=source_root,
                repo=str(scope.get("repo", "product")),
                sha=str(snapshot.get("sha", "WORKTREE")),
                records=records,
            )
            stage_report["static"]["source_files"] = len(source_files)
        else:
            stage_report["static"] = {
                "status": "BLOCKED",
                "reason": "No Java sources matched",
            }
            add_diagnostic(
                graph,
                code="STATIC_SOURCE_EMPTY",
                severity="warning",
                summary="No source files matched static.source_globs",
            )
    else:
        stage_report["static"] = {"status": "BLOCKED", "reason": "Source root missing"}
        add_diagnostic(
            graph,
            code="STATIC_SOURCE_ROOT_MISSING",
            severity="warning",
            summary="Product source root is missing; static graph is not available",
            details={
                "configured_root": static.get("root"),
                "not_equivalent_to_empty_repo": True,
            },
        )

    post_static_report = add_selector_bindings(
        graph, manifest.get("post_static_bindings", [])
    )
    post_static_report["status"] = (
        "BLOCKED"
        if post_static_report.get("blocked", 0)
        else "PASSED"
        if post_static_report.get("added", 0)
        else "NOT_REQUESTED"
    )
    stage_report["post_static_bindings"] = post_static_report

    critical = manifest.get("critical_path") or {}
    stage_report["critical_path"] = mark_critical_path(
        graph, critical.get("node_selectors", [])
    )
    paths = compute_static_paths(
        graph, critical.get("source_selector", {}), critical.get("target_selector", {})
    )
    stage_report["critical_path"]["static_paths"] = paths
    graph["closure"]["static_critical_paths"] = {"count": len(paths), "paths": paths}

    lsp = manifest.get("lsp") or {}
    unknown_lsp = sorted(set(lsp) - {"tool_profile", "bindings"})
    if unknown_lsp:
        raise ValueError(
            "local manifest LSP is data-only; unsupported keys "
            f"{unknown_lsp}. Supply post_static_bindings instead of caller argv."
        )
    lsp_profile = lsp.get("tool_profile")
    if lsp_profile not in {None, "bindings-only-v1"}:
        raise ValueError(f"unsupported local LSP tool_profile: {lsp_profile}")
    semantic_bindings = lsp.get("bindings", [])
    if not isinstance(semantic_bindings, list) or not all(
        isinstance(item, dict) for item in semantic_bindings
    ):
        raise ValueError("lsp.bindings must be an array of objects")
    binding_report = add_selector_bindings(
        graph, semantic_bindings, attach_endpoint_evidence=True
    )
    if lsp_profile == "bindings-only-v1" and binding_report.get("blocked", 0):
        lsp_status = "BLOCKED"
    elif lsp_profile == "bindings-only-v1" and binding_report.get("added", 0):
        lsp_status = "PASSED"
    elif lsp_profile == "bindings-only-v1":
        lsp_status = "BLOCKED"
    else:
        lsp_status = "NOT_REQUESTED"
    stage_report["lsp"] = {
        "status": lsp_status,
        "tool_profile": lsp_profile,
        "semantic_bindings": binding_report.get("added", 0),
        "blocked_bindings": binding_report.get("blocked", 0),
        "rule": "Caller-controlled LSP argv is forbidden; observations arrive as typed bindings.",
    }

    sandbox_report: list[dict[str, Any]] = []
    sandbox = manifest.get("sandbox") or {}
    jacoco_path = resolve_path(base, sandbox.get("jacoco"))
    if jacoco_path and jacoco_path.is_file():
        sandbox_report.append(
            {
                "kind": "jacoco",
                **ingest_jacoco(
                    graph,
                    jacoco_path,
                    environment_class=sandbox.get("environment_class", "synthetic"),
                ),
            }
        )
    for value in sandbox.get("receipts", []):
        receipt_path = resolve_path(base, value)
        if receipt_path and receipt_path.is_file():
            sandbox_report.append(
                {
                    "kind": "receipt",
                    **ingest_receipt(graph, receipt_path, lane="SANDBOX"),
                }
            )
        else:
            sandbox_report.append(
                {"kind": "receipt", "status": "BLOCKED", "path": value}
            )
    stage_report["sandbox"] = sandbox_report or [
        {"status": "UNVERIFIED", "reason": "No sandbox evidence supplied"}
    ]

    production_report: list[dict[str, Any]] = []
    production = manifest.get("production") or {}
    for log in production.get("logs", []):
        log_path = resolve_path(base, log.get("path"))
        if log_path and log_path.is_file():
            production_report.append(
                {
                    "kind": "log",
                    **ingest_log(
                        graph,
                        log_path,
                        anchors=log.get("anchors", []),
                        environment_class=log.get("environment_class", "unknown"),
                        authority=log.get("authority", "unknown"),
                    ),
                }
            )
        else:
            production_report.append(
                {"kind": "log", "status": "BLOCKED", "path": log.get("path")}
            )
    for value in production.get("receipts", []):
        receipt_path = resolve_path(base, value)
        if receipt_path and receipt_path.is_file():
            production_report.append(
                {"kind": "receipt", **ingest_receipt(graph, receipt_path, lane="PROD")}
            )
        else:
            production_report.append(
                {"kind": "receipt", "status": "BLOCKED", "path": value}
            )
    stage_report["production"] = production_report or [
        {"status": "UNVERIFIED", "reason": "No production evidence supplied"}
    ]

    sessions_report: list[dict[str, Any]] = []
    for session_config in manifest.get("sessions", []):
        session_path = resolve_path(base, session_config.get("path"))
        if not session_path or not session_path.is_file():
            sessions_report.append(
                {
                    "status": "BLOCKED",
                    "path": session_config.get("path"),
                    "agent": session_config.get("agent"),
                }
            )
            continue
        session_root = resolve_path(base, session_config.get("root")) or source_root
        session = parse_session(
            session_path,
            agent=session_config.get("agent", "unknown"),
            root=session_root,
        )
        sessions_report.append(ingest_session(graph, session))
    stage_report["sessions"] = sessions_report or [
        {"status": "UNVERIFIED", "reason": "No session JSONL supplied"}
    ]

    invariants, events = _resolve_invariant_links(graph, manifest.get("invariants", []))
    add_invariants_and_events(graph, invariants=invariants, events=events)
    stage_report["settlement"] = evaluate_all(graph)
    stage_report["agent_coverage"] = compute_agent_coverage(graph)
    graph["closure"]["critical_edges"] = _critical_edge_metrics(graph)
    communities = compute_communities(graph)
    stage_report["communities"] = {"count": len(communities)}

    errors = validate_graph(graph)
    if errors:
        for error in errors:
            add_diagnostic(
                graph, code="GRAPH_VALIDATION_ERROR", severity="error", summary=error
            )
    graph["closure"]["validation"] = {"ok": not errors, "errors": errors}
    stage_report["graphrag"] = export_graphrag(graph, output_dir / "graphrag")
    graph["build_report"] = stage_report

    graph_path = output_dir / "code-truth-graph.json"
    write_json(graph_path, graph)
    render_html(graph, output_dir / html_name)
    blocked_stages = sorted(
        name
        for name, value in stage_report.items()
        if (
            isinstance(value, dict)
            and value.get("status") in {"BLOCKED", "FAILED", "ERROR"}
        )
        or (
            isinstance(value, list)
            and any(
                isinstance(item, dict)
                and item.get("status") in {"BLOCKED", "FAILED", "ERROR"}
                for item in value
            )
        )
    )
    report = {
        "ok": not errors and not blocked_stages,
        "graph": "code-truth-graph.json",
        "html": html_name,
        "manifest": str(manifest_path.resolve()),
        "scope_mode": scope.get("mode"),
        "stages": stage_report,
        "blocked_stages": blocked_stages,
        "counts": {
            "nodes": len(graph["nodes"]),
            "edges": len(graph["edges"]),
            "evidence": len(graph["evidence"]),
            "invariants": len(graph["invariants"]),
            "diagnostics": len(graph["diagnostics"]),
        },
        "hard_truth_rule": manifest.get(
            "hard_truth_rule",
            "Synthetic evidence never settles external production truth.",
        ),
    }
    write_json(output_dir / "verification-report.json", report)
    return report
