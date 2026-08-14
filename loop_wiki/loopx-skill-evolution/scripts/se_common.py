#!/usr/bin/env python3
"""Shared exits, errors and sealing primitives for Skill/prompt evolution.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagreed, 64 the input or invocation is unusable.

The sealing primitive at the bottom is the one piece the rest of the module
leans on. A holdout that is "kept separate by convention" is kept separate until
someone writes a convenient helper, so separation here is a commitment: the
answers are hashed into a seal before the experiment runs, and the runner is
handed cases with no answer field at all. Revealing compares the answers against
the seal, so an answer set swapped after the fact does not match and the run is
refused rather than scored.
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

# Anything that makes two renders of one prompt differ. A prompt carrying a
# timestamp is not comparable across runs and silently destroys prompt-cache
# reuse, so both effects are caught by the same check.
VOLATILE_PATTERNS = (
    re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"),
    re.compile(r"\brandom[_-]?(?:seed|bytes|nonce)\b", re.IGNORECASE),
    re.compile(r"\bnonce\s*[:=]"),
    re.compile(r"\bgenerated[_ ]at\b", re.IGNORECASE),
    re.compile(r"\bepoch\s*[:=]\s*\d+"),
)


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


def find_volatile(text: str) -> list[str]:
    """Substrings that would make two renders of one prompt differ."""
    found = []
    for pattern in VOLATILE_PATTERNS:
        found.extend(match.group(0) for match in pattern.finditer(text))
    return sorted(set(found))


def seal(answers: Any) -> str:
    """A commitment to an answer set, computed before the experiment runs.

    Not encryption -- it does not have to be. The point is that the answers
    cannot be substituted afterwards to match whatever the candidate produced,
    and that the runner never needs the answers at all in order to run.
    """
    return digest({"sealed_answers": answers})


def reveal(answers: Any, sealed_digest: str) -> Any:
    """Open a seal, refusing if the answers are not the ones committed to."""
    if seal(answers) != sealed_digest:
        raise ContractError(
            "the revealed answers do not match the seal recorded before the run; "
            "either the holdout was edited after seeing results, or these are not "
            "the answers this experiment committed to -- both make the score "
            "meaningless in the same way"
        )
    return answers
