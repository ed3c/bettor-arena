#!/usr/bin/env python3
"""Positive properties, and one planted control per failure named in #101.

Every control asserts on the substring its own rule raises. A control that only
checks "something was refused" passes when a neighbouring guard fires first, and
stays green while the rule it was written for is deleted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from gt_admit import admit, modes_for, probe, require_mode_allowed, validate_profile
from gt_common import (
    ADMISSION_STATES,
    AUTHORITY,
    FORBIDDEN_FLAGS,
    MODE_EFFECTS,
    MODES,
    STATES,
    ContractError,
    argv_for,
    find_conflict_markers,
    find_host_paths,
)
from gt_publish import publication_decision, require_separate_operation

ADMISSION = {
    "tool": "git-town",
    "version": "21.1.0",
    "sha256": "sha256:" + "1" * 64,
    "provenance": "https://github.com/git-town/git-town/releases/tag/v21.1.0",
    "license": "MIT",
    "sbom_ref": "data/git-town/sbom-21.1.0.json",
}

PROFILE = {
    "main_branch": "main",
    "perennial_branches": [],
    "push_hook": False,
    "sync_strategy": "rebase",
    "ship_strategy": "api",
}

PRESENT = {
    "state": "EXECUTABLE_PRESENT_NOT_ADMITTED",
    "path": "/opt/bin/git-town",
    "reported_version": "git-town 21.1.0",
    "reason": "present, and presence is not admission",
}

ABSENT = {
    "state": "EXECUTABLE_ABSENT",
    "path": None,
    "reported_version": None,
    "reason": "git-town is not on PATH. Nothing was run",
}


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

    # The non-negotiable command shape, exactly.
    if argv_for("sync_local_no_push") != [
        "git",
        "town",
        "sync",
        "--stack",
        "--non-interactive",
        "--no-auto-resolve",
        "--no-push",
    ]:
        raise ContractError(f"the sync argv drifted: {argv_for('sync_local_no_push')}")
    checks += 1

    # Dry run precedes live, and carries --dry-run on top of the same shape.
    dry = argv_for("sync_dry_run")
    if dry[:-1] != argv_for("sync_local_no_push") or dry[-1] != "--dry-run":
        raise ContractError(
            f"the dry-run argv is not the live shape plus --dry-run: {dry}"
        )
    checks += 1

    # No mode carries a flag a human owns.
    for mode in MODES:
        overlap = sorted(set(argv_for(mode)) & set(FORBIDDEN_FLAGS))
        if overlap:
            raise ContractError(f"mode {mode} carries {overlap}")
    checks += 1

    # Every mode declares its effects, and only the live sync writes.
    if sorted(MODE_EFFECTS) != sorted(MODES):
        raise ContractError("a mode has no declared effects")
    writers = sorted(name for name, eff in MODE_EFFECTS.items() if eff["writes_tree"])
    if writers != ["sync_local_no_push"]:
        raise ContractError(f"modes that write the tree: {writers}")
    if any(eff["network"] for eff in MODE_EFFECTS.values()):
        raise ContractError(
            "a mode declared network access; --no-push means none of them do"
        )
    checks += 1

    # Absence unlocks nothing, and a human review cannot promote it.
    absent = admit(ABSENT, ADMISSION, PROFILE, live_local_reviewed=True)
    if absent["state"] != "EXECUTABLE_ABSENT" or absent["modes_available"]:
        raise ContractError(
            f"an absent executable produced {absent['state']} with {absent['modes_available']}"
        )
    checks += 1

    # Present but version-mismatched is not admitted.
    mismatch = admit(
        {**PRESENT, "reported_version": "git-town 20.0.0"}, ADMISSION, PROFILE, True
    )
    if mismatch["state"] != "EXECUTABLE_PRESENT_NOT_ADMITTED":
        raise ContractError(f"a version mismatch produced {mismatch['state']}")
    if "describes a different program" not in mismatch["reason"]:
        raise ContractError("the mismatch refusal did not say why")
    checks += 1

    # Unreviewed gets dry run; reviewed gets live local. Neither gets push.
    unreviewed = admit(PRESENT, ADMISSION, PROFILE, live_local_reviewed=False)
    reviewed = admit(PRESENT, ADMISSION, PROFILE, live_local_reviewed=True)
    if (
        unreviewed["state"] != "ADMITTED_DRY_RUN_ONLY"
        or "sync_local_no_push" in unreviewed["modes_available"]
    ):
        raise ContractError("an unreviewed admission unlocked the live lane")
    if reviewed["state"] != "ADMITTED_LOCAL_NO_PUSH":
        raise ContractError(f"a reviewed admission produced {reviewed['state']}")
    if require_mode_allowed(reviewed, "sync_local_no_push")[-1] != "--no-push":
        raise ContractError("the admitted live argv lost --no-push")
    checks += 1

    if sorted(modes_for("ADMITTED_LOCAL_NO_PUSH")) != sorted(MODES):
        raise ContractError(
            "the fully admitted state does not unlock exactly the mode set"
        )
    checks += 1

    # The authority table, unchanged and complete.
    if set(AUTHORITY) != {"GIT_TOWN", "GITHUB_GATE", "LOOPX", "HUMAN"}:
        raise ContractError("the authority table drifted")
    for owned in (
        "semantic conflicts",
        "remote publication",
        "merge or ship",
        "production rollback",
    ):
        if owned not in AUTHORITY["HUMAN"]:
            raise ContractError(f"{owned!r} left the Human column")
    checks += 1

    # Publication is a separate one-operation gate, and it is never automatic.
    decision = publication_decision(
        reviewed, local_receipt_head="a" * 40, github_check_head="a" * 40
    )
    if (
        not decision["may_request"]
        or decision["performed"]
        or decision["owner"] != "HUMAN_OR_TRUSTED_OPERATOR"
    ):
        raise ContractError(f"the publication decision drifted: {decision}")
    checks += 1

    # A stale local receipt or an old GitHub check blocks the request.
    stale = publication_decision(
        reviewed, local_receipt_head="a" * 40, github_check_head="b" * 40
    )
    if stale["may_request"] or "different commit" not in stale["reason"]:
        raise ContractError("a check at another head did not block publication")
    checks += 1

    if validate_profile(PROFILE)["ship_strategy"] != "api":
        raise ContractError("the profile lost its ship strategy")
    checks += 1

    # Conflict markers are detectable, and ordinary text is not.
    sample = (
        ("<" * 7) + " ours\nmine\n" + ("=" * 7) + "\ntheirs\n" + (">" * 7) + " theirs\n"
    )
    if len(find_conflict_markers(sample)) != 3:
        raise ContractError("the conflict-marker detector missed a real conflict")
    if find_conflict_markers("a < b and c > d and e == f\n"):
        raise ContractError("ordinary comparisons were reported as conflict markers")
    checks += 1

    if not find_host_paths("/" + "Users" + "/someone/repo/x"):
        raise ContractError("a host path passed the scanner")
    checks += 1

    if STATES[-1] != "HUMAN_ADMIT" or len(STATES) != 11:
        raise ContractError("the state sequence drifted")
    if ADMISSION_STATES[0] != "EXECUTABLE_ABSENT":
        raise ContractError("the admission vocabulary no longer starts at absence")
    checks += 1

    # The live probe on this machine, whatever it is, is a legal state.
    if probe()["state"] not in ADMISSION_STATES:
        raise ContractError("the probe produced a state outside the vocabulary")
    checks += 1

    return checks


def controls() -> int:
    reviewed = admit(PRESENT, ADMISSION, PROFILE, live_local_reviewed=True)
    unreviewed = admit(PRESENT, ADMISSION, PROFILE, live_local_reviewed=False)
    absent = admit(ABSENT, ADMISSION, PROFILE, live_local_reviewed=True)

    cases: list[tuple[str, str, Callable[[], Any]]] = [
        (
            "arbitrary argv supplied by a caller",
            "can supply --continue",
            lambda: argv_for("sync --continue"),
        ),
        (
            "an unknown mode",
            "The set is closed",
            lambda: argv_for("ship"),
        ),
        (
            "the live lane under an unreviewed admission",
            "has not admitted",
            lambda: require_mode_allowed(unreviewed, "sync_local_no_push"),
        ),
        (
            "any lane with no executable present",
            "has not admitted",
            lambda: require_mode_allowed(absent, "sync_dry_run"),
        ),
        (
            "an admission with no checksum",
            "fields drifted",
            lambda: admit(
                PRESENT,
                {k: v for k, v in ADMISSION.items() if k != "sha256"},
                PROFILE,
                True,
            ),
        ),
        (
            "an admission pinned to latest",
            "can be replaced without the string moving",
            lambda: admit(PRESENT, {**ADMISSION, "version": "latest"}, PROFILE, True),
        ),
        (
            "an admission with no real provenance",
            "is not a provenance",
            lambda: admit(
                PRESENT, {**ADMISSION, "provenance": "downloaded it"}, PROFILE, True
            ),
        ),
        (
            "a checksum that is not a checksum",
            "must be sha256:",
            lambda: admit(PRESENT, {**ADMISSION, "sha256": "abc"}, PROFILE, True),
        ),
        (
            "push hook enabled",
            "would let a strategy through",
            lambda: admit(PRESENT, ADMISSION, {**PROFILE, "push_hook": True}, True),
        ),
        (
            "a force-push sync strategy",
            "would let a strategy through",
            lambda: admit(
                PRESENT,
                ADMISSION,
                {**PROFILE, "sync_strategy": "rebase-and-force-push"},
                True,
            ),
        ),
        (
            "a ship strategy that is not the API",
            "would let a strategy through",
            lambda: admit(
                PRESENT, ADMISSION, {**PROFILE, "ship_strategy": "fast-forward"}, True
            ),
        ),
        (
            "a host path in the config",
            "works exactly once",
            lambda: admit(
                PRESENT,
                ADMISSION,
                {**PROFILE, "main_branch": "/" + "Users" + "/someone/repo/main"},
                True,
            ),
        ),
        (
            "a profile field dropped",
            "profile fields drifted",
            lambda: validate_profile(
                {k: v for k, v in PROFILE.items() if k != "ship_strategy"}
            ),
        ),
        (
            "publication performed rather than requested",
            "one operation a human performs",
            lambda: require_separate_operation(
                {
                    **publication_decision(reviewed, "a" * 40, "a" * 40),
                    "performed": True,
                }
            ),
        ),
        (
            "publication on a stale local receipt",
            "different commit",
            lambda: _require_requestable(
                publication_decision(reviewed, "a" * 40, "c" * 40)
            ),
        ),
        (
            "publication with no admission at all",
            "nothing to publish about",
            lambda: _require_requestable(
                publication_decision(absent, "a" * 40, "a" * 40)
            ),
        ),
        (
            "a short head on a publication decision",
            "must be a full 40-character",
            lambda: publication_decision(reviewed, "abc1234", "abc1234"),
        ),
    ]
    for label, expect, action in cases:
        control(label, expect, action)
    return len(cases)


def _require_requestable(decision: dict[str, Any]) -> None:
    if not decision["may_request"]:
        raise ContractError(decision["reason"])


def run_selftest(root: Path) -> tuple[int, int]:
    return positive_properties(), controls()
