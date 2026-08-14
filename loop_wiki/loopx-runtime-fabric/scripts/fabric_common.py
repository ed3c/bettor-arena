#!/usr/bin/env python3
"""Shared exits, errors and encoding for the LoopX Runtime Fabric.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagrees, 64 the input or invocation is unusable.

There is a third distinction this module needs and the others did not: a
*provider* failure is neither of those. A sandbox that will not start has told
you nothing about the task, and normalising it into a gate FAIL manufactures
evidence about code that never ran.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

OK = 0
BAD = 2
USAGE = 64

SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")

# Failure classes. The split is the point: a caller that cannot tell
# PROVIDER_UNAVAILABLE from GATE_FAIL will retry the wrong thing, or worse,
# record a verdict about code that was never executed.
FAILURE_CLASSES = {
    "TASK_FAILURE",
    "GATE_FAILURE",
    "PROVIDER_UNAVAILABLE",
    "PROVIDER_ERROR",
    "POLICY_REFUSAL",
    "LEASE_REFUSAL",
}


class ContractError(Exception):
    """A checked invariant disagreed. Exit 2."""


class InputError(Exception):
    """The input is absent or unreadable. Exit 64, never 2."""


class ProviderUnavailable(Exception):
    """The runtime could not be reached or started.

    Deliberately not a ContractError. Nothing about the task was observed, so
    nothing about the task may be concluded.
    """


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


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


def positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ContractError(f"{label} must be a positive integer")
    return value


def contained_relative_path(value: Any, label: str) -> str:
    """A repository-relative path that cannot leave its workspace.

    Checked as a path, not as a string: `a/../../b` contains no leading slash
    and still escapes, and a substring check for ".." would reject the
    legitimate filename "..config" while missing "a/%2e%2e/b" on any layer that
    decodes.
    """
    text = non_empty_str(value, label)
    path = PurePosixPath(text)
    if path.is_absolute():
        raise ContractError(f"{label} must be repository-relative, got {text!r}")
    if any(part == ".." for part in path.parts):
        raise ContractError(f"{label} escapes its workspace: {text!r}")
    if "\\" in text:
        raise ContractError(f"{label} must use POSIX separators: {text!r}")
    return text


SUBJECT_KEYS = {"repository", "commit", "tree", "task_id"}


def validate_subject(value: Any, label: str) -> dict[str, Any]:
    subject = exact_object(value, SUBJECT_KEYS, label)
    for field in ("commit", "tree"):
        if SHA40.fullmatch(str(subject[field])) is None:
            raise ContractError(f"{label}.{field} must be a full 40-hex sha")
    non_empty_str(subject["repository"], f"{label}.repository")
    non_empty_str(subject["task_id"], f"{label}.task_id")
    return subject
