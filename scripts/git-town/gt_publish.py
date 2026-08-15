#!/usr/bin/env python3
"""The publication gate: one operation, and a human performs it.

Everything else in this module is local. Publication is the point where a local
result becomes something other people act on, and it is deliberately a different
kind of thing: `publication_decision` returns whether a request *may be made*,
never whether one was made, and `performed` is always false coming out of here.

The two heads have to be the same commit. A local receipt at one head and a
GitHub check at another are two facts about two commits, and the sentence that
combines them ("local is green and CI is green") is true of neither.
"""

from __future__ import annotations

from typing import Any

from gt_common import ContractError, digest

FULL_SHA_LENGTH = 40


def _full(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != FULL_SHA_LENGTH
        or not all(c in "0123456789abcdef" for c in value)
    ):
        raise ContractError(
            f"{label} must be a full 40-character commit SHA; a short SHA names a commit "
            "only relative to a repository that has it, and a publication decision is "
            "read where that repository is not"
        )
    return value


def publication_decision(
    admission: dict[str, Any], local_receipt_head: str, github_check_head: str
) -> dict[str, Any]:
    """Whether a publication request may be made. Never whether one was made."""
    _full(local_receipt_head, "local_receipt_head")
    _full(github_check_head, "github_check_head")

    if admission["state"] not in ("ADMITTED_DRY_RUN_ONLY", "ADMITTED_LOCAL_NO_PUSH"):
        return _decision(
            False,
            f"the runtime is {admission['state']}, so nothing local was produced by an "
            "admitted program and there is nothing to publish about. Not admitted",
            local_receipt_head,
            github_check_head,
        )

    if local_receipt_head != github_check_head:
        return _decision(
            False,
            f"the local receipt is at {local_receipt_head[:12]} and the GitHub check is at "
            f"{github_check_head[:12]}. Those are two facts about a different commit each, "
            "and 'local is green and CI is green' is true of neither",
            local_receipt_head,
            github_check_head,
        )

    return _decision(
        True,
        "the local receipt and the GitHub check name the same commit; a human may make "
        "the publication request",
        local_receipt_head,
        github_check_head,
    )


def _decision(
    may: bool, reason: str, local_head: str, check_head: str
) -> dict[str, Any]:
    return {
        "schema_version": "loopx/git-town-publication-decision/v1",
        "may_request": may,
        # Always false out of this function. There is no argument that makes it
        # true, because there is no code here that publishes.
        "performed": False,
        "owner": "HUMAN_OR_TRUSTED_OPERATOR",
        "reason": reason,
        "local_receipt_head": local_head,
        "github_check_head": check_head,
        # The receipts stay separate. Folded into one, "the sync ran" and "a
        # human admitted it" become the same record, and only one of them is a
        # decision.
        "receipt_kinds": [
            "LOCAL_SYNC",
            "LOCAL_VERIFICATION",
            "PUBLICATION",
            "HUMAN_ADMIT",
        ],
        "decision_digest": digest({"may": may, "head": local_head}),
    }


def require_separate_operation(decision: dict[str, Any]) -> None:
    """Refuse a decision that has published something."""
    if decision.get("performed"):
        raise ContractError(
            "a publication decision reports that it performed the publication. Requesting "
            "and publishing are deliberately different things: publication is the one "
            "operation a human performs, and a gate that can do it has removed the gate"
        )
    if decision.get("owner") != "HUMAN_OR_TRUSTED_OPERATOR":
        raise ContractError(
            f"publication ownership drifted to {decision.get('owner')!r}"
        )
