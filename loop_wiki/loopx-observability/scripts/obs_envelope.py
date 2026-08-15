#!/usr/bin/env python3
"""Project ledger events into OpenTelemetry-shaped envelopes, and rebuild them.

The projection law this enforces: a trace store is a reader. Deleting the whole
projection and rebuilding it from the ledger under the same policy version must
reproduce byte-identical envelopes. That is the property that makes a trace
store safe to lose -- and the property that makes a trace store which disagrees
with the ledger a detectable fault rather than a second opinion.

Envelopes carry OpenTelemetry-compatible correlation fields (trace_id, span_id)
without importing an SDK or naming a backend. Langfuse, an OTLP collector or a
JSONL file are adapters over this shape, not participants in it.
"""

from __future__ import annotations

import hashlib
from typing import Any

from obs_common import (
    ContractError,
    canonical_bytes,
    digest,
    exact_object,
    iso_timestamp,
    non_empty_str,
    sha256_ref,
    validate_subject,
)
from obs_redaction import compile_policy, redact, validate_policy

LEDGER_EVENT_KEYS = {
    "sequence",
    "event_id",
    "event_digest",
    "previous_digest",
    "recorded_at",
    "subject",
    "todo_id",
    "attempt",
    "event_type",
    "lifecycle_state",
    "actor",
    "payload",
}
ACTOR_KEYS = {"actor_id", "class"}
ACTOR_CLASSES = {"STRATEGY", "WORKER", "GATE", "REDUCER", "HUMAN_OPERATOR"}

ENVELOPE_KEYS = {
    "schema_version",
    "envelope_id",
    "subject",
    "todo_id",
    "attempt",
    "ledger",
    "correlation",
    "actor",
    "event_type",
    "lifecycle_state",
    "observed_at",
    "attributes",
    "redaction",
    "authority",
}

LIFECYCLE_STATES = {
    "ACTIVE",
    "DISPATCHED",
    "RUNNING",
    "GATE_PASS",
    "GATE_FAIL",
    "RETRY_SCHEDULED",
    "QUOTA_EXHAUSTED",
    "HITL_PENDING",
    "TODO_COMPLETED",
    "COMPLETED_WITH_EXCEPTION",
    "TASK_FAILED",
    "CANCELLED",
}


def validate_ledger_event(value: Any, label: str = "ledger event") -> dict[str, Any]:
    event = exact_object(value, LEDGER_EVENT_KEYS, label)
    sequence = event["sequence"]
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 0:
        raise ContractError(f"{label}.sequence must be a non-negative integer")
    non_empty_str(event["event_id"], f"{label}.event_id")
    sha256_ref(event["event_digest"], f"{label}.event_digest")
    if event["previous_digest"] is not None:
        sha256_ref(event["previous_digest"], f"{label}.previous_digest")
    iso_timestamp(event["recorded_at"], f"{label}.recorded_at")
    validate_subject(event["subject"], f"{label}.subject")
    if event["todo_id"] is not None:
        non_empty_str(event["todo_id"], f"{label}.todo_id")
    attempt = event["attempt"]
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 0:
        raise ContractError(f"{label}.attempt must be a non-negative integer")
    non_empty_str(event["event_type"], f"{label}.event_type")
    if event["lifecycle_state"] not in LIFECYCLE_STATES:
        raise ContractError(
            f"{label}.lifecycle_state {event['lifecycle_state']!r} is outside the "
            "declared vocabulary"
        )
    actor = exact_object(event["actor"], ACTOR_KEYS, f"{label}.actor")
    non_empty_str(actor["actor_id"], f"{label}.actor.actor_id")
    if actor["class"] not in ACTOR_CLASSES:
        raise ContractError(
            f"{label}.actor.class must be one of {sorted(ACTOR_CLASSES)}"
        )
    if not isinstance(event["payload"], dict):
        raise ContractError(f"{label}.payload must be an object")
    return event


def validate_chain(events: list[dict[str, Any]]) -> None:
    """Sequences contiguous from 0 and digests chained.

    A projection over a gapped chain would render a coherent-looking history of
    a task that never happened that way, so the gap is refused here rather than
    rendered.
    """
    if not events:
        raise ContractError("ledger is empty; there is nothing to project")
    previous: str | None = None
    for index, event in enumerate(events):
        if event["sequence"] != index:
            raise ContractError(
                f"ledger sequence gap: expected {index}, found {event['sequence']}; "
                "a projection over a gap would show continuity that never existed"
            )
        if event["previous_digest"] != previous:
            raise ContractError(
                f"ledger chain break at sequence {index}: previous_digest does not "
                "match the digest of the event before it"
            )
        previous = event["event_digest"]


def _correlation(event: dict[str, Any]) -> dict[str, str]:
    """Derive OTel-shaped ids from the subject and event, deterministically.

    Derived rather than generated: a random id would make two rebuilds of the
    same ledger differ, which would destroy the only property this module
    actually promises.
    """
    task_seed = canonical_bytes(
        {
            "repository": event["subject"]["repository"],
            "task_id": event["subject"]["task_id"],
        }
    )
    span_seed = canonical_bytes(
        {"event_id": event["event_id"], "sequence": event["sequence"]}
    )
    return {
        "trace_id": hashlib.sha256(task_seed).hexdigest()[:32],
        "span_id": hashlib.sha256(span_seed).hexdigest()[:16],
    }


def project_event(event: dict[str, Any], compiled: dict[str, Any]) -> dict[str, Any]:
    validate_ledger_event(event)
    attributes, removed = redact(event["payload"], compiled)
    return {
        "schema_version": "loopx/observability-envelope/v1",
        "envelope_id": f"env-{event['sequence']:06d}-{event['event_id']}",
        "subject": event["subject"],
        "todo_id": event["todo_id"],
        "attempt": event["attempt"],
        "ledger": {
            "sequence": event["sequence"],
            "event_digest": event["event_digest"],
        },
        "correlation": _correlation(event),
        "actor": event["actor"],
        "event_type": event["event_type"],
        "lifecycle_state": event["lifecycle_state"],
        "observed_at": event["recorded_at"],
        "attributes": attributes,
        "redaction": {
            "policy_version": compiled["policy"]["policy_version"],
            "removed_paths": removed,
        },
        # Stated on every envelope rather than in documentation only: a reader
        # that has one envelope and no README still learns the projection has no
        # authority over the state it describes.
        "authority": "PROJECTION_ONLY",
    }


def project(events: list[dict[str, Any]], policy: dict[str, Any]) -> dict[str, Any]:
    validate_policy(policy)
    compiled = compile_policy(policy)
    for event in events:
        validate_ledger_event(event)
    validate_chain(events)

    envelopes = [project_event(event, compiled) for event in events]
    return {
        "schema_version": "loopx/observability-projection/v1",
        "policy_version": policy["policy_version"],
        "source_head": {
            "sequence": events[-1]["sequence"],
            "event_digest": events[-1]["event_digest"],
        },
        "envelope_count": len(envelopes),
        "envelopes": envelopes,
        "projection_digest": digest(envelopes),
        "authority": "PROJECTION_ONLY",
        "canonical_writer": "LOOPX_LEDGER_REDUCER",
    }


def rebuild_matches(
    events: list[dict[str, Any]], policy: dict[str, Any], stored: dict[str, Any]
) -> dict[str, Any]:
    """Delete-and-rebuild, compared as bytes.

    Comparing digests alone would pass a stored projection that agrees on its
    own self-reported digest while disagreeing on content, so the envelope
    bytes are compared directly and the digest is checked as a separate claim.
    """
    rebuilt = project(events, policy)

    # Policy version first, and the order matters. Every envelope records the
    # policy it was built under, so a version mismatch also makes the byte
    # comparison fail -- and would report "the trace store disagrees with the
    # ledger", which is the wrong diagnosis for someone who simply changed
    # policy. Rebuild equality is only defined within one policy version, so
    # that has to be established before equality is even asked.
    if stored.get("policy_version") != policy["policy_version"]:
        raise ContractError(
            f"stored projection was built under policy {stored.get('policy_version')!r} "
            f"but is being compared against {policy['policy_version']!r}; rebuild "
            "equality is only defined within one policy version"
        )
    if canonical_bytes(rebuilt["envelopes"]) != canonical_bytes(
        stored.get("envelopes")
    ):
        raise ContractError(
            "rebuilt projection does not reproduce the stored envelopes; the trace "
            "store disagrees with the ledger it claims to describe"
        )
    if stored.get("projection_digest") != rebuilt["projection_digest"]:
        raise ContractError(
            "stored projection_digest does not match its own envelopes; the digest "
            "was not recomputed when the content changed"
        )
    return {
        "rebuilt": True,
        "envelope_count": rebuilt["envelope_count"],
        "projection_digest": rebuilt["projection_digest"],
        "policy_version": policy["policy_version"],
    }
