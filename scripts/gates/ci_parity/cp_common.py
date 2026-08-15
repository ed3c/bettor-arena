#!/usr/bin/env python3
"""Shared exits, vocabulary, and the surfaces that have no local equivalent.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagreed, 64 the input or invocation is unusable.

The whole module exists for one sentence: **a local PASS is not a remote PASS.**
A green local run and a green GitHub run are two observations of two different
machines, and the interesting cases are exactly the ones where they disagree. So
`PARITY` is a claim about a comparison, and a comparison needs two sides -- a
local result with no exact-head remote result is `NOT_EXERCISED`, never `PARITY`.

`GITHUB_ONLY` is the other half. Some of what a workflow does has no local
counterpart at all: the token permissions it runs under, the hosted runner image,
the cache and artifact services, the billing, and the concurrency cancellation
that can remove the only run at the current head. Nothing local can be evidence
about any of them, so a parity claim that covers them is refused rather than
weakened.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

OK = 0
BAD = 2
USAGE = 64

# The verdict vocabulary. PARTIAL is not a weak PARITY: it means some compared
# surface agreed and some was never compared, and collapsing it upward is the
# failure this vocabulary exists to prevent.
VERDICTS = ("PARITY", "PARTIAL", "DIVERGED", "NOT_EXERCISED")

STATES = [
    "WORKFLOW_AND_ACTION_IDENTITIES_PINNED",
    "REQUIRED_JOB_STEP_SURFACE_INVENTORIED",
    "LOCAL_SIMULATOR_IDENTITY_PINNED_OR_ABSENT",
    "EVENT_PAYLOAD_MATERIALIZED",
    "LOCAL_RUN_COMPLETE",
    "GITHUB_EXACT_HEAD_RUN_INGESTED",
    "DIFFERENCES_NORMALIZED",
    "PARITY_VERDICT",
    "PUBLICATION_POLICY_DECISION",
]

# Surfaces a local run cannot observe. Listed rather than described, because a
# description gets weakened one adjective at a time.
GITHUB_ONLY = (
    "TOKEN_PERMISSIONS",
    "HOSTED_RUNNER_IMAGE",
    "CACHE_SERVICE",
    "ARTIFACT_SERVICE",
    "BILLING",
    "CONCURRENCY_CANCELLATION",
    "SECRETS_STORE",
)

# Every conclusion GitHub can report, and whether it is a pass. Enumerated in
# full: the states that are neither success nor failure are exactly the ones
# that get read as "not a failure, so fine".
CONCLUSIONS = {
    "success": "PASS",
    "failure": "FAIL",
    "skipped": "SKIPPED",
    "cancelled": "CANCELLED",
    "action_required": "ACTION_REQUIRED",
    "neutral": "NEUTRAL",
    "timed_out": "FAIL",
    "startup_failure": "FAIL",
}

# A conclusion that is not a pass and not a failure. None of these is evidence
# that the job would have passed, and a cancelled run is the one that hides
# hardest: concurrency cancellation can remove the only run at the current head.
NOT_EVIDENCE = ("SKIPPED", "CANCELLED", "ACTION_REQUIRED", "NEUTRAL")

FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
ACTION_REF = re.compile(r"^(?P<name>[^@]+)@(?P<ref>[^\s#]+)")

# Runner labels whose image moves under a fixed name. Not an error -- it is what
# GitHub provides -- but a parity claim about runner behaviour cannot be pinned
# to it, so it is recorded as unpinnable rather than pinned.
MUTABLE_RUNNERS = ("ubuntu-latest", "macos-latest", "windows-latest")

# Shapes that must never reach a tracked receipt.
SECRET_SHAPES = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{16,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    re.compile(r"\b(?:token|secret|password)\s*[:=]\s*[^\s\"'{}$]{8,}", re.IGNORECASE),
    # A host path is someone's machine. Built from parts because the repository's
    # root-coupling gate scans tracked source for a literal home root, and a
    # detector for the pattern is indistinguishable from an instance of it.
    *(re.compile(rf"/{root}/[^/\s]+/") for root in ("Users", "home")),
)


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


def non_empty_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value


def full_sha(value: Any, label: str) -> str:
    """Exactly forty hex characters.

    A short SHA is refused rather than expanded. Expanding it here would mean
    resolving it against some repository, and the whole point of pinning a head
    is that the receipt says which commit without needing one.
    """
    if not isinstance(value, str) or FULL_SHA.fullmatch(value) is None:
        raise ContractError(
            f"{label} must be a full 40-character commit SHA; a short SHA names a "
            f"commit only relative to a repository that has it, and a receipt is read "
            f"where that repository is not"
        )
    return value


def find_secrets(text: str) -> list[str]:
    """Credential and host-path shapes, reported as shapes rather than values."""
    found: list[str] = []
    for pattern in SECRET_SHAPES:
        for match in pattern.finditer(text):
            raw = match.group(0)
            # Never echo the value. A gate that prints what it found in order to
            # prove it found it puts the secret in a log, which is where the
            # receipt was not allowed to put it.
            found.append(f"{pattern.pattern[:24]}...[{len(raw)} chars]")
    return sorted(set(found))


def require_clean_receipt(value: Any, label: str) -> None:
    text = json.dumps(value, sort_keys=True)
    found = find_secrets(text)
    if found:
        raise ContractError(
            f"{label} contains {len(found)} credential or host-path shape(s): {found}. "
            "A receipt is committed, mirrored and read by every later session"
        )
