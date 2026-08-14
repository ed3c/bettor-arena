#!/usr/bin/env python3
"""Drafting, signing and accepting a Human decision request.

A request is a question, not a change. LoopX accepts or rejects it, and the thing
that makes acceptance safe is that the request names exactly which world it was
drafted against: the ledger head and the state revision. A request drafted while
looking at a screen and submitted after the ledger moved is a decision about
something that is no longer there, and it looks identical to a fresh one.

Signing is HMAC-SHA256 and it is named as such -- it authenticates the holder of
the signer key and nothing more. The key is never stored here, never rendered,
and never written into a receipt; only the key *id* travels.

Replay is handled by keying the request id on its content, so submitting the same
decision twice is one request rather than two. A nonce would have been the other
option and it is the wrong one here: two identical decisions with different
nonces are two decisions, and one Human clicking twice is not.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "contracts"))

from hc_vocab import (  # noqa: E402
    CONSOLE_MAY,
    CONSOLE_MAY_NOT,
    EXCEPTION_SCOPE_KEYS,
    SIGNATURE_ALGORITHM,
    ContractError,
    digest,
    exact_object,
    find_unredacted,
    non_empty_str,
    signature_matches,
)

DRAFT_KEYS = {"action", "task_id", "reason", "scope"}

# What the signature covers: the decision, its bindings and its format tag.
# The request id and the signature itself are derived, so signing them would
# be signing a value that depends on the signature.
SIGNED_KEYS = DRAFT_KEYS | {"schema_version", "ledger_head", "state_revision"}


def draft(value: Any, projection: dict[str, Any]) -> dict[str, Any]:
    """Draft a request against the projection currently on screen."""
    request = exact_object(value, DRAFT_KEYS, "draft")
    action = request["action"]
    if action in CONSOLE_MAY_NOT:
        raise ContractError(
            f"{action} is on the list of things the console may not express. It is a "
            "list rather than a principle because a principle gets weakened one "
            "adjective at a time"
        )
    if action not in CONSOLE_MAY:
        raise ContractError(
            f"{action!r} is not an action the console can draft. The set is closed: "
            f"{sorted(CONSOLE_MAY)}. An action that is not here cannot be added by "
            "passing a different string"
        )
    non_empty_str(request["task_id"], "draft.task_id")
    non_empty_str(request["reason"], "draft.reason")

    if request["task_id"] not in projection["tasks"]:
        raise ContractError(
            f"task {request['task_id']!r} is not in the projection this request was "
            "drafted against"
        )

    if action == "REQUEST_SCOPED_EXCEPTION":
        scope = request["scope"]
        if not isinstance(scope, dict) or set(scope) != EXCEPTION_SCOPE_KEYS:
            raise ContractError(
                f"a scoped exception needs {sorted(EXCEPTION_SCOPE_KEYS)}. An exception "
                "without a subject, a gate and an expiry is an unscoped force-skip with "
                "a better name"
            )
        for field in ("subject", "gate"):
            non_empty_str(scope[field], f"scope.{field}")
        expiry = scope["expires_after_revisions"]
        if not isinstance(expiry, int) or isinstance(expiry, bool) or expiry < 1:
            raise ContractError(
                "scope.expires_after_revisions must be a positive integer; an exception "
                "that never expires is permanent, and nothing about it says so"
            )
    elif request["scope"] is not None:
        raise ContractError(
            f"{action} carries a scope; only a scoped exception has one"
        )

    body = {
        "schema_version": "loopx/console-decision-request/v1",
        "action": action,
        "task_id": request["task_id"],
        "reason": request["reason"],
        "scope": request["scope"],
        # The two bindings that make acceptance safe. Both, because the head can
        # move without the revision and the revision cannot move without the head.
        "ledger_head": projection["ledger_head"],
        "state_revision": projection["state_revision"],
    }
    leaks = find_unredacted(body)
    if leaks:
        raise ContractError(f"the drafted request contains {leaks}")
    return {
        **body,
        # Keyed on content. The same decision submitted twice is one request; a
        # nonce would have made it two, and one Human clicking twice is not two
        # decisions.
        "request_id": "req-" + digest(body)[7:23],
        "signed": False,
    }


def sign_request(request: dict[str, Any], key: bytes, key_id: str) -> dict[str, Any]:
    """Attach a signature over the request body. The key never enters the result."""
    non_empty_str(key_id, "signer key id")
    if not isinstance(key, bytes) or len(key) < 16:
        raise ContractError("the signer key must be at least 16 bytes")
    body = {field: request[field] for field in sorted(SIGNED_KEYS)}
    from hc_vocab import sign  # local import keeps the key path narrow

    return {
        **request,
        "signed": True,
        "signer_key_id": key_id,
        "signature_algorithm": SIGNATURE_ALGORITHM,
        "signature": sign(body, key),
    }


def accept(
    request: dict[str, Any],
    projection: dict[str, Any],
    key: bytes,
    seen: set[str],
) -> dict[str, Any]:
    """LoopX's side. Accept or reject; never mutate anything here.

    `seen` is the set of request ids already accepted. Passed in rather than held
    as module state, so a caller cannot get deduplication for free by forgetting
    to persist it.
    """
    if not request.get("signed"):
        return _reject(
            request,
            "the request is unsigned; an unsigned Human action is an assertion that someone acted",
        )

    body = {field: request[field] for field in sorted(SIGNED_KEYS)}
    if not signature_matches(body, key, request.get("signature", "")):
        return _reject(
            request,
            "the signature does not match the request body. Either the body changed "
            "after signing or a different key produced it, and those are the same "
            "shape from here",
        )

    if request["request_id"] in seen:
        return _reject(
            request,
            "this request id has already been accepted. A duplicate is one decision "
            "submitted twice, and acting on it twice is acting on a decision nobody made",
        )

    if request["ledger_head"] != projection["ledger_head"]:
        return _reject(
            request,
            f"the request binds ledger head {request['ledger_head']} and the ledger is "
            f"at {projection['ledger_head']}. The decision was made about a world that "
            "has moved, and a stale request looks exactly like a fresh one",
        )

    if request["state_revision"] != projection["state_revision"]:
        return _reject(
            request,
            "the request binds a state revision the projection no longer has. The "
            "screen the Human read is not the screen the projection would render now",
        )

    return {
        "outcome": "ACCEPTED",
        "request_id": request["request_id"],
        "action": request["action"],
        "task_id": request["task_id"],
        "ledger_head": request["ledger_head"],
        "state_revision": request["state_revision"],
        # What acceptance means, said out loud. LoopX has taken delivery of a
        # question; nothing has been mutated, no gate has moved, and the required
        # gates still have to be revalidated afterwards.
        "mutated": False,
        "gate_verdict_written": False,
        "requires_gate_revalidation": True,
        "receipt_digest": digest(
            {"request": request["request_id"], "head": request["ledger_head"]}
        ),
    }


def _reject(request: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "outcome": "REJECTED",
        "request_id": request.get("request_id"),
        "action": request.get("action"),
        "reason": reason,
        "mutated": False,
        "gate_verdict_written": False,
        "requires_gate_revalidation": False,
    }
