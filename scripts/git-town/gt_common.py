#!/usr/bin/env python3
"""Admission vocabulary for the Git Town runtime, and the shape of what it may run.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant disagreed,
64 the input or invocation is unusable, 70 the provider is unavailable.

70 is the one that matters here. The executable is not installed on this machine,
and that is a state -- `EXECUTABLE_ABSENT` -- not a failure and not a pass.
Reporting it as 2 would say the admission disagreed with something; reporting it
as 0 would say a tool that is not here ran and was fine.

The command shape is a closed set of *modes*, not an argv the caller supplies.
That is the whole difference between admitting a tool and admitting a shell: a
caller that can pass argv can pass `--continue`, and `--continue` is the flag
that resolves a semantic conflict on the agent's own judgement.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

OK = 0
BAD = 2
USAGE = 64
PROVIDER = 70

# #101's state machine, in order.
STATES = [
    "SHARED_SKILL_AND_PUBLICATION_POLICY_PINNED",
    "EXECUTABLE_VERSION_CHECKSUM_PROVENANCE_PINNED",
    "LICENSE_SBOM_DEPENDENCY_REVIEW",
    "REPOSITORY_PROFILE_AND_CONFIG_CANDIDATE",
    "ISOLATED_STACK_FIXTURE",
    "DRY_RUN_NO_PUSH_SYNC",
    "LIVE_LOCAL_NO_PUSH_SYNC",
    "CONFLICT_PROMPT_TIMEOUT_RESIDUE_CANARIES",
    "LOCAL_RECEIPT_AND_ROLLBACK_SUBJECT",
    "GITHUB_PUBLICATION_GATE",
    "HUMAN_ADMIT",
]

# What the runtime can be. ABSENT is first because it is the state on this
# machine and the one an admission is most likely to paper over.
ADMISSION_STATES = (
    "EXECUTABLE_ABSENT",
    "EXECUTABLE_PRESENT_NOT_ADMITTED",
    "ADMITTED_DRY_RUN_ONLY",
    "ADMITTED_LOCAL_NO_PUSH",
)

# The closed set of modes. A mode is a name; the argv belongs to this file.
# `sync` is the only one that touches branches, and it carries --no-push in its
# own definition rather than in a caller's hands.
MODES = {
    "version": ["git", "town", "--version"],
    "config": ["git", "town", "config"],
    "sync_dry_run": [
        "git",
        "town",
        "sync",
        "--stack",
        "--non-interactive",
        "--no-auto-resolve",
        "--no-push",
        "--dry-run",
    ],
    "sync_local_no_push": [
        "git",
        "town",
        "sync",
        "--stack",
        "--non-interactive",
        "--no-auto-resolve",
        "--no-push",
    ],
}

# Flags no mode may ever contain. Enumerated rather than described, because each
# one is a decision a human owns and every one of them has a plausible reason to
# be added at 2am.
FORBIDDEN_FLAGS = (
    "--continue",
    "--skip",
    "--undo",
    "--abort",
    "--force",
    "--force-with-lease",
    "--push",
    "--auto-resolve",
    "--ship",
    "--merge",
    "--no-verify",
)

# Every mode declares whether it can change the working tree, and whether it can
# reach the network. Both false for everything except the live sync's tree write.
MODE_EFFECTS = {
    "version": {"writes_tree": False, "network": False},
    "config": {"writes_tree": False, "network": False},
    "sync_dry_run": {"writes_tree": False, "network": False},
    "sync_local_no_push": {"writes_tree": True, "network": False},
}

# What each authority owns. A table rather than a paragraph: the interesting
# question is always "who decided this", and a paragraph answers it differently
# depending on who is reading.
AUTHORITY = {
    "GIT_TOWN": ["local branch hierarchy", "bounded local synchronization"],
    "GITHUB_GATE": ["exact-head publication decision"],
    "LOOPX": ["canonical task state"],
    "HUMAN": [
        "semantic conflicts",
        "remote publication",
        "merge or ship",
        "release promotion",
        "production rollback",
        "config activation",
    ],
}

# Conflict markers, in a form that is not itself a conflict marker: a file
# containing the literal seven characters would be flagged by every tool that
# scans for them, including this repository's own gates.
CONFLICT_MARKERS = ("<" * 7, "=" * 7, ">" * 7)

# A host path is someone's machine. Built from parts because the repository's
# root-coupling gate scans tracked source for a literal home root.
HOST_PATH = tuple(re.compile(rf"/{root}/[^/\s]+/") for root in ("Users", "home"))

SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class ContractError(Exception):
    """A checked invariant disagreed. Exit 2."""


class InputError(Exception):
    """The input is absent or unreadable. Exit 64, never 2."""


class ProviderAbsent(Exception):
    """The executable is not here. Exit 70, never 2 and never 0."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def load_json(path) -> Any:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise InputError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise InputError(f"invalid JSON in {path}: {exc}") from exc


def exact_object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    if set(value) != keys:
        raise ContractError(
            f"{label} fields drifted; missing={sorted(keys - set(value))}, "
            f"extra={sorted(set(value) - keys)}"
        )
    return value


def non_empty_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value


def sha256_ref(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise ContractError(f"{label} must be sha256:<64 lowercase hex>")
    return value


def argv_for(mode: str) -> list[str]:
    """The argv for an admitted mode. There is no path that takes one."""
    if mode not in MODES:
        raise ContractError(
            f"{mode!r} is not an admitted mode. The set is closed: {sorted(MODES)}. A "
            "caller that can supply argv can supply --continue, and --continue resolves "
            "a semantic conflict on the agent's own judgement"
        )
    argv = list(MODES[mode])
    # Checked at the point of use rather than only at definition. A flag added to
    # the table later would otherwise be admitted by the table having been checked
    # once, at a time when it did not contain the flag.
    forbidden = sorted(set(argv) & set(FORBIDDEN_FLAGS))
    if forbidden:
        raise ContractError(
            f"mode {mode!r} carries {forbidden}, which no mode may contain. Each of "
            "these is a decision a human owns"
        )
    return argv


def find_host_paths(text: str) -> list[str]:
    found: list[str] = []
    for pattern in HOST_PATH:
        found.extend(match.group(0) for match in pattern.finditer(text))
    return sorted(set(found))


def find_conflict_markers(text: str) -> list[str]:
    """Markers left in a file. A silent conflict marker is a committed conflict."""
    return sorted({marker for marker in CONFLICT_MARKERS if marker in text})
