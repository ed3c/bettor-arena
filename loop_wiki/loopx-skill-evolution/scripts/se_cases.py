#!/usr/bin/env python3
"""Case sets, and the mechanical separation between a runner and the answers.

`runner_payload` is the whole idea. The function that builds what an arm sees
constructs a fresh object with an explicit field list, rather than copying a
case and deleting the answer. Deletion is a step someone can forget; construction
from a whitelist has no equivalent step to forget, and a new field added to a
case later does not silently reach the runner.

`scan_payload_for_leaks` is the check on top: the built payload is serialised
and searched for every sealed answer string. It is deliberately redundant with
the construction above, because the two fail differently -- construction protects
against forgetting to strip, and the scan protects against an answer that ended
up inside a field the whitelist does allow.
"""

from __future__ import annotations

from typing import Any

from se_common import (
    ContractError,
    canonical_bytes,
    digest,
    exact_object,
    non_empty_str,
    seal,
)

CASE_KEYS = {"case_id", "kind", "prompt", "inputs", "expected", "hard_gate_ids"}

CASE_KINDS = {"DEV", "HOLDOUT", "MUTATION"}

# What an arm is allowed to see. `expected` is not here, and neither is
# `hard_gate_ids` -- knowing which gates will be applied is itself a hint.
RUNNER_VISIBLE_FIELDS = ("case_id", "kind", "prompt", "inputs")


def validate_case(value: Any, label: str) -> dict[str, Any]:
    case = exact_object(value, CASE_KEYS, label)
    non_empty_str(case["case_id"], f"{label}.case_id")
    non_empty_str(case["prompt"], f"{label}.prompt")
    if case["kind"] not in CASE_KINDS:
        raise ContractError(f"{label}.kind must be one of {sorted(CASE_KINDS)}")
    if not isinstance(case["inputs"], dict):
        raise ContractError(f"{label}.inputs must be an object")
    non_empty_str(case["expected"], f"{label}.expected")
    gates = case["hard_gate_ids"]
    if not isinstance(gates, list) or not gates or gates != sorted(gates):
        raise ContractError(
            f"{label}.hard_gate_ids must be a sorted non-empty list; a case with no "
            "deterministic gate can only be scored by the judge, and the judge is "
            "advisory"
        )
    return case


def validate_case_set(value: Any, label: str, kind: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ContractError(f"{label} must be a non-empty list")
    seen: set[str] = set()
    for index, case in enumerate(value):
        checked = validate_case(case, f"{label}[{index}]")
        if checked["kind"] != kind:
            raise ContractError(
                f"{label}[{index}] is a {checked['kind']} case in the {kind} set; a "
                "holdout case sitting in the dev set has been seen, and it is a "
                "holdout in name only"
            )
        if checked["case_id"] in seen:
            raise ContractError(f"duplicate case_id {checked['case_id']!r} in {label}")
        seen.add(checked["case_id"])
    return value


def case_set_digest(cases: list[dict[str, Any]]) -> str:
    return digest(sorted(cases, key=lambda case: case["case_id"]))


def holdout_seal(cases: list[dict[str, Any]]) -> str:
    """Commit to the holdout answers before the run."""
    return seal(
        sorted(
            ({"case_id": c["case_id"], "expected": c["expected"]} for c in cases),
            key=lambda entry: entry["case_id"],
        )
    )


def runner_payload(case: dict[str, Any]) -> dict[str, Any]:
    """What an arm sees. Built from a whitelist, never stripped from the case."""
    return {field: case[field] for field in RUNNER_VISIBLE_FIELDS}


def scan_payload_for_leaks(payload: Any, cases: list[dict[str, Any]]) -> list[str]:
    """Case ids whose answer appears somewhere in what the runner receives.

    Redundant with `runner_payload` on purpose: construction protects against
    forgetting to strip a field, and this protects against an answer that ended
    up inside a field the whitelist allows -- an example embedded in a prompt,
    say, which no field-level rule would ever notice.
    """
    blob = canonical_bytes(payload).decode("utf-8")
    return sorted(
        case["case_id"]
        for case in cases
        if case["expected"] and case["expected"] in blob
    )


def build_run_input(
    cases: list[dict[str, Any]], all_answers: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Payloads for a whole case set, refusing if any answer is reachable."""
    payloads = [runner_payload(case) for case in cases]
    leaked = scan_payload_for_leaks(payloads, all_answers)
    if leaked:
        raise ContractError(
            f"the runner payload contains the expected answer for {leaked}; whatever "
            "the field-level separation says, the answer is reachable, and a score "
            "measured against it is a score for reading"
        )
    return payloads
