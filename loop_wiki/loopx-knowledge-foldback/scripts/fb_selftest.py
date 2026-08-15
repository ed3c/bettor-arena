#!/usr/bin/env python3
"""Positive properties plus one planted control per named failure in #71.

Each control mutates the good fixtures in exactly one place and asserts the
fold-back refuses, matching on the substring its own rule raises. A control that
changed two things could pass because of the change nobody was testing, and a
control satisfied by an unrelated error reports a rule as enforced when the rule
enforcing it is a different one.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

from fb_bundle import validate_bundle, validate_receipt
from fb_common import ContractError
from fb_history import rollback, validate_history
from fb_pipeline import admit_bundle, fold_back, rerun_is_noop

NAMES = (
    "change-delta",
    "cards",
    "patches",
    "similarity",
    "revision-history",
    "decisions",
)


def load_bundle_inputs(root: Path) -> dict[str, Any]:
    good = root / "tests/fixtures/good"
    return {
        name: json.loads((good / f"{name}.json").read_text(encoding="utf-8"))
        for name in NAMES
    }


def _fold(inputs: dict[str, Any]) -> dict[str, Any]:
    return fold_back(
        inputs["change-delta"],
        inputs["cards"],
        inputs["patches"],
        inputs["similarity"],
        inputs["revision-history"],
        inputs.get("_anchor_states"),
    )


def _run(inputs: dict[str, Any]) -> dict[str, Any]:
    folded = _fold(inputs)
    return admit_bundle(
        folded["bundle"],
        inputs["revision-history"],
        inputs["decisions"],
        inputs["cards"],
    )


def _patch(inputs: dict[str, Any], patch_id: str) -> dict[str, Any]:
    for patch in inputs["patches"]:
        if patch["patch_id"] == patch_id:
            return patch
    raise KeyError(patch_id)


def _card(inputs: dict[str, Any], key: str) -> dict[str, Any]:
    for card in inputs["cards"]:
        if card["canonical_key"] == key:
            return card
    raise KeyError(key)


def _anchor(inputs: dict[str, Any], anchor_id: str) -> dict[str, Any]:
    for anchor in inputs["change-delta"]["anchors"]:
        if anchor["anchor_id"] == anchor_id:
            return anchor
    raise KeyError(anchor_id)


# --- controls -----------------------------------------------------------------


def _static_diff_becomes_tested(inputs: dict[str, Any]) -> None:
    # retry_interval has no test execution covering it, only a diff.
    _patch(inputs, "p-002")["evidence_class"] = "TEST"


def _runtime_inferred_from_static(inputs: dict[str, Any]) -> None:
    _patch(inputs, "p-002")["evidence_class"] = "RUNTIME"


def _unattested_runtime(inputs: dict[str, Any]) -> None:
    inputs["change-delta"]["runtime_observations"][0]["adapter_attested"] = False


def _failed_test_counted_as_tested(inputs: dict[str, Any]) -> None:
    inputs["change-delta"]["test_executions"][0]["exit_code"] = 1
    _patch(inputs, "p-001")["evidence_class"] = "TEST"


def _model_summary_as_evidence(inputs: dict[str, Any]) -> None:
    _anchor(inputs, "an-append")["kind"] = "MODEL_SUMMARY"


def _new_card_id_for_existing_key(inputs: dict[str, Any]) -> None:
    _card(inputs, "rule:retry-interval")["card_id"] = "card-0123456789abcdef"


def _conclusion_flip_as_update(inputs: dict[str, Any]) -> None:
    _patch(inputs, "p-002")["kind"] = "UPDATE"


def _supersede_without_flip(inputs: dict[str, Any]) -> None:
    patch = _patch(inputs, "p-001")
    patch["kind"] = "SUPERSEDE"


def _code_rewrites_an_adr(inputs: dict[str, Any]) -> None:
    patch = _patch(inputs, "p-003")
    patch["kind"] = "UPDATE"
    patch["claim_after"] = "retry policy is exponential backoff from 1s"


def _similarity_produces_a_patch(inputs: dict[str, Any]) -> None:
    patch = copy.deepcopy(_patch(inputs, "p-002"))
    patch.update(
        {
            "patch_id": "p-004",
            "canonical_key": "rule:cache-warming",
            "card_id": _card(inputs, "rule:cache-warming")["card_id"],
            "kind": "UPDATE",
            "match_reason": "SEMANTIC_SIMILARITY",
            "claim_before": "the card cache is warmed on boot",
            "claim_after": "the card cache is warmed lazily",
        }
    )
    inputs["patches"].append(patch)
    inputs["decisions"].append(
        {
            "patch_id": "p-004",
            "decision": "ADMIT",
            "actor": "ed3c",
            "at": "2026-08-15T11:00:00Z",
            "note": "",
        }
    )


def _dependency_counted_twice(inputs: dict[str, Any]) -> None:
    _patch(inputs, "p-002")["source_dependency_keys"] = [
        "notes/meeting.md",
        "notes/meeting.md",
    ]


def _patch_against_stale_revision(inputs: dict[str, Any]) -> None:
    # The history moved on; the card the patch was computed from did not. Done
    # by advancing the history rather than by editing the card's revision
    # number, which would also break the patch's rollback target and the control
    # would then be satisfied by that instead.
    from fb_history import revision_id

    history = inputs["revision-history"]
    entry = copy.deepcopy(
        next(
            r
            for r in history["revisions"]
            if r["canonical_key"] == "rule:retry-interval"
        )
    )
    entry.update(
        {
            "revision": 2,
            "claim": "retries use a fixed 5s interval, capped at 3 attempts",
            "origin_digest": "another-foldback",
        }
    )
    entry["revision_id"] = revision_id(entry)
    history["revisions"] = [*history["revisions"], entry]


def _anchor_from_foreign_commit(inputs: dict[str, Any]) -> None:
    _anchor(inputs, "an-retry")["commit"] = "9f" * 20


def _fabricated_line_numbers(inputs: dict[str, Any]) -> None:
    # The anchor still validates in shape; the recheck says the content moved.
    inputs["_anchor_states"] = [
        {"anchor_id": "an-retry", "state": "STALE_MOVED", "found_at": [15, 19]},
        {"anchor_id": "an-append", "state": "FRESH", "found_at": [40, 52]},
    ]


def _before_equals_after(inputs: dict[str, Any]) -> None:
    inputs["change-delta"]["before"]["commit"] = inputs["change-delta"]["after"][
        "commit"
    ]


def _mutable_ref_kind(inputs: dict[str, Any]) -> None:
    inputs["change-delta"]["after"]["ref_kind"] = "BRANCH"


def _interface_delta_without_symbol(inputs: dict[str, Any]) -> None:
    inputs["change-delta"]["public_interface_delta"] = sorted(
        [*inputs["change-delta"]["public_interface_delta"], "undeclared_symbol"]
    )


def _symbol_delta_in_unchanged_file(inputs: dict[str, Any]) -> None:
    inputs["change-delta"]["symbol_delta"][0]["path"] = "src/never_touched.py"


def _partial_decision_set(inputs: dict[str, Any]) -> None:
    inputs["decisions"] = inputs["decisions"][:1]


def _rejection_without_a_note(inputs: dict[str, Any]) -> None:
    for decision in inputs["decisions"]:
        if decision["decision"] == "REJECT":
            decision["note"] = ""


def _patch_renames_the_card(inputs: dict[str, Any]) -> None:
    _patch(inputs, "p-002")["card_id"] = "card-fedcba9876543210"


def _noop_that_changes_the_claim(inputs: dict[str, Any]) -> None:
    patch = _patch(inputs, "p-001")
    patch["kind"] = "NOOP"
    patch["claim_after"] = "something else entirely"


def _conflict_with_nothing_unresolved(inputs: dict[str, Any]) -> None:
    _patch(inputs, "p-003")["unresolved"] = []


def _rollback_that_deletes(inputs: dict[str, Any]) -> None:
    _patch(inputs, "p-002")["rollback"] = {
        "kind": "DELETE_REVISION",
        "restores_revision": 1,
    }


def _claim_before_mismatch(inputs: dict[str, Any]) -> None:
    _patch(inputs, "p-002")["claim_before"] = "retries use whatever the config says"


def _patch_with_no_anchor(inputs: dict[str, Any]) -> None:
    _patch(inputs, "p-002")["supporting_anchor_ids"] = []


def _duplicate_history_revision(inputs: dict[str, Any]) -> None:
    history = inputs["revision-history"]
    history["revisions"] = [
        *history["revisions"],
        copy.deepcopy(history["revisions"][0]),
    ]


def _history_goes_backwards(inputs: dict[str, Any]) -> None:
    history = inputs["revision-history"]
    entry = copy.deepcopy(history["revisions"][0])
    entry["revision"] = 1
    entry["claim"] = "an earlier claim reinstated in place"
    entry["origin_digest"] = "tampered"
    from fb_history import revision_id

    entry["revision_id"] = revision_id(entry)
    history["revisions"] = [*history["revisions"], entry]


CONTROLS: list[tuple[str, Callable[[dict[str, Any]], None], str]] = [
    (
        "static-diff-recorded-as-tested",
        _static_diff_becomes_tested,
        "does not show what it does",
    ),
    (
        "runtime-inferred-from-static-diff",
        _runtime_inferred_from_static,
        "does not show what it does",
    ),
    ("unattested-runtime-observation", _unattested_runtime, "not adapter-attested"),
    (
        "failed-test-counted-as-verification",
        _failed_test_counted_as_tested,
        "only supports",
    ),
    ("model-summary-cited-as-evidence", _model_summary_as_evidence, "closes a loop"),
    ("new-card-id-for-existing-key", _new_card_id_for_existing_key, "forks the card"),
    ("conclusion-flip-as-update", _conclusion_flip_as_update, "Use SUPERSEDE"),
    ("supersede-without-a-flip", _supersede_without_flip, "buries a live claim"),
    (
        "code-change-rewrites-an-adr",
        _code_rewrites_an_adr,
        "does not amend the decision",
    ),
    (
        "similarity-alone-produces-a-patch",
        _similarity_produces_a_patch,
        "cannot rewrite one",
    ),
    ("source-dependency-counted-twice", _dependency_counted_twice, "more than once"),
    (
        "patch-against-a-stale-revision",
        _patch_against_stale_revision,
        "no longer current",
    ),
    (
        "anchor-from-a-foreign-commit",
        _anchor_from_foreign_commit,
        "diff this delta does not cover",
    ),
    (
        "fabricated-line-numbers-after-movement",
        _fabricated_line_numbers,
        "fabricated citations",
    ),
    ("before-equals-after", _before_equals_after, "NOOP, not a delta"),
    ("mutable-ref-as-subject", _mutable_ref_kind, "IMMUTABLE_COMMIT"),
    (
        "interface-delta-without-symbol",
        _interface_delta_without_symbol,
        "whichever is read first wins",
    ),
    (
        "symbol-delta-in-an-unchanged-file",
        _symbol_delta_in_unchanged_file,
        "did not come from this diff",
    ),
    ("partial-decision-set", _partial_decision_set, "only partly saw"),
    ("rejection-without-a-note", _rejection_without_a_note, "re-proposed"),
    ("patch-renames-the-card", _patch_renames_the_card, "second card nobody asked for"),
    (
        "noop-that-changes-the-claim",
        _noop_that_changes_the_claim,
        "NOOP that changes the claim",
    ),
    (
        "conflict-with-nothing-unresolved",
        _conflict_with_nothing_unresolved,
        "nothing unresolved",
    ),
    ("rollback-that-deletes-history", _rollback_that_deletes, "erase the evidence"),
    ("claim-before-does-not-match-card", _claim_before_mismatch, "stale read"),
    ("revision-with-no-citation", _patch_with_no_anchor, "written from memory"),
    ("duplicate-revision-in-history", _duplicate_history_revision, "already there"),
    (
        "history-rewritten-not-appended",
        _history_goes_backwards,
        "rather than appended to",
    ),
]


def run_selftest(root: Path) -> tuple[int, int]:
    base = load_bundle_inputs(root)
    positives = 0

    folded = _fold(copy.deepcopy(base))
    validate_bundle(folded["bundle"])
    positives += 1

    # Similarity surfaces a card without patching it. Both halves matter: the
    # card must appear (so it is not silently dropped) and must not be patchable.
    review = folded["bundle"]["candidates_for_review"]
    if review != ["rule:cache-warming"]:
        raise ContractError(f"similarity candidate not surfaced for review: {review}")
    if any(
        row["patchable"] for row in folded["bundle"]["located"] if row["similarity"]
    ):
        raise ContractError("a similarity match was marked patchable")
    positives += 1

    if folded["preserved_open"] != ["adr:retry-policy-decision"]:
        raise ContractError("the ADR conflict was not preserved as open")
    positives += 1

    first = _run(copy.deepcopy(base))
    validate_receipt(first["receipt"])
    if first["outcome"] != "APPENDED" or len(first["appended_revision_ids"]) != 3:
        raise ContractError(f"unexpected first admit: {first['outcome']}")
    positives += 1

    # The rejected patch is in the history, not absent from it.
    rejected = [r for r in first["history"]["revisions"] if r["state"] == "REJECTED"]
    if [r["canonical_key"] for r in rejected] != ["adr:retry-policy-decision"]:
        raise ContractError(
            "the rejected patch is not in the history; a declined proposal that "
            "leaves no trace gets proposed again with nothing to say it was declined"
        )
    positives += 1

    # A rejection does not advance the card.
    from fb_history import current_revision

    if current_revision(first["history"], "adr:retry-policy-decision") != 1:
        raise ContractError("a rejected patch advanced the card revision")
    positives += 1

    # Idempotence, against the history the first run produced.
    second = admit_bundle(
        folded["bundle"], first["history"], base["decisions"], base["cards"]
    )
    rerun_is_noop(first, second)
    positives += 1

    # Supersession keeps the old claim reachable.
    superseded = next(
        r
        for r in first["history"]["revisions"]
        if r["canonical_key"] == "rule:retry-interval" and r["revision"] == 1
    )
    new = next(
        r
        for r in first["history"]["revisions"]
        if r["canonical_key"] == "rule:retry-interval"
        and r["patch_kind"] == "SUPERSEDE"
    )
    if new["supersedes_revision_id"] != superseded["revision_id"]:
        raise ContractError("the superseding revision does not name what it replaced")
    if superseded not in first["history"]["revisions"]:
        raise ContractError("the superseded claim was removed rather than marked")
    positives += 1

    # Rollback appends and keeps everything, including the evidence it cited.
    rolled = rollback(
        first["history"], new["revision_id"], "ed3c", "2026-08-16T09:00:00Z"
    )
    validate_history(rolled)
    if len(rolled["revisions"]) != len(first["history"]["revisions"]) + 1:
        raise ContractError("rollback did not append exactly one revision")
    for revision in first["history"]["revisions"]:
        if revision not in rolled["revisions"]:
            raise ContractError(
                f"rollback removed revision {revision['revision_id']}; a rollback that "
                "erased the revision would also erase the evidence that justified it"
            )
    if rolled["revisions"][-1]["claim"] != superseded["claim"]:
        raise ContractError("rollback did not restore the previous claim")
    positives += 1

    # And rolling the same revision back twice is the same rollback.
    twice = rollback(rolled, new["revision_id"], "ed3c", "2026-08-16T10:00:00Z")
    if len(twice["revisions"]) != len(rolled["revisions"]):
        raise ContractError("rolling the same revision back twice appended twice")
    positives += 1

    failures = []
    for name, mutate, needle in CONTROLS:
        inputs = copy.deepcopy(base)
        mutate(inputs)
        try:
            _run(inputs)
        except ContractError as exc:
            if needle not in str(exc):
                failures.append(
                    f"{name} was refused, but for the wrong reason: expected a message "
                    f"containing {needle!r}, got {exc}"
                )
            continue
        except Exception as exc:  # noqa: BLE001
            failures.append(
                f"{name} raised {type(exc).__name__}: {exc} -- that is a broken "
                "control, not a refusal; nothing was measured"
            )
            continue
        failures.append(f"{name} was accepted")

    if failures:
        raise ContractError(
            "planted controls did not behave:\n  " + "\n  ".join(failures)
        )
    return positives, len(CONTROLS)
