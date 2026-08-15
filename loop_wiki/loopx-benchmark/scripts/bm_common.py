#!/usr/bin/env python3
"""Shared exits, vocabulary, and the reason a number is not a claim.

Exit codes follow the repository contract: 0 ok, 2 a checked invariant
disagreed, 64 the input or invocation is unusable.

The PDF this programme comes from carries numbers: `<30MB`, `<50MB`, TTFT
figures, speedups, token counts, cost and hardware recommendations. A number in
a source proposal is a thing someone measured somewhere, on hardware nobody here
has, with software nobody here pinned. It is a hypothesis with a decimal point,
and a decimal point is the most persuasive thing in any document.

So a measurement here never becomes a claim by being taken. The ladder is:

    CLAIM_UNVERIFIED   nothing was measured for this claim, or what was measured
                       does not answer it
    PROFILE_OBSERVED   measured, on one named profile, and it says nothing about
                       any other profile
    CORROBORATED       measured on independent profiles that agree

and nothing promotes itself. `PROFILE_OBSERVED` is the one that gets rounded up
in a summary, which is why the profile travels inside the verdict rather than
beside it.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

OK = 0
BAD = 2
USAGE = 64

# The benchmark state machine from #100, in order.
STATES = [
    "WORKLOAD_SUBJECT_ENVIRONMENT_PINNED",
    "ADAPTER_HOST_MODEL_PROVIDER_PINNED",
    "WARMUP_POLICY_APPLIED",
    "RAW_TRIALS_EXECUTED",
    "FAILURES_RETAINED",
    "OBSERVATIONS_RECORDED",
    "SUMMARY_DERIVED",
    "COMPARABILITY_GATES",
    "PROFILE_SCOPED_REPORT",
    "CLAIM_VERDICT",
]

# The ladder. Ordered, and nothing climbs it on its own.
VERDICTS = ("CLAIM_UNVERIFIED", "PROFILE_OBSERVED", "CORROBORATED")

# Every outcome a trial can have. Enumerated in full because the three that are
# not OK are exactly the ones that get dropped before the mean is taken -- and a
# mean over the runs that finished is a different statistic with the same name.
TRIAL_OUTCOMES = ("OK", "FAILED", "TIMEOUT", "OOM")
NON_OK = ("FAILED", "TIMEOUT", "OOM")

# The case families #100 requires. A family with no case is absent, not passing.
FAMILIES = (
    "ledger_append_replay_snapshot",
    "gate_startup_and_execution",
    "worktree_bootstrap_and_cleanup",
    "lsp_cold_warm_and_pool_reuse",
    "knowledge_build_and_query",
    "prompt_prefix_suffix_bytes",
    "host_startup_and_task_latency",
    "local_cloud_same_workload",
    "gc_residue_and_ceilings",
)

# Cache state is part of the subject, not a footnote. A warm run compared against
# a cold one without the label is the single easiest way to produce a speedup.
CACHE_STATES = ("COLD", "WARM", "UNKNOWN")

# Where a run happened. Not interchangeable: a laptop with a warm page cache and
# a shared CI runner are different machines, and a VPS is a third.
LOCALES = ("LOCAL", "SHARED_RUNNER", "CLOUD_VPS", "SYNTHETIC")

# A synthetic run is deterministic and carries no timing meaning at all. It
# exists so CI can prove the *pipeline* works without publishing a number from a
# shared runner whose neighbours nobody can see.
SYNTHETIC_LOCALE = "SYNTHETIC"

# Version strings that name a moving target. Not refused outright -- sometimes it
# is all that is available -- but a trial pinned to one cannot be CORROBORATED,
# because the thing that was measured can be replaced without the string moving.
MUTABLE_VERSIONS = re.compile(
    r"(^|[:@/-])(latest|main|master|edge|nightly|stable)$", re.IGNORECASE
)


class ContractError(Exception):
    """A checked invariant disagreed. Exit 2."""


class InputError(Exception):
    """The input is absent or unreadable. Exit 64, never 2."""


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


def positive_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ContractError(f"{label} must be a positive integer")
    return value


def mutable_version(value: str) -> bool:
    return MUTABLE_VERSIONS.search(value) is not None


def quantiles(values: list[float]) -> dict[str, float]:
    """Order statistics, reported by rank rather than interpolated.

    Nearest-rank, and the rank is reported alongside. An interpolated p99 over
    five samples is a number computed from two of them, and it reads exactly like
    a p99 over ten thousand.
    """
    if not values:
        raise ContractError("no values to summarise")
    ordered = sorted(values)
    count = len(ordered)

    def at(fraction: float) -> float:
        rank = max(1, min(count, -(-int(fraction * count * 100) // 100)))
        return ordered[rank - 1]

    return {
        "n": count,
        "min": ordered[0],
        "median": at(0.5),
        "p90": at(0.90),
        "p99": at(0.99),
        "max": ordered[-1],
    }
