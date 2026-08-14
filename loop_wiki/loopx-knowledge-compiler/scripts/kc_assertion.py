#!/usr/bin/env python3
"""Layer 2 -- assertion graph. What kind of claim it is, and how far it may rise.

A sentence in a notes file is a SOURCE_STATEMENT. It does not become a fact
because a model found it convincing, and it does not become a fact because a
scaffold was generated from it. The verification state is a separate axis from
the claim kind, and the ceiling below binds them:

    kind                 highest verification state reachable
    SOURCE_STATEMENT     VERIFIED_BY_EXECUTION   (someone ran it)
    INFERENCE            CORROBORATED            (never verified on its own)
    HYPOTHESIS           UNVERIFIED
    NORM                 ADMITTED_BY_HUMAN

An INFERENCE reaching VERIFIED_BY_EXECUTION would mean the compiler executed a
conclusion it drew itself. Whatever was executed was a statement; promote that,
and let the inference stay an inference.

Unknowns and contradictions are recorded, never resolved. An UNKNOWN carrying an
answer is the "filled from model memory" failure: the sources did not say, and
something wrote it down anyway.
"""

from __future__ import annotations

from typing import Any

from kc_common import (
    ContractError,
    exact_object,
    non_empty_str,
    require,
)
from kc_source import corroboration_count

CLAIM_KINDS = ("SOURCE_STATEMENT", "INFERENCE", "HYPOTHESIS", "NORM")

VERIFICATION_STATES = (
    "UNVERIFIED",
    "CORROBORATED",
    "VERIFIED_BY_EXECUTION",
    "ADMITTED_BY_HUMAN",
    "CONTRADICTED",
    "UNKNOWN",
)

# Rank only orders the three states that describe growing evidential strength.
# CONTRADICTED and UNKNOWN are not weak PASSes; they are different answers, and
# giving them a rank would let a max() quietly promote them.
_STRENGTH = {"UNVERIFIED": 0, "CORROBORATED": 1, "VERIFIED_BY_EXECUTION": 2}

CEILING = {
    "SOURCE_STATEMENT": "VERIFIED_BY_EXECUTION",
    "INFERENCE": "CORROBORATED",
    "HYPOTHESIS": "UNVERIFIED",
    "NORM": "ADMITTED_BY_HUMAN",
}

ASSERTION_KEYS = {
    "assertion_id",
    "kind",
    "text",
    "source_ids",
    "verification_state",
    "execution_receipt",
    "resolution",
}

GRAPH_KEYS = {"schema_version", "notes_subject", "assertions", "contradictions"}

CONTRADICTION_KEYS = {"contradiction_id", "assertion_ids", "state", "note"}


def validate_assertion(
    value: Any, label: str, sources_by_id: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    assertion = exact_object(value, ASSERTION_KEYS, label)
    non_empty_str(assertion["assertion_id"], f"{label}.assertion_id")
    non_empty_str(assertion["text"], f"{label}.text")

    kind = assertion["kind"]
    if kind not in CLAIM_KINDS:
        raise ContractError(f"{label}.kind must be one of {list(CLAIM_KINDS)}")

    state = assertion["verification_state"]
    if state not in VERIFICATION_STATES:
        raise ContractError(
            f"{label}.verification_state must be one of {list(VERIFICATION_STATES)}"
        )

    ids = assertion["source_ids"]
    if not isinstance(ids, list):
        raise ContractError(f"{label}.source_ids must be a list")
    if ids != sorted(ids):
        raise ContractError(f"{label}.source_ids must be sorted")
    for source_id in ids:
        if source_id not in sources_by_id:
            raise ContractError(
                f"{label} cites {source_id!r}, which is not in the source manifest; "
                "a citation to nothing is worse than no citation, because it reads "
                "as provenance"
            )

    if state == "UNKNOWN":
        if ids:
            raise ContractError(
                f"{label} is UNKNOWN but cites sources; if a source addressed it, it "
                "is not unknown"
            )
        if assertion["resolution"] is not None:
            raise ContractError(
                f"{label} is UNKNOWN but carries resolution="
                f"{assertion['resolution']!r}; the sources did not say, so whatever "
                "wrote that answer was not reading the sources"
            )
    elif not ids:
        raise ContractError(
            f"{label} has no source_ids and is not UNKNOWN; a claim with no source "
            "and no unknown marker entered from outside the notes"
        )

    ceiling = CEILING[kind]
    if state in _STRENGTH and _STRENGTH[state] > _STRENGTH.get(ceiling, -1):
        raise ContractError(
            f"{label} is a {kind} at {state}, above its ceiling {ceiling}; whatever "
            "was executed was a statement, not the conclusion drawn from it"
        )

    # Execution is a receipt or it did not happen. This is the "model prose
    # marked TESTED without execution" control.
    if state == "VERIFIED_BY_EXECUTION":
        receipt = assertion["execution_receipt"]
        if not isinstance(receipt, dict):
            raise ContractError(
                f"{label} claims VERIFIED_BY_EXECUTION with no execution receipt; "
                "prose asserting that something was tested is prose"
            )
        exact_object(
            receipt,
            {"command", "exit_code", "output_digest"},
            f"{label}.execution_receipt",
        )
        non_empty_str(receipt["command"], f"{label}.execution_receipt.command")
        if receipt["exit_code"] != 0:
            raise ContractError(
                f"{label} claims VERIFIED_BY_EXECUTION but its receipt exited "
                f"{receipt['exit_code']}; a run that failed verified nothing"
            )
    elif assertion["execution_receipt"] is not None:
        raise ContractError(
            f"{label} carries an execution receipt at state {state}; either the run "
            "supports the claim or it should not be attached to it"
        )
    return assertion


def validate_graph(
    value: Any, sources_by_id: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    graph = exact_object(value, GRAPH_KEYS, "assertion graph")
    require(
        graph["schema_version"] == "loopx/knowledge-assertion-graph/v1",
        "assertion graph schema version drifted",
    )

    assertions = graph["assertions"]
    if not isinstance(assertions, list) or not assertions:
        raise ContractError("assertion graph.assertions must be a non-empty list")

    seen: set[str] = set()
    for index, assertion in enumerate(assertions):
        validated = validate_assertion(assertion, f"assertions[{index}]", sources_by_id)
        if validated["assertion_id"] in seen:
            raise ContractError(f"duplicate assertion_id {validated['assertion_id']!r}")
        seen.add(validated["assertion_id"])

    contradictions = graph["contradictions"]
    if not isinstance(contradictions, list):
        raise ContractError("assertion graph.contradictions must be a list")
    for index, entry in enumerate(contradictions):
        label = f"contradictions[{index}]"
        record = exact_object(entry, CONTRADICTION_KEYS, label)
        non_empty_str(record["contradiction_id"], f"{label}.contradiction_id")
        ids = record["assertion_ids"]
        if not isinstance(ids, list) or len(ids) < 2:
            raise ContractError(f"{label}.assertion_ids must name at least two claims")
        if ids != sorted(ids):
            raise ContractError(f"{label}.assertion_ids must be sorted")
        for assertion_id in ids:
            if assertion_id not in seen:
                raise ContractError(f"{label} names unknown assertion {assertion_id!r}")
        # OPEN or ESCALATED only. A compiler may notice a contradiction; it may
        # not decide which side wins -- that is the "silently reconciled"
        # failure, and after it the losing claim is simply gone.
        if record["state"] not in {"OPEN", "ESCALATED_TO_HUMAN"}:
            raise ContractError(
                f"{label}.state must be OPEN or ESCALATED_TO_HUMAN, got "
                f"{record['state']!r}; a compiler that resolves a contradiction has "
                "deleted one side of it and nobody will see which"
            )

    # Every contradicted assertion must actually appear in a contradiction
    # record, or the graph says "contradicted" while showing nothing to compare.
    recorded = {aid for entry in contradictions for aid in entry["assertion_ids"]}
    for assertion in assertions:
        if assertion["verification_state"] == "CONTRADICTED" and (
            assertion["assertion_id"] not in recorded
        ):
            raise ContractError(
                f"assertion {assertion['assertion_id']!r} is CONTRADICTED but appears "
                "in no contradiction record; the claim it disagrees with is missing"
            )
    return graph


def confidence_ceiling(
    assertion: dict[str, Any], sources_by_id: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """How far this claim may rise, and on how much independent support."""
    cited = [sources_by_id[sid] for sid in assertion["source_ids"]]
    independent = corroboration_count(cited)
    return {
        "assertion_id": assertion["assertion_id"],
        "kind": assertion["kind"],
        "state": assertion["verification_state"],
        "kind_ceiling": CEILING[assertion["kind"]],
        "cited_source_count": len(cited),
        "independent_support": independent,
        # Stated rather than derived silently: CORROBORATED means two
        # independent dependency keys, and a claim that cites four notes all
        # descending from one upstream doc has one.
        "corroboration_satisfied": independent >= 2,
    }


def check_corroboration(
    graph: dict[str, Any], sources_by_id: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """CORROBORATED requires two independent sources, counted by dependency key."""
    ceilings = []
    for assertion in graph["assertions"]:
        ceiling = confidence_ceiling(assertion, sources_by_id)
        if (
            assertion["verification_state"] == "CORROBORATED"
            and not ceiling["corroboration_satisfied"]
        ):
            raise ContractError(
                f"assertion {assertion['assertion_id']!r} is CORROBORATED on "
                f"{ceiling['cited_source_count']} citations but only "
                f"{ceiling['independent_support']} independent source; sources "
                "sharing a dependency key are one piece of evidence quoted twice"
            )
        ceilings.append(ceiling)
    return ceilings
