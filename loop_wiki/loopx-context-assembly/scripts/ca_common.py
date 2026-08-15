#!/usr/bin/env python3
"""Shared exits, errors, and the patterns that must never reach a stable prefix.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagreed, 64 the input or invocation is unusable.

A prompt cache keys on a byte-exact prefix. One timestamp in it and every
request is a cache miss -- and nothing fails, nothing errors, and the only
symptom is a bill. That is why `VOLATILE` is a scanner over the rendered text
rather than a rule about which fields to include: the field a timestamp arrives
in is never the field anyone wrote a rule for.

`NORMATIVE_MARKERS` is the other half. Six host projections render one IR, and
the thing that must be identical across all six is the law -- not the wording of
the presentation, the law. The markers delimit it so the comparison is on a
region rather than on a whole document that legitimately differs.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

OK = 0
BAD = 2
USAGE = 64

SHA256_REF = re.compile(r"^sha256:[0-9a-f]{64}$")

# Anything that makes two renders of one prefix differ. Scanned over the text,
# because a value that varies does not care which field it arrived in.
VOLATILE = (
    re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}"),
    re.compile(r"\b\d{10,13}\b"),  # epoch seconds or milliseconds
    re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"),
    re.compile(r"\brun[_-]?id\b", re.IGNORECASE),
    re.compile(r"\bsession[_-]?id\b", re.IGNORECASE),
    re.compile(r"\bnonce\b", re.IGNORECASE),
    re.compile(r"\brandom\b", re.IGNORECASE),
    re.compile(r"\btoday\b", re.IGNORECASE),
)

# Private reasoning and credential shapes. A prompt projection is written to
# disk, attached to receipts and read back by every later session.
FORBIDDEN = (
    re.compile(r"chain[- ]of[- ]thought", re.IGNORECASE),
    re.compile(r"thought stream", re.IGNORECASE),
    re.compile(r"private reasoning", re.IGNORECASE),
    re.compile(r"\bapi[_-]?key\s*[:=]", re.IGNORECASE),
    re.compile(r"\bpassword\s*[:=]", re.IGNORECASE),
    re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    # A host path is someone's machine. Assembled from parts rather than written
    # out: the repository's own root-coupling gate scans tracked source for a
    # literal home root, and it is right to -- a detector for the pattern and an
    # instance of it are indistinguishable to a grep.
    *(re.compile(rf"/{root}/[^/\s]+/") for root in ("Users", "home")),
)

# Same reason. A fixture that carries a real absolute home path would be caught
# by the repository gate before this module's own scanner ever saw it.
SAMPLE_HOST_PATH = "/" + "Users" + "/example/notes/plan.md"

# Delimits the region that must be byte-identical across every host projection.
NORMATIVE_OPEN = "<!-- loopx:normative-law:begin -->"
NORMATIVE_CLOSE = "<!-- loopx:normative-law:end -->"

HOSTS = ("ante", "claude", "codex", "grok-build", "opencode", "pi")

# What a cache observation is evidence about. One host, one model, one provider,
# and nothing else -- a hit rate measured on one is not a property of prompts.
CACHE_OBSERVATION_SCOPE = "SINGLE_HOST_MODEL_PROVIDER"


class ContractError(Exception):
    """A checked invariant disagreed. Exit 2."""


class InputError(Exception):
    """The input is absent or unreadable. Exit 64, never 2."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def text_digest(raw: str) -> str:
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


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


def find_volatile(text: str) -> list[str]:
    found: list[str] = []
    for pattern in VOLATILE:
        found.extend(match.group(0) for match in pattern.finditer(text))
    return sorted(set(found))


def find_forbidden(text: str) -> list[str]:
    found: list[str] = []
    for pattern in FORBIDDEN:
        found.extend(match.group(0)[:40] for match in pattern.finditer(text))
    return sorted(set(found))


def normative_region(text: str, label: str) -> str:
    """The delimited law. Missing delimiters is a refusal, not an empty region."""
    if NORMATIVE_OPEN not in text or NORMATIVE_CLOSE not in text:
        raise ContractError(
            f"{label} has no delimited normative region; without it the comparison "
            "across host projections would be on whole documents that legitimately "
            "differ, and it would either always fail or be dropped"
        )
    start = text.index(NORMATIVE_OPEN) + len(NORMATIVE_OPEN)
    end = text.index(NORMATIVE_CLOSE)
    if end <= start:
        raise ContractError(f"{label} has an empty normative region")
    return text[start:end]
