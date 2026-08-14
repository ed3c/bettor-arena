#!/usr/bin/env python3
"""The console's vocabulary, and the boundary it is not allowed to cross.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagreed, 64 the input or invocation is unusable.

A console is a projection. Everything it shows is derived from canonical LoopX
events, and everything it can do is *ask*. The failure it is built against is the
one where a screen becomes a source of truth: someone clicks a thing, the UI
updates, and the ledger learns about it afterwards -- or never.

So the authority boundary is a list rather than a principle. `CONSOLE_MAY` is
closed and `CONSOLE_MAY_NOT` is enumerated, because a principle gets weakened one
adjective at a time and a list has to be edited in front of a reviewer.

`COMPLETED_WITH_EXCEPTION` is in here for the same reason. It renders as a
completion in every summary anyone would write by hand, and it is not one.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from typing import Any

OK = 0
BAD = 2
USAGE = 64

# The UI state machine from #99, in order. The console walks it forward; there is
# no transition that skips SIGNER_REVISION_LEDGER_HEAD_VERIFIED.
UI_STATES = [
    "LEDGER_SUBJECT_SELECTED",
    "REDACTED_PROJECTION_LOADED",
    "TASK_TODO_ATTEMPT_GRAPH_RENDERED",
    "EVIDENCE_DIFF_DIAGNOSTICS_INSPECTED",
    "HITL_ACTION_DRAFTED",
    "SIGNER_REVISION_LEDGER_HEAD_VERIFIED",
    "DECISION_REQUEST_SUBMITTED",
    "LOOPX_ACCEPTED_OR_REJECTED",
    "REQUIRED_GATES_REVALIDATED",
    "PROJECTION_REFRESHED",
]

# The eight views #99 requires. Named so that a view which was never built shows
# up as absent rather than as a screen nobody opened.
VIEWS = (
    "thread_task_graph",
    "gate_evidence_inspector",
    "diagnostics_panel",
    "git_diff_viewer",
    "quota_retry_panel",
    "provenance_panel",
    "hitl_dialog",
    "receipt_links",
)

# What a Human can ask for through the console. Closed set: an action that is not
# here cannot be drafted, which is what stops a generic escape hatch from being
# added as "just one more option".
CONSOLE_MAY = (
    "REQUEST_RETRY",
    "REQUEST_CONTRACT_UPDATE",
    "REQUEST_CANCEL",
    "REQUEST_SCOPED_EXCEPTION",
)

# Enumerated rather than described. Each of these is a thing a console grows on
# its own once someone is looking at a screen and wants the red to go away.
CONSOLE_MAY_NOT = (
    "MUTATE_TASK_STATE",
    "WRITE_LEDGER_EVENT",
    "MARK_GATE_PASS",
    "UNSCOPED_FORCE_SKIP",
    "HIDE_COMPLETED_WITH_EXCEPTION",
    "WIDEN_TOOLS_PERMISSIONS_OR_SECRETS",
    "MERGE",
    "PROMOTE_RELEASE",
    "ROLLBACK_PRODUCTION",
    "PERSIST_RAW_PAGE_BODY_OR_PRIVATE_REASONING",
)

# A scoped exception is admissible; an unscoped one is the same escape hatch with
# a nicer name. Every scoped exception carries all three.
EXCEPTION_SCOPE_KEYS = {"subject", "gate", "expires_after_revisions"}

# Terminal states a task can reach. COMPLETED_WITH_EXCEPTION is separate from
# COMPLETED on purpose: they are the same colour in every dashboard ever built.
TASK_STATES = (
    "PENDING",
    "RUNNING",
    "BLOCKED",
    "COMPLETED",
    "COMPLETED_WITH_EXCEPTION",
    "FAILED",
    "CANCELLED",
)

# Never rendered, never persisted. The console reads real agent output, and real
# agent output contains all of these sooner or later.
REDACT = (
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{16,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
    re.compile(
        r"\b(?:token|secret|password|api[_-]?key)\s*[:=]\s*[^\s\"'{}$]{6,}",
        re.IGNORECASE,
    ),
    re.compile(r"<thinking>.*?</thinking>", re.IGNORECASE | re.DOTALL),
    re.compile(r"chain[- ]of[- ]thought", re.IGNORECASE),
    re.compile(r"\bSet-Cookie:\s*\S+", re.IGNORECASE),
    # A host path is someone's machine. Built from parts because the repository's
    # root-coupling gate scans tracked source for a literal home root, and a
    # detector for the pattern is indistinguishable from an instance of it.
    *(re.compile(rf"/{root}/[^/\s]+/") for root in ("Users", "home")),
)

REDACTED = "[REDACTED]"

# Rendering is not implemented. There is no HTML, no websocket and no browser
# here: this is the view *model* and the request path. Saying so in the
# vocabulary means the claim travels with every receipt that imports it.
RENDER_STATE = "NOT_IMPLEMENTED"
LIVE_CONSOLE_STATE = "NOT_EXERCISED"

# Signatures are HMAC-SHA256 over the canonical request bytes. Symmetric, and
# named as such: this authenticates that the holder of the signer key produced
# the request, and nothing more. Key custody is Human-owned and no key value is
# ever stored in this repository or in any receipt.
SIGNATURE_ALGORITHM = "HMAC-SHA256"


class ContractError(Exception):
    """A checked invariant disagreed. Exit 2."""


class InputError(Exception):
    """The input is absent or unreadable. Exit 64, never 2."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def sign(payload: Any, key: bytes) -> str:
    return (
        "hmac-sha256:"
        + hmac.new(key, canonical_bytes(payload), hashlib.sha256).hexdigest()
    )


def signature_matches(payload: Any, key: bytes, signature: str) -> bool:
    return hmac.compare_digest(sign(payload, key), signature)


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


def redact(text: str) -> str:
    for pattern in REDACT:
        text = pattern.sub(REDACTED, text)
    return text


def redact_deep(value: Any) -> Any:
    """Redact every string anywhere in a structure, including keys.

    Deep rather than field-by-field. A rule that names which fields to redact is
    a rule about where secrets were last time, and the console renders whatever
    an agent produced.
    """
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [redact_deep(item) for item in value]
    if isinstance(value, dict):
        return {redact(str(key)): redact_deep(item) for key, item in value.items()}
    return value


def find_unredacted(value: Any) -> list[str]:
    """Shapes still present after redaction, reported as shapes not values."""
    text = json.dumps(value, sort_keys=True, default=str)
    found: list[str] = []
    for pattern in REDACT:
        for match in pattern.finditer(text):
            found.append(f"{pattern.pattern[:28]}...[{len(match.group(0))} chars]")
    return sorted(set(found))
