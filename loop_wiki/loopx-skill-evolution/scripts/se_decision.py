#!/usr/bin/env python3
"""Scoring and the decision. Hard gates first, and they are not averaged.

The rule this file exists to enforce fits in one line: **a failed hard gate is
not a low score.** A gate is a statement that something must hold; averaging it
with a judge's 4-out-of-5 turns "this must hold" into "this usually holds", and
the difference only becomes visible the one time it matters.

So `score_run` returns two separate things and never a blend:

    gate_state   PASS or FAIL, deterministic
    judge_score  a number, advisory, ignored by the decision unless calibrated

A judge may only be counted at all if it has been calibrated against
deterministic labels, and calibration is a field with a receipt rather than an
adjective.

The outcome vocabulary is three-valued, because two-valued would force every
null result into REJECTED. An experiment that could not tell the arms apart did
not reject the candidate -- it failed to answer, and those are different things
to a person deciding whether to run it again.
"""

from __future__ import annotations

from typing import Any

from se_common import (
    ContractError,
    exact_object,
    non_empty_str,
    require,
)

OUTCOMES = ("CANDIDATE", "REJECTED", "INCONCLUSIVE")

RUN_KEYS = {
    "run_id",
    "arm",
    "case_id",
    "repetition",
    "gate_results",
    "judge_scores",
    "unsupported_claims",
    "tokens",
    "elapsed_ms",
    "host_id",
    "model_id",
    "provider_id",
}

GATE_RESULT_KEYS = {"gate_id", "state", "detail"}
GATE_STATES = {"PASS", "FAIL", "NOT_EXERCISED"}

JUDGE_KEYS = {"judge_id", "score", "calibrated_against", "calibration_receipt"}


def validate_run(value: Any, label: str) -> dict[str, Any]:
    run = exact_object(value, RUN_KEYS, label)
    non_empty_str(run["run_id"], f"{label}.run_id")
    non_empty_str(run["case_id"], f"{label}.case_id")
    for field in ("host_id", "model_id", "provider_id"):
        non_empty_str(run[field], f"{label}.{field}")
    if not isinstance(run["repetition"], int) or run["repetition"] < 1:
        raise ContractError(f"{label}.repetition must be a positive integer")
    for field in ("tokens", "elapsed_ms", "unsupported_claims"):
        value_ = run[field]
        if not isinstance(value_, int) or isinstance(value_, bool) or value_ < 0:
            raise ContractError(f"{label}.{field} must be a non-negative integer")

    gates = run["gate_results"]
    if not isinstance(gates, list) or not gates:
        raise ContractError(f"{label}.gate_results must be non-empty")
    for index, gate_value in enumerate(gates):
        gate = exact_object(
            gate_value, GATE_RESULT_KEYS, f"{label}.gate_results[{index}]"
        )
        non_empty_str(gate["gate_id"], f"{label}.gate_results[{index}].gate_id")
        if gate["state"] not in GATE_STATES:
            raise ContractError(
                f"{label}.gate_results[{index}].state must be one of {sorted(GATE_STATES)}"
            )

    judges = run["judge_scores"]
    if not isinstance(judges, list):
        raise ContractError(f"{label}.judge_scores must be a list")
    for index, judge_value in enumerate(judges):
        judge = exact_object(judge_value, JUDGE_KEYS, f"{label}.judge_scores[{index}]")
        non_empty_str(judge["judge_id"], f"{label}.judge_scores[{index}].judge_id")
        score = judge["score"]
        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise ContractError(f"{label}.judge_scores[{index}].score must be a number")
        # Calibration is a receipt, not an adjective. An uncalibrated judge is
        # kept and reported; it just cannot move the decision.
        if judge["calibrated_against"] is not None:
            non_empty_str(
                judge["calibration_receipt"],
                f"{label}.judge_scores[{index}].calibration_receipt",
            )
        elif judge["calibration_receipt"] is not None:
            raise ContractError(
                f"{label}.judge_scores[{index}] carries a calibration receipt without "
                "naming what it was calibrated against"
            )
    return run


def gate_state(run: dict[str, Any]) -> str:
    """PASS only if every gate passed. NOT_EXERCISED is not a pass."""
    states = {gate["state"] for gate in run["gate_results"]}
    if "FAIL" in states:
        return "FAIL"
    if "NOT_EXERCISED" in states:
        return "NOT_EXERCISED"
    return "PASS"


def calibrated_judge_scores(run: dict[str, Any]) -> list[float]:
    return [
        float(judge["score"])
        for judge in run["judge_scores"]
        if judge["calibrated_against"] is not None
    ]


def summarise_arm(runs: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    """Per-arm totals. Gate outcomes counted, judge scores kept beside them."""
    arm_runs = [run for run in runs if run["arm"] == arm]
    if not arm_runs:
        raise ContractError(f"no runs for arm {arm!r}")
    passed = sum(1 for run in arm_runs if gate_state(run) == "PASS")
    scores = [s for run in arm_runs for s in calibrated_judge_scores(run)]
    return {
        "arm": arm,
        "runs": len(arm_runs),
        "gate_passes": passed,
        "gate_pass_rate": passed / len(arm_runs),
        "unsupported_claims": sum(run["unsupported_claims"] for run in arm_runs),
        "tokens": sum(run["tokens"] for run in arm_runs),
        "elapsed_ms": sum(run["elapsed_ms"] for run in arm_runs),
        # Reported next to the gates, never folded into them.
        "calibrated_judge_mean": (sum(scores) / len(scores)) if scores else None,
        "uncalibrated_judge_count": sum(
            1
            for run in arm_runs
            for judge in run["judge_scores"]
            if judge["calibrated_against"] is None
        ),
    }


def check_execution_consistency(
    runs: list[dict[str, Any]], contract: dict[str, Any]
) -> None:
    """Every arm ran under the declared host, model and provider.

    A model swapped between arms produces a perfectly clean-looking comparison
    of two different things, and nothing downstream of the number can see it.
    """
    for field in ("host_id", "model_id", "provider_id"):
        observed = sorted({run[field] for run in runs})
        if observed != [contract[field]]:
            raise ContractError(
                f"runs used {field} {observed} but the execution contract declares "
                f"{contract[field]!r}; arms compared under different {field}s measure "
                "the difference between them, not between the prompts"
            )


def decide(
    experiment: dict[str, Any],
    runs: list[dict[str, Any]],
    holdout_summary: dict[str, Any],
    mutation_summary: dict[str, Any],
    cross_host: list[dict[str, Any]],
) -> dict[str, Any]:
    """CANDIDATE, REJECTED or INCONCLUSIVE, with the reason recorded."""
    contract = experiment["execution_contract"]
    for run_index, run in enumerate(runs):
        validate_run(run, f"runs[{run_index}]")
    check_execution_consistency(runs, contract)

    summaries = {
        arm: summarise_arm(runs, arm) for arm in ("current", "candidate", "baseline")
    }
    reps = contract["repetitions"]
    for arm, summary in summaries.items():
        if summary["runs"] < reps:
            raise ContractError(
                f"arm {arm!r} has {summary['runs']} runs but the contract declares "
                f"{reps} repetitions; a shorter arm is a different experiment, and "
                "the shortfall is invisible in a rate"
            )

    reasons = []
    candidate, current, baseline = (
        summaries["candidate"],
        summaries["current"],
        summaries["baseline"],
    )

    # Hard gates first, and no judge score participates in this branch.
    if candidate["gate_pass_rate"] < current["gate_pass_rate"]:
        return _outcome(
            "REJECTED",
            [
                f"candidate passes hard gates at {candidate['gate_pass_rate']:.2f} "
                f"against current's {current['gate_pass_rate']:.2f}; a failed gate is "
                "not a low score and no judge total can compensate for it"
            ],
            summaries,
            holdout_summary,
            mutation_summary,
            cross_host,
        )

    if holdout_summary["gate_pass_rate"] < current["gate_pass_rate"]:
        reasons.append(
            f"the sealed holdout pass rate {holdout_summary['gate_pass_rate']:.2f} is "
            f"below current's development rate {current['gate_pass_rate']:.2f}; the "
            "gain did not survive cases the candidate was not developed against"
        )
        return _outcome(
            "REJECTED",
            reasons,
            summaries,
            holdout_summary,
            mutation_summary,
            cross_host,
        )

    if mutation_summary["caught_rate"] < 1.0:
        reasons.append(
            f"the candidate missed {mutation_summary['missed']} trap case(s); a "
            "procedure that does not notice a planted violation will not notice a "
            "real one"
        )
        return _outcome(
            "REJECTED",
            reasons,
            summaries,
            holdout_summary,
            mutation_summary,
            cross_host,
        )

    # Cross-host is per host, never folded. One host cannot establish a
    # universal result, and a majority vote across hosts would let a strong
    # result on one hide a regression on another.
    replicated = [row for row in cross_host if row["state"] == "REPLICATED"]
    regressed = [row for row in cross_host if row["state"] == "REGRESSED"]
    if regressed:
        return _outcome(
            "REJECTED",
            [f"regressed on host(s) {sorted(r['host_id'] for r in regressed)}"],
            summaries,
            holdout_summary,
            mutation_summary,
            cross_host,
        )
    if len(replicated) < 2:
        reasons.append(
            f"replicated on {len(replicated)} host(s); one host, model and provider "
            "cannot establish that a prompt is better in general, and this is an "
            "unanswered question rather than a rejection"
        )
        return _outcome(
            "INCONCLUSIVE",
            reasons,
            summaries,
            holdout_summary,
            mutation_summary,
            cross_host,
        )

    if candidate["gate_pass_rate"] == current["gate_pass_rate"]:
        # Equal on the gates. The judge is not allowed to break the tie.
        if candidate["tokens"] >= current["tokens"]:
            reasons.append(
                "candidate matches current on hard gates without reducing token cost; "
                "there is no measured reason to change, and an advisory judge may not "
                "supply one"
            )
            return _outcome(
                "INCONCLUSIVE",
                reasons,
                summaries,
                holdout_summary,
                mutation_summary,
                cross_host,
            )
        reasons.append(
            f"equal hard-gate rate at lower token cost "
            f"({candidate['tokens']} against {current['tokens']})"
        )
    else:
        reasons.append(
            f"candidate improves the hard-gate rate to {candidate['gate_pass_rate']:.2f} "
            f"from {current['gate_pass_rate']:.2f}, holds on the sealed holdout, and "
            "catches every trap"
        )

    if baseline["gate_pass_rate"] >= candidate["gate_pass_rate"]:
        reasons.append(
            f"the no-skill baseline reaches {baseline['gate_pass_rate']:.2f}, at or "
            "above the candidate; the task does not need this Skill, so the finding "
            "is that it should shrink rather than that this patch is good"
        )
        return _outcome(
            "INCONCLUSIVE",
            reasons,
            summaries,
            holdout_summary,
            mutation_summary,
            cross_host,
        )

    return _outcome(
        "CANDIDATE", reasons, summaries, holdout_summary, mutation_summary, cross_host
    )


def _outcome(
    outcome: str,
    reasons: list[str],
    summaries: dict[str, Any],
    holdout: dict[str, Any],
    mutation: dict[str, Any],
    cross_host: list[dict[str, Any]],
) -> dict[str, Any]:
    require(outcome in OUTCOMES, f"unknown outcome {outcome!r}")
    return {
        "outcome": outcome,
        "reasons": reasons,
        "arms": summaries,
        "sealed_holdout": holdout,
        "mutation": mutation,
        "cross_host": sorted(cross_host, key=lambda row: row["host_id"]),
        # Stated on the decision itself, where someone reading the number will
        # see it, rather than in a document they would have to already doubt.
        "judge_authority": "ADVISORY_ONLY",
        "gate_authority": "DETERMINISTIC_AND_NON_COMPENSATORY",
    }
