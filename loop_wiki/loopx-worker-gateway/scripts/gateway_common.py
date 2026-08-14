#!/usr/bin/env python3
"""Deterministic primitives and validators for LoopX Worker Gateway v1."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any

OK, BAD, USAGE = 0, 2, 64
DG = re.compile(r"^sha256:[0-9a-f]{64}$")
H40 = re.compile(r"^[0-9a-f]{40}$")
ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ENV = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
HOSTS = {"codex-cli", "claude-code", "grok-build", "opencode", "pi", "ante", "fixture-host"}
STATUSES = {"PASS", "FAIL", "NOT_EXERCISED", "SKIPPED_BY_POLICY", "ABSENT"}
SECRET_KEYS = re.compile(r"(?:^|_)(?:TOKEN|SECRET|PASSWORD|PASS|COOKIE|PRIVATE_KEY|API_KEY)(?:$|_)", re.I)
SECRET_VALUES = [
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}", re.I),
]
FORBIDDEN_AUTHORITY_KEYS = {
    "gate_verdict", "gate_passed", "state_transition", "loopx_state",
    "human_admit", "promotion", "rollback", "durable_memory_write",
    "chain_of_thought", "thought_stream", "private_reasoning",
}

class ContractError(ValueError):
    pass

class InputError(ValueError):
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

def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()

def exact_object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    if set(value) != keys:
        raise ContractError(
            f"{label} fields drifted; missing={sorted(keys-set(value))}, extra={sorted(set(value)-keys)}"
        )
    return value

def bounded(value: Any, label: str, maximum: int = 4096, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or "\0" in value or len(value) > maximum:
        raise ContractError(f"{label} must be bounded text")
    if not allow_empty and not value.strip():
        raise ContractError(f"{label} is empty")
    return value

def stable_id(value: Any, label: str) -> str:
    text = bounded(value, label, 128)
    if not ID.fullmatch(text):
        raise ContractError(f"{label} must be a stable lower identifier")
    return text

def sha_ref(value: Any, label: str, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not DG.fullmatch(value):
        raise ContractError(f"{label} must be sha256:<64 lower-hex>")
    return value

def relpath(value: Any, label: str, allow_dot: bool = False) -> str:
    text = bounded(value, label, 512)
    if text == "." and allow_dot:
        return text
    path = PurePosixPath(text)
    if "\\" in text or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ContractError(f"{label} must be a normalized relative path")
    if any(part.lower() in {".git", ".env", "credentials", "cookies", "auth.json", "keychain"} for part in path.parts):
        raise ContractError(f"{label} enters a forbidden control/secret path")
    return text

def validate_subject(value: Any, label: str) -> dict[str, Any]:
    subject = exact_object(value, {"repository", "commit", "tree", "task_id"}, label)
    if not REPO.fullmatch(bounded(subject["repository"], f"{label}.repository", 256)):
        raise ContractError(f"{label}.repository must be owner/name")
    for key in ("commit", "tree"):
        if not isinstance(subject[key], str) or not H40.fullmatch(subject[key]):
            raise ContractError(f"{label}.{key} must be exact 40-hex")
    stable_id(subject["task_id"], f"{label}.task_id")
    return subject

def validate_artifact(value: Any, label: str) -> dict[str, Any]:
    keys = {"artifact_id", "kind", "path", "digest", "bytes", "media_type", "producer"}
    artifact = exact_object(value, keys, label)
    stable_id(artifact["artifact_id"], f"{label}.artifact_id")
    if artifact["kind"] not in {
        "STDOUT", "STDERR", "GIT_DIFF", "FILE", "TRACE",
        "WORKER_EVENT", "PROCESS_TREE", "CLEANUP_REPORT"
    }:
        raise ContractError(f"{label}.kind is unsupported")
    relpath(artifact["path"], f"{label}.path")
    sha_ref(artifact["digest"], f"{label}.digest")
    if type(artifact["bytes"]) is not int or not 0 <= artifact["bytes"] <= 104_857_600:
        raise ContractError(f"{label}.bytes is outside budget")
    bounded(artifact["media_type"], f"{label}.media_type", 128)
    stable_id(artifact["producer"], f"{label}.producer")
    return artifact

def verify_content_digest(value: dict[str, Any], label: str) -> None:
    observed = value.get("content_digest")
    raw = copy.deepcopy(value)
    raw.pop("content_digest", None)
    if observed != digest(raw):
        raise ContractError(f"{label}.content_digest mismatch")

def reject_authority_or_private_fields(value: Any, label: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_AUTHORITY_KEYS:
                raise ContractError(f"{label} contains forbidden authority/private field: {key}")
            reject_authority_or_private_fields(child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_authority_or_private_fields(child, f"{label}[{index}]")

def reject_secret_payload(value: Any, label: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if SECRET_KEYS.search(str(key)):
                raise ContractError(f"{label} contains secret-shaped key: {key}")
            reject_secret_payload(child, f"{label}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_secret_payload(child, f"{label}[{index}]")
    elif isinstance(value, str):
        for pattern in SECRET_VALUES:
            if pattern.search(value):
                raise ContractError(f"{label} contains secret-shaped value")

def make_artifact(path: Path, root: Path, artifact_id: str, kind: str, producer: str, media_type: str) -> dict[str, Any]:
    try:
        relative = path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as exc:
        raise ContractError(f"artifact escaped output root: {path}") from exc
    return {
        "artifact_id": stable_id(artifact_id, "artifact_id"),
        "kind": kind,
        "path": relpath(relative, "artifact.path"),
        "digest": file_digest(path),
        "bytes": path.stat().st_size,
        "media_type": media_type,
        "producer": stable_id(producer, "producer"),
    }
