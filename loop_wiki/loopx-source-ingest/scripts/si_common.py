#!/usr/bin/env python3
"""Shared exits, errors, and the rule that a locator must be read, never computed.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagreed, 64 the input or invocation is unusable.

`LOCATOR_ORIGINS` at the bottom is the module's spine. Every timestamp, page
number and bounding box carries where it came from, and only one of the origins
is admissible:

    READ_FROM_ARTIFACT   parsed out of the captured bytes
    ESTIMATED            computed from text length, reading speed, position
    ASSUMED              a default someone picked

An estimated timestamp looks exactly like a real one -- same format, same
plausible value, and it will be quoted back as if someone had checked. The only
thing that separates them is a field saying which it is, so that field is
mandatory and only one value passes.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import PurePosixPath
from typing import Any

OK = 0
BAD = 2
USAGE = 64

SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
VTT_CUE = re.compile(
    r"^(\d{2}):(\d{2}):(\d{2})\.(\d{3}) --> (\d{2}):(\d{2}):(\d{2})\.(\d{3})"
)

SOURCE_TYPES = (
    "YOUTUBE_TRANSCRIPT",
    "VTT",
    "SRT",
    "PDF_PAGE",
    "PDF_FIGURE",
    "MARKDOWN",
    "ARTICLE",
    "PAPER",
    "SOURCE_CODE",
    "COMMAND_OUTPUT",
    "LOG",
    "TEST_ARTIFACT",
    "RUNTIME_ARTIFACT",
    "KEYFRAME",
    "SCREENSHOT",
)

# Only the first is admissible on an evidence record. The other two exist so a
# pipeline can *say* it estimated rather than silently presenting a guess.
LOCATOR_ORIGINS = ("READ_FROM_ARTIFACT", "ESTIMATED", "ASSUMED")
ADMISSIBLE_ORIGIN = "READ_FROM_ARTIFACT"

CAPTURE_STATES = ("CAPTURED", "BLOCKED_BY_RIGHTS", "BLOCKED_BY_ACCESS", "ABSENT", "GAP")

# A capture state that carries no bytes. None of these may produce an evidence
# record, and each is a different thing to schedule.
NON_EVIDENCE_STATES = {"BLOCKED_BY_RIGHTS", "BLOCKED_BY_ACCESS", "ABSENT", "GAP"}


class ContractError(Exception):
    """A checked invariant disagreed. Exit 2."""


class InputError(Exception):
    """The input is absent or unreadable. Exit 64, never 2."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def byte_digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load_json(path) -> Any:
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


def normalise_path(value: str, label: str) -> PurePosixPath:
    non_empty_str(value, label)
    path = PurePosixPath(value.rstrip("/"))
    if path.is_absolute():
        raise ContractError(f"{label} must be repository-relative, got {value!r}")
    if ".." in path.parts:
        raise ContractError(f"{label} contains a traversal segment")
    return path


def require_read_origin(origin: Any, label: str) -> str:
    """Only a locator parsed out of captured bytes may become evidence."""
    if origin not in LOCATOR_ORIGINS:
        raise ContractError(f"{label} must be one of {list(LOCATOR_ORIGINS)}")
    if origin != ADMISSIBLE_ORIGIN:
        raise ContractError(
            f"{label} is {origin}; a timestamp computed from text length looks exactly "
            "like one that was read -- same format, same plausible value -- and it "
            "will be quoted back as though someone checked"
        )
    return origin
