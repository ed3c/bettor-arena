#!/usr/bin/env python3
"""Positive properties plus one planted control per named failure in #72.

Each control mutates the good fixtures in exactly one place and asserts the
evaluation refuses, matching on the substring its own rule raises.

Several controls here mutate the *result* rather than the input -- a candidate
that failed a gate but scored well with a judge, for example. That is
deliberate: the failures #72 names are mostly failures of interpretation, and
the only way to plant one is to hand the decision a result set that a careless
reading would score in the candidate's favour.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

from se_common import ContractError
from se_pipeline import evaluate
from se_release import build_receipt, validate_receipt

NAMES = (
    "experiment",
    "dev-cases",
    "mutation-cases",
    "holdout-cases",
    "dev-runs",
    "mutation-runs",
    "holdout-runs",
    "cross-host",
    "host-projections",
)


def load_inputs(root: Path) -> dict[str, Any]:
    good = root / "tests/fixtures/good"
    return {
        name: json.loads((good / f"{name}.json").read_text(encoding="utf-8"))
        for name in NAMES
    }


def _evaluate(inputs: dict[str, Any]) -> dict[str, Any]:
    return evaluate(
        inputs["experiment"],
        inputs["dev-cases"],
        inputs["mutation-cases"],
        inputs["holdout-cases"],
        inputs["dev-runs"],
        inputs["mutation-runs"],
        inputs["holdout-runs"],
        inputs["cross-host"],
    )


def _arm(inputs: dict[str, Any], name: str) -> dict[str, Any]:
    for arm in inputs["experiment"]["arms"]:
        if arm["arm"] == name:
            return arm
    raise KeyError(name)


def _candidate_runs(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    return [run for run in inputs["dev-runs"] if run["arm"] == "candidate"]


# --- controls that must raise -------------------------------------------------


def _holdout_answer_in_prompt(inputs: dict[str, Any]) -> None:
    # The answer reaches the runner through a field the whitelist allows.
    answer = inputs["holdout-cases"][0]["expected"]
    inputs["dev-cases"][0]["prompt"] += f" (for example: {answer})"
    inputs["experiment"]["dev_case_set_digest"] = _dev_digest(inputs)


def _holdout_case_in_dev_set(inputs: dict[str, Any]) -> None:
    leaked = copy.deepcopy(inputs["holdout-cases"][0])
    leaked["kind"] = "DEV"
    inputs["dev-cases"].append(leaked)
    inputs["experiment"]["dev_case_set_digest"] = _dev_digest(inputs)


def _holdout_kind_case_in_dev_set(inputs: dict[str, Any]) -> None:
    # The same leak with the kind left honest, so the set-membership rule is the
    # one that has to catch it rather than the id-overlap rule.
    leaked = copy.deepcopy(inputs["holdout-cases"][0])
    leaked["case_id"] = "dev-leaked"
    inputs["dev-cases"].append(leaked)
    inputs["experiment"]["dev_case_set_digest"] = _dev_digest(inputs)


def _holdout_answers_swapped_after_the_run(inputs: dict[str, Any]) -> None:
    inputs["holdout-cases"][0]["expected"] = "whatever the candidate happened to say"


def _reveal_authority_widened(inputs: dict[str, Any]) -> None:
    inputs["experiment"]["sealed_holdout"]["reveal_authority"] = "RUNNER"


def _different_tools_between_arms(inputs: dict[str, Any]) -> None:
    _arm(inputs, "candidate")["notes"] = "ran with an extra tool"
    for run in _candidate_runs(inputs):
        run["provider_id"] = "another-provider"


def _model_changed_mid_comparison(inputs: dict[str, Any]) -> None:
    _candidate_runs(inputs)[0]["model_id"] = "claude-opus-5-preview"


def _failed_gate_compensated_by_judge(inputs: dict[str, Any]) -> None:
    # Every candidate run fails a gate, but the judge loves it. The decision
    # must reject on the gates and never look at the score.
    for run in _candidate_runs(inputs):
        run["gate_results"][0]["state"] = "FAIL"
        run["judge_scores"] = [
            {
                "judge_id": "clarity",
                "score": 5.0,
                "calibrated_against": "deterministic-labels-v1",
                "calibration_receipt": "sha256:" + "ee" * 32,
            }
        ]


def _one_lucky_run(inputs: dict[str, Any]) -> None:
    keep = {run["run_id"] for run in _candidate_runs(inputs)[:1]}
    inputs["dev-runs"] = [
        run
        for run in inputs["dev-runs"]
        if run["arm"] != "candidate" or run["run_id"] in keep
    ]


def _repetitions_below_floor(inputs: dict[str, Any]) -> None:
    inputs["experiment"]["execution_contract"]["repetitions"] = 1


def _stopping_when_it_looks_good(inputs: dict[str, Any]) -> None:
    inputs["experiment"]["execution_contract"]["stopping_rule"] = "WHEN_SIGNIFICANT"


def _candidate_prompt_carries_a_timestamp(inputs: dict[str, Any]) -> None:
    _arm(inputs, "candidate")["content_bytes"] += (
        "\nGenerated at 2026-08-15T09:00:00Z\n"
    )


def _mutation_suite_derived_from_failures(inputs: dict[str, Any]) -> None:
    inputs["experiment"]["mutation_suite"]["derived_from"] = "CANDIDATE_FAILURES"


def _mutation_suite_grew_after_the_run(inputs: dict[str, Any]) -> None:
    inputs["mutation-cases"].append(copy.deepcopy(inputs["mutation-cases"][0]))
    inputs["mutation-cases"][-1]["case_id"] = "mut-004"


def _dev_cases_edited_after_declaration(inputs: dict[str, Any]) -> None:
    inputs["dev-cases"][0]["expected"] = "something more convenient"


def _baseline_arm_given_content(inputs: dict[str, Any]) -> None:
    _arm(inputs, "baseline")["content_bytes"] = "# a small skill, for fairness"


def _candidate_identical_to_current(inputs: dict[str, Any]) -> None:
    _arm(inputs, "candidate")["content_digest"] = _arm(inputs, "current")[
        "content_digest"
    ]


def _gate_declared_as_judge_too(inputs: dict[str, Any]) -> None:
    inputs["experiment"]["advisory_judges"] = sorted(
        [*inputs["experiment"]["advisory_judges"], "no-gate-bypass"]
    )


def _no_hard_gates_at_all(inputs: dict[str, Any]) -> None:
    inputs["experiment"]["hard_gates"] = []


def _mutable_skill_release(inputs: dict[str, Any]) -> None:
    inputs["experiment"]["subject"]["ref_kind"] = "BRANCH"


def _uncalibrated_judge_carries_a_receipt(inputs: dict[str, Any]) -> None:
    _candidate_runs(inputs)[0]["judge_scores"][1]["calibration_receipt"] = (
        "sha256:" + "ff" * 32
    )


def _case_with_no_hard_gate(inputs: dict[str, Any]) -> None:
    inputs["dev-cases"][0]["hard_gate_ids"] = []
    inputs["experiment"]["dev_case_set_digest"] = _dev_digest(inputs)


def _duplicate_cross_host_row(inputs: dict[str, Any]) -> None:
    inputs["cross-host"].append(copy.deepcopy(inputs["cross-host"][0]))


def _dev_digest(inputs: dict[str, Any]) -> str:
    from se_cases import case_set_digest

    return case_set_digest(inputs["dev-cases"])


RAISING_CONTROLS: list[tuple[str, Callable[[dict[str, Any]], None], str]] = [
    (
        "holdout-answer-reachable-in-prompt",
        _holdout_answer_in_prompt,
        "a score for reading",
    ),
    (
        "holdout-case-id-also-in-dev-set",
        _holdout_case_in_dev_set,
        "a shared case is a case it was",
    ),
    (
        "holdout-kind-case-inside-dev-set",
        _holdout_kind_case_in_dev_set,
        "holdout in name only",
    ),
    (
        "holdout-answers-swapped-after-run",
        _holdout_answers_swapped_after_the_run,
        "do not match the seal",
    ),
    ("reveal-authority-widened", _reveal_authority_widened, "GRADER_ONLY"),
    (
        "provider-changed-between-arms",
        _different_tools_between_arms,
        "not between the prompts",
    ),
    (
        "model-changed-mid-comparison",
        _model_changed_mid_comparison,
        "not between the prompts",
    ),
    (
        "one-lucky-run-declared-winner",
        _one_lucky_run,
        "a shorter arm is a different experiment",
    ),
    ("repetitions-below-the-floor", _repetitions_below_floor, "luckier sample"),
    (
        "stopping-when-it-looks-good",
        _stopping_when_it_looks_good,
        "null result becomes a win",
    ),
    (
        "candidate-prompt-carries-a-timestamp",
        _candidate_prompt_carries_a_timestamp,
        "volatile values",
    ),
    (
        "mutation-suite-from-candidate-failures",
        _mutation_suite_derived_from_failures,
        "transcription",
    ),
    (
        "mutation-suite-grew-after-the-run",
        _mutation_suite_grew_after_the_run,
        "with its failures in view",
    ),
    (
        "dev-cases-edited-after-declaration",
        _dev_cases_edited_after_declaration,
        "a different evaluation",
    ),
    ("baseline-arm-given-content", _baseline_arm_given_content, "not needed at all"),
    (
        "candidate-identical-to-current",
        _candidate_identical_to_current,
        "nothing to evaluate",
    ),
    (
        "gate-also-declared-as-judge",
        _gate_declared_as_judge_too,
        "whichever is convenient",
    ),
    ("no-hard-gates-declared", _no_hard_gates_at_all, "the judge is advisory"),
    ("mutable-skill-release-as-subject", _mutable_skill_release, "IMMUTABLE_RELEASE"),
    (
        "uncalibrated-judge-with-a-receipt",
        _uncalibrated_judge_carries_a_receipt,
        "without naming what",
    ),
    ("case-with-no-hard-gate", _case_with_no_hard_gate, "the judge is advisory"),
    ("duplicate-cross-host-row", _duplicate_cross_host_row, "twice"),
]


# --- controls that must produce a non-CANDIDATE outcome -----------------------


def _judge_cannot_rescue_failed_gates(inputs: dict[str, Any]) -> None:
    _failed_gate_compensated_by_judge(inputs)


def _holdout_regressed(inputs: dict[str, Any]) -> None:
    for run in inputs["holdout-runs"]:
        run["gate_results"][0]["state"] = "FAIL"


def _trap_missed(inputs: dict[str, Any]) -> None:
    for gate in inputs["mutation-runs"][0]["gate_results"]:
        gate["state"] = "PASS"


def _single_host_replication(inputs: dict[str, Any]) -> None:
    inputs["cross-host"][1]["state"] = "NOT_EXERCISED"


def _regressed_on_another_host(inputs: dict[str, Any]) -> None:
    inputs["cross-host"][1]["state"] = "REGRESSED"


def _baseline_matches_candidate(inputs: dict[str, Any]) -> None:
    for run in inputs["dev-runs"]:
        if run["arm"] == "baseline":
            for gate in run["gate_results"]:
                gate["state"] = "PASS"


OUTCOME_CONTROLS: list[tuple[str, Callable[[dict[str, Any]], None], str, str]] = [
    (
        "failed-gates-with-a-perfect-judge",
        _judge_cannot_rescue_failed_gates,
        "REJECTED",
        "no judge total can compensate",
    ),
    ("holdout-regression", _holdout_regressed, "REJECTED", "did not survive cases"),
    ("trap-missed", _trap_missed, "REJECTED", "will not notice a real one"),
    (
        "replicated-on-one-host-only",
        _single_host_replication,
        "INCONCLUSIVE",
        "cannot establish that a prompt is better in general",
    ),
    (
        "regressed-on-another-host",
        _regressed_on_another_host,
        "REJECTED",
        "regressed on host",
    ),
    (
        "no-skill-baseline-matches-candidate",
        _baseline_matches_candidate,
        "INCONCLUSIVE",
        "should shrink",
    ),
]


def run_selftest(root: Path) -> tuple[int, int]:
    base = load_inputs(root)
    positives = 0

    result = _evaluate(copy.deepcopy(base))
    if result["decision"]["outcome"] != "CANDIDATE":
        raise ContractError(
            f"the positive experiment decided {result['decision']['outcome']}; with no "
            "arm that reaches CANDIDATE, every rejection control below passes for free"
        )
    positives += 1

    if result["state_trace"][-1] != "DECIDED":
        raise ContractError("the pipeline did not reach a decision")
    # Ordering is load-bearing, not presentational: the seal is opened at the
    # holdout stage, so the dev and mutation stages must precede it.
    trace = result["state_trace"]
    if trace.index("SEALED_HOLDOUT") < trace.index("MUTATION_TRAP_EVAL"):
        raise ContractError("the holdout was opened before the mutation stage ran")
    positives += 1

    decision = result["decision"]
    if decision["judge_authority"] != "ADVISORY_ONLY":
        raise ContractError("the decision does not state that judges are advisory")
    if decision["gate_authority"] != "DETERMINISTIC_AND_NON_COMPENSATORY":
        raise ContractError(
            "the decision does not state that gates are non-compensatory"
        )
    positives += 1

    # Uncalibrated judges are kept and counted, not dropped -- a reader should be
    # able to see how much of the scoring had no calibration behind it.
    if decision["arms"]["candidate"]["uncalibrated_judge_count"] == 0:
        raise ContractError(
            "the uncalibrated judge disappeared from the summary; dropping it hides "
            "how much of the scoring rested on nothing"
        )
    positives += 1

    fixture = build_receipt(
        base["experiment"],
        decision,
        "FIXTURE_ONLY",
        base["host-projections"],
        "2026-08-15T12:00:00Z",
    )
    validate_receipt(fixture)
    if fixture["capability_state"] != "NOT_UNLOCKED":
        raise ContractError("fixture-only evidence unlocked a capability")
    positives += 1

    live = build_receipt(
        base["experiment"],
        decision,
        "LIVE_EXERCISED",
        base["host-projections"],
        "2026-08-15T12:00:00Z",
    )
    validate_receipt(live)
    if live["capability_state"] != "UNLOCKED_PENDING_ADMIT":
        raise ContractError("live evidence did not reach the pending-admit state")
    if live["canonical_mutation"] != "NONE_PERFORMED":
        raise ContractError("the receipt recorded a canonical mutation")
    if live["proposed_release"]["target_repository"] != "skills-shared":
        raise ContractError(
            "the proposed release does not target the shared repository"
        )
    positives += 1

    # A rejection still produces a receipt, and it proposes nothing.
    rejected = copy.deepcopy(decision)
    rejected["outcome"] = "REJECTED"
    rejected_receipt = build_receipt(
        base["experiment"],
        rejected,
        "LIVE_EXERCISED",
        base["host-projections"],
        "2026-08-15T12:00:00Z",
    )
    validate_receipt(rejected_receipt)
    if rejected_receipt["proposed_release"] is not None:
        raise ContractError("a rejected experiment proposed a release")
    if rejected_receipt["capability_state"] != "NOT_UNLOCKED":
        raise ContractError("a rejected experiment unlocked a capability")
    positives += 1

    # Deterministic: two evaluations of one experiment agree.
    again = _evaluate(copy.deepcopy(base))
    if again["evaluation_digest"] != result["evaluation_digest"]:
        raise ContractError("two evaluations of one experiment disagreed")
    positives += 1

    failures = []
    for name, mutate, needle in RAISING_CONTROLS:
        inputs = copy.deepcopy(base)
        mutate(inputs)
        try:
            _evaluate(inputs)
        except ContractError as exc:
            if needle not in str(exc):
                failures.append(
                    f"{name} was refused, but for the wrong reason: expected a message "
                    f"containing {needle!r}, got {exc}"
                )
            continue
        except Exception as exc:  # noqa: BLE001
            failures.append(
                f"{name} raised {type(exc).__name__}: {exc} -- that is a broken "
                "control, not a refusal; nothing was measured"
            )
            continue
        failures.append(f"{name} was accepted")

    for name, mutate, expected, needle in OUTCOME_CONTROLS:
        inputs = copy.deepcopy(base)
        mutate(inputs)
        try:
            outcome = _evaluate(inputs)["decision"]
        except Exception as exc:  # noqa: BLE001
            failures.append(
                f"{name} raised {type(exc).__name__}: {exc} -- this control checks the "
                "decision, so a refusal means the decision was never reached"
            )
            continue
        if outcome["outcome"] != expected:
            failures.append(
                f"{name} decided {outcome['outcome']}, expected {expected}; reasons "
                f"were {outcome['reasons']}"
            )
        elif not any(needle in reason for reason in outcome["reasons"]):
            failures.append(
                f"{name} reached {expected} but for the wrong reason: no reason "
                f"contained {needle!r}; got {outcome['reasons']}"
            )

    if failures:
        raise ContractError(
            "planted controls did not behave:\n  " + "\n  ".join(failures)
        )
    return positives, len(RAISING_CONTROLS) + len(OUTCOME_CONTROLS)
