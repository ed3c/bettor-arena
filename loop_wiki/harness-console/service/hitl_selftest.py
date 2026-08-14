#!/usr/bin/env python3
"""Positive properties, and one planted control per failure named in #99.

Every control asserts on the substring its own rule raises. A control that only
checks "something was refused" passes when a neighbouring guard fires first, and
stays green while the rule it was written for is deleted.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "contracts"))
sys.path.insert(0, str(HERE.parents[0] / "app"))

from hc_vocab import (  # noqa: E402
    CONSOLE_MAY,
    CONSOLE_MAY_NOT,
    LIVE_CONSOLE_STATE,
    RENDER_STATE,
    UI_STATES,
    VIEWS,
    ContractError,
    redact,
)
from hc_views import render  # noqa: E402
from hitl_reducer import rebuild_matches, reduce, require_complete  # noqa: E402
from hitl_request import accept, draft, sign_request  # noqa: E402

HEAD = "ledger-head-0f21ac"
KEY = b"a-signer-key-that-is-long-enough"
KEY_ID = "human-operator-1"

EVENTS: list[dict[str, Any]] = [
    {
        "sequence": 1,
        "kind": "TASK_CREATED",
        "task_id": "t1",
        "payload": {"parent": None},
    },
    {
        "sequence": 2,
        "kind": "TASK_STATE_CHANGED",
        "task_id": "t1",
        "payload": {"state": "RUNNING"},
    },
    {
        "sequence": 3,
        "kind": "ATTEMPT_STARTED",
        "task_id": "t1",
        "payload": {"attempt": 1},
    },
    {
        "sequence": 4,
        "kind": "GATE_EVALUATED",
        "task_id": "t1",
        "payload": {
            "gate": "contracts",
            "verdict": "FAIL",
            "detail": "two schemas drifted",
        },
    },
    {
        "sequence": 5,
        "kind": "DIAGNOSTIC_EMITTED",
        "task_id": "t1",
        "payload": {"tool": "ruff", "message": "F401 unused import"},
    },
    {
        "sequence": 6,
        "kind": "DIFF_PRODUCED",
        "task_id": "t1",
        "payload": {"path": "scripts/x.py", "patch": "@@ -1 +1 @@\n-import os\n"},
    },
    {
        "sequence": 7,
        "kind": "QUOTA_OBSERVED",
        "task_id": "t1",
        "payload": {"retries_left": 2, "tokens_used": 41000},
    },
    {
        "sequence": 8,
        "kind": "PROVENANCE_RECORDED",
        "task_id": "t1",
        "payload": {"kind": "stack-receipt", "ref": "sha256:" + "e" * 64},
    },
    {
        "sequence": 9,
        "kind": "TASK_CREATED",
        "task_id": "t2",
        "payload": {"parent": "t1"},
    },
    {
        "sequence": 10,
        "kind": "EXCEPTION_ADMITTED",
        "task_id": "t2",
        "payload": {"gate": "lineage", "admitted_by": "human-operator-1"},
    },
    {
        "sequence": 11,
        "kind": "TASK_STATE_CHANGED",
        "task_id": "t2",
        "payload": {"state": "COMPLETED_WITH_EXCEPTION"},
    },
]

DRAFT = {
    "action": "REQUEST_RETRY",
    "task_id": "t1",
    "reason": "the contracts gate failed on a stale projection; re-render and retry",
    "scope": None,
}


def _events(**changes: Any) -> list[dict[str, Any]]:
    return copy.deepcopy(EVENTS)


def control(label: str, expect: str, action: Callable[[], Any]) -> None:
    try:
        action()
    except ContractError as exc:
        if expect not in str(exc):
            raise ContractError(
                f"control {label!r} was refused, but by a different rule: {exc}. A "
                "control that only checks 'something was refused' passes when a "
                "neighbouring guard fires and stays green while its own rule is deleted"
            ) from exc
        return
    raise ContractError(f"control {label!r} was not refused")


def positive_properties() -> int:
    checks = 0
    projection = reduce(EVENTS, HEAD)

    if projection["completeness"] != "COMPLETE" or projection["missing_sequences"]:
        raise ContractError(
            "a contiguous event list did not reduce to a COMPLETE projection"
        )
    require_complete(projection)
    checks += 1

    if projection["authority"] != "READ_ONLY_PROJECTION":
        raise ContractError("the projection claimed something other than read-only")
    checks += 1

    # Delete it and rebuild it. The property that makes a UI database safe to
    # throw away.
    if not rebuild_matches(EVENTS, HEAD, projection):
        raise ContractError(
            "a rebuild from the same events produced a different projection"
        )
    checks += 1

    # Event order must not matter; only sequence does.
    shuffled = list(reversed(EVENTS))
    if reduce(shuffled, HEAD) != projection:
        raise ContractError("the projection depends on the order events arrived in")
    checks += 1

    # A gap is INCOMPLETE, and it names which events are missing.
    gapped = [event for event in EVENTS if event["sequence"] not in (3, 7)]
    holed = reduce(gapped, HEAD)
    if holed["completeness"] != "INCOMPLETE" or holed["missing_sequences"] != [3, 7]:
        raise ContractError(f"a gapped event list reduced to {holed['completeness']}")
    checks += 1

    views = render(projection)
    if sorted(views["views"]) != sorted(VIEWS) or views["view_count"] != 8:
        raise ContractError(f"render produced {sorted(views['views'])}")
    checks += 1

    if views["render_state"] != "NOT_IMPLEMENTED" or RENDER_STATE != "NOT_IMPLEMENTED":
        raise ContractError("the view layer claimed a rendering that does not exist")
    checks += 1

    # The exception is counted on its own line, not folded into COMPLETED.
    graph = views["views"]["thread_task_graph"]
    if graph["completed_with_exception"] != 1 or graph["completed_clean"] != 0:
        raise ContractError(
            f"COMPLETED_WITH_EXCEPTION was folded into completion: {graph['counts_by_state']}"
        )
    checks += 1

    inspector = views["views"]["gate_evidence_inspector"]
    if inspector["counts_by_verdict"] != {"FAIL": 1} or inspector["may_write_verdict"]:
        raise ContractError(
            "the gate inspector altered or claimed authority over a verdict"
        )
    checks += 1

    # Every view is bounded and says whether it truncated.
    for name, view in views["views"].items():
        if name == "hitl_dialog":
            continue
        if "truncated" not in view or "limit" not in view:
            raise ContractError(f"view {name} is unbounded")
    checks += 1

    # A bounded view that actually had to truncate still says so.
    many = [
        {
            "sequence": 100 + i,
            "kind": "DIAGNOSTIC_EMITTED",
            "task_id": "t1",
            "payload": {"i": i},
        }
        for i in range(150)
    ]
    wide = render(reduce(EVENTS + many, HEAD))["views"]["diagnostics_panel"]
    if not wide["truncated"] or wide["shown"] != 100 or wide["total"] != 151:
        raise ContractError(
            f"a truncated view reported {wide['shown']}/{wide['total']}"
        )
    checks += 1

    # A per-entry diff cap, separate from the list cap.
    big = copy.deepcopy(EVENTS)
    big.append(
        {
            "sequence": 12,
            "kind": "DIFF_PRODUCED",
            "task_id": "t1",
            "payload": {"path": "big.txt", "patch": "x" * 9000},
        }
    )
    diff_view = render(reduce(big, HEAD))["views"]["git_diff_viewer"]
    entry = [item for item in diff_view["items"] if item["path"] == "big.txt"][0]
    if not entry["patch_truncated"] or len(entry["patch"]) > 4096:
        raise ContractError("an unbounded diff reached the view")
    checks += 1

    # The dialog is not draftable on a gapped projection.
    if render(holed)["views"]["hitl_dialog"]["draftable"]:
        raise ContractError("the HITL dialog was draftable on an incomplete projection")
    checks += 1

    dialog = views["views"]["hitl_dialog"]
    if sorted(dialog["available_actions"]) != sorted(CONSOLE_MAY):
        raise ContractError("the dialog offered actions outside the closed set")
    if sorted(dialog["refused_actions"]) != sorted(CONSOLE_MAY_NOT):
        raise ContractError("the refused-action list drifted out of the dialog")
    checks += 1

    # Draft, sign, accept.
    request = draft(DRAFT, projection)
    if request["signed"]:
        raise ContractError("a draft was born signed")
    signed = sign_request(request, KEY, KEY_ID)
    outcome = accept(signed, projection, KEY, set())
    if outcome["outcome"] != "ACCEPTED":
        raise ContractError(
            f"a valid request was {outcome['outcome']}: {outcome.get('reason')}"
        )
    if outcome["mutated"] or outcome["gate_verdict_written"]:
        raise ContractError("accepting a request mutated state or wrote a gate verdict")
    if not outcome["requires_gate_revalidation"]:
        raise ContractError("acceptance did not require the gates to be revalidated")
    checks += 1

    # The signer key never enters the signed request.
    import json as _json

    if KEY.decode() in _json.dumps(signed) or KEY.decode() in _json.dumps(outcome):
        raise ContractError("the signer key reached the request or the receipt")
    if signed["signer_key_id"] != KEY_ID:
        raise ContractError("the key id did not travel with the request")
    checks += 1

    # A scoped exception carries all three parts.
    scoped = draft(
        {
            "action": "REQUEST_SCOPED_EXCEPTION",
            "task_id": "t2",
            "reason": "lineage gate blocked on a merge commit; scope it to this subject",
            "scope": {"subject": "t2", "gate": "lineage", "expires_after_revisions": 3},
        },
        projection,
    )
    if scoped["scope"]["expires_after_revisions"] != 3:
        raise ContractError("the exception scope lost its expiry")
    checks += 1

    # Two identical decisions are one request, by construction.
    if draft(DRAFT, projection)["request_id"] != request["request_id"]:
        raise ContractError("the same decision drafted twice produced two request ids")
    checks += 1

    # Redaction, on real shapes.
    for probe in (
        "token: ghp_" + "a" * 32,
        "<thinking>secret plan</thinking>",
        "api_key=abcdef123456",
    ):
        if "[REDACTED]" not in redact(probe):
            raise ContractError(f"redaction missed {probe[:20]!r}")
    checks += 1

    if UI_STATES[-1] != "PROJECTION_REFRESHED" or len(UI_STATES) != 10:
        raise ContractError("the UI state sequence drifted")
    if LIVE_CONSOLE_STATE != "NOT_EXERCISED":
        raise ContractError("a live console was claimed")
    checks += 1

    return checks


def controls() -> int:
    projection = reduce(EVENTS, HEAD)
    request = sign_request(draft(DRAFT, projection), KEY, KEY_ID)

    moved = reduce(
        EVENTS
        + [{"sequence": 12, "kind": "ATTEMPT_STARTED", "task_id": "t1", "payload": {}}],
        HEAD,
    )
    other_head = reduce(EVENTS, "ledger-head-99ffff")

    cases: list[tuple[str, str, Callable[[], Any]]] = [
        (
            "a stale state revision",
            "screen the Human read is not the screen",
            lambda: _require_accepted(accept(request, moved, KEY, set())),
        ),
        (
            "a stale ledger head",
            "a world that has moved",
            lambda: _require_accepted(accept(request, other_head, KEY, set())),
        ),
        (
            "an unsigned Human action",
            "an assertion that someone acted",
            lambda: _require_accepted(
                accept(draft(DRAFT, projection), projection, KEY, set())
            ),
        ),
        (
            "a duplicate Human action",
            "acting on a decision nobody made",
            lambda: _require_accepted(
                accept(request, projection, KEY, {request["request_id"]})
            ),
        ),
        (
            "a request signed with a different key",
            "a different key produced it",
            lambda: _require_accepted(
                accept(request, projection, b"a-different-key-long-enough!", set())
            ),
        ),
        (
            "a request body edited after signing",
            "the body changed after signing",
            lambda: _require_accepted(
                accept(
                    {**request, "reason": "something else entirely"},
                    projection,
                    KEY,
                    set(),
                )
            ),
        ),
        (
            "a missing event rendered as continuous history",
            "exactly what the screen would not show",
            lambda: require_complete(
                reduce([e for e in EVENTS if e["sequence"] != 5], HEAD)
            ),
        ),
        (
            "a duplicated ledger event",
            "not the event the ledger recorded",
            lambda: reduce(EVENTS + [copy.deepcopy(EVENTS[3])], HEAD),
        ),
        (
            "an unscoped force skip",
            "not an action the console can draft",
            lambda: draft({**DRAFT, "action": "FORCE_SKIP"}, projection),
        ),
        (
            "an explicitly forbidden action",
            "weakened one adjective at a time",
            lambda: draft({**DRAFT, "action": "MARK_GATE_PASS"}, projection),
        ),
        (
            "a merge issued from the console",
            "weakened one adjective at a time",
            lambda: draft({**DRAFT, "action": "MERGE"}, projection),
        ),
        (
            "a rollback issued from the console",
            "weakened one adjective at a time",
            lambda: draft({**DRAFT, "action": "ROLLBACK_PRODUCTION"}, projection),
        ),
        (
            "an exception with no scope",
            "unscoped force-skip with a better name",
            lambda: draft(
                {
                    **DRAFT,
                    "action": "REQUEST_SCOPED_EXCEPTION",
                    "scope": {"subject": "t2"},
                },
                projection,
            ),
        ),
        (
            "an exception that never expires",
            "permanent, and nothing about it says so",
            lambda: draft(
                {
                    **DRAFT,
                    "action": "REQUEST_SCOPED_EXCEPTION",
                    "scope": {
                        "subject": "t2",
                        "gate": "lineage",
                        "expires_after_revisions": 0,
                    },
                },
                projection,
            ),
        ),
        (
            "a secret in the projection",
            "the last point before it reaches a screen",
            lambda: _leak_projection(),
        ),
        (
            "private reasoning in a request",
            "the drafted request contains",
            lambda: draft(
                {**DRAFT, "reason": "retry; see <thinking>the real reason</thinking>"},
                projection,
            ),
        ),
        (
            "a gate verdict the ledger cannot carry",
            "none of them may be promoted to PASS",
            lambda: reduce(
                EVENTS
                + [
                    {
                        "sequence": 12,
                        "kind": "GATE_EVALUATED",
                        "task_id": "t1",
                        "payload": {"gate": "x", "verdict": "PROBABLY_FINE"},
                    }
                ],
                HEAD,
            ),
        ),
        (
            "a task state the machine does not have",
            "which is not a task state",
            lambda: reduce(
                EVENTS
                + [
                    {
                        "sequence": 12,
                        "kind": "TASK_STATE_CHANGED",
                        "task_id": "t1",
                        "payload": {"state": "MOSTLY_DONE"},
                    }
                ],
                HEAD,
            ),
        ),
        (
            "an event kind the console does not understand",
            "is inventing history",
            lambda: reduce(
                EVENTS
                + [
                    {
                        "sequence": 12,
                        "kind": "UI_CLICKED",
                        "task_id": "t1",
                        "payload": {},
                    }
                ],
                HEAD,
            ),
        ),
        (
            "an empty ledger rendered as an empty projection",
            "render identically",
            lambda: reduce([], HEAD),
        ),
        (
            "a request for a task the projection does not have",
            "not in the projection this request was drafted against",
            lambda: draft({**DRAFT, "task_id": "t99"}, projection),
        ),
        (
            "a signer key that is too short",
            "at least 16 bytes",
            lambda: sign_request(draft(DRAFT, projection), b"short", KEY_ID),
        ),
    ]
    for label, expect, action in cases:
        control(label, expect, action)
    return len(cases)


def _leak_projection() -> Any:
    """A secret that survives redaction would have to be introduced after it.

    Redaction runs over the whole structure, so this plants the leak where the
    scanner runs: the check is that the reducer scans its own output rather than
    trusting the redaction that just ran.
    """
    import hitl_reducer

    original = hitl_reducer.redact_deep
    try:
        hitl_reducer.redact_deep = lambda value: value
        return reduce(
            EVENTS
            + [
                {
                    "sequence": 12,
                    "kind": "DIAGNOSTIC_EMITTED",
                    "task_id": "t1",
                    "payload": {"message": "token: ghp_" + "a" * 32},
                }
            ],
            HEAD,
        )
    finally:
        hitl_reducer.redact_deep = original


def _require_accepted(outcome: dict[str, Any]) -> None:
    """Force a rejection to surface as a refusal, so the control can see it."""
    if outcome["outcome"] != "ACCEPTED":
        raise ContractError(outcome["reason"])


def run_selftest(root: Path) -> tuple[int, int]:
    return positive_properties(), controls()
