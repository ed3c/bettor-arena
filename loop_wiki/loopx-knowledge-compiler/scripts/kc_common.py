#!/usr/bin/env python3
"""Shared exits, errors and deterministic encoding for the Knowledge Compiler.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagreed, 64 the input or invocation is unusable. The distinction carries real
weight here, because this module's whole subject is the difference between "the
notes say nothing about X" and "X is false". A compiler that collapsed absence
into refusal would answer questions the sources never addressed.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

OK = 0
BAD = 2
USAGE = 64

SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

# A locator must say where in the source, not merely which source. "the design
# notes" is not a locator; "notes/design.md#L40-L52" is.
LOCATOR = re.compile(r"^[A-Za-z0-9._\-/]+#L\d+(?:-L\d+)?$")


class ContractError(Exception):
    """A checked invariant disagreed. Exit 2."""


class InputError(Exception):
    """The input is absent or unreadable. Exit 64, never 2."""


def canonical_bytes(value: Any) -> bytes:
    """Encode deterministically.

    Every idempotence claim in this module rests on this function: the same
    notes subject compiled twice is compared as bytes, so key order must not be
    able to make identical content look different.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def text_digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load_json(path: Path) -> Any:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON in {path}: {exc}") from exc


def exact_object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    if set(value) != keys:
        raise ContractError(
            f"{label} fields drifted; missing={sorted(keys - set(value))}, "
            f"extra={sorted(set(value) - keys)}"
        )
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def non_empty_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value


def sha256_ref(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_REF.fullmatch(value) is None:
        raise ContractError(f"{label} must be sha256:<64 lowercase hex>")
    return value


def iso_timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or ISO_UTC.fullmatch(value) is None:
        raise ContractError(f"{label} must be an RFC3339 UTC timestamp ending in Z")
    return value


NOTES_SUBJECT_KEYS = {"repository", "commit", "tree", "ref", "ref_kind"}


def validate_notes_subject(value: Any, label: str = "notes_subject") -> dict[str, Any]:
    """A Notes Repo pinned as a real Git subject.

    `ref_kind` must be `IMMUTABLE_COMMIT`. A branch name moves, so a receipt
    that recorded only `main` names a different tree tomorrow and every claim
    traced back to it becomes unverifiable without saying so.
    """
    subject = exact_object(value, NOTES_SUBJECT_KEYS, label)
    for field in ("commit", "tree"):
        if SHA40.fullmatch(str(subject[field])) is None:
            raise ContractError(f"{label}.{field} must be a full 40-hex sha")
    non_empty_str(subject["repository"], f"{label}.repository")
    non_empty_str(subject["ref"], f"{label}.ref")
    if subject["ref_kind"] != "IMMUTABLE_COMMIT":
        raise ContractError(
            f"{label}.ref_kind must be IMMUTABLE_COMMIT; a mutable branch names a "
            "different tree tomorrow, so every assertion traced to it silently "
            "loses its source"
        )
    return subject
