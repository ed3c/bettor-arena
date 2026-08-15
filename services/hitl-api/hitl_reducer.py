#!/usr/bin/env python3
"""Canonical events in, projection out. Delete the projection and it comes back.

The console never stores anything a rebuild could not reproduce. That is not a
tidiness preference: a UI database that has drifted from the ledger renders
confidently and wrongly, and there is no symptom -- the screen looks exactly the
same either way. So `reduce` is a pure function of the event list, and the
projection carries the digest of the events it came from.

The gap check is the other half. Events carry sequence numbers, and a missing one
must not be rendered as continuous history: a graph drawn from events 1,2,4 looks
identical to a graph drawn from 1,2,3,4, and the difference is whatever happened
in 3. So a gap makes the projection INCOMPLETE and names the missing sequences.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "packages/harness-console-contracts")
)

from hc_vocab import (  # noqa: E402
    TASK_STATES,
    ContractError,
    digest,
    exact_object,
    find_unredacted,
    non_empty_str,
    redact_deep,
)

EVENT_KEYS = {"sequence", "kind", "task_id", "payload"}

EVENT_KINDS = (
    "TASK_CREATED",
    "TASK_STATE_CHANGED",
    "ATTEMPT_STARTED",
    "GATE_EVALUATED",
    "DIAGNOSTIC_EMITTED",
    "DIFF_PRODUCED",
    "QUOTA_OBSERVED",
    "PROVENANCE_RECORDED",
    "EXCEPTION_ADMITTED",
)

# Gate verdicts the ledger can carry. The console displays them; it never writes
# one, and it never maps one onto another.
GATE_VERDICTS = (
    "PASS",
    "FAIL",
    "ABSENT",
    "NOT_IMPLEMENTED",
    "NOT_EXERCISED",
    "SKIPPED_BY_POLICY",
)


def validate_event(value: Any, label: str) -> dict[str, Any]:
    event = exact_object(value, EVENT_KEYS, label)
    sequence = event["sequence"]
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        raise ContractError(f"{label}.sequence must be a positive integer")
    if event["kind"] not in EVENT_KINDS:
        raise ContractError(
            f"{label}.kind is {event['kind']!r}, which is not a canonical event kind. "
            f"Known: {sorted(EVENT_KINDS)}. A console that renders an event it does not "
            "understand is inventing history"
        )
    non_empty_str(event["task_id"], f"{label}.task_id")
    if not isinstance(event["payload"], dict):
        raise ContractError(f"{label}.payload must be an object")
    return event


def reduce(events: list[Any], ledger_head: str) -> dict[str, Any]:
    """Fold canonical events into the read-only projection the console renders."""
    non_empty_str(ledger_head, "ledger_head")
    validated = [
        validate_event(event, f"events[{index}]") for index, event in enumerate(events)
    ]
    if not validated:
        raise ContractError(
            "no events to reduce. An empty projection and a projection of an empty "
            "ledger are different situations and they render identically"
        )

    ordered = sorted(validated, key=lambda event: event["sequence"])
    sequences = [event["sequence"] for event in ordered]
    if len(set(sequences)) != len(sequences):
        duplicates = sorted({s for s in sequences if sequences.count(s) > 1})
        raise ContractError(
            f"duplicate event sequences {duplicates}. Two events at one sequence means "
            "one of them is not the event the ledger recorded"
        )

    # The gap check. Named sequences, not a count: "13 of 15 events" is a number
    # a reader rounds off, and "3 and 7 are missing" is a question.
    expected = range(sequences[0], sequences[-1] + 1)
    missing = sorted(set(expected) - set(sequences))

    tasks: dict[str, dict[str, Any]] = {}
    gates: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    diffs: list[dict[str, Any]] = []
    quota: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    exceptions: list[dict[str, Any]] = []

    for event in ordered:
        task_id = event["task_id"]
        payload = event["payload"]
        task = tasks.setdefault(
            task_id,
            {"task_id": task_id, "state": "PENDING", "attempts": 0, "parent": None},
        )
        kind = event["kind"]
        if kind == "TASK_CREATED":
            task["parent"] = payload.get("parent")
        elif kind == "TASK_STATE_CHANGED":
            state = payload.get("state")
            if state not in TASK_STATES:
                raise ContractError(
                    f"event {event['sequence']} moves task {task_id!r} to {state!r}, "
                    f"which is not a task state. Known: {sorted(TASK_STATES)}"
                )
            task["state"] = state
        elif kind == "ATTEMPT_STARTED":
            task["attempts"] += 1
        elif kind == "GATE_EVALUATED":
            verdict = payload.get("verdict")
            if verdict not in GATE_VERDICTS:
                raise ContractError(
                    f"event {event['sequence']} reports gate verdict {verdict!r}. "
                    f"Known: {sorted(GATE_VERDICTS)}; none of them may be promoted to PASS"
                )
            gates.append({"sequence": event["sequence"], "task_id": task_id, **payload})
        elif kind == "DIAGNOSTIC_EMITTED":
            diagnostics.append(
                {"sequence": event["sequence"], "task_id": task_id, **payload}
            )
        elif kind == "DIFF_PRODUCED":
            diffs.append({"sequence": event["sequence"], "task_id": task_id, **payload})
        elif kind == "QUOTA_OBSERVED":
            quota.append({"sequence": event["sequence"], "task_id": task_id, **payload})
        elif kind == "PROVENANCE_RECORDED":
            provenance.append(
                {"sequence": event["sequence"], "task_id": task_id, **payload}
            )
        elif kind == "EXCEPTION_ADMITTED":
            exceptions.append(
                {"sequence": event["sequence"], "task_id": task_id, **payload}
            )

    projection = {
        "schema_version": "loopx/console-projection/v1",
        "ledger_head": ledger_head,
        # The revision a decision request has to bind. Derived from the events, so
        # it moves whenever anything the console showed has moved.
        "state_revision": digest({"head": ledger_head, "sequences": sequences}),
        "tasks": {task_id: tasks[task_id] for task_id in sorted(tasks)},
        "gates": gates,
        "diagnostics": diagnostics,
        "diffs": diffs,
        "quota": quota,
        "provenance": provenance,
        "exceptions": exceptions,
        "event_count": len(ordered),
        "first_sequence": sequences[0],
        "last_sequence": sequences[-1],
        "missing_sequences": missing,
        # INCOMPLETE, not a warning. A graph drawn from 1,2,4 and a graph drawn
        # from 1,2,3,4 are the same picture.
        "completeness": "COMPLETE" if not missing else "INCOMPLETE",
        "source_digest": digest(ordered),
        "authority": "READ_ONLY_PROJECTION",
    }

    redacted = redact_deep(projection)
    leaks = find_unredacted(redacted)
    if leaks:
        raise ContractError(
            f"the projection still contains {leaks} after redaction. The console "
            "renders whatever an agent produced, and this is the last point before it "
            "reaches a screen or a cache"
        )
    return redacted


def require_complete(projection: dict[str, Any]) -> None:
    """Refuse to treat a gapped projection as history."""
    if projection["completeness"] != "COMPLETE":
        raise ContractError(
            f"the projection is missing events {projection['missing_sequences']} and "
            "would be rendered as continuous history. Whatever happened in those "
            "events is exactly what the screen would not show"
        )


def rebuild_matches(
    events: list[Any], ledger_head: str, projection: dict[str, Any]
) -> bool:
    """Delete the projection, rebuild it, and check nothing was lost.

    The property that makes a UI database safe to throw away -- and the one that
    quietly stops holding the first time something is written to the projection
    that was not derived from an event.
    """
    return reduce(events, ledger_head) == projection
