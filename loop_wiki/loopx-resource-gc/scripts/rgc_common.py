#!/usr/bin/env python3
"""Shared exits, errors and the retention vocabulary.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagreed, 64 the input or invocation is unusable. There is a fourth state this
module needs and does not encode as an exit code: disk exhaustion. It is a typed
resource state on the receipt instead, because a full disk is not a task that
failed and not a gate that disagreed -- reporting it as either sends someone to
debug code that was fine.

The retention classes below are closed. A resource whose class is not in the
list is refused rather than defaulted, because the default anyone would pick is
the permissive one and the resource nobody classified is the one nobody looked
at.
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
ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

# The resource classes #97 names. Closed, and each one carries its own default
# retention because "how long do we keep this" is a property of what it is.
RESOURCE_CLASSES = {
    "WORKTREE": "MUTABLE_RECREATABLE",
    "BRANCH": "MUTABLE_RECREATABLE",
    "PROCESS": "EPHEMERAL",
    "PORT": "EPHEMERAL",
    "MOUNT": "EPHEMERAL",
    "STDIO_LOG": "EXPIRING",
    "ARTIFACT": "CONTENT_ADDRESSED",
    "LOOPX_SNAPSHOT": "MUTABLE_RECREATABLE",
    "LEDGER_SEGMENT": "IMMUTABLE_EVIDENCE",
    "HUMAN_DECISION": "IMMUTABLE_EVIDENCE",
    "RELEASE_RECEIPT": "IMMUTABLE_EVIDENCE",
    "BLOCKED_EVIDENCE": "IMMUTABLE_EVIDENCE",
    "LSP_INDEX": "MUTABLE_RECREATABLE",
    "DEPENDENCY_CACHE": "MUTABLE_RECREATABLE",
    "VECTOR_INDEX": "MUTABLE_RECREATABLE",
    "GRAPH_INDEX": "MUTABLE_RECREATABLE",
    "WAL": "IMMUTABLE_EVIDENCE",
    "MEMORY_PROJECTION": "MUTABLE_RECREATABLE",
    "CI_SIMULATION_CACHE": "EXPIRING",
}

RETENTION_KINDS = (
    "IMMUTABLE_EVIDENCE",
    "CONTENT_ADDRESSED",
    "MUTABLE_RECREATABLE",
    "EXPIRING",
    "EPHEMERAL",
)

# The two that may never be selected for deletion by this module at all, no
# matter what a plan says or a human admits. Deleting a ledger segment or a
# Human decision destroys the record of why everything else was allowed.
NEVER_DELETABLE = {"IMMUTABLE_EVIDENCE"}


class ContractError(Exception):
    """A checked invariant disagreed. Exit 2."""


class InputError(Exception):
    """The input is absent or unreadable. Exit 64, never 2."""


class ResourceExhausted(Exception):
    """A resource limit was reached. Neither a task failure nor a gate refusal."""


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
        raise ContractError(f"{label} must be repository-relative, got {value!r}")
    if ".." in path.parts:
        raise ContractError(
            f"{label} contains a traversal segment; a GC that can climb out of the "
            "root it was pointed at deletes outside the tree it was scoped to"
        )
    return path


def classify(resource_class: str, label: str) -> str:
    """The retention kind for a resource class, refusing unknown classes."""
    if resource_class not in RESOURCE_CLASSES:
        raise ContractError(
            f"{label} has unknown resource class {resource_class!r}; the vocabulary is "
            f"closed ({len(RESOURCE_CLASSES)} classes) because the default anyone "
            "would pick is the permissive one, and an unclassified resource is one "
            "nobody looked at"
        )
    return RESOURCE_CLASSES[resource_class]
