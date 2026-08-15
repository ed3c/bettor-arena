#!/usr/bin/env python3
"""Shared exits, errors and deterministic encoding for LoopX Observability.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagrees, 64 the input or invocation is unusable. Absence and refusal must not
look alike -- a missing ledger file and a ledger that violates the projection
law are different answers, and a caller that cannot tell them apart will treat
a broken pipe as a verdict.
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
HEX32 = re.compile(r"^[0-9a-f]{32}$")
HEX16 = re.compile(r"^[0-9a-f]{16}$")
ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


class ContractError(Exception):
    """A checked invariant disagreed. Exit 2."""


class InputError(Exception):
    """The input is absent or unreadable. Exit 64, never 2."""


def canonical_bytes(value: Any) -> bytes:
    """Encode deterministically.

    Every rebuild claim in this module rests on this function: two projections
    of the same events are compared as bytes, so key order must not be able to
    make identical content look different.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


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


SUBJECT_KEYS = {"repository", "commit", "tree", "task_id"}


def validate_subject(value: Any, label: str) -> dict[str, Any]:
    subject = exact_object(value, SUBJECT_KEYS, label)
    for field in ("commit", "tree"):
        if SHA40.fullmatch(str(subject[field])) is None:
            raise ContractError(f"{label}.{field} must be a full 40-hex sha")
    non_empty_str(subject["repository"], f"{label}.repository")
    non_empty_str(subject["task_id"], f"{label}.task_id")
    return subject
