#!/usr/bin/env python3
"""The experiment contract. Three arms, one execution contract, pinned subjects.

An A/B between two prompts is only an A/B if everything else is the same. The
most common way this goes wrong is not deceit -- it is that the candidate was
run later, on a newer model snapshot, with one extra tool enabled because
someone was debugging. The comparison still produces a number, and the number is
about the wrong thing.

So the execution contract (tools, context policy, model, provider, host,
repetitions) is declared once and every arm points at that one object. Arms
cannot carry their own; there is no field for it. That is a shape rather than a
rule, and it is why nobody has to remember it.

Three arms, and the baseline is not optional:

    current     the released Skill as it stands
    candidate   the proposed patch
    baseline    no skill at all

Without the baseline, "candidate beats current" cannot distinguish a better
procedure from a task the model does well with no procedure at all -- and the
second case means the Skill should shrink, not grow.
"""

from __future__ import annotations

from typing import Any

from se_common import (
    SHA40,
    ContractError,
    exact_object,
    find_volatile,
    non_empty_str,
    require,
    sha256_ref,
)

ARMS = ("current", "candidate", "baseline")

SUBJECT_KEYS = {"repository", "commit", "skill_id", "skill_release", "ref_kind"}

EXECUTION_KEYS = {
    "host_id",
    "model_id",
    "provider_id",
    "tools_allowlist",
    "context_policy",
    "max_context_tokens",
    "repetitions",
    "ordering",
    "stopping_rule",
}

ARM_KEYS = {"arm", "content_digest", "content_bytes", "notes"}

EXPERIMENT_KEYS = {
    "schema_version",
    "experiment_id",
    "subject",
    "execution_contract",
    "arms",
    "dev_case_set_digest",
    "mutation_suite",
    "sealed_holdout",
    "hard_gates",
    "advisory_judges",
}

MUTATION_KEYS = {"suite_digest", "sealed_at", "derived_from", "case_count"}
HOLDOUT_KEYS = {"seal", "case_count", "sealed_at", "reveal_authority"}

ORDERINGS = {"INTERLEAVED", "RANDOMIZED_FIXED_SEED"}
STOPPING_RULES = {"FIXED_REPETITIONS"}


def validate_subject(value: Any) -> dict[str, Any]:
    subject = exact_object(value, SUBJECT_KEYS, "experiment.subject")
    non_empty_str(subject["repository"], "subject.repository")
    non_empty_str(subject["skill_id"], "subject.skill_id")
    non_empty_str(subject["skill_release"], "subject.skill_release")
    if SHA40.fullmatch(str(subject["commit"])) is None:
        raise ContractError("subject.commit must be a full 40-hex sha")
    if subject["ref_kind"] != "IMMUTABLE_RELEASE":
        raise ContractError(
            "subject.ref_kind must be IMMUTABLE_RELEASE; a Skill identified by a "
            "mutable branch names different content tomorrow, and every arm in this "
            "experiment would then be compared against something that moved"
        )
    return subject


def validate_execution_contract(value: Any) -> dict[str, Any]:
    contract = exact_object(value, EXECUTION_KEYS, "experiment.execution_contract")
    for field in ("host_id", "model_id", "provider_id", "context_policy"):
        non_empty_str(contract[field], f"execution_contract.{field}")

    tools = contract["tools_allowlist"]
    if not isinstance(tools, list) or tools != sorted(tools):
        raise ContractError("execution_contract.tools_allowlist must be a sorted list")

    reps = contract["repetitions"]
    if not isinstance(reps, int) or isinstance(reps, bool) or reps < 3:
        raise ContractError(
            "execution_contract.repetitions must be at least 3; one run of each arm "
            "cannot separate a better prompt from a luckier sample, and a single-run "
            "winner is the most common way an evolution loop convinces itself"
        )
    if contract["ordering"] not in ORDERINGS:
        raise ContractError(
            f"execution_contract.ordering must be one of {sorted(ORDERINGS)}; arms run "
            "in blocks drift with whatever changed between the blocks"
        )
    if contract["stopping_rule"] not in STOPPING_RULES:
        raise ContractError(
            f"execution_contract.stopping_rule must be one of {sorted(STOPPING_RULES)}; "
            "stopping when the numbers look good is how a null result becomes a win"
        )
    tokens = contract["max_context_tokens"]
    if not isinstance(tokens, int) or tokens < 1:
        raise ContractError("execution_contract.max_context_tokens must be positive")
    return contract


def validate_arm(value: Any, label: str) -> dict[str, Any]:
    arm = exact_object(value, ARM_KEYS, label)
    if arm["arm"] not in ARMS:
        raise ContractError(f"{label}.arm must be one of {list(ARMS)}")
    sha256_ref(arm["content_digest"], f"{label}.content_digest")

    content = arm["content_bytes"]
    if arm["arm"] == "baseline":
        if content:
            raise ContractError(
                f"{label} is the baseline arm and carries content; the baseline is "
                "the no-skill control, and giving it content removes the only arm "
                "that could show the Skill is not needed at all"
            )
        return arm

    non_empty_str(content, f"{label}.content_bytes")
    # Cache comparability, checked on the content rather than promised in prose.
    volatile = find_volatile(content)
    if volatile:
        raise ContractError(
            f"{label} content contains volatile values {volatile}; a prompt that "
            "differs between renders is not comparable across arms and defeats "
            "prompt-cache reuse at the same time"
        )
    return arm


def validate_experiment(value: Any) -> dict[str, Any]:
    experiment = exact_object(value, EXPERIMENT_KEYS, "experiment")
    require(
        experiment["schema_version"] == "loopx/skill-evolution-experiment/v1",
        "experiment schema version drifted",
    )
    non_empty_str(experiment["experiment_id"], "experiment.experiment_id")
    validate_subject(experiment["subject"])
    validate_execution_contract(experiment["execution_contract"])
    sha256_ref(experiment["dev_case_set_digest"], "experiment.dev_case_set_digest")

    arms = experiment["arms"]
    if not isinstance(arms, list) or len(arms) != 3:
        raise ContractError(
            "experiment.arms must name exactly current, candidate and baseline"
        )
    seen = set()
    digests = {}
    for index, value_ in enumerate(arms):
        arm = validate_arm(value_, f"arms[{index}]")
        if arm["arm"] in seen:
            raise ContractError(f"duplicate arm {arm['arm']!r}")
        seen.add(arm["arm"])
        digests[arm["arm"]] = arm["content_digest"]
    if seen != set(ARMS):
        raise ContractError(
            f"experiment.arms must cover {list(ARMS)}, got {sorted(seen)}"
        )
    if digests["current"] == digests["candidate"]:
        raise ContractError(
            "current and candidate have the same content digest; there is nothing to "
            "evaluate, and a green result here would be read as evidence for a change"
        )

    mutation = exact_object(
        experiment["mutation_suite"], MUTATION_KEYS, "mutation_suite"
    )
    sha256_ref(mutation["suite_digest"], "mutation_suite.suite_digest")
    if not isinstance(mutation["case_count"], int) or mutation["case_count"] < 1:
        raise ContractError("mutation_suite.case_count must be positive")
    # The suite must be sealed against something other than the candidate's own
    # failures. A trap written after watching the candidate fail is a trap the
    # candidate was always going to fail, and it measures nothing.
    if mutation["derived_from"] not in {"TASK_SPECIFICATION", "PRIOR_INCIDENTS"}:
        raise ContractError(
            "mutation_suite.derived_from must be TASK_SPECIFICATION or PRIOR_INCIDENTS; "
            "a suite derived from the candidate's observed failures tests the failures "
            "it was written from, which is not sensitivity, it is transcription"
        )

    holdout = exact_object(experiment["sealed_holdout"], HOLDOUT_KEYS, "sealed_holdout")
    sha256_ref(holdout["seal"], "sealed_holdout.seal")
    if not isinstance(holdout["case_count"], int) or holdout["case_count"] < 1:
        raise ContractError("sealed_holdout.case_count must be positive")
    if holdout["reveal_authority"] != "GRADER_ONLY":
        raise ContractError(
            "sealed_holdout.reveal_authority must be GRADER_ONLY; anything else means "
            "the thing being evaluated can reach the answers it is being evaluated on"
        )

    gates = experiment["hard_gates"]
    if not isinstance(gates, list) or not gates:
        raise ContractError(
            "experiment.hard_gates must be non-empty; with no deterministic gate, the "
            "only signal left is the judge, and the judge is advisory"
        )
    if gates != sorted(gates):
        raise ContractError("experiment.hard_gates must be sorted")

    judges = experiment["advisory_judges"]
    if not isinstance(judges, list) or judges != sorted(judges):
        raise ContractError("experiment.advisory_judges must be a sorted list")
    overlap = sorted(set(gates) & set(judges))
    if overlap:
        raise ContractError(
            f"{overlap} are declared as both hard gate and advisory judge; a check "
            "that is deterministic in one column and a score in the other will be "
            "read as whichever is convenient"
        )
    return experiment
