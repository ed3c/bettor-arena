from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .constants import (
    FILES,
    FORBIDDEN_REASONING_KEYS,
    MACHINE_PATH_PATTERN,
    SECRET_PATTERN,
)


class Red(Exception):
    """The document was readable and violated a contract."""


class BadInput(Exception):
    """The document could not be read or parsed."""


class BadUsage(Exception):
    """The CLI invocation is invalid."""


@dataclass(frozen=True)
class Document:
    value: dict[str, Any]
    raw: bytes


def encode_json(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def digest_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def read_document(path: Path) -> Document:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise BadInput(f"{path}: unreadable: {error}") from error
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BadInput(f"{path}: invalid JSON: {error}") from error
    if not isinstance(value, dict):
        raise BadInput(f"{path}: top level must be an object")
    return Document(value=value, raw=raw)


def load_bundle(root: Path) -> dict[str, Document]:
    return {name: read_document(root / relative) for name, relative in FILES.items()}


def scan_durable(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_REASONING_KEYS:
                raise Red(f"{path}.{key}: private reasoning fields are forbidden")
            scan_durable(child, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            scan_durable(child, f"{path}[{index}]")
        return
    if isinstance(value, str):
        if SECRET_PATTERN.search(value):
            raise Red(f"{path}: secret-shaped material is forbidden")
        if MACHINE_PATH_PATTERN.search(value):
            raise Red(f"{path}: machine-local absolute paths are forbidden")


def resolve_relative(root: Path, raw: str, label: str) -> Path:
    path = Path(raw)
    if path.is_absolute() or ".." in path.parts:
        raise Red(f"{label}: artifact path must be repository-relative")
    resolved = (root / path).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise Red(f"{label}: artifact path escapes repository") from error
    return resolved


def validate_artifact(
    root: Path | None,
    binding: dict[str, Any],
    documents: dict[str, Document],
    artifact_id: str,
    document_id: str,
    expected_path: str,
) -> None:
    try:
        reference = binding["artifacts"][artifact_id]
    except (KeyError, TypeError) as error:
        raise Red(f"{artifact_id}: artifact reference is absent") from error
    if reference.get("path") != expected_path:
        raise Red(f"{artifact_id}: artifact path differs from the declared route")
    observed = digest_bytes(documents[document_id].raw)
    if reference.get("digest") != observed:
        raise Red(f"{artifact_id}: artifact digest does not bind exact bytes")
    if root is None:
        return
    path = resolve_relative(root, reference["path"], artifact_id)
    try:
        disk_raw = path.read_bytes()
    except OSError as error:
        raise Red(f"{artifact_id}: artifact is unreadable: {error}") from error
    if digest_bytes(disk_raw) != reference["digest"]:
        raise Red(f"{artifact_id}: artifact digest does not bind exact bytes")
