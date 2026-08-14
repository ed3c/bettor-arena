#!/usr/bin/env python3
"""Positive properties, and one planted control per failure named in #100.

Every control asserts on the substring its own rule raises. A control that only
checks "something was refused" passes when a neighbouring guard fires first, and
stays green while the rule it was written for is deleted.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from bm_claim import (
    ORIGINS,
    evaluate,
    independent,
    profile_of,
    require_no_universal_claim,
)
from bm_common import (
    FAMILIES,
    NON_OK,
    STATES,
    TRIAL_OUTCOMES,
    VERDICTS,
    ContractError,
    quantiles,
)
from bm_report import MIN_OK_TRIALS, comparable, summarize
from bm_run import SYNTHETIC_ENVIRONMENT, synthetic

COMMIT = "c" * 40

SUBJECT = {
    "commit": COMMIT,
    "tree_dirty": False,
    "dependency_digest": "sha256:" + "d" * 64,
    "enforcement_policy": "gates-strict-v1",
}

LAPTOP = {
    "os": "darwin-25.4",
    "arch": "arm64",
    "cpu": "apple-m3",
    "ram_gb": 32,
    "runtime": "python-3.12.4",
    "image": "none",
    "locale": "LOCAL",
}

RUNNER = {
    "os": "ubuntu-24.04",
    "arch": "x86_64",
    "cpu": "amd-epyc-7763",
    "ram_gb": 16,
    "runtime": "python-3.12.4",
    "image": "ghcr.io/actions/runner@sha256:" + "a" * 64,
    "locale": "SHARED_RUNNER",
}

IDENTITIES = {
    "host": "claude",
    "model": "opus-5",
    "provider": "anthropic",
    "tool_versions": {"python": "3.12.4", "bun": "1.3.11"},
}

WORKLOAD = {
    "family": "gate_startup_and_execution",
    "name": "placement-gate-cold-start",
    "seed": 7,
    "repetitions": 8,
    "warmup": 1,
    "stopping_rule": "fixed repetitions; no early stop on a favourable trial",
    "command": ["python3", "scripts/gates/check_placement.py", "--selftest"],
}

CLAIM = {
    "id": "rss-under-30mb",
    "statement": "the placement gate's peak RSS stays under 30 MB",
    "metric": "peak_rss_mb",
    "origin": "MEASURED_HERE",
    "threshold": 30,
    "comparator": "lt",
}


def _trials(count: int, failures: int = 0, cache: str = "COLD") -> list[dict[str, Any]]:
    out = []
    for index in range(count):
        if index < failures:
            out.append(
                {
                    "index": index,
                    "outcome": "TIMEOUT",
                    "wall_ms": None,
                    "peak_rss_mb": None,
                    "cache_state": cache,
                    "detail": "exceeded 30s",
                }
            )
        else:
            out.append(
                {
                    "index": index,
                    "outcome": "OK",
                    "wall_ms": 100.0 + index * 5,
                    "peak_rss_mb": 12.0 + index,
                    "cache_state": cache,
                    "detail": "",
                }
            )
    return out


def _report(
    environment=None, workload=None, trials=None, subject=None, identities=None
):
    workload = workload or WORKLOAD
    return summarize(
        subject or SUBJECT,
        environment or LAPTOP,
        identities or IDENTITIES,
        workload,
        trials if trials is not None else _trials(workload["repetitions"]),
    )


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
    report = _report()

    if report["trial_count"] != 8 or report["ok_count"] != 8:
        raise ContractError("a clean run did not summarise all of its trials")
    checks += 1

    # Failures stay in the count, and the count is the declared repetition count.
    with_failures = _report(trials=_trials(8, failures=2))
    if with_failures["trial_count"] != 8 or with_failures["ok_count"] != 6:
        raise ContractError("a failing trial left the count")
    if with_failures["failure_count"] != 2 or with_failures["counts"]["TIMEOUT"] != 2:
        raise ContractError("failures were not counted by outcome")
    if len(with_failures["trials"]) != 8:
        raise ContractError("the raw trials were not retained")
    checks += 1

    # Dropping a failure changes the numbers. Demonstrated rather than asserted:
    # this is the whole reason the failures are kept.
    kept = [t for t in with_failures["trials"] if t["outcome"] == "OK"]
    trimmed_workload = {**WORKLOAD, "repetitions": len(kept)}
    reindexed = [{**t, "index": i} for i, t in enumerate(kept)]
    trimmed = _report(workload=trimmed_workload, trials=reindexed)
    # The median does not flinch -- timeouts carry no duration, so every
    # percentile is exactly where it was. What moves is the success rate, and
    # that is the number a dropped trial actually manufactures.
    if trimmed["timing_ms"]["median"] != with_failures["timing_ms"]["median"]:
        raise ContractError("dropping durationless trials moved a duration percentile")
    if with_failures["success_rate"] != 0.75 or trimmed["success_rate"] != 1.0:
        raise ContractError(
            f"dropping two timeouts moved the success rate from "
            f"{with_failures['success_rate']} to {trimmed['success_rate']}; if these were "
            "equal the retained failures would be proving nothing"
        )
    if trimmed["failure_count"] != 0 or with_failures["failure_count"] != 2:
        raise ContractError("the failure counts did not separate the two reports")
    checks += 1

    # Below the floor, no timing statistic at all -- and it says why.
    thin_workload = {**WORKLOAD, "repetitions": 6}
    thin = _report(workload=thin_workload, trials=_trials(6, failures=3))
    if thin["timing_ms"] is not None or not thin["summary_withheld"]:
        raise ContractError("a summary was derived from 3 successful trials")
    if f"{MIN_OK_TRIALS}" not in thin["summary_withheld"]:
        raise ContractError("the withheld summary did not say what the floor was")
    checks += 1

    # A mixed cache state withholds the summary rather than averaging it.
    mixed = _trials(8)
    for trial in mixed[:4]:
        trial["cache_state"] = "WARM"
    mixed_report = _report(trials=mixed)
    if mixed_report["timing_ms"] is not None:
        raise ContractError("a warm and a cold run were summarised together")
    if (
        not mixed_report["mixed_cache_states"]
        or "speedup" not in mixed_report["summary_withheld"]
    ):
        raise ContractError("the mixed cache state was not the reason given")
    checks += 1

    # Percentiles report the rank that produced them.
    stats = quantiles([1.0, 2.0, 3.0, 4.0, 5.0])
    if stats["n"] != 5 or stats["p99"] != 5.0 or stats["median"] != 3.0:
        raise ContractError(f"nearest-rank quantiles drifted: {stats}")
    checks += 1

    # Comparability: same everything is comparable, and a dirty tree is not.
    if not comparable(report, _report())["comparable"]:
        raise ContractError("two identical reports were not comparable")
    dirty = _report(subject={**SUBJECT, "tree_dirty": True})
    verdict = comparable(report, dirty)
    if verdict["comparable"] or not any("dirty" in r for r in verdict["reasons"]):
        raise ContractError("a dirty tree was treated as a commit")
    checks += 1

    other_workload = comparable(report, _report(workload={**WORKLOAD, "seed": 99}))
    if other_workload["comparable"]:
        raise ContractError("two different workloads compared as the same subject")
    checks += 1

    # One profile observes; it does not corroborate.
    one = evaluate(CLAIM, [report])
    if one["verdict"] != "PROFILE_OBSERVED":
        raise ContractError(f"one profile produced {one['verdict']}: {one['reason']}")
    if one["promotable_by_gate"] or one["promotion_owner"] != "HUMAN_ADMIT":
        raise ContractError("a verdict claimed it could promote itself")
    checks += 1

    # The same box twice is still one profile.
    twice = evaluate(CLAIM, [report, _report()])
    if twice["verdict"] != "PROFILE_OBSERVED":
        raise ContractError(
            f"running the same machine twice produced {twice['verdict']}; repetition "
            "raises confidence in the mean, it does not widen what the mean is about"
        )
    checks += 1

    # Two genuinely different machines corroborate.
    both = evaluate(CLAIM, [report, _report(environment=RUNNER)])
    if both["verdict"] != "CORROBORATED":
        raise ContractError(
            f"two independent profiles produced {both['verdict']}: {both['reason']}"
        )
    if len(both["profiles"]) != 2:
        raise ContractError(
            "the corroborating profiles did not travel with the verdict"
        )
    checks += 1

    if not independent(profile_of(report), profile_of(_report(environment=RUNNER))):
        raise ContractError("a laptop and a shared runner were called the same profile")
    if independent(profile_of(report), profile_of(_report())):
        raise ContractError("one machine was called two independent profiles")
    checks += 1

    # A source proposal never becomes evidence.
    for origin in ("SOURCE_PROPOSAL", "VENDOR_BENCHMARK"):
        proposed = evaluate(
            {**CLAIM, "origin": origin}, [report, _report(environment=RUNNER)]
        )
        if proposed["verdict"] != "CLAIM_UNVERIFIED":
            raise ContractError(f"a {origin} claim reached {proposed['verdict']}")
        if "hypothesis with a decimal point" not in proposed["reason"]:
            raise ContractError("the origin refusal did not name why")
    checks += 1

    # A profile that fails the claim is reported, not dropped.
    heavy = _report(
        environment=RUNNER,
        trials=[{**t, "peak_rss_mb": 90.0} for t in _trials(8)],
    )
    mixed_verdict = evaluate(CLAIM, [report, heavy])
    if mixed_verdict["verdict"] != "CLAIM_UNVERIFIED":
        raise ContractError("a disagreeing profile was dropped from the verdict")
    if len(mixed_verdict["evidence"]) != 2:
        raise ContractError("the disagreeing profile left the evidence list")
    checks += 1

    # Synthetic runs prove the pipeline and never a number.
    synth = synthetic({**WORKLOAD, "repetitions": 8})
    synth_report = summarize(
        SUBJECT, SYNTHETIC_ENVIRONMENT, IDENTITIES, WORKLOAD, synth["trials"]
    )
    if synth_report["failure_count"] != 1:
        raise ContractError(
            "the synthetic run has no retained failure to exercise the path"
        )
    excluded = evaluate(CLAIM, [synth_report])
    if excluded["verdict"] != "CLAIM_UNVERIFIED":
        raise ContractError(
            f"a synthetic report supported a claim: {excluded['verdict']}"
        )
    if not any("synthetic" in note for note in excluded["notes"]):
        raise ContractError("the synthetic exclusion was not stated")
    checks += 1

    # Two synthetic runs are byte-identical; that is the only thing they promise.
    if synthetic({**WORKLOAD, "repetitions": 8}) != synth:
        raise ContractError("the synthetic run is not deterministic")
    checks += 1

    # A moving version string blocks corroboration and says so.
    floating = _report(
        environment=RUNNER,
        identities={
            **IDENTITIES,
            "tool_versions": {"python": "3.12.4", "bun": "latest"},
        },
    )
    if "tool_versions.bun=latest" not in floating["moving_targets"]:
        raise ContractError("a mutable version string was not recorded")
    guarded = evaluate(CLAIM, [report, floating])
    if guarded["verdict"] == "CORROBORATED":
        raise ContractError("a report pinned to `latest` corroborated a claim")
    checks += 1

    if sorted(VERDICTS) != sorted(set(VERDICTS)) or VERDICTS[0] != "CLAIM_UNVERIFIED":
        raise ContractError("the verdict ladder drifted")
    if STATES[-1] != "CLAIM_VERDICT" or len(STATES) != 10:
        raise ContractError("the state sequence drifted")
    if set(NON_OK) | {"OK"} != set(TRIAL_OUTCOMES):
        raise ContractError("the trial outcome vocabulary drifted")
    checks += 1

    if len(FAMILIES) != 9:
        raise ContractError(
            f"{len(FAMILIES)} case families, expected the nine #100 names"
        )
    checks += 1

    return checks


def controls() -> int:
    report = _report()
    cases: list[tuple[str, str, Callable[[], Any]]] = [
        (
            "a dropped trial",
            "not a complete 0..n-1 run",
            lambda: _report(trials=[t for t in _trials(8) if t["index"] != 4]),
        ),
        (
            "fewer trials than declared repetitions",
            "matching it is not optional",
            lambda: _report(trials=_trials(6)),
        ),
        (
            "no trials at all",
            "only one of them is honest",
            lambda: _report(trials=[]),
        ),
        (
            "a failure recorded as an absence",
            "not absences",
            lambda: _report(
                trials=[{**_trials(8)[0], "outcome": "SKIPPED"}] + _trials(8)[1:]
            ),
        ),
        (
            "a success with no wall time",
            "succeeded with no wall time",
            lambda: _report(
                trials=[{**_trials(8)[0], "wall_ms": None}] + _trials(8)[1:]
            ),
        ),
        (
            "a short commit as the subject",
            "must be a full 40-character SHA",
            lambda: _report(subject={**SUBJECT, "commit": "c" * 12}),
        ),
        (
            "a locale nothing measured",
            "does not carry between them",
            lambda: _report(environment={**LAPTOP, "locale": "SOMEWHERE"}),
        ),
        (
            "an unknown cache state",
            "cache_state is",
            lambda: _report(
                trials=[{**_trials(8)[0], "cache_state": "HOT"}] + _trials(8)[1:]
            ),
        ),
        (
            "a workload family that does not exist",
            "workload.family is",
            lambda: _report(workload={**WORKLOAD, "family": "vibes"}),
        ),
        (
            "a report with no reproduction command",
            "nothing about it says so",
            lambda: _report(workload={**WORKLOAD, "command": []}),
        ),
        (
            "a claim about something nothing measures",
            "calling it a metric would hide that",
            lambda: evaluate({**CLAIM, "metric": "developer_happiness"}, [report]),
        ),
        (
            "a claim origin outside the vocabulary",
            "claim.origin is",
            lambda: evaluate({**CLAIM, "origin": "EVERYONE_KNOWS"}, [report]),
        ),
        (
            "a local observation read as a guarantee",
            "a VPS has none of those",
            lambda: require_no_universal_claim(evaluate(CLAIM, [report])),
        ),
        (
            "a negative duration",
            "must be null or a non-negative number",
            lambda: _report(trials=[{**_trials(8)[0], "wall_ms": -5}] + _trials(8)[1:]),
        ),
        (
            "zero declared repetitions",
            "workload.repetitions must be a positive integer",
            lambda: _report(workload={**WORKLOAD, "repetitions": 0}),
        ),
        (
            "an environment field dropped",
            "environment fields drifted",
            lambda: _report(
                environment={k: v for k, v in LAPTOP.items() if k != "cpu"}
            ),
        ),
        (
            "identities with no tool versions",
            "tool_versions must be a non-empty object",
            lambda: _report(identities={**IDENTITIES, "tool_versions": {}}),
        ),
        (
            "a claim with no threshold",
            "claim.threshold must be a number",
            lambda: evaluate({**CLAIM, "threshold": "small"}, [report]),
        ),
        (
            "an unknown comparator",
            "claim.comparator is",
            lambda: evaluate({**CLAIM, "comparator": "roughly"}, [report]),
        ),
        (
            "an empty quantile input",
            "no values to summarise",
            lambda: quantiles([]),
        ),
    ]
    for label, expect, action in cases:
        control(label, expect, action)

    if sorted(ORIGINS) != ["MEASURED_HERE", "SOURCE_PROPOSAL", "VENDOR_BENCHMARK"]:
        raise ContractError("the claim origin vocabulary drifted")
    return len(cases)


def run_selftest(root: Path) -> tuple[int, int]:
    return positive_properties(), controls()
