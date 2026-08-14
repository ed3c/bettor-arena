#!/usr/bin/env python3
"""Shared exits, errors, and the three answers this module keeps apart.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagreed, 64 the input or invocation is unusable.

The vocabulary at the bottom is the module's whole point. These three are
routinely collapsed into one, and the collapse is invisible in the output:

    CLEAN        the server looked and found nothing wrong
    UNKNOWN      nobody looked -- unsupported language, unindexed path
    SERVER_FAILED the server crashed, timed out, or never initialised

A crashed server returns no diagnostics. So does a clean file. So does a file
in a language the server does not handle. Reporting all three as "zero errors"
means a broken index and a genuinely clean tree produce identical evidence, and
whoever reads it downstream cannot tell which one they have.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any

OK = 0
BAD = 2
USAGE = 64

SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

# Never merged, never defaulted to one another.
QUERY_STATES = ("CLEAN", "FINDINGS", "UNKNOWN", "SERVER_FAILED", "NOT_EXERCISED")

# The states in which a result carries usable evidence about the code. UNKNOWN
# and SERVER_FAILED do not, and that is the distinction the module protects.
EVIDENCE_BEARING = {"CLEAN", "FINDINGS"}


class ContractError(Exception):
    """A checked invariant disagreed. Exit 2."""


class InputError(Exception):
    """The input is absent or unreadable. Exit 64, never 2."""


class ServerUnavailable(Exception):
    """The language server could not be used. Not a finding about the code."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def text_digest(raw: bytes) -> str:
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


def positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ContractError(f"{label} must be a positive integer")
    return value


def sha256_ref(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_REF.fullmatch(value) is None:
        raise ContractError(f"{label} must be sha256:<64 lowercase hex>")
    return value


def iso_timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or ISO_UTC.fullmatch(value) is None:
        raise ContractError(f"{label} must be an RFC3339 UTC timestamp ending in Z")
    return value


def parse_time(value: str, label: str) -> datetime:
    iso_timestamp(value, label)
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def normalise_path(value: str, label: str) -> PurePosixPath:
    non_empty_str(value, label)
    path = PurePosixPath(value.rstrip("/"))
    if path.is_absolute():
        raise ContractError(f"{label} must be workspace-relative, got {value!r}")
    if ".." in path.parts:
        raise ContractError(
            f"{label} contains a traversal segment; a query that can climb out of its "
            "workspace returns results about a tree it was not asked about"
        )
    return path


def state_bears_evidence(state: str, label: str) -> bool:
    if state not in QUERY_STATES:
        raise ContractError(f"{label} must be one of {list(QUERY_STATES)}")
    return state in EVIDENCE_BEARING
