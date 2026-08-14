#!/usr/bin/env python3
"""Layer 4 -- System Spec IR. Components, and the acceptance cases behind them.

The failure this layer exists to catch is compression. Three notes describing
three distinct situations become one requirement -- "handle errors" -- and the
two cases that were folded in are now untestable, because nothing records that
they were ever separate. The scaffold that follows will have one code path and
look complete.

So every requirement lists `derived_from_assertions`, and a requirement derived
from more than one assertion must list one acceptance case per assertion. If the
cases really are the same case, that is a claim someone can look at and dispute.
Rendering them as one silently is not.
"""

from __future__ import annotations

from typing import Any

from kc_common import (
    ContractError,
    exact_object,
    non_empty_str,
    require,
)

SPEC_KEYS = {
    "schema_version",
    "notes_subject",
    "components",
    "requirements",
    "open_unknowns",
}

COMPONENT_KEYS = {
    "component_id",
    "boundary",
    "inputs",
    "outputs",
    "effects",
    "authority",
    "invariants",
    "failure_modes",
    "rollback",
}

REQUIREMENT_KEYS = {
    "requirement_id",
    "component_id",
    "statement",
    "derived_from_assertions",
    "derived_from_cards",
    "acceptance_cases",
}

ACCEPTANCE_KEYS = {"case_id", "given", "expect", "assertion_id"}

AUTHORITIES = {"OBSERVATION_ONLY", "PROPOSES", "DECIDES_WITH_HUMAN_ADMIT"}


def validate_component(value: Any, label: str) -> dict[str, Any]:
    component = exact_object(value, COMPONENT_KEYS, label)
    non_empty_str(component["component_id"], f"{label}.component_id")
    non_empty_str(component["boundary"], f"{label}.boundary")

    for field in ("inputs", "outputs", "effects", "invariants", "failure_modes"):
        if not isinstance(component[field], list):
            raise ContractError(f"{label}.{field} must be a list")
    if not component["invariants"]:
        raise ContractError(
            f"{label} declares no invariants; a component with nothing that must "
            "hold has nothing a test could check"
        )
    if not component["failure_modes"]:
        raise ContractError(
            f"{label} declares no failure modes; every component in this repository "
            "has at least the one where its input is absent"
        )
    if component["authority"] not in AUTHORITIES:
        raise ContractError(f"{label}.authority must be one of {sorted(AUTHORITIES)}")
    # Effects without rollback is the shape that cannot be undone after a bad
    # admit, so the spec has to say what undoes it before code is planned.
    if component["effects"] and not component["rollback"]:
        raise ContractError(
            f"{label} declares effects {component['effects']} but no rollback; an "
            "effect nobody can reverse is a one-way door drawn as a component"
        )
    return component


def validate_spec(
    value: Any, assertions_by_id: dict[str, Any], card_keys: set[str]
) -> dict[str, Any]:
    spec = exact_object(value, SPEC_KEYS, "system spec")
    require(
        spec["schema_version"] == "loopx/knowledge-system-spec/v1",
        "system spec schema version drifted",
    )

    components = spec["components"]
    if not isinstance(components, list) or not components:
        raise ContractError("system spec.components must be a non-empty list")
    component_ids = set()
    for index, component in enumerate(components):
        validated = validate_component(component, f"components[{index}]")
        component_ids.add(validated["component_id"])

    requirements = spec["requirements"]
    if not isinstance(requirements, list) or not requirements:
        raise ContractError("system spec.requirements must be a non-empty list")

    for index, value_ in enumerate(requirements):
        label = f"requirements[{index}]"
        requirement = exact_object(value_, REQUIREMENT_KEYS, label)
        non_empty_str(requirement["requirement_id"], f"{label}.requirement_id")
        non_empty_str(requirement["statement"], f"{label}.statement")
        if requirement["component_id"] not in component_ids:
            raise ContractError(
                f"{label} targets unknown component {requirement['component_id']!r}"
            )

        derived = requirement["derived_from_assertions"]
        if not isinstance(derived, list) or not derived:
            raise ContractError(
                f"{label} is derived from no assertion; a requirement with no source "
                "came from the compiler's own prior, not from the notes"
            )
        if derived != sorted(derived):
            raise ContractError(f"{label}.derived_from_assertions must be sorted")
        for assertion_id in derived:
            if assertion_id not in assertions_by_id:
                raise ContractError(f"{label} cites unknown assertion {assertion_id!r}")
            state = assertions_by_id[assertion_id]["verification_state"]
            if state == "UNKNOWN":
                raise ContractError(
                    f"{label} is derived from UNKNOWN assertion {assertion_id!r}; "
                    "building a requirement on an unknown answers it by implication"
                )

        for card_key in requirement["derived_from_cards"]:
            if card_key not in card_keys:
                raise ContractError(f"{label} cites unknown card {card_key!r}")

        cases = requirement["acceptance_cases"]
        if not isinstance(cases, list) or not cases:
            raise ContractError(f"{label} has no acceptance cases")

        covered = []
        for case_index, case_value in enumerate(cases):
            case_label = f"{label}.acceptance_cases[{case_index}]"
            case = exact_object(case_value, ACCEPTANCE_KEYS, case_label)
            non_empty_str(case["case_id"], f"{case_label}.case_id")
            non_empty_str(case["given"], f"{case_label}.given")
            non_empty_str(case["expect"], f"{case_label}.expect")
            if case["assertion_id"] not in derived:
                raise ContractError(
                    f"{case_label} covers {case['assertion_id']!r}, which this "
                    "requirement is not derived from"
                )
            covered.append(case["assertion_id"])

        # The compression control. n independent assertions, n cases -- or the
        # collapse is visible in the diff instead of invisible in the scaffold.
        missing = sorted(set(derived) - set(covered))
        if missing:
            raise ContractError(
                f"{label} folds {len(derived)} independent assertions into "
                f"{len(set(covered))} acceptance case(s); {missing} would have no "
                "case of their own, and the situations they describe become "
                "untestable the moment the scaffold renders one code path"
            )

    unknowns = spec["open_unknowns"]
    if not isinstance(unknowns, list):
        raise ContractError("system spec.open_unknowns must be a list")
    if unknowns != sorted(unknowns):
        raise ContractError("system spec.open_unknowns must be sorted")

    # Every UNKNOWN in the graph must be carried forward. An unknown that is
    # neither listed nor cited has been dropped, and a dropped unknown reads
    # downstream as a question nobody had.
    declared = {
        assertion_id
        for assertion_id, assertion in assertions_by_id.items()
        if assertion["verification_state"] == "UNKNOWN"
    }
    lost = sorted(declared - set(unknowns))
    if lost:
        raise ContractError(
            f"unknown assertions {lost} are not carried into system spec"
            ".open_unknowns; an unknown that stops being visible has been answered "
            "by omission"
        )
    return spec
