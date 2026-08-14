#!/usr/bin/env python3
"""Shared deterministic primitives for the LoopX append-only ledger."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from datetime import datetime, timezone
from typing import Any

OK, BAD, USAGE = 0, 2, 64
DG = re.compile(r"^sha256:[0-9a-f]{64}$")
H40 = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
SUBJECT_KEYS = {"repository", "commit", "tree", "task_id"}
ARTIFACT_KEYS = {"artifact_id", "kind", "path", "digest", "bytes", "media_type", "producer"}
EVENT_KEYS = {"schema_version", "event_id", "subject", "sequence", "previous_event_digest", "event_digest", "occurred_at", "type", "actor", "payload"}
EVENT_PAYLOAD_KEYS = {"todo_id", "command_id", "request_ref", "worker_result_ref", "gate_observation", "quota_delta", "human_decision", "transition"}
PRIVATE_KEYS = {"thought", "thought_stream", "chain_of_thought", "private_reasoning", "raw_thought"}
FORBIDDEN_PATH_PARTS = {".git", ".env", "credentials", "cookies", "auth.json", "keychain"}
ARTIFACT_KINDS = {"STDOUT", "STDERR", "GIT_DIFF", "LSP_DIAGNOSTICS", "LINTER_REPORT", "TEST_REPORT", "FILE", "TRACE", "HUMAN_DECISION"}
ALLOWED_TRANSITIONS = {
    ("READY", "DISPATCHED"), ("RETRY", "DISPATCHED"),
    ("DISPATCHED", "RUNNING"), ("RUNNING", "RETRY"),
    ("RUNNING", "HITL_PENDING"), ("RETRY", "HITL_PENDING"),
    ("HITL_PENDING", "READY"), ("HITL_PENDING", "CANCELLED"),
    ("RUNNING", "COMPLETED"), ("RUNNING", "COMPLETED_WITH_EXCEPTION"),
    ("RUNNING", "FAILED"), ("READY", "CANCELLED"),
}

class ContractError(ValueError):
    pass

class InputError(ValueError):
    pass

class BusyError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    raw = value if isinstance(value, (bytes, bytearray)) else canonical_bytes(value)
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def file_digest(path: Path) -> str:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InputError(f"missing JSON: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise InputError(f"unreadable JSON: {path}: {exc}") from exc


def exact_object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    present = set(value)
    if present != keys:
        raise ContractError(
            f"{label} fields drifted; missing={sorted(keys - present)}, extra={sorted(present - keys)}"
        )
    return value


def bounded_text(value: Any, label: str, maximum: int = 4096) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or "\0" in value:
        raise ContractError(f"{label} must be a non-empty bounded string")
    return value


def stable_id(value: Any, label: str) -> str:
    text = bounded_text(value, label, 128)
    if not ID.fullmatch(text):
        raise ContractError(f"{label} must be a stable lower-kebab identifier")
    return text


def sha256_ref(value: Any, label: str, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not DG.fullmatch(value):
        raise ContractError(f"{label} must be sha256:<64 lower-hex>")
    return value


def relative_path(value: Any, label: str, allow_dot: bool = False) -> str:
    text = bounded_text(value, label, 512)
    if text == "." and allow_dot:
        return text
    path = PurePosixPath(text)
    if "\\" in text or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ContractError(f"{label} must be a normalized relative path")
    if any(part.lower() in FORBIDDEN_PATH_PARTS for part in path.parts):
        raise ContractError(f"{label} enters a forbidden secret/control path")
    return text



def validate_rfc3339_utc(value: Any, label: str) -> str:
    text = bounded_text(value, label, 32)
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ContractError(f"{label} must be canonical UTC RFC3339 seconds") from exc
    if parsed.year < 2000:
        raise ContractError(f"{label} is implausible")
    return text

def validate_subject(value: Any, label: str) -> dict[str, Any]:
    subject = exact_object(value, SUBJECT_KEYS, label)
    if not REPO.fullmatch(bounded_text(subject["repository"], f"{label}.repository", 256)):
        raise ContractError(f"{label}.repository must be owner/name")
    for key in ("commit", "tree"):
        if not isinstance(subject[key], str) or not H40.fullmatch(subject[key]):
            raise ContractError(f"{label}.{key} must be exact 40-hex")
    stable_id(subject["task_id"], f"{label}.task_id")
    return subject


def validate_artifact(value: Any, label: str) -> dict[str, Any]:
    artifact = exact_object(value, ARTIFACT_KEYS, label)
    stable_id(artifact["artifact_id"], f"{label}.artifact_id")
    relative_path(artifact["path"], f"{label}.path")
    sha256_ref(artifact["digest"], f"{label}.digest")
    if type(artifact["bytes"]) is not int or not 0 <= artifact["bytes"] <= 104_857_600:
        raise ContractError(f"{label}.bytes is outside the evidence budget")
    if artifact["kind"] not in ARTIFACT_KINDS:
        raise ContractError(f"{label}.kind is unsupported")
    bounded_text(artifact["media_type"], f"{label}.media_type", 128)
    stable_id(artifact["producer"], f"{label}.producer")
    return artifact


def reject_private_fields(value: Any, label: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in PRIVATE_KEYS:
                raise ContractError(f"{label} contains private reasoning field: {key}")
            reject_private_fields(child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_private_fields(child, f"{label}[{index}]")


def validate_event_digest(event: dict[str, Any], label: str) -> None:
    expected = dict(event)
    expected.pop("event_digest", None)
    if event["event_digest"] != digest(expected):
        raise ContractError(f"{label}.event_digest mismatch")


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        dir_fd = os.open(path.parent, os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def append_fsync(path: Path, raw_line: bytes) -> None:
    if b"\n" in raw_line.rstrip(b"\n"):
        raise ContractError("one event must occupy exactly one JSONL line")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("ab", buffering=0) as handle:
        handle.write(raw_line.rstrip(b"\n") + b"\n")
        os.fsync(handle.fileno())


def snapshot_summary(snapshot: dict[str, Any] | None, events_path: Path) -> dict[str, Any]:
    if snapshot is None:
        return {
            "event_count": 0,
            "last_sequence": -1,
            "head_digest": None,
            "state_revision": 0,
            "events_file_digest": file_digest(events_path),
        }
    ledger = snapshot["ledger"]
    return {
        "event_count": ledger["event_count"],
        "last_sequence": ledger["last_sequence"],
        "head_digest": ledger["head_digest"],
        "state_revision": snapshot["state_revision"],
        "events_file_digest": file_digest(events_path),
    }
