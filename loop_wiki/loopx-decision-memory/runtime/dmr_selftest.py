#!/usr/bin/env python3
"""Positive properties plus one planted control per named failure in #103.

The fixtures come from `good_bundle()` in the module this runtime sits on, so
the two halves cannot drift apart: a proposal shape that stops satisfying the
contracts stops satisfying this suite in the same run.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from memory import ContractError, digest, good_bundle  # noqa: E402

from dmr_authority import LADDER, invalidation_proposals, outranks, resolve
from dmr_event import append, build_event, current, validate_event
from dmr_lifecycle import export, redact_log, residue, tombstone
from dmr_pipeline import admit, delete, handoff, lifecycle_sweep
from dmr_projection import (
    cross_scope_leak,
    rebuild,
    rebuild_matches,
    validate_projection,
)

FAR_FUTURE = "2099-01-01T00:00:00Z"


def _bundle() -> tuple[dict[str, Any], dict[str, Any]]:
    return good_bundle()


def _admitted_log() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    proposal, decision = _bundle()
    result = admit([], proposal, decision)
    return result["log"], proposal, decision


# --- controls -----------------------------------------------------------------


def _model_admits_itself(proposal: dict[str, Any], decision: dict[str, Any]) -> None:
    decision["authority"]["kind"] = "AGENT"


def _private_reasoning_persists(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    proposal["statement"] = (
        "The private reasoning behind this was that the boundary looked wrong."
    )


def _secret_shaped_value(proposal: dict[str, Any], decision: dict[str, Any]) -> None:
    proposal["statement"] = "Use api_key = sk-live-abc123 when calling the service."


def _rejected_reaches_durable(
    proposal: dict[str, Any], decision: dict[str, Any]
) -> None:
    decision["decision"] = "REJECT"


# The needles name the layer that actually refuses. Two of these are caught by
# the contracts this runtime sits on rather than by the runtime itself, and the
# control asserts the message those contracts raise -- pointing them at a
# runtime message would have meant adding a second, unreachable check just so
# the control had something to match.
CONTROLS: list[tuple[str, Callable[[dict, dict], None], str]] = [
    ("model-admits-its-own-memory", _model_admits_itself, "Human authority required"),
    ("private-reasoning-persists", _private_reasoning_persists, "private reasoning"),
    ("secret-shaped-value-persists", _secret_shaped_value, "secret-shaped statement"),
]


def run_selftest(module_root: Path) -> tuple[int, int]:
    positives = 0
    failures: list[str] = []

    # --- positives ----------------------------------------------------------
    log, proposal, decision = _admitted_log()
    if len(log) != 1 or log[0]["state"] != "ACTIVE":
        raise ContractError(f"admission produced {log}")
    if log[0]["writer"] != "LOOPX_LEDGER_REDUCER":
        raise ContractError("the event was not written by the reducer")
    validate_event(log[0])
    positives += 1

    replay = admit(log, proposal, decision)
    if replay["outcome"] != "NOOP" or replay["appended"]:
        raise ContractError(
            f"replaying one admission appended {replay['appended']}; the memory would "
            "gain a revision nobody decided"
        )
    positives += 1

    rejected = admit(log, proposal, {**copy.deepcopy(decision), "decision": "REJECT"})
    if rejected["outcome"] != "REJECTED" or rejected["appended"]:
        raise ContractError("a rejected proposal reached durable state")
    if len(rejected["log"]) != len(log):
        raise ContractError("a rejection changed the log")
    positives += 1

    # A genuinely new decision supersedes, and leaves exactly one ACTIVE.
    second = copy.deepcopy(decision)
    second["decision_id"] = "decision-second"
    second["created_at"] = "2026-08-15T00:00:00Z"
    superseded = admit(log, proposal, second)
    if superseded["outcome"] != "APPENDED":
        raise ContractError(f"a new decision produced {superseded['outcome']}")
    # Asked of current(), not by counting ACTIVE events: in an append-only log
    # the admission that made revision 1 active still says ACTIVE forever.
    head = current(superseded["log"], proposal["canonical_key"])
    if head is None or head["revision"] != 2:
        raise ContractError(f"supersession left head {head}")
    if head["supersedes_event_id"] != log[0]["event_id"]:
        raise ContractError("the supersession does not name what it replaced")
    old = [event for event in superseded["log"] if event["revision"] == 1]
    if not old or old[0]["content"] != proposal["statement"]:
        raise ContractError("the superseded claim is no longer readable")
    positives += 1

    # The authority ladder, both directions.
    if not outranks("SOURCE", "MEMORY"):
        raise ContractError("SOURCE does not outrank MEMORY")
    if outranks("MEMORY", "TEST"):
        raise ContractError("MEMORY outranks TEST")
    if list(LADDER)[-1] != "MEMORY":
        raise ContractError("MEMORY is not the lowest rung")
    resolution = resolve(
        [
            {
                "rung": "MEMORY",
                "statement": "old claim",
                "ref": "m",
                "observed_at": FAR_FUTURE,
            },
            {
                "rung": "SOURCE",
                "statement": "current claim",
                "ref": "s",
                "observed_at": FAR_FUTURE,
            },
        ]
    )
    if (
        resolution["answer"] != "current claim"
        or not resolution["memory_was_overridden"]
    ):
        raise ContractError(f"the ladder resolved to {resolution}")
    if not resolution["overridden"]:
        raise ContractError("the overridden claim was dropped rather than named")
    positives += 1

    # A contradicted memory is contested, not deleted.
    proposals = invalidation_proposals(resolution, "memory-x")
    if not proposals or proposals[0]["proposed_state"] != "CONTESTED":
        raise ContractError("a contradicted memory was not contested")
    if not proposals[0]["requires_human"]:
        raise ContractError("an invalidation was proposed without a human")
    positives += 1

    # Projection is rebuildable and not canonical.
    projection = rebuild(log)
    validate_projection(projection)
    if projection["canonical"] is not False:
        raise ContractError("the projection claimed to be canonical")
    if not rebuild_matches(log, projection):
        raise ContractError("a fresh rebuild did not match itself")
    positives += 1

    # Deleting the projection loses nothing: it rebuilds from events alone.
    if rebuild(log)["projection_digest"] != projection["projection_digest"]:
        raise ContractError("two rebuilds of one log disagreed")
    positives += 1

    # The capsule is bounded and says what it dropped.
    scope = proposal["scope"]["valid_from_commit"]
    full = handoff(log, scope, 4096)["capsule"]
    tiny = handoff(log, scope, 256)["capsule"]
    if not full["complete"] or full["dropped_for_budget"]:
        raise ContractError("the full capsule dropped entries")
    if tiny["complete"] or not tiny["dropped_for_budget"]:
        raise ContractError(
            "a capsule that hit its budget reported itself complete; a reader would "
            "conclude the missing memories do not exist"
        )
    if tiny["approx_bytes"] > tiny["max_bytes"]:
        raise ContractError("the capsule exceeded its own budget")
    positives += 1

    # No cross-scope leakage.
    if cross_scope_leak(full, {"other-project", "other-session"}):
        raise ContractError("the capsule carried another project's memories")
    positives += 1

    # Deletion: content unretrievable, history intact.
    removed = delete(
        log, proposal["canonical_key"], "ed3c", "2026-08-16T09:00:00Z", "request"
    )
    if removed["residue"] or removed["content_retrievable"]:
        raise ContractError(f"content survived deletion: {removed['residue']}")
    if not removed["history_preserved"] or len(removed["log"]) < len(log):
        raise ContractError("deletion removed history")
    if not removed["tombstone"]["removed_event_ids"]:
        raise ContractError("the tombstone named no events")
    if removed["projection"]["entry_count"] != 0:
        raise ContractError("a tombstoned memory survived into the projection")
    for event in removed["log"]:
        if event["content"] == proposal["statement"]:
            raise ContractError("the removed statement is still in the log")
    positives += 1

    # And an export of a tombstoned memory is refused.
    try:
        export(
            removed["log"], proposal["canonical_key"], "ed3c", "2026-08-16T10:00:00Z"
        )
    except ContractError as exc:
        if "authorised the removal" not in str(exc):
            failures.append(f"export refusal read: {exc}")
    else:
        failures.append("a tombstoned memory was exported")

    # Expiry is not deletion.
    swept = lifecycle_sweep(log, FAR_FUTURE, "ed3c")
    if not swept["due"] or not swept["appended"]:
        raise ContractError("an expired memory was not swept")
    if swept["content_removed"]:
        raise ContractError("an expiry removed content")
    if rebuild(swept["log"])["entry_count"] != 0:
        raise ContractError("an expired memory stayed in the projection")
    if not any(event["content"] == proposal["statement"] for event in swept["log"]):
        raise ContractError(
            "expiry removed the content; expiry stops a memory being current, it does "
            "not delete what was said"
        )
    positives += 1

    # --- controls -----------------------------------------------------------
    for name, mutate, needle in CONTROLS:
        bad_proposal, bad_decision = _bundle()
        mutate(bad_proposal, bad_decision)
        try:
            admit([], bad_proposal, bad_decision)
        except ContractError as exc:
            if needle not in str(exc):
                failures.append(
                    f"{name} refused for the wrong reason: expected {needle!r}, got {exc}"
                )
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{name} raised {type(exc).__name__}: {exc}")
        else:
            failures.append(f"{name} was accepted")

    # A rejected decision cannot build an admitted event even directly.
    bad_proposal, bad_decision = _bundle()
    _rejected_reaches_durable(bad_proposal, bad_decision)
    try:
        build_event(bad_proposal, bad_decision, "MEMORY_ADMITTED", "ACTIVE", 1)
    except ContractError as exc:
        if "rather than by a person" not in str(exc):
            failures.append(f"direct-build refusal read: {exc}")
    else:
        failures.append("a REJECT decision built an admitted event")

    # Two ACTIVE revisions of one memory.
    # Same revision, different origin: two events claiming one point in the
    # memory's history. Bumping the revision instead would be a legitimate new
    # revision and the control would test nothing.
    forged = copy.deepcopy(log[0])
    forged["origin_digest"] = "forged"
    from dmr_event import event_id as _event_id

    forged["event_id"] = _event_id(forged)
    try:
        append(log, [forged])
    except ContractError as exc:
        if "whichever it saw last" not in str(exc):
            failures.append(f"two-active refusal read: {exc}")
    else:
        failures.append("a second event at one revision was appended")

    # An event whose writer is not the reducer.
    impostor = {**copy.deepcopy(log[0]), "writer": "AGENT"}
    try:
        validate_event(impostor)
    except ContractError as exc:
        if "nobody admitted" not in str(exc):
            failures.append(f"writer refusal read: {exc}")
    else:
        failures.append("an event written by an agent was accepted")

    # A projection promoted to canonical.
    promoted = {**rebuild(log), "canonical": True}
    try:
        validate_projection(promoted)
    except ContractError as exc:
        if "promoted" not in str(exc):
            failures.append(f"projection refusal read: {exc}")
    else:
        failures.append("a projection claiming to be canonical was accepted")

    # A tombstone that drops history.
    event, record = tombstone(
        log, proposal["canonical_key"], "ed3c", "2026-08-16T09:00:00Z", "r"
    )
    from dmr_lifecycle import validate_tombstone

    try:
        validate_tombstone({**record, "history_preserved": False})
    except ContractError as exc:
        if "audit trail" not in str(exc):
            failures.append(f"tombstone refusal read: {exc}")
    else:
        failures.append("a tombstone that drops history was accepted")

    # A redaction that missed an event leaves retrievable content.
    half = redact_log([*log], "some-other-key")
    if not residue(half, digest(log[0]["content"])):
        failures.append(
            "the residue check found nothing when the content was still present; it "
            "would then report a partial redaction as clean"
        )

    if failures:
        raise ContractError(
            "planted controls did not behave:\n  " + "\n  ".join(failures)
        )
    _ = current, event
    return positives, len(CONTROLS) + 7
