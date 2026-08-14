#!/usr/bin/env python3
"""Provider identity, and why a managed benchmark is not OSS evidence.

Mem0 can be run two ways, and the difference is not a deployment detail:

    OSS_SELF_HOSTED   a package you pin, a store you run, a model you chose
    MANAGED_SERVICE   a URL, a version you are told, a model that changes

Numbers from one do not describe the other. A recall figure from the managed
service was produced by a model nobody in this repository selected, on hardware
nobody here provisioned, against an index nobody here built -- and the OSS
deployment shares none of those. So a receipt records which mode produced it,
and `evidence_applies_to` refuses to widen: a MANAGED_SERVICE receipt is
evidence about MANAGED_SERVICE and nothing else.

The rule reads as pedantic until the day someone plans capacity from it.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from memory import SHA, ContractError  # noqa: E402

MODES = ("OSS_SELF_HOSTED", "MANAGED_SERVICE")

IDENTITY_KEYS = {
    "mode",
    "package_version",
    "server_endpoint",
    "storage_identity",
    "embedding_identity",
    "llm_identity",
    "namespace",
}

# What a receipt from each mode is evidence about. Deliberately not a hierarchy:
# neither mode's numbers describe the other, in either direction.
EVIDENCE_SCOPE = {
    "OSS_SELF_HOSTED": ("OSS_SELF_HOSTED",),
    "MANAGED_SERVICE": ("MANAGED_SERVICE",),
}


def validate_identity(value: Any, label: str = "provider identity") -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != IDENTITY_KEYS:
        missing = sorted(IDENTITY_KEYS - set(value or {}))
        extra = sorted(set(value or {}) - IDENTITY_KEYS)
        raise ContractError(f"{label} fields drifted; missing={missing}, extra={extra}")

    mode = value["mode"]
    if mode not in MODES:
        raise ContractError(f"{label}.mode must be one of {list(MODES)}")

    for field in (
        "storage_identity",
        "embedding_identity",
        "llm_identity",
        "namespace",
    ):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ContractError(
                f"{label}.{field} must be named; a projection whose embedding or store "
                "is unrecorded cannot be rebuilt into the same index later, and the "
                "difference shows up as retrieval quality rather than as an error"
            )

    if mode == "OSS_SELF_HOSTED":
        if (
            not isinstance(value["package_version"], str)
            or not value["package_version"]
        ):
            raise ContractError(
                f"{label} is self-hosted with no pinned package version; the thing "
                "that produced this index is then whatever was installed that day"
            )
        if value["server_endpoint"] is not None:
            raise ContractError(
                f"{label} is self-hosted and names a server endpoint; if a hosted "
                "endpoint answered the query, the numbers describe that service"
            )
    else:
        if (
            not isinstance(value["server_endpoint"], str)
            or not value["server_endpoint"]
        ):
            raise ContractError(f"{label} is managed with no endpoint recorded")
        if value["package_version"] is not None:
            raise ContractError(
                f"{label} is managed and pins a package version; the service runs what "
                "it runs, and recording a local version implies a control nobody has"
            )
    return value


def evidence_applies_to(identity: dict[str, Any]) -> tuple[str, ...]:
    """Which modes a receipt from this identity is evidence about."""
    validate_identity(identity)
    return EVIDENCE_SCOPE[identity["mode"]]


def require_same_mode(receipt_identity: dict[str, Any], claimed_mode: str) -> None:
    """Refuse a receipt being read as evidence about a mode it did not run in."""
    if claimed_mode not in MODES:
        raise ContractError(f"unknown mode {claimed_mode!r}")
    scope = evidence_applies_to(receipt_identity)
    if claimed_mode not in scope:
        raise ContractError(
            f"a {receipt_identity['mode']} receipt is being read as evidence about "
            f"{claimed_mode}. The model, the hardware and the index are all different, "
            "and none of them are ones this repository selected -- the number describes "
            "the service that produced it"
        )


PROVIDER_STATES = ("AVAILABLE", "UNAVAILABLE", "NOT_EXERCISED")


def provider_state(value: Any, label: str) -> str:
    """A provider's own health. Never a verdict about memory or a task.

    Kept as its own vocabulary because the three answers get merged constantly:
    a store that is down, a query that found nothing, and a memory that
    disagrees with the repository are three different situations, and only the
    third is about memory at all.
    """
    if value not in PROVIDER_STATES:
        raise ContractError(
            f"{label} must be one of {list(PROVIDER_STATES)}; an unreachable store "
            "reported as a passing query says the memory was checked when nothing was"
        )
    return value


def digest_ref(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA.fullmatch(value) is None:
        raise ContractError(f"{label} must be sha256:<64 hex>")
    return value
