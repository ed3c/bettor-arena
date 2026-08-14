#!/usr/bin/env python3
"""Admitting an executable, and refusing to admit most of what looks like one.

An admission names a specific binary: a version, a checksum of the bytes, where
they came from, and the licence they came under. Anything less names a *tool*,
and a tool is not a thing that ran.

`probe` reports what is actually on this machine. On a machine without Git Town
that is `EXECUTABLE_ABSENT`, which is a state -- and the port exits 70 for it
rather than 2, because "the provider is not here" and "the admission disagreed"
are different answers that both read as non-zero.

The repository profile is closed and path-neutral. Path-neutral because a config
that names someone's home directory is a config that works exactly once, and the
second machine's failure looks like a Git Town problem.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from gt_common import (
    ADMISSION_STATES,
    AUTHORITY,
    ContractError,
    argv_for,
    digest,
    exact_object,
    find_host_paths,
    non_empty_str,
    sha256_ref,
)

ADMISSION_KEYS = {"tool", "version", "sha256", "provenance", "license", "sbom_ref"}

PROFILE_KEYS = {
    "main_branch",
    "perennial_branches",
    "push_hook",
    "sync_strategy",
    "ship_strategy",
}

# The profile values this repository will accept. A closed set rather than a
# validated shape: "sync_strategy is a string" admits `rebase-and-force-push`.
ALLOWED_PROFILE = {
    "push_hook": (False,),
    "sync_strategy": ("merge", "rebase"),
    "ship_strategy": ("api",),
}


def probe(binary: str = "git-town") -> dict[str, Any]:
    """What is actually installed. Absence is reported, never inferred away."""
    path = shutil.which(binary)
    if path is None:
        return {
            "state": "EXECUTABLE_ABSENT",
            "path": None,
            "reported_version": None,
            "reason": (
                f"{binary} is not on PATH. Nothing was run, so nothing about Git Town's "
                "behaviour follows -- this is absence, not a disagreement"
            ),
        }
    try:
        done = subprocess.run(
            argv_for("version"), capture_output=True, text=True, timeout=15, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "state": "EXECUTABLE_ABSENT",
            "path": path,
            "reported_version": None,
            "reason": f"{binary} is on PATH but did not answer --version: {exc}",
        }
    return {
        "state": "EXECUTABLE_PRESENT_NOT_ADMITTED",
        "path": path,
        "reported_version": done.stdout.strip() or done.stderr.strip(),
        "reason": "present, and presence is not admission",
    }


def validate_admission(value: Any) -> dict[str, Any]:
    """A complete admission or none. There is no partial pin."""
    admission = exact_object(value, ADMISSION_KEYS, "admission")
    for field in ("tool", "version", "provenance", "license", "sbom_ref"):
        non_empty_str(admission[field], f"admission.{field}")
    sha256_ref(admission["sha256"], "admission.sha256")
    if admission["version"].lower() in ("latest", "main", "head"):
        raise ContractError(
            f"admission.version is {admission['version']!r}, which names whatever is "
            "current rather than what was reviewed. The bytes behind it can be replaced "
            "without the string moving"
        )
    if not admission["provenance"].startswith(("https://", "pkg:")):
        raise ContractError(
            "admission.provenance must be a URL or a package URL; 'downloaded it' is not "
            "a provenance"
        )
    return admission


def validate_profile(value: Any) -> dict[str, Any]:
    """The repository configuration. Closed, and free of anyone's home directory."""
    profile = exact_object(value, PROFILE_KEYS, "profile")
    non_empty_str(profile["main_branch"], "profile.main_branch")
    perennial = profile["perennial_branches"]
    if not isinstance(perennial, list):
        raise ContractError("profile.perennial_branches must be a list")

    for field, allowed in ALLOWED_PROFILE.items():
        if profile[field] not in allowed:
            raise ContractError(
                f"profile.{field} is {profile[field]!r}; this repository admits "
                f"{list(allowed)}. A validated shape rather than a closed set would let "
                "a strategy through on the grounds that it is a string"
            )

    paths = find_host_paths(str(profile))
    if paths:
        raise ContractError(
            f"the profile contains host paths {paths}. A config that names someone's home "
            "directory works exactly once, and the second machine's failure looks like a "
            "Git Town problem"
        )
    return profile


def admit(
    probe_result: dict[str, Any],
    admission: Any,
    profile: Any,
    live_local_reviewed: bool,
) -> dict[str, Any]:
    """Combine a probe, a pin and a profile into an admission state.

    `live_local_reviewed` is the human's signal and it is a parameter rather than
    a derived value. Nothing here can conclude that a human reviewed something.
    """
    admission = validate_admission(admission)
    profile = validate_profile(profile)

    if probe_result["state"] == "EXECUTABLE_ABSENT":
        state = "EXECUTABLE_ABSENT"
        reason = probe_result["reason"]
    elif (
        probe_result["reported_version"]
        and admission["version"] not in probe_result["reported_version"]
    ):
        state = "EXECUTABLE_PRESENT_NOT_ADMITTED"
        reason = (
            f"the installed executable reports {probe_result['reported_version']!r} and the "
            f"admission pins {admission['version']!r}. A pin that does not match what is "
            "installed describes a different program"
        )
    elif live_local_reviewed:
        state = "ADMITTED_LOCAL_NO_PUSH"
        reason = "pinned, profile closed, and a human reviewed the live local lane"
    else:
        state = "ADMITTED_DRY_RUN_ONLY"
        reason = (
            "pinned and profile closed, but no human has reviewed the live local lane. "
            "Dry run is what an unreviewed admission gets"
        )

    if state not in ADMISSION_STATES:
        raise ContractError(f"admission produced unknown state {state!r}")

    return {
        "schema_version": "loopx/git-town-admission/v1",
        "state": state,
        "reason": reason,
        "probe": probe_result,
        "admission": admission,
        "profile": profile,
        "modes_available": modes_for(state),
        # The table, on the record. The interesting question is always "who
        # decided this", and a paragraph answers it differently by reader.
        "authority": AUTHORITY,
        "publication_is_separate_gate": True,
        "human_admit_required": True,
        "admission_digest": digest(
            {"state": state, "admission": admission, "profile": profile}
        ),
    }


def modes_for(state: str) -> list[str]:
    """Which modes an admission state unlocks. Absence unlocks nothing."""
    if state in ("EXECUTABLE_ABSENT", "EXECUTABLE_PRESENT_NOT_ADMITTED"):
        return []
    if state == "ADMITTED_DRY_RUN_ONLY":
        return ["version", "config", "sync_dry_run"]
    return ["version", "config", "sync_dry_run", "sync_local_no_push"]


def require_mode_allowed(admission_result: dict[str, Any], mode: str) -> list[str]:
    """The only way to get an argv. Refuses before it builds."""
    if mode not in admission_result["modes_available"]:
        raise ContractError(
            f"mode {mode!r} is not available under {admission_result['state']}; available: "
            f"{admission_result['modes_available']}. Running it anyway would be running a "
            "program this repository has not admitted"
        )
    return argv_for(mode)
