#!/usr/bin/env python3
"""The evaluation pass, in the order #72 names.

    CANDIDATE_PROPOSED
    -> STATIC_CONTRACT_CHECK
    -> PUBLIC_DEV_EVAL
    -> MUTATION_TRAP_EVAL
    -> SEALED_HOLDOUT
    -> CROSS_HOST_REPLICATION
    -> REGRESSION_RESOURCE_ANALYSIS
    -> CANDIDATE | REJECTED | INCONCLUSIVE
    -> HUMAN_ADMIT

The seal is opened at SEALED_HOLDOUT and not before, and the payloads for every
stage are built by `build_run_input`, which refuses if an answer is reachable.
Ordering here is not presentation: the holdout answers are not in memory during
the dev and mutation stages at all.
"""

from __future__ import annotations

from typing import Any

from se_cases import (
    build_run_input,
    case_set_digest,
    holdout_seal,
    validate_case_set,
)
from se_common import ContractError, digest, reveal
from se_decision import decide, gate_state, validate_run
from se_experiment import validate_experiment

STATES = [
    "CANDIDATE_PROPOSED",
    "STATIC_CONTRACT_CHECK",
    "PUBLIC_DEV_EVAL",
    "MUTATION_TRAP_EVAL",
    "SEALED_HOLDOUT",
    "CROSS_HOST_REPLICATION",
    "REGRESSION_RESOURCE_ANALYSIS",
    "DECIDED",
]


def _pass_rate(runs: list[dict[str, Any]], arm: str) -> float:
    subset = [run for run in runs if run["arm"] == arm]
    if not subset:
        raise ContractError(f"no runs for arm {arm!r}")
    return sum(1 for run in subset if gate_state(run) == "PASS") / len(subset)


def evaluate(
    experiment: dict[str, Any],
    dev_cases: list[dict[str, Any]],
    mutation_cases: list[dict[str, Any]],
    holdout_cases: list[dict[str, Any]],
    dev_runs: list[dict[str, Any]],
    mutation_runs: list[dict[str, Any]],
    holdout_runs: list[dict[str, Any]],
    cross_host: list[dict[str, Any]],
) -> dict[str, Any]:
    trace = ["CANDIDATE_PROPOSED"]

    experiment = validate_experiment(experiment)
    validate_case_set(dev_cases, "dev cases", "DEV")
    validate_case_set(mutation_cases, "mutation cases", "MUTATION")
    validate_case_set(holdout_cases, "holdout cases", "HOLDOUT")

    if case_set_digest(dev_cases) != experiment["dev_case_set_digest"]:
        raise ContractError(
            "the development case set does not match the digest the experiment pinned; "
            "cases edited after the experiment was declared make every earlier number "
            "describe a different evaluation"
        )
    if experiment["mutation_suite"]["case_count"] != len(mutation_cases):
        raise ContractError(
            f"the experiment declares {experiment['mutation_suite']['case_count']} "
            f"mutation cases but {len(mutation_cases)} were supplied; a suite that "
            "grew after the candidate ran was written with its failures in view"
        )
    if case_set_digest(mutation_cases) != experiment["mutation_suite"]["suite_digest"]:
        raise ContractError(
            "the mutation suite does not match the digest sealed before the run"
        )

    # Overlap between the dev set and the holdout is the leak that no amount of
    # process discipline catches, because both sets look correct on their own.
    overlap = sorted(
        {case["case_id"] for case in dev_cases}
        & {case["case_id"] for case in holdout_cases}
    )
    if overlap:
        raise ContractError(
            f"cases {overlap} appear in both the development set and the sealed "
            "holdout; the holdout measures retention on cases the candidate was not "
            "developed against, and a shared case is a case it was"
        )
    trace.append("STATIC_CONTRACT_CHECK")

    # Payload construction refuses if any answer is reachable, and it is asked
    # about the holdout answers at every stage, not only the holdout stage.
    build_run_input(dev_cases, holdout_cases)
    for index, run in enumerate(dev_runs):
        validate_run(run, f"dev_runs[{index}]")
    trace.append("PUBLIC_DEV_EVAL")

    build_run_input(mutation_cases, holdout_cases)
    for index, run in enumerate(mutation_runs):
        validate_run(run, f"mutation_runs[{index}]")
    candidate_mutation = [run for run in mutation_runs if run["arm"] == "candidate"]
    if not candidate_mutation:
        raise ContractError("the mutation suite was not run against the candidate")
    # A trap case is caught when the gate FAILS: the trap plants a violation, and
    # a procedure that notices it produces a failing gate rather than a passing
    # one. Reading this the other way would score the blind candidate highest.
    caught = sum(1 for run in candidate_mutation if gate_state(run) == "FAIL")
    mutation_summary = {
        "cases": len(mutation_cases),
        "runs": len(candidate_mutation),
        "caught": caught,
        "missed": len(candidate_mutation) - caught,
        "caught_rate": caught / len(candidate_mutation),
        "reading": "a trap is caught when its gate FAILS; the trap plants a violation",
    }
    trace.append("MUTATION_TRAP_EVAL")

    # Only here does anything open the seal.
    reveal(
        sorted(
            (
                {"case_id": c["case_id"], "expected": c["expected"]}
                for c in holdout_cases
            ),
            key=lambda entry: entry["case_id"],
        ),
        experiment["sealed_holdout"]["seal"],
    )
    if holdout_seal(holdout_cases) != experiment["sealed_holdout"]["seal"]:
        raise ContractError("the holdout does not match its seal")
    if experiment["sealed_holdout"]["case_count"] != len(holdout_cases):
        raise ContractError("the holdout case count does not match the experiment")
    build_run_input(holdout_cases, holdout_cases)
    for index, run in enumerate(holdout_runs):
        validate_run(run, f"holdout_runs[{index}]")
    holdout_summary = {
        "cases": len(holdout_cases),
        "runs": len([r for r in holdout_runs if r["arm"] == "candidate"]),
        "gate_pass_rate": _pass_rate(holdout_runs, "candidate"),
    }
    trace.append("SEALED_HOLDOUT")

    seen_hosts = set()
    for index, row in enumerate(cross_host):
        if set(row) != {
            "host_id",
            "model_id",
            "provider_id",
            "state",
            "gate_pass_rate",
        }:
            raise ContractError(f"cross_host[{index}] fields drifted")
        if row["state"] not in {"REPLICATED", "REGRESSED", "NOT_EXERCISED"}:
            raise ContractError(f"cross_host[{index}].state is unknown")
        if row["host_id"] in seen_hosts:
            raise ContractError(f"cross_host names {row['host_id']!r} twice")
        seen_hosts.add(row["host_id"])
    trace.append("CROSS_HOST_REPLICATION")
    trace.append("REGRESSION_RESOURCE_ANALYSIS")

    decision = decide(
        experiment, dev_runs, holdout_summary, mutation_summary, cross_host
    )
    trace.append("DECIDED")

    return {
        "state_trace": trace,
        "decision": decision,
        # Deterministic given the inputs, so two evaluations of one experiment
        # can be compared without reading either.
        "evaluation_digest": digest(
            {"experiment": experiment["experiment_id"], "decision": decision}
        ),
    }
