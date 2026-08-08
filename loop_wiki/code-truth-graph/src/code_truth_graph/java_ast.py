from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .model import (
    add_diagnostic,
    add_evidence,
    attach_evidence_to_edge,
    attach_evidence_to_node,
    ensure_edge,
    ensure_node,
)
from .util import sha256_file


class JavaAstError(RuntimeError):
    pass


MINIMAL_ENV = {
    "PATH": os.defpath,
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
}


def compile_extractor(tool_source: Path, build_dir: Path) -> Path:
    javac = shutil.which("javac")
    if not javac:
        raise JavaAstError("javac not found; Java AST extraction requires a JDK")
    build_dir.mkdir(parents=True, exist_ok=True)
    class_file = build_dir / "CodeGraphAstExtractor.class"
    needs_compile = (
        not class_file.exists()
        or class_file.stat().st_mtime < tool_source.stat().st_mtime
    )
    if needs_compile:
        result = subprocess.run(
            [javac, "-d", str(build_dir), str(tool_source)],
            capture_output=True,
            text=True,
            check=False,
            env=MINIMAL_ENV,
            timeout=30,
        )
        if result.returncode != 0:
            raise JavaAstError(f"failed to compile AST extractor:\n{result.stderr}")
    return build_dir


def extract_java_records(
    *,
    root: Path,
    source_files: list[Path],
    tool_source: Path,
    build_dir: Path,
    classpath: str = "",
) -> list[dict[str, Any]]:
    if not source_files:
        return []
    java = shutil.which("java")
    if not java:
        raise JavaAstError("java not found")
    classes = compile_extractor(tool_source, build_dir)
    command = [java, "-cp", str(classes), "CodeGraphAstExtractor", "--root", str(root)]
    if classpath:
        command += ["--classpath", classpath]
    command += ["--", *[str(path) for path in source_files]]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        env=MINIMAL_ENV,
        timeout=30,
    )
    if result.returncode != 0:
        raise JavaAstError(
            f"AST extractor failed ({result.returncode}):\n{result.stderr}"
        )
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(result.stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise JavaAstError(
                f"invalid AST extractor JSONL at line {line_number}: {line}"
            ) from exc
    return records


def _snippet(
    root: Path, path: str, start_line: int, end_line: int, padding: int = 2
) -> dict[str, Any]:
    source = root / path
    if not source.is_file():
        return {}
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    first = max(1, start_line - padding)
    last = min(len(lines), max(end_line, start_line) + padding)
    text = "\n".join(
        f"{number:>5} │ {lines[number - 1]}" for number in range(first, last + 1)
    )
    return {"snippet": text, "snippet_start": first, "snippet_end": last}


def ingest_java_ast(
    graph: dict[str, Any],
    *,
    root: Path,
    repo: str,
    sha: str,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    node_count = 0
    edge_count = 0
    unresolved = 0
    source_hashes: dict[str, str] = {}
    ast_evidence_by_path: dict[str, str] = {}

    for record in records:
        if record.get("record") == "diagnostic":
            add_diagnostic(
                graph,
                code=str(record.get("code", "JAVAC_DIAGNOSTIC")),
                severity=str(record.get("severity", "info")),
                summary=str(record.get("summary", "")),
                details={
                    key: value
                    for key, value in record.items()
                    if key not in {"record", "code", "severity", "summary"}
                },
            )
            continue
        path = str(record.get("path", ""))
        if path and path not in source_hashes and (root / path).is_file():
            source_hashes[path] = sha256_file(root / path)
        if path and path not in ast_evidence_by_path:
            ast_evidence_by_path[path] = add_evidence(
                graph,
                method="JAVA_AST",
                status="observed",
                source=f"{repo}@{sha}:{path}",
                summary="Compiler AST parsed this source file",
                authority="deterministic",
                environment_class="source",
                details={
                    "sha256": source_hashes.get(path),
                    "semantic_fallback_is_not_absence": True,
                },
            )
        evidence_id = ast_evidence_by_path.get(path)
        if record.get("record") == "node":
            metadata = dict(record.get("metadata") or {})
            metadata.update(
                _snippet(
                    root,
                    path,
                    int(record.get("start_line", 1)),
                    int(record.get("end_line", 1)),
                )
            )
            node = ensure_node(
                graph,
                node_id=str(record["id"]),
                kind=str(record.get("kind", "symbol")),
                label=str(record.get("label", record["id"])),
                critical=False,
                location={
                    "repo": repo,
                    "path": path,
                    "start_line": int(record.get("start_line", 1)),
                    "end_line": int(
                        record.get("end_line", record.get("start_line", 1))
                    ),
                    "symbol": str(record.get("symbol", "")),
                    "sha": sha,
                },
                metadata=metadata,
            )
            if evidence_id:
                attach_evidence_to_node(graph, node["id"], evidence_id)
            if not metadata.get("semantic_resolved", True):
                unresolved += 1
            node_count += 1
        elif record.get("record") == "edge":
            source_id = str(record["source"])
            target_id = str(record["target"])
            for missing_id in (source_id, target_id):
                ensure_node(
                    graph,
                    node_id=missing_id,
                    kind="unresolved_symbol",
                    label=missing_id.rsplit(":", 1)[-1],
                    metadata={"semantic_resolved": False},
                )
            kind = str(record.get("kind", "RELATED_TO"))
            metadata = dict(record.get("metadata") or {})
            metadata.update({"path": path, "line": int(record.get("line", 1))})
            critical = kind in {"HTTP_PAYLOAD", "HTTP_REQUEST", "ROUTES_TO"}
            edge = ensure_edge(
                graph,
                source=source_id,
                target=target_id,
                kind=kind,
                critical=critical,
                metadata=metadata,
            )
            method = (
                "STATIC_DATAFLOW"
                if kind in {"DATA_FLOW", "ARGUMENT_TO_PARAMETER", "HTTP_PAYLOAD"}
                else "JAVA_AST"
            )
            edge_evidence = add_evidence(
                graph,
                method=method,
                status="possible",
                source=f"{repo}@{sha}:{path}:{record.get('line', 1)}",
                summary=f"AST-derived {kind} edge",
                authority="deterministic",
                environment_class="source",
                details={"semantic_resolved": metadata.get("semantic_resolved", True)},
            )
            attach_evidence_to_edge(graph, edge["id"], edge_evidence)
            edge_count += 1
    return {"nodes": node_count, "edges": edge_count, "unresolved_symbols": unresolved}
