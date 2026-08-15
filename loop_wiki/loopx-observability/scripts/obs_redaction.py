#!/usr/bin/env python3
"""Deterministic redaction: what leaves the ledger, and what is recorded as gone.

Redaction here is not "strip anything that looks dangerous and hope". Two
properties make it checkable:

1. it is *deterministic* -- the same events under the same policy version
   produce byte-identical envelopes, which is what lets a deleted projection be
   rebuilt and compared rather than merely re-generated;
2. it is *self-reporting* -- every envelope records the policy version and the
   exact field paths removed, so a projection cannot quietly drop a field and
   still look complete.

A projection that silently omits is worse than one that visibly redacts: the
reader of a redacted field knows to go ask; the reader of a missing one does
not know there was anything to ask about.
"""

from __future__ import annotations

import re
from typing import Any

from obs_common import ContractError, exact_object, non_empty_str, require

POLICY_KEYS = {
    "schema_version",
    "policy_version",
    "drop_keys",
    "drop_value_patterns",
    "max_string_bytes",
    "max_array_items",
}

# Keys whose *values* never leave the ledger, whatever they contain.
DEFAULT_DROP_KEYS = [
    "authorization",
    "chain_of_thought",
    "cookie",
    "credential",
    "env",
    "page_body",
    "password",
    "private_key",
    "reasoning_trace",
    "scratchpad",
    "secret",
    "session",
    "thought_stream",
    "token",
]

# Value shapes that are secret-like regardless of the key they arrive under --
# a token pasted into a field called "note" is still a token.
DEFAULT_DROP_VALUE_PATTERNS = [
    r"\b(?:ghp_|github_pat_|gho_|ghs_|sk-)[A-Za-z0-9_-]{16,}\b",
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    r"\baws_secret_access_key\b",
    r"https://[^/\s:@]+:[^/\s@]+@",
]

REDACTED = "[REDACTED]"
TRUNCATED = "[TRUNCATED]"


def validate_policy(value: Any) -> dict[str, Any]:
    policy = exact_object(value, POLICY_KEYS, "redaction policy")
    require(
        policy["schema_version"] == "loopx/redaction-policy/v1",
        "redaction policy schema version drifted",
    )
    non_empty_str(policy["policy_version"], "redaction policy.policy_version")

    for field in ("drop_keys", "drop_value_patterns"):
        items = policy[field]
        if not isinstance(items, list) or not items:
            raise ContractError(f"redaction policy.{field} must be a non-empty array")
        if sorted(items) != items:
            raise ContractError(
                f"redaction policy.{field} must be sorted; an unsorted list makes two "
                "equivalent policies produce different digests"
            )
        if len(set(items)) != len(items):
            raise ContractError(f"redaction policy.{field} must be unique")

    # The default sets are a floor, not a suggestion. A policy may add to them;
    # removing one would let a later policy version quietly widen what escapes.
    missing = sorted(set(DEFAULT_DROP_KEYS) - set(policy["drop_keys"]))
    if missing:
        raise ContractError(
            f"redaction policy drops fewer keys than the floor: {missing}"
        )
    missing = sorted(
        set(DEFAULT_DROP_VALUE_PATTERNS) - set(policy["drop_value_patterns"])
    )
    if missing:
        raise ContractError(
            f"redaction policy drops fewer value patterns than the floor: {missing}"
        )

    for field in ("max_string_bytes", "max_array_items"):
        limit = policy[field]
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ContractError(f"redaction policy.{field} must be a positive integer")
    return policy


def compile_policy(policy: dict[str, Any]) -> dict[str, Any]:
    return {
        "policy": policy,
        "drop_keys": {key.lower() for key in policy["drop_keys"]},
        "patterns": [re.compile(p) for p in policy["drop_value_patterns"]],
    }


def redact(value: Any, compiled: dict[str, Any]) -> tuple[Any, list[str]]:
    """Return the redacted value and every path that was removed or truncated.

    The path list is the receipt. Without it a reader cannot distinguish a field
    that was never produced from one that was removed on the way out.
    """
    removed: list[str] = []
    result = _walk(value, compiled, "", removed)
    return result, sorted(removed)


def _walk(value: Any, compiled: dict[str, Any], path: str, removed: list[str]) -> Any:
    policy = compiled["policy"]

    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key in sorted(value):
            here = f"{path}.{key}" if path else key
            if key.lower() in compiled["drop_keys"]:
                out[key] = REDACTED
                removed.append(here)
                continue
            out[key] = _walk(value[key], compiled, here, removed)
        return out

    if isinstance(value, list):
        limit = policy["max_array_items"]
        out_list = [
            _walk(item, compiled, f"{path}[{index}]", removed)
            for index, item in enumerate(value[:limit])
        ]
        if len(value) > limit:
            out_list.append(TRUNCATED)
            removed.append(f"{path}[{limit}:]")
        return out_list

    if isinstance(value, str):
        for pattern in compiled["patterns"]:
            if pattern.search(value):
                removed.append(path)
                return REDACTED
        limit = policy["max_string_bytes"]
        if len(value.encode("utf-8")) > limit:
            removed.append(path)
            # Cut on a byte boundary that stays valid UTF-8.
            cut = value.encode("utf-8")[:limit].decode("utf-8", "ignore")
            return cut + TRUNCATED
        return value

    return value
