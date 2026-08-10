from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

from .model import add_diagnostic, add_evidence, attach_evidence_to_node
from .util import read_jsonl, stable_id

READ_NAMES = {"read", "read_file", "readfile", "cat", "open_file", "view"}
GREP_NAMES = {"grep", "rg", "search", "search_files", "find_in_file"}
EDIT_NAMES = {"edit", "edit_file", "write", "write_file", "apply_patch", "create_file"}
TEST_NAMES = {"bash", "shell", "run_command", "exec", "terminal"}


def _walk(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _parse_jsonish(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {"command": value}
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    return {}


def _tool_candidate(obj: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    name = obj.get("name") or obj.get("tool_name") or obj.get("toolName")
    if not name and isinstance(obj.get("tool"), str):
        name = obj["tool"]
    if not name and obj.get("type") in {"tool_use", "tool_call"}:
        name = (
            obj.get("function", {}).get("name")
            if isinstance(obj.get("function"), dict)
            else None
        )
    if not name:
        return None
    payload = (
        obj.get("input")
        or obj.get("arguments")
        or obj.get("args")
        or obj.get("tool_input")
    )
    if payload is None and isinstance(obj.get("function"), dict):
        payload = obj["function"].get("arguments")
    return str(name), _parse_jsonish(payload)


def _file_from_payload(payload: dict[str, Any]) -> str | None:
    keys = (
        "file_path",
        "path",
        "file",
        "target_file",
        "TargetFile",
        "TargetPath",
        "AbsolutePath",
    )
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    command = payload.get("command") or payload.get("cmd") or payload.get("CommandLine")
    if isinstance(command, list):
        command = " ".join(str(item) for item in command)
    if isinstance(command, str):
        patterns = [
            r"(?:cat|sed|head|tail|less|bat)\s+(?:-[^ ]+\s+)*['\"]?([^'\"\s|;]+)",
            r"(?:rg|grep)[^\n]*?\s+['\"]?([^'\"\s|;]+\.(?:java|kt|swift|go|js|ts|py|md))",
        ]
        for pattern in patterns:
            match = re.search(pattern, command)
            if match:
                return match.group(1)
    return None


def _line_range(payload: dict[str, Any]) -> tuple[int, int]:
    start = (
        payload.get("line_start")
        or payload.get("start_line")
        or payload.get("offset")
        or 1
    )
    end = payload.get("line_end") or payload.get("end_line")
    limit = payload.get("limit")
    try:
        start_int = max(1, int(start))
    except (TypeError, ValueError):
        start_int = 1
    if end is not None:
        try:
            end_int = max(start_int, int(end))
        except (TypeError, ValueError):
            end_int = start_int
    elif limit is not None:
        try:
            end_int = start_int + max(0, int(limit) - 1)
        except (TypeError, ValueError):
            end_int = start_int
    else:
        end_int = 10**9
    return start_int, end_int


def _stage(name: str) -> str:
    lowered = name.lower().replace(" ", "_")
    if lowered in READ_NAMES:
        return "RETRIEVED"
    if lowered in GREP_NAMES:
        return "ENUMERATED"
    if lowered in EDIT_NAMES:
        return "EDITED"
    if lowered in TEST_NAMES:
        return "TESTED"
    return "DELIVERED_TO_CONTEXT"


def parse_session(
    path: Path, *, agent: str, root: Path | None = None
) -> dict[str, Any]:
    rows = read_jsonl(path)
    accesses: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int, str]] = set()
    session_id: str | None = None
    thread_id: str | None = None
    parse_warnings: list[str] = []

    for line_number, row in enumerate(rows, start=1):
        session_id = session_id or row.get("session_id") or row.get("sessionId")
        thread_id = thread_id or row.get("thread_id") or row.get("threadId")
        for obj in _walk(row):
            candidate = _tool_candidate(obj)
            if candidate is None:
                continue
            name, payload = candidate
            file_value = _file_from_payload(payload)
            if not file_value:
                continue
            path_value = Path(file_value).expanduser()
            if root and path_value.is_absolute():
                try:
                    normalized = (
                        path_value.resolve().relative_to(root.resolve()).as_posix()
                    )
                except ValueError:
                    normalized = path_value.as_posix()
            else:
                normalized = path_value.as_posix()
            start, end = _line_range(payload)
            stage = _stage(name)
            key = (normalized, start, end, stage)
            if key in seen:
                continue
            seen.add(key)
            accesses.append(
                {
                    "id": stable_id(
                        "access", agent, normalized, start, end, stage, line_number
                    ),
                    "file": normalized,
                    "line_start": start,
                    "line_end": end,
                    "stage": stage,
                    "tool": name,
                    "event_line": line_number,
                    "at": obj.get("timestamp")
                    or row.get("timestamp")
                    or row.get("created_at"),
                }
            )
    if not accesses:
        parse_warnings.append(
            "No file-range tool events were recognized; this is UNKNOWN coverage, not zero coverage."
        )
    return {
        "id": stable_id("agent-session", agent, session_id or thread_id or path.name),
        "agent": agent,
        "source": str(path),
        "session_id": session_id,
        "thread_id": thread_id,
        "event_count": len(rows),
        "accesses": accesses,
        "warnings": parse_warnings,
    }


def _path_matches(node_path: str, access_path: str) -> bool:
    normalized_node = node_path.replace("\\", "/").lstrip("./")
    normalized_access = access_path.replace("\\", "/").lstrip("./")
    # Virtual graph nodes have no source path. A directory-wide Grep such as
    # path="." must never make those nodes look retrieved merely because both
    # strings normalize to empty. Directory scope is discoverability telemetry,
    # not proof that every file or virtual node entered the model context.
    if not normalized_node or not normalized_access:
        return False
    return (
        normalized_node == normalized_access
        or normalized_access.endswith("/" + normalized_node)
        or normalized_node.endswith("/" + normalized_access)
    )


def ingest_session(graph: dict[str, Any], session: dict[str, Any]) -> dict[str, Any]:
    touched_nodes: set[str] = set()
    for access in session.get("accesses", []):
        for node in graph["nodes"]:
            location = node.get("location") or {}
            if not _path_matches(str(location.get("path", "")), str(access["file"])):
                continue
            start = int(location.get("start_line", 1))
            end = int(location.get("end_line", start))
            if end < int(access["line_start"]) or start > int(access["line_end"]):
                continue
            evidence_id = add_evidence(
                graph,
                method="CLAUDE_SESSION"
                if session["agent"].lower().startswith("claude")
                else "CODEX_SESSION",
                status="observed",
                source=f"{session['source']}:{access['event_line']}",
                summary=f"{session['agent']} {access['stage'].lower()} {access['file']}:{access['line_start']}-{access['line_end']}",
                authority="agent-telemetry",
                environment_class="agent_session",
                observed_at=access.get("at"),
                details={
                    "session_id": session.get("session_id") or session.get("thread_id"),
                    "access_id": access["id"],
                    "stage": access["stage"],
                    "tool": access["tool"],
                    "coverage_is_not_verification": True,
                },
            )
            attach_evidence_to_node(graph, node["id"], evidence_id)
            touched_nodes.add(node["id"])
    graph["agent_sessions"].append(
        {**session, "touched_node_ids": sorted(touched_nodes)}
    )
    if not session.get("accesses"):
        add_diagnostic(
            graph,
            code="SESSION_SCOPE_UNKNOWN",
            severity="warning",
            summary=f"No retrievable file ranges were parsed from {session['source']}",
            details={"agent": session["agent"], "not_equivalent_to_zero": True},
        )
    return {
        "session_id": session["id"],
        "accesses": len(session.get("accesses", [])),
        "touched_nodes": len(touched_nodes),
    }


def compute_agent_coverage(graph: dict[str, Any]) -> dict[str, Any]:
    critical_nodes = {node["id"] for node in graph["nodes"] if node.get("critical")}
    per_session: list[dict[str, Any]] = []
    union: set[str] = set()
    for session in graph.get("agent_sessions", []):
        touched = set(session.get("touched_node_ids", [])) & critical_nodes
        union |= touched
        per_session.append(
            {
                "id": session["id"],
                "agent": session["agent"],
                "critical_nodes_touched": len(touched),
                "critical_nodes_total": len(critical_nodes),
                "ratio": (len(touched) / len(critical_nodes))
                if critical_nodes
                else None,
            }
        )
    result = {
        "critical_nodes_total": len(critical_nodes),
        "critical_nodes_retrieved_union": len(union),
        "ratio": (len(union) / len(critical_nodes)) if critical_nodes else None,
        "per_session": per_session,
        "rule": "Agent retrieval is a predictor of blind spots, not evidence of correctness.",
    }
    graph["closure"]["agent_retrieval"] = result
    return result
