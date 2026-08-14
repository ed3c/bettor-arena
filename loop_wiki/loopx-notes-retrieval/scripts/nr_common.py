#!/usr/bin/env python3
"""Shared exits, errors, and the four things a retrieval can mean by "nothing".

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagreed, 64 the input or invocation is unusable, 70 the provider is absent.

The vocabulary below exists because a vector search returning an empty list is
the most over-interpreted result in this whole system. It means one thing:

    no chunk in this index was close enough to this query embedding

It does not mean the notes are silent on the subject. It does not mean the claim
is false. And it is indistinguishable, in an empty list, from an index that was
never built, a provider that is not installed, and a subject that moved since
the index was made.

    HIT              chunks came back
    MISS             the index answered, and nothing was near enough
    NOT_INDEXED      this content is not in the index
    PROVIDER_ABSENT  nothing was asked, because nothing was there to ask

`ABSENCE_PROOF` is the field that stops the slide: no retrieval state proves
absence, and the one that comes closest -- MISS -- says so on the record.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

OK = 0
BAD = 2
USAGE = 64
PROVIDER = 70

SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

RETRIEVAL_STATES = ("HIT", "MISS", "NOT_INDEXED", "PROVIDER_ABSENT")

# What each state proves about the notes. Every value is the same, deliberately:
# a retrieval says something about an index, and nothing about the world.
ABSENCE_PROOF = {
    "HIT": "NONE",
    "MISS": "NONE",
    "NOT_INDEXED": "NONE",
    "PROVIDER_ABSENT": "NONE",
}

PROJECTION_ROLES = ("OPENWIKI_STATIC", "VECTOR", "GRAPH")

# The final authority, and it is not any of the projections above.
FINAL_AUTHORITY = "CURRENT_SOURCE_AND_EVIDENCE"

FRESHNESS_STATES = ("CURRENT", "STALE_SUBJECT", "STALE_POLICY", "NOT_BUILT")


class ContractError(Exception):
    """A checked invariant disagreed. Exit 2."""


class InputError(Exception):
    """The input is absent or unreadable. Exit 64, never 2."""


class ProviderAbsent(Exception):
    """No vector or graph provider. Exit 70, and never a claim about content."""


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


def retrieval_state(value: Any, label: str) -> str:
    if value not in RETRIEVAL_STATES:
        raise ContractError(
            f"{label} must be one of {list(RETRIEVAL_STATES)}; an empty result list "
            "is the same shape for a miss, an unbuilt index and an absent provider, "
            "and only this field tells them apart"
        )
    return value


def proves_absence(state: str) -> str:
    """What this retrieval state proves about the notes. Always NONE."""
    retrieval_state(state, "state")
    return ABSENCE_PROOF[state]
