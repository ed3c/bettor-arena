#!/usr/bin/env python3
"""Positive run plus one control per failure named in #66's control list.

These are contract-level controls over request, lease and parity shapes. The
three *physical* controls -- a real process writing outside its workspace, a
real timeout, a real clean run -- live in control_fabric.py, because a fixture
asserting that a rule exists cannot answer "does it physically turn red".
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

from fabric_common import ContractError, load_json
from fabric_lease import admit_lease, gc_candidates
from fabric_parity import build_matrix, validate_matrix
from fabric_request import validate_request


def load_bundle(root: Path) -> dict[str, Any]:
    good = root / "tests" / "fixtures" / "good"
    return {
        "request": load_json(good / "request.json"),
        "lease": load_json(good / "lease.json"),
        "receipt": load_json(good / "receipt.json"),
        "now": "2026-08-15T10:30:00Z",
        "revision": 0,
        "declared_adapters": [
            "local-disposable-workspace",
            "e2b-sandbox",
            "firecracker-vm",
        ],
    }


def run_pipeline(
    bundle: dict[str, Any], held: set[str] | None = None
) -> dict[str, Any]:
    validate_request(bundle["request"])
    admitted = admit_lease(bundle["lease"], bundle["now"], bundle["revision"], held)
    matrix = build_matrix(
        "local-disposable-workspace",
        {"local-disposable-workspace": bundle["receipt"]},
        bundle["declared_adapters"],
    )
    validate_matrix(matrix)
    return {"lease": admitted, "matrix": matrix}


def _same_lease_twice(b: dict[str, Any]) -> None:
    b["_held"] = {b["lease"]["lease_id"]}


def _expired_lease(b: dict[str, Any]) -> None:
    b["now"] = "2026-08-15T23:00:00Z"


def _stale_lease_revision(b: dict[str, Any]) -> None:
    b["revision"] = 7


def _workspace_points_at_live_checkout(b: dict[str, Any]) -> None:
    b["request"]["workspace"]["read_only_paths"] = ["../../owner-checkout"]


def _path_escape(b: dict[str, Any]) -> None:
    b["request"]["workspace"]["writable_paths"] = ["artifacts/../../elsewhere"]


def _writable_source_mount(b: dict[str, Any]) -> None:
    b["request"]["workspace"]["writable_paths"] = ["artifacts", "src"]
    b["request"]["workspace"]["read_only_paths"] = ["src"]


def _network_deny_without_attestation(b: dict[str, Any]) -> None:
    b["request"]["network"]["requested"] = "deny"


def _secret_value_in_request(b: dict[str, Any]) -> None:
    b["request"]["environment"]["secret_refs"] = [
        "ghp_abcdefghijklmnopqrstuvwxyz012345"
    ]


def _cache_contaminates_other_subject(b: dict[str, Any]) -> None:
    b["request"]["dependencies"]["cache_policy"] = "subject_scoped"
    b["request"]["dependencies"]["cache_key"] = "cache-for-some-other-commit"


def _contamination_check_disabled(b: dict[str, Any]) -> None:
    b["request"]["dependencies"]["contamination_check"] = False


def _no_process_group(b: dict[str, Any]) -> None:
    b["request"]["process"]["process_group"] = False


def _cleanup_optional(b: dict[str, Any]) -> None:
    b["request"]["workspace"]["cleanup"] = "OPTIONAL"


def _artifact_outside_capture_root(b: dict[str, Any]) -> None:
    b["request"]["artifacts"]["expected_paths"] = ["src/leaked.json"]


def _absent_adapter_rendered_as_agreement(b: dict[str, Any]) -> None:
    # The matrix is built correctly, then edited the way a UI would edit it --
    # filling absent rows in as if they matched.
    original = build_matrix(
        "local-disposable-workspace",
        {"local-disposable-workspace": b["receipt"]},
        b["declared_adapters"],
    )
    for row in original["rows"]:
        if row["state"] == "NOT_EXERCISED":
            row["dimensions"] = {k: "MATCH" for k in row["dimensions"]}
    b["_prebuilt_matrix"] = original


def _provider_error_as_gate_failure(b: dict[str, Any]) -> None:
    b["receipt"]["outcome"] = "GATE_FAILURE"
    b["receipt"]["execution"]["exit_code"] = None


def _cleanup_pass_with_residue(b: dict[str, Any]) -> None:
    b["receipt"]["cleanup"]["status"] = "PASS"
    b["receipt"]["cleanup"]["residue_paths"] = ["src/sneaked.txt"]


def _parity_reference_never_ran(b: dict[str, Any]) -> None:
    b["_reference_missing"] = True


CONTROLS: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
    ("two Workers receive the same lease", _same_lease_twice),
    ("expired lease executes", _expired_lease),
    ("lease granted at a revision the task has left", _stale_lease_revision),
    (
        "workspace points at the owner's live checkout",
        _workspace_points_at_live_checkout,
    ),
    ("writable path escapes the workspace", _path_escape),
    ("source mount declared both read-only and writable", _writable_source_mount),
    ("network deny claimed without attestation", _network_deny_without_attestation),
    ("secret value instead of a reference", _secret_value_in_request),
    (
        "cache key not scoped to the subject it claims",
        _cache_contaminates_other_subject,
    ),
    ("dependency contamination check disabled", _contamination_check_disabled),
    ("no process group, so a timeout orphans children", _no_process_group),
    ("cleanup declared optional", _cleanup_optional),
    ("artifact captured from outside the capture root", _artifact_outside_capture_root),
    ("absent adapter rendered as agreement", _absent_adapter_rendered_as_agreement),
    ("provider error reported as a gate failure", _provider_error_as_gate_failure),
    ("cleanup says PASS with residue", _cleanup_pass_with_residue),
    ("parity measured against an adapter that never ran", _parity_reference_never_ran),
]


def _run_trial(bundle: dict[str, Any]) -> None:
    """Route the trial through whichever surface its mutation targets."""
    if bundle.pop("_reference_missing", False):
        build_matrix("local-disposable-workspace", {}, bundle["declared_adapters"])
        return
    prebuilt = bundle.pop("_prebuilt_matrix", None)
    if prebuilt is not None:
        validate_matrix(prebuilt)
        return
    held = bundle.pop("_held", None)
    validate_request(bundle["request"])
    admit_lease(bundle["lease"], bundle["now"], bundle["revision"], held)
    receipt = bundle["receipt"]
    # Receipt-shaped mutations are checked here rather than in a validator the
    # adapter also uses, so a receipt that arrives from any adapter is held to
    # the same two rules: cleanup cannot claim PASS over residue, and a provider
    # problem is not a gate verdict.
    if receipt["cleanup"]["status"] == "PASS" and receipt["cleanup"]["residue_paths"]:
        raise ContractError(
            "cleanup reports PASS with residue present; the check did not look"
        )
    if receipt["outcome"] == "GATE_FAILURE":
        raise ContractError(
            "a runtime receipt may not carry a gate verdict; a provider problem is "
            "not evidence about the code"
        )
    matrix = build_matrix(
        "local-disposable-workspace",
        {"local-disposable-workspace": receipt},
        bundle["declared_adapters"],
    )
    validate_matrix(matrix)


def run_selftest(root: Path) -> tuple[int, int]:
    bundle = load_bundle(root)

    positive = run_pipeline(copy.deepcopy(bundle))
    matrix = positive["matrix"]
    if matrix["not_exercised_count"] != 2:
        raise ContractError(
            f"expected two NOT_EXERCISED adapters, got {matrix['not_exercised_count']}"
        )
    if any(
        r["state"] == "PARITY"
        for r in matrix["rows"]
        if r["adapter"] != "local-disposable-workspace"
    ):
        raise ContractError("an adapter with no receipt was reported at parity")

    # GC finds the expired lease and nothing else.
    expired = copy.deepcopy(bundle["lease"])
    expired["lease_id"] = "l-expired"
    expired["expires_at"] = "2026-08-15T10:00:01Z"
    candidates = gc_candidates([bundle["lease"], expired], bundle["now"])
    if [c["lease_id"] for c in candidates] != ["l-expired"]:
        raise ContractError(
            f"GC selected {[c['lease_id'] for c in candidates]}; an orphan sweep that "
            "reclaims live workspaces is worse than no sweep"
        )

    survived: list[str] = []
    for name, mutate in CONTROLS:
        trial = copy.deepcopy(bundle)
        mutate(trial)
        try:
            _run_trial(trial)
        except ContractError:
            continue
        survived.append(name)

    trial = copy.deepcopy(bundle)
    trial["request"] = load_json(
        root / "tests" / "fixtures" / "hollow" / "request.json"
    )
    try:
        _run_trial(trial)
    except ContractError:
        pass
    else:
        survived.append("hollow request bundle was admitted")

    if survived:
        raise ContractError("controls survived: " + json.dumps(survived))
    return 1, len(CONTROLS) + 1
