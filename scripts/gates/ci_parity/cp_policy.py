#!/usr/bin/env python3
"""The event payload a local run claims to reproduce, and the billing decision.

Two things that get decided by accident.

The **event payload** is the first. A local run that materialises a `push`
payload and a workflow that only fires on `pull_request: [ready_for_review]` are
not running the same thing, and every step can still pass on both sides. So the
payload is materialised against the workflow's declared triggers and refused if
the workflow could not have fired on it.

**Billing** is the second. GitHub bills per job, rounded up to the minute. Four
sub-minute jobs cost four minutes; one job with four steps costs one. That is a
real trade against fault localisation -- a grouped job says less about which
check failed -- so the split is recorded as a decision with a stated reason,
rather than being whatever the file happened to grow into.
"""

from __future__ import annotations

from typing import Any

from cp_common import ContractError, digest, non_empty_str

PAYLOAD_KEYS = {"event", "action", "ref", "head_sha", "draft"}

# GitHub bills whole minutes per job. Not a policy choice here -- it is the
# billing unit, and it is why job count and job duration are not the same
# question.
BILLING_UNIT_SECONDS = 60


def materialize_payload(value: Any, triggers: dict[str, Any]) -> dict[str, Any]:
    """Build the event payload, and check the workflow could have fired on it."""
    if not isinstance(value, dict) or set(value) != PAYLOAD_KEYS:
        raise ContractError(
            f"event payload fields drifted; expected {sorted(PAYLOAD_KEYS)}"
        )
    event = non_empty_str(value["event"], "payload.event")
    non_empty_str(value["ref"], "payload.ref")

    if event not in triggers["events"]:
        raise ContractError(
            f"the payload is a {event!r} event, but the workflow declares "
            f"{triggers['events']}. Every step can pass locally under an event the "
            "workflow would never have fired on, and the run that was compared is one "
            "that could not have happened"
        )

    if event == "pull_request":
        declared = triggers["pull_request_types"]
        action = value["action"]
        if declared and action not in declared:
            raise ContractError(
                f"the payload is a pull_request {action!r}, but the workflow only fires "
                f"on {declared}. This repository's required workflow fires on "
                "ready_for_review alone, which is what makes draft-first a requirement "
                "rather than a preference"
            )
        if value["draft"] and action == "ready_for_review":
            raise ContractError(
                "a ready_for_review payload cannot also be a draft; the event is the "
                "draft -> ready transition"
            )

    return {
        **value,
        "would_fire": True,
        "payload_digest": digest(value),
    }


def billing_decision(
    jobs: dict[str, float], grouped: bool, reason: str
) -> dict[str, Any]:
    """Cost of the current job split, and the decision that produced it.

    Takes each job's observed duration in seconds. It reports both what the split
    costs and what the alternative would have cost, because a split is only
    defensible against a number.
    """
    if not jobs:
        raise ContractError("a billing decision needs at least one job")
    # Deliberately not required here. An empty reason is exactly the state this
    # function exists to surface -- a split nobody decided on -- so refusing it
    # at the constructor would make `require_decided` a guard that can never
    # fire, which reads as protection while testing nothing.
    if not isinstance(reason, str):
        raise ContractError("billing.reason must be a string")

    def billed(seconds: float) -> int:
        if seconds < 0:
            raise ContractError("a job duration cannot be negative")
        return max(1, -(-int(seconds) // BILLING_UNIT_SECONDS))

    per_job = {name: billed(seconds) for name, seconds in sorted(jobs.items())}
    split_minutes = sum(per_job.values())
    merged_minutes = billed(sum(jobs.values()))
    sub_minute = sorted(
        name for name, seconds in jobs.items() if seconds < BILLING_UNIT_SECONDS
    )

    return {
        "jobs": per_job,
        "split_billed_minutes": split_minutes,
        "merged_billed_minutes": merged_minutes,
        "overhead_minutes": split_minutes - merged_minutes,
        "sub_minute_jobs": sub_minute,
        "grouped": grouped,
        "reason": reason,
        # The state the controls exist for: several sub-minute jobs each billing
        # a full minute, with nobody having decided that fault localisation was
        # worth it.
        "undecided_split": len(sub_minute) > 1 and not grouped and not reason.strip(),
        "decision_digest": digest(
            {"jobs": per_job, "grouped": grouped, "reason": reason}
        ),
    }


def require_decided(decision: dict[str, Any]) -> None:
    if decision["undecided_split"]:
        raise ContractError(
            f"{len(decision['sub_minute_jobs'])} sub-minute jobs each bill a full "
            f"minute ({decision['overhead_minutes']} minutes of overhead) with no "
            "recorded reason. Splitting for fault localisation is a fine answer; not "
            "having answered is not"
        )
