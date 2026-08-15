#!/usr/bin/env python3
"""Positive run plus one control per failure named in #67's control list.

A control that survives is reported by name. Each was also checked to fail for
its own reason via scripts/probe_controls.py -- a control that turns red for an
unrelated reason is a false negative wearing a green badge, and the failure it
names would still get through.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

from obs_action import admit_request
from obs_common import ContractError, canonical_bytes, load_json
from obs_envelope import project, rebuild_matches


def load_bundle(root: Path) -> dict[str, Any]:
    good = root / "tests" / "fixtures" / "good"
    return {
        "events": load_json(good / "ledger.json"),
        "policy": load_json(good / "redaction-policy.json"),
        "projection": load_json(good / "projection.json"),
        "state": load_json(good / "state.json"),
        "request": load_json(good / "action-request.json"),
    }


def run_pipeline(
    bundle: dict[str, Any], consumed: set[str] | None = None
) -> dict[str, Any]:
    """Project -> rebuild-and-compare -> admit a console request."""
    projection = project(bundle["events"], bundle["policy"])
    rebuild = rebuild_matches(bundle["events"], bundle["policy"], bundle["projection"])
    proposal = admit_request(
        bundle["request"], bundle["state"], bundle["projection"], consumed
    )
    return {"projection": projection, "rebuild": rebuild, "proposal": proposal}


def _trace_store_disagrees(b: dict[str, Any]) -> None:
    b["projection"]["envelopes"][1]["lifecycle_state"] = "TODO_COMPLETED"


def _digest_not_recomputed(b: dict[str, Any]) -> None:
    b["projection"]["projection_digest"] = "sha256:" + "0" * 64


def _redacted_event_claims_continuity(b: dict[str, Any]) -> None:
    del b["events"][2]


def _chain_broken(b: dict[str, Any]) -> None:
    b["events"][3]["previous_digest"] = "sha256:" + "9" * 64


def _secret_in_envelope(b: dict[str, Any]) -> None:
    # A policy that no longer drops env: the planted token would reach the
    # envelope, so the policy floor must refuse the policy itself.
    b["policy"]["drop_keys"] = [k for k in b["policy"]["drop_keys"] if k != "env"]


def _signed_in_body_pattern_removed(b: dict[str, Any]) -> None:
    b["policy"]["drop_value_patterns"] = [
        p for p in b["policy"]["drop_value_patterns"] if "PRIVATE KEY" not in p
    ]


def _unbounded_stdout(b: dict[str, Any]) -> None:
    b["policy"]["max_string_bytes"] = 0


def _stale_revision(b: dict[str, Any]) -> None:
    b["request"]["observed_state"]["state_revision"] = 1


def _stale_ledger_head(b: dict[str, Any]) -> None:
    b["request"]["observed_state"]["ledger_head"] = "sha256:" + "7f" * 32


def _stale_projection_shown(b: dict[str, Any]) -> None:
    b["request"]["displayed_projection_digest"] = "sha256:" + "5e" * 32


def _unsigned_action(b: dict[str, Any]) -> None:
    b["request"]["signer"]["signature_ref"] = "not-a-digest"


def _duplicate_action(b: dict[str, Any]) -> None:
    b["_consumed"] = {b["request"]["request_id"]}


def _console_commands_instead_of_proposing(b: dict[str, Any]) -> None:
    b["request"]["signer"]["mark_pass"] = True


def _console_persists_private_reasoning(b: dict[str, Any]) -> None:
    b["request"]["signer"]["chain_of_thought"] = "the operator was thinking about..."


def _policy_version_mismatch(b: dict[str, Any]) -> None:
    b["policy"]["policy_version"] = "2026-01-01.0"


def _unsorted_policy(b: dict[str, Any]) -> None:
    b["policy"]["drop_keys"] = list(reversed(b["policy"]["drop_keys"]))


def _action_outside_vocabulary(b: dict[str, Any]) -> None:
    b["request"]["requested_action"] = "MARK_GATE_PASS"


CONTROLS: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
    ("trace store modified to disagree with the ledger", _trace_store_disagrees),
    ("projection digest not recomputed after content changed", _digest_not_recomputed),
    (
        "removed ledger event makes the projection claim continuity",
        _redacted_event_claims_continuity,
    ),
    ("ledger chain broken between two events", _chain_broken),
    ("policy stops dropping a secret-shaped key", _secret_in_envelope),
    ("policy stops dropping a signed-in body pattern", _signed_in_body_pattern_removed),
    ("policy allows unbounded strings", _unbounded_stdout),
    ("console sends a stale state revision", _stale_revision),
    ("console sends a stale ledger head", _stale_ledger_head),
    (
        "console acted on a projection that is no longer current",
        _stale_projection_shown,
    ),
    ("action request is unsigned", _unsigned_action),
    ("duplicate request would commit twice", _duplicate_action),
    (
        "console tries to command rather than propose",
        _console_commands_instead_of_proposing,
    ),
    ("console persists private reasoning", _console_persists_private_reasoning),
    ("rebuild compared across policy versions", _policy_version_mismatch),
    (
        "policy arrays unsorted, so equal policies would digest differently",
        _unsorted_policy,
    ),
    ("requested action outside the admitted vocabulary", _action_outside_vocabulary),
]


def run_selftest(root: Path) -> tuple[int, int]:
    bundle = load_bundle(root)

    positive = run_pipeline(copy.deepcopy(bundle))
    if positive["projection"]["authority"] != "PROJECTION_ONLY":
        raise ContractError("projection claims authority it does not have")
    if positive["proposal"]["canonical_writer"] != "LOOPX_LEDGER_REDUCER":
        raise ContractError("proposal names a writer other than the reducer")
    if not positive["rebuild"]["rebuilt"]:
        raise ContractError("rebuild did not reproduce the stored projection")

    # Backend absence must not change any of this. There is no backend in this
    # path at all, and that is the point: LoopX correctness cannot depend on a
    # trace store being reachable.
    twice = run_pipeline(copy.deepcopy(bundle))
    if canonical_bytes(twice["projection"]) != canonical_bytes(positive["projection"]):
        raise ContractError(
            "two projections of the same ledger differ; not deterministic"
        )

    survived: list[str] = []
    for name, mutate in CONTROLS:
        trial = copy.deepcopy(bundle)
        mutate(trial)
        consumed = trial.pop("_consumed", None)
        try:
            run_pipeline(trial, consumed)
        except ContractError:
            continue
        survived.append(name)

    for name, key, path in (
        ("hollow ledger", "events", "ledger.json"),
        ("hollow projection", "projection", "projection.json"),
    ):
        trial = copy.deepcopy(bundle)
        trial[key] = load_json(root / "tests" / "fixtures" / "hollow" / path)
        try:
            run_pipeline(trial)
        except ContractError:
            continue
        survived.append(f"{name} bundle was admitted")

    if survived:
        raise ContractError("controls survived: " + json.dumps(survived))
    return 1, len(CONTROLS) + 2
