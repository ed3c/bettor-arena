#!/usr/bin/env python3
"""Trials in, report out -- with everything that failed still in the count.

Three things this file exists to prevent, each of which produces a better number
and none of which is detectable from the number:

  * dropping the runs that failed. A mean over the trials that finished is a
    different statistic wearing the same name, and a timeout is the most
    interesting trial in the set;
  * comparing across subjects. Two summaries with the same shape are
    comparable-looking regardless of whether they measured the same workload on
    the same commit under the same enforcement policy;
  * calling five runs a tail. p99 over five samples is one of those five, and it
    is reported here with the rank that produced it so the reader can see that.

`summarize` therefore takes every trial, counts the failures into `n`, and refuses
to derive timing statistics at all if the OK count is below the declared minimum.
Refusing is the point: a summary that quietly describes three surviving runs is
worse than no summary, because it looks like the other ones.
"""

from __future__ import annotations

from typing import Any

from bm_common import (
    CACHE_STATES,
    FAMILIES,
    LOCALES,
    NON_OK,
    TRIAL_OUTCOMES,
    ContractError,
    digest,
    exact_object,
    mutable_version,
    non_empty_str,
    positive_int,
    quantiles,
)

SUBJECT_KEYS = {"commit", "tree_dirty", "dependency_digest", "enforcement_policy"}
ENVIRONMENT_KEYS = {"os", "arch", "cpu", "ram_gb", "runtime", "image", "locale"}
IDENTITY_KEYS = {"host", "model", "provider", "tool_versions"}
WORKLOAD_KEYS = {
    "family",
    "name",
    "seed",
    "repetitions",
    "warmup",
    "stopping_rule",
    "command",
}
TRIAL_KEYS = {"index", "outcome", "wall_ms", "peak_rss_mb", "cache_state", "detail"}

# Below this many OK trials, no timing statistic is derived. Not a heuristic
# about statistical power -- it is the point at which a percentile is a single
# observation with a percentile's name on it.
MIN_OK_TRIALS = 5


def validate_subject(value: Any) -> dict[str, Any]:
    subject = exact_object(value, SUBJECT_KEYS, "subject")
    non_empty_str(subject["commit"], "subject.commit")
    if len(subject["commit"]) != 40:
        raise ContractError(
            "subject.commit must be a full 40-character SHA; a short SHA names a commit "
            "only relative to a repository that has it"
        )
    if not isinstance(subject["tree_dirty"], bool):
        raise ContractError("subject.tree_dirty must be a boolean")
    non_empty_str(subject["dependency_digest"], "subject.dependency_digest")
    non_empty_str(subject["enforcement_policy"], "subject.enforcement_policy")
    return subject


def validate_environment(value: Any) -> dict[str, Any]:
    env = exact_object(value, ENVIRONMENT_KEYS, "environment")
    for field in ("os", "arch", "cpu", "runtime", "image"):
        non_empty_str(env[field], f"environment.{field}")
    if not isinstance(env["ram_gb"], (int, float)) or env["ram_gb"] <= 0:
        raise ContractError("environment.ram_gb must be a positive number")
    if env["locale"] not in LOCALES:
        raise ContractError(
            f"environment.locale is {env['locale']!r}; known: {sorted(LOCALES)}. A laptop "
            "with a warm page cache, a shared CI runner and a VPS are three different "
            "machines and the number does not carry between them"
        )
    return env


def validate_identities(value: Any) -> dict[str, Any]:
    ident = exact_object(value, IDENTITY_KEYS, "identities")
    for field in ("host", "model", "provider"):
        non_empty_str(ident[field], f"identities.{field}")
    versions = ident["tool_versions"]
    if not isinstance(versions, dict) or not versions:
        raise ContractError("identities.tool_versions must be a non-empty object")
    for tool, version in versions.items():
        non_empty_str(version, f"identities.tool_versions[{tool}]")
    return ident


def moving_targets(
    identities: dict[str, Any], environment: dict[str, Any]
) -> list[str]:
    """Every identity that names something replaceable under a fixed string."""
    found = [
        f"tool_versions.{tool}={version}"
        for tool, version in sorted(identities["tool_versions"].items())
        if mutable_version(version)
    ]
    for field in ("model", "provider"):
        if mutable_version(identities[field]):
            found.append(f"identities.{field}={identities[field]}")
    if mutable_version(environment["image"]):
        found.append(f"environment.image={environment['image']}")
    return found


def validate_workload(value: Any) -> dict[str, Any]:
    workload = exact_object(value, WORKLOAD_KEYS, "workload")
    if workload["family"] not in FAMILIES:
        raise ContractError(
            f"workload.family is {workload['family']!r}; known: {sorted(FAMILIES)}"
        )
    non_empty_str(workload["name"], "workload.name")
    non_empty_str(workload["stopping_rule"], "workload.stopping_rule")
    positive_int(workload["repetitions"], "workload.repetitions")
    if not isinstance(workload["warmup"], int) or workload["warmup"] < 0:
        raise ContractError("workload.warmup must be a non-negative integer")
    if not isinstance(workload["seed"], int):
        raise ContractError("workload.seed must be an integer")
    if not isinstance(workload["command"], list) or not workload["command"]:
        raise ContractError(
            "workload.command must be the exact argv; a report without the command that "
            "produced it is not reproducible, and nothing about it says so"
        )
    return workload


def validate_trial(value: Any, label: str) -> dict[str, Any]:
    trial = exact_object(value, TRIAL_KEYS, label)
    if trial["outcome"] not in TRIAL_OUTCOMES:
        raise ContractError(
            f"{label}.outcome is {trial['outcome']!r}; known: {sorted(TRIAL_OUTCOMES)}. "
            "FAILED, TIMEOUT and OOM are outcomes, not absences"
        )
    if not isinstance(trial["index"], int) or trial["index"] < 0:
        raise ContractError(f"{label}.index must be a non-negative integer")
    if trial["cache_state"] not in CACHE_STATES:
        raise ContractError(
            f"{label}.cache_state is {trial['cache_state']!r}; known: {sorted(CACHE_STATES)}"
        )
    for field in ("wall_ms", "peak_rss_mb"):
        measure = trial[field]
        if measure is not None and (
            not isinstance(measure, (int, float)) or measure < 0
        ):
            raise ContractError(
                f"{label}.{field} must be null or a non-negative number"
            )
    if trial["outcome"] == "OK" and trial["wall_ms"] is None:
        raise ContractError(f"{label} succeeded with no wall time")
    return trial


def summarize(
    subject: Any,
    environment: Any,
    identities: Any,
    workload: Any,
    trials: list[Any],
) -> dict[str, Any]:
    """Derive a report. Every trial stays; the failures are counted, not dropped."""
    subject = validate_subject(subject)
    environment = validate_environment(environment)
    identities = validate_identities(identities)
    workload = validate_workload(workload)

    if not trials:
        raise ContractError(
            "no trials. An empty run and a run whose trials were dropped produce the "
            "same report, and only one of them is honest"
        )
    validated = [
        validate_trial(trial, f"trials[{index}]") for index, trial in enumerate(trials)
    ]

    indices = [trial["index"] for trial in validated]
    if sorted(indices) != list(range(len(indices))):
        raise ContractError(
            f"trial indices are {sorted(indices)}, not a complete 0..n-1 run. A gap is a "
            "trial that was executed and is not in this report"
        )
    if len(validated) != workload["repetitions"]:
        raise ContractError(
            f"{len(validated)} trials against {workload['repetitions']} declared "
            "repetitions. Declaring the count separately is what makes a dropped trial "
            "visible; matching it is not optional"
        )

    ok = [trial for trial in validated if trial["outcome"] == "OK"]
    by_outcome = {
        outcome: sum(1 for t in validated if t["outcome"] == outcome)
        for outcome in TRIAL_OUTCOMES
    }
    failures = sum(by_outcome[outcome] for outcome in NON_OK)

    cache_states = sorted({trial["cache_state"] for trial in ok})
    mixed_cache = len(cache_states) > 1

    timing: dict[str, Any] | None = None
    rss: dict[str, Any] | None = None
    withheld: str | None = None
    if len(ok) < MIN_OK_TRIALS:
        withheld = (
            f"only {len(ok)} trial(s) succeeded, below the {MIN_OK_TRIALS} needed before a "
            "percentile is anything but one observation with a percentile's name on it"
        )
    elif mixed_cache:
        withheld = (
            f"the successful trials mix cache states {cache_states}. A warm run and a cold "
            "run summarised together produce a speedup that belongs to neither"
        )
    else:
        timing = quantiles([float(trial["wall_ms"]) for trial in ok])
        measured_rss = [
            float(t["peak_rss_mb"]) for t in ok if t["peak_rss_mb"] is not None
        ]
        rss = quantiles(measured_rss) if measured_rss else None

    return {
        "schema_version": "loopx/benchmark-report/v1",
        "subject": subject,
        "environment": environment,
        "identities": identities,
        "workload": workload,
        # Every trial, verbatim. The report is the raw record plus a derivation,
        # not a derivation that happens to mention how many runs there were.
        "trials": validated,
        "counts": by_outcome,
        "trial_count": len(validated),
        "ok_count": len(ok),
        "failure_count": failures,
        # Derived here rather than left to the reader, because it is the number a
        # dropped trial actually moves. Timeouts carry no duration, so removing
        # them leaves every percentile exactly where it was -- the median does not
        # flinch, and the run silently becomes one that never failed.
        "success_rate": len(ok) / len(validated),
        "cache_states_observed": cache_states,
        "mixed_cache_states": mixed_cache,
        "timing_ms": timing,
        "peak_rss_mb": rss,
        # Why there is no number, when there is no number. A report with an absent
        # summary and a report that was never run look the same without this.
        "summary_withheld": withheld,
        "moving_targets": moving_targets(identities, environment),
        # Carried, always. A number measured on SHARED_RUNNER is a fact about a
        # machine whose neighbours nobody can see.
        "locale": environment["locale"],
        "numbers_are_claims": False,
        "report_digest": digest(
            {"subject": subject, "workload": workload, "trials": validated}
        ),
    }


def comparable(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Whether two reports measured the same thing. Reasons, not a boolean."""
    reasons: list[str] = []
    for field in ("commit", "dependency_digest", "enforcement_policy"):
        if left["subject"][field] != right["subject"][field]:
            reasons.append(
                f"subject.{field} differs ({left['subject'][field]} vs "
                f"{right['subject'][field]})"
            )
    if left["subject"]["tree_dirty"] or right["subject"]["tree_dirty"]:
        reasons.append(
            "one of the trees was dirty; a dirty tree is not a commit, and the report "
            "names a commit it did not measure"
        )
    for field in ("family", "name", "seed", "command"):
        if left["workload"][field] != right["workload"][field]:
            reasons.append(f"workload.{field} differs")
    if left["cache_states_observed"] != right["cache_states_observed"]:
        reasons.append(
            f"cache states differ ({left['cache_states_observed']} vs "
            f"{right['cache_states_observed']}); comparing a warm run with a cold one "
            "is how a speedup gets manufactured without anyone lying"
        )
    return {
        "comparable": not reasons,
        "reasons": reasons or ["same subject, workload, policy and cache state"],
    }
