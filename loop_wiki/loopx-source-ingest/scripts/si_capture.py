#!/usr/bin/env python3
"""Capture, rights, and the credentials that must not end up in a locator.

Three things happen here and each has a way of going quietly wrong.

**Rights are checked before bytes are read**, not after. A capture that reads
first and checks second has already made the copy, and the check then decides
whether to admit something that already exists on disk.

**A blocked source is recorded, never omitted.** The failure #104 names is
"unsupported/blocked source silently omitted" -- and silence is indistinguishable
from "we looked and there was nothing". Every declared source ends in exactly one
capture state, and four of the five carry no bytes.

**A URL is a place a credential hides.** Session tokens, signed URLs and API keys
arrive in query strings, and a locator is the field that gets copied into every
downstream note. So the URL is stripped to its path before it becomes a locator,
and the stripped parameters are counted rather than kept.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse, urlunparse

from si_common import (
    CAPTURE_STATES,
    NON_EVIDENCE_STATES,
    ContractError,
    byte_digest,
    exact_object,
    iso_timestamp,
    non_empty_str,
)

# Query parameters that carry access rather than identity. Matched by name
# because their values are opaque by design -- a token that looked like a token
# would not be much of a token.
CREDENTIAL_PARAMS = re.compile(
    r"^(?:access_token|api[_-]?key|auth|authorization|credential|id_token|key|"
    r"password|refresh_token|session|sig|signature|token|x-amz-signature|"
    r"x-goog-signature)$",
    re.IGNORECASE,
)

DECLARATION_KEYS = {
    "source_id",
    "source_type",
    "url",
    "dependency_key",
    "rights_state",
    "destination_authorized",
    "declared_by",
}

RIGHTS_STATES = ("AUTHORIZED", "NOT_AUTHORIZED", "UNKNOWN")


def strip_credentials(url: str) -> tuple[str, list[str]]:
    """Return the URL without credential-bearing parameters, and their names.

    Names, not values. Recording the value would move the credential from the
    URL into the receipt, which is the same problem one file further along.
    """
    parsed = urlparse(url)
    kept, removed = [], []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if CREDENTIAL_PARAMS.fullmatch(key):
            removed.append(key)
        else:
            kept.append(f"{key}={value}")
    cleaned = urlunparse(parsed._replace(query="&".join(kept), fragment=""))
    return cleaned, sorted(removed)


def validate_declaration(value: Any, label: str) -> dict[str, Any]:
    declaration = exact_object(value, DECLARATION_KEYS, label)
    non_empty_str(declaration["source_id"], f"{label}.source_id")
    non_empty_str(declaration["dependency_key"], f"{label}.dependency_key")
    non_empty_str(declaration["declared_by"], f"{label}.declared_by")

    if declaration["rights_state"] not in RIGHTS_STATES:
        raise ContractError(
            f"{label}.rights_state must be one of {list(RIGHTS_STATES)}"
        )
    if not isinstance(declaration["destination_authorized"], bool):
        raise ContractError(f"{label}.destination_authorized must be a boolean")

    url = declaration["url"]
    if url is not None:
        non_empty_str(url, f"{label}.url")
        _, removed = strip_credentials(url)
        if removed:
            raise ContractError(
                f"{label}.url carries {removed} in its query string. A URL becomes a "
                "locator, and a locator is copied into every note that cites the "
                "source -- strip it before declaring, not after"
            )
    return declaration


def capture(
    declaration: dict[str, Any], root: Path, relative: str | None, at: str
) -> dict[str, Any]:
    """Capture an artifact, or record precisely why not. Never omits."""
    validate_declaration(declaration, "declaration")
    iso_timestamp(at, "capture.at")

    # Rights first. A capture that reads and then checks has already made the
    # copy, and the check is then deciding about something that exists.
    if declaration["rights_state"] != "AUTHORIZED":
        return _blocked(
            declaration,
            "BLOCKED_BY_RIGHTS",
            f"rights are {declaration['rights_state']}; capturing first and checking "
            "afterwards means the copy already exists when the check runs",
            at,
        )
    if not declaration["destination_authorized"]:
        return _blocked(
            declaration,
            "BLOCKED_BY_ACCESS",
            "the data destination is not authorized; raw source copied to an "
            "unapproved provider is a copy nobody can recall",
            at,
        )
    if relative is None:
        return _blocked(
            declaration,
            "GAP",
            "no artifact was captured. A gap is schedulable work; omitting it "
            "silently is indistinguishable from having looked and found nothing",
            at,
        )

    path = root / relative
    try:
        raw = path.read_bytes()
    except OSError as exc:
        return _blocked(
            declaration,
            "ABSENT",
            f"the declared artifact could not be read: {exc}",
            at,
        )

    return {
        "source_id": declaration["source_id"],
        "source_type": declaration["source_type"],
        "state": "CAPTURED",
        "artifact_path": relative,
        "artifact_digest": byte_digest(raw),
        "artifact_bytes": len(raw),
        "captured_at": at,
        "locator_base": strip_credentials(declaration["url"])[0]
        if declaration["url"]
        else relative,
        "dependency_key": declaration["dependency_key"],
        "reason": "captured under authorized rights to an authorized destination",
    }


def _blocked(
    declaration: dict[str, Any], state: str, reason: str, at: str
) -> dict[str, Any]:
    if state not in CAPTURE_STATES or state not in NON_EVIDENCE_STATES:
        raise ContractError(f"{state!r} is not a non-evidence capture state")
    return {
        "source_id": declaration["source_id"],
        "source_type": declaration["source_type"],
        "state": state,
        "artifact_path": None,
        "artifact_digest": None,
        "artifact_bytes": 0,
        "captured_at": at,
        "locator_base": None,
        "dependency_key": declaration["dependency_key"],
        "reason": reason,
    }


def bears_evidence(capture_record: dict[str, Any]) -> bool:
    """Only a CAPTURED artifact can support an evidence record."""
    state = capture_record["state"]
    if state not in CAPTURE_STATES:
        raise ContractError(f"unknown capture state {state!r}")
    return state == "CAPTURED"


def gaps(captures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Everything that did not produce bytes, as schedulable work."""
    return sorted(
        (
            {
                "source_id": record["source_id"],
                "state": record["state"],
                "reason": record["reason"],
                "schedulable": True,
            }
            for record in captures
            if record["state"] in NON_EVIDENCE_STATES
        ),
        key=lambda entry: entry["source_id"],
    )
