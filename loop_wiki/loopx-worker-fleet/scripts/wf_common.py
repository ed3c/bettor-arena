#!/usr/bin/env python3
"""Shared exits, errors, and the path-overlap rule the whole fleet rests on.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagreed, 64 the input or invocation is unusable.

`paths_overlap` at the bottom is small and load-bearing. Two Workers holding
"different" path leases that turn out to nest is the failure that produces a
tree neither of them wrote alone, and the obvious implementation of the check is
wrong in a way that looks right:

    "loop_wiki/a".startswith("loop_wiki/a")     -> True, correct
    "loop_wiki/ab".startswith("loop_wiki/a")    -> True, WRONG
    "loop_wiki/a/b".startswith("loop_wiki/a")   -> True, correct

A string prefix says `loop_wiki/ab` is inside `loop_wiki/a`. It is not; they are
siblings. The comparison has to be by path component, or the scheduler refuses
leases that were fine and eventually someone loosens it.
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


class ContractError(Exception):
    """A checked invariant disagreed. Exit 2."""


class InputError(Exception):
    """The input is absent or unreadable. Exit 64, never 2."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


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


def sha256_ref_or_none(value: Any, label: str) -> str | None:
    """A digest, or None. Anything else is a malformed digest, not an absent one."""
    if value is None:
        return None
    if not isinstance(value, str) or SHA256_REF.fullmatch(value) is None:
        raise ContractError(
            f"{label} must be sha256:<64 lowercase hex> or null; a truncated or "
            "mistyped digest is not the same as no digest, and treating it as absent "
            "would let a typo read as 'not exercised'"
        )
    return value


def iso_timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or ISO_UTC.fullmatch(value) is None:
        raise ContractError(f"{label} must be an RFC3339 UTC timestamp ending in Z")
    return value


def parse_time(value: str, label: str) -> datetime:
    iso_timestamp(value, label)
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def normalise_path(value: str, label: str) -> PurePosixPath:
    """A repository-relative path with no traversal and no absolute root."""
    non_empty_str(value, label)
    path = PurePosixPath(value.rstrip("/"))
    if path.is_absolute():
        raise ContractError(f"{label} must be repository-relative, got {value!r}")
    if ".." in path.parts:
        raise ContractError(
            f"{label} contains a traversal segment; a lease that can climb out of "
            "itself is not a lease on the path it names"
        )
    return path


def paths_overlap(left: str, right: str) -> bool:
    """Do these two path leases cover any of the same tree?

    By component, not by string prefix. `loop_wiki/ab` and `loop_wiki/a` are
    siblings; a startswith test calls them nested, and the scheduler would then
    refuse a pair of leases that were never in conflict.
    """
    a = normalise_path(left, "path")
    b = normalise_path(right, "path")
    if a == b:
        return True
    shorter, longer = (a, b) if len(a.parts) <= len(b.parts) else (b, a)
    return longer.parts[: len(shorter.parts)] == shorter.parts


def glob_root(pattern: str) -> str:
    """The concrete directory a `path/**` lease actually covers."""
    return pattern.rstrip("/").removesuffix("/**").rstrip("/")
