#!/usr/bin/env python3
"""Shared exits, errors and evidence classes for knowledge fold-back.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagreed, 64 the input or invocation is unusable.

The one idea that carries most of this module is at the bottom of the file:
STATIC, TEST and RUNTIME evidence are separate kinds, and none of them implies
another. A diff proves a line changed. A passing test proves that line executed
under the inputs the test supplies. Neither proves what the code does in
production. Folding them into one "verified" flag is how a static diff ends up
recorded as observed behaviour, and once written down nobody can tell which one
it was.
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


class ContractError(Exception):
    """A checked invariant disagreed. Exit 2."""


class InputError(Exception):
    """The input is absent or unreadable. Exit 64, never 2."""


def canonical_bytes(value: Any) -> bytes:
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


SUBJECT_KEYS = {"repository", "commit", "tree", "ref_kind"}


def validate_subject(value: Any, label: str) -> dict[str, Any]:
    subject = exact_object(value, SUBJECT_KEYS, label)
    for field in ("commit", "tree"):
        if SHA40.fullmatch(str(subject[field])) is None:
            raise ContractError(f"{label}.{field} must be a full 40-hex sha")
    non_empty_str(subject["repository"], f"{label}.repository")
    if subject["ref_kind"] != "IMMUTABLE_COMMIT":
        raise ContractError(
            f"{label}.ref_kind must be IMMUTABLE_COMMIT; a fold-back receipt that "
            "names a branch describes a diff nobody can reproduce tomorrow"
        )
    return subject


# --- evidence classes ---------------------------------------------------------
#
# Ordered by what they can support, and deliberately not a ladder: none of these
# implies another, so there is no max() that could promote one into the next.

EVIDENCE_CLASSES = ("STATIC", "TEST", "RUNTIME")

EVIDENCE_SUPPORTS = {
    # A diff shows what the source says now. It does not show what it does.
    "STATIC": "the code says this",
    # A green test shows the path executed under the inputs the test supplies.
    "TEST": "this executed and produced this, under these inputs",
    # A runtime observation shows what happened on a real run with real values.
    "RUNTIME": "this really ran in this environment and behaved this way",
}

# Every class needs its own receipt kind, because a receipt is what distinguishes
# an observation from an assertion about one.
EVIDENCE_RECEIPT_REQUIRED = {
    "STATIC": "diff_ref",
    "TEST": "test_execution",
    "RUNTIME": "runtime_observation",
}


def validate_evidence_class(value: Any, label: str) -> str:
    if value not in EVIDENCE_CLASSES:
        raise ContractError(
            f"{label} must be one of {list(EVIDENCE_CLASSES)}; these are separate "
            "kinds of evidence and none of them implies another"
        )
    return value
