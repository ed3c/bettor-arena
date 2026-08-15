#!/usr/bin/env python3
"""Positive run plus one control per failure this leaf exists to refuse.

A control that survives is reported by name. A validator whose controls quietly
pass is worse than none: it produces a green that means nothing.

Each control was also checked to fail for its own reason rather than
incidentally -- `scripts/probe_controls.py` prints the actual error per control,
because a control turning red for an unrelated reason leaves the failure it
names still getting through.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

from strategy_common import ContractError, load_json
from strategy_checkpoint import admit_resume
from strategy_engine import admit_proposal, compile_resume_envelope


def load_bundle(root: Path) -> dict[str, Any]:
    good = root / "tests" / "fixtures" / "good"
    return {
        "subject": load_json(good / "subject.json"),
        "state": load_json(good / "state.json"),
        "checkpoint": load_json(good / "checkpoint.json"),
        "proposal": load_json(good / "proposal.json"),
        "interrupt": load_json(good / "interrupt.json"),
        "decision": load_json(good / "decision.json"),
        "gate_classes": load_json(good / "gate-classes.json"),
        "observations": load_json(good / "revalidation-observations.json"),
    }


def run_pipeline(
    bundle: dict[str, Any],
    consumed_tokens: set[str] | None = None,
    consumed_decisions: set[str] | None = None,
) -> dict[str, Any]:
    """Resume -> propose -> decide: the whole admission path in one call."""
    resume = admit_resume(
        bundle["checkpoint"], bundle["state"], bundle["subject"], consumed_tokens
    )
    admission = admit_proposal(bundle["proposal"], bundle["state"], bundle["subject"])
    if admission["outcome"] != "ACCEPTED":
        raise ContractError(f"proposal rejected: {admission.get('reason')}")
    envelope = compile_resume_envelope(
        bundle["interrupt"],
        bundle["decision"],
        bundle["state"],
        bundle["gate_classes"],
        bundle["observations"],
        consumed_decisions,
    )
    return {"resume": resume, "admission": admission, "envelope": envelope}


def _stale_checkpoint(b: dict[str, Any]) -> None:
    b["checkpoint"]["based_on"] = {
        "state_revision": 6,
        "ledger_head": "sha256:" + "11" * 32,
    }


def _divergent_checkpoint(b: dict[str, Any]) -> None:
    b["checkpoint"]["based_on"]["ledger_head"] = "sha256:" + "22" * 32


def _checkpoint_ahead(b: dict[str, Any]) -> None:
    b["checkpoint"]["based_on"]["state_revision"] = 8


def _planner_writes_canonical_state(b: dict[str, Any]) -> None:
    b["checkpoint"]["graph_cursor"]["todo_state"] = {"todo-verify-contracts": "PASS"}


def _planner_resets_quota(b: dict[str, Any]) -> None:
    b["checkpoint"]["graph_cache"]["quota"] = {"attempts_used": 0}


def _duplicate_resume(b: dict[str, Any]) -> None:
    b["_tokens"] = {b["checkpoint"]["resume_token"]}


def _duplicate_decision(b: dict[str, Any]) -> None:
    b["_decisions"] = {b["decision"]["decision_id"]}


def _proposal_claims_write_authority(b: dict[str, Any]) -> None:
    b["proposal"]["authority"]["state_write"] = True


def _checkpoint_claims_authority(b: dict[str, Any]) -> None:
    b["proposal"]["planner"]["checkpoint_authority"] = "CANONICAL"


def _decision_bound_to_other_interrupt(b: dict[str, Any]) -> None:
    b["decision"]["interrupt_digest"] = "sha256:" + "33" * 32


def _interrupt_terms_edited_after_signing(b: dict[str, Any]) -> None:
    b["interrupt"]["gate_ids"] = ["gate-flaky-timing", "gate-credential-scan"]


def _decision_not_allowed_by_interrupt(b: dict[str, Any]) -> None:
    b["interrupt"]["allowed_decisions"] = ["CANCEL"]
    body = {k: v for k, v in b["interrupt"].items() if k != "interrupt_digest"}
    from strategy_common import digest

    b["interrupt"]["interrupt_digest"] = digest(body)
    b["decision"]["interrupt_digest"] = b["interrupt"]["interrupt_digest"]


def _unsigned_decision(b: dict[str, Any]) -> None:
    b["decision"]["authority"]["signer_id"] = "x"


def _wrong_subject_decision(b: dict[str, Any]) -> None:
    b["decision"]["subject"]["task_id"] = "some-other-task"


def _exception_without_expiry(b: dict[str, Any]) -> None:
    b["decision"]["exception"]["expires_at"] = ""


def _exception_claims_clean_terminal(b: dict[str, Any]) -> None:
    b["decision"]["exception"]["terminal_visibility"] = "TODO_COMPLETED"


def _exception_waives_non_waivable(b: dict[str, Any]) -> None:
    b["decision"]["exception"]["gate_ids"] = ["gate-credential-scan"]


def _exception_on_undeclared_gate(b: dict[str, Any]) -> None:
    b["decision"]["exception"]["gate_ids"] = ["gate-never-declared"]


def _revalidation_not_required(b: dict[str, Any]) -> None:
    b["decision"]["revalidation_required"] = False


def _resume_without_fresh_observation(b: dict[str, Any]) -> None:
    b["observations"].pop("gate-flaky-timing")


def _failure_outside_exception_scope(b: dict[str, Any]) -> None:
    b["interrupt"]["gate_ids"] = ["gate-flaky-timing", "gate-contract-shape"]
    body = {k: v for k, v in b["interrupt"].items() if k != "interrupt_digest"}
    from strategy_common import digest

    b["interrupt"]["interrupt_digest"] = digest(body)
    b["decision"]["interrupt_digest"] = b["interrupt"]["interrupt_digest"]
    b["observations"]["gate-contract-shape"] = "FAIL"


def _generic_force_skip(b: dict[str, Any]) -> None:
    b["decision"]["authority"]["force_skip"] = True


def _stale_interrupt(b: dict[str, Any]) -> None:
    b["state"] = {"state_revision": 9, "ledger_head": "sha256:" + "44" * 32}
    b["checkpoint"]["based_on"] = b["state"]
    b["proposal"]["based_on"] = b["state"]
    b["proposal"]["command"]["expected_state_revision"] = 9


CONTROLS: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
    ("stale checkpoint resumes against a newer ledger head", _stale_checkpoint),
    ("divergent checkpoint at the same revision", _divergent_checkpoint),
    ("checkpoint claims a revision ahead of the ledger", _checkpoint_ahead),
    (
        "planner projection carries canonical Todo state",
        _planner_writes_canonical_state,
    ),
    ("planner resets the quota through its cache", _planner_resets_quota),
    ("duplicate resume token replays the checkpoint", _duplicate_resume),
    ("duplicate decision id applies the same decision twice", _duplicate_decision),
    ("proposal claims state-write authority", _proposal_claims_write_authority),
    ("proposal claims canonical checkpoint authority", _checkpoint_claims_authority),
    ("decision is bound to a different interrupt", _decision_bound_to_other_interrupt),
    (
        "interrupt terms edited after the digest was signed",
        _interrupt_terms_edited_after_signing,
    ),
    (
        "decision is not among the interrupt's allowed decisions",
        _decision_not_allowed_by_interrupt,
    ),
    ("decision signer is not a usable identity", _unsigned_decision),
    ("decision names another task subject", _wrong_subject_decision),
    ("exception has no expiry", _exception_without_expiry),
    ("exception claims a clean terminal state", _exception_claims_clean_terminal),
    ("exception tries to waive a non-waivable gate", _exception_waives_non_waivable),
    ("exception targets a gate with no declared class", _exception_on_undeclared_gate),
    ("decision declares revalidation is not required", _revalidation_not_required),
    (
        "resume proceeds with no fresh gate observation",
        _resume_without_fresh_observation,
    ),
    (
        "a gate outside the exception's scope is still failing",
        _failure_outside_exception_scope,
    ),
    ("a generic force-skip field reappears", _generic_force_skip),
    ("interrupt was raised at a revision the task has left", _stale_interrupt),
]


def run_selftest(root: Path) -> tuple[int, int]:
    bundle = load_bundle(root)

    positive = run_pipeline(copy.deepcopy(bundle))
    envelope = positive["envelope"]
    if envelope["terminal_visibility"] != "COMPLETED_WITH_EXCEPTION":
        raise ContractError(
            "a scoped exception must stay visible as COMPLETED_WITH_EXCEPTION, got "
            f"{envelope['terminal_visibility']}"
        )
    if envelope["canonical_writer"] != "LOOPX_LEDGER_REDUCER":
        raise ContractError("envelope names a writer other than the reducer")
    if envelope["proposed_event"] != "ADMIT_EXCEPTION":
        raise ContractError("envelope proposes the wrong reducer event")

    survived: list[str] = []
    for name, mutate in CONTROLS:
        trial = copy.deepcopy(bundle)
        mutate(trial)
        tokens = trial.pop("_tokens", None)
        decisions = trial.pop("_decisions", None)
        try:
            run_pipeline(trial, tokens, decisions)
        except ContractError:
            continue
        survived.append(name)

    for name, path in (
        ("hollow decision", root / "tests" / "fixtures" / "hollow" / "decision.json"),
        (
            "hollow checkpoint",
            root / "tests" / "fixtures" / "hollow" / "checkpoint.json",
        ),
    ):
        trial = copy.deepcopy(bundle)
        key = "decision" if "decision" in name else "checkpoint"
        trial[key] = load_json(path)
        try:
            run_pipeline(trial)
        except ContractError:
            continue
        survived.append(f"{name} bundle was admitted")

    if survived:
        raise ContractError("controls survived: " + json.dumps(survived))
    return 1, len(CONTROLS) + 2
