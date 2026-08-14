#!/usr/bin/env python3
"""The forward pass. Pinned notes subject in, candidate receipt out.

The state machine #70 names, in order, with each transition refusing rather than
repairing:

    NOTES_SUBJECT_PINNED
    -> SOURCE_INVENTORY
    -> ASSERTIONS_COMPILED
    -> CONFLICTS/UNKNOWNS_SCHEDULED
    -> CARDS_COMPILED
    -> SYSTEM_SPEC_EMITTED
    -> CODEOPS_PLANNED
    -> SCAFFOLD_RENDERED_IN_DISPOSABLE_TREE
    -> STATIC/TEST GATES
    -> CANDIDATE_RECEIPT
    -> HUMAN ADMIT OR REVISE

The last transition is not in this file, and that is the point. Compile stops at
CANDIDATE_RECEIPT.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kc_assertion import check_corroboration, validate_graph
from kc_card import compile_cards, validate_card_graph
from kc_codeop import uncovered_requirements, validate_plan
from kc_common import ContractError, digest
from kc_scaffold import emit_receipt, render
from kc_source import validate_manifest
from kc_spec import validate_spec

STATES = [
    "NOTES_SUBJECT_PINNED",
    "SOURCE_INVENTORY",
    "ASSERTIONS_COMPILED",
    "CONFLICTS_UNKNOWNS_SCHEDULED",
    "CARDS_COMPILED",
    "SYSTEM_SPEC_EMITTED",
    "CODEOPS_PLANNED",
    "SCAFFOLD_RENDERED_IN_DISPOSABLE_TREE",
    "STATIC_TEST_GATES",
    "CANDIDATE_RECEIPT",
]


def compile_subject(
    manifest: dict[str, Any],
    graph: dict[str, Any],
    grouping: dict[str, dict[str, str]],
    spec: dict[str, Any],
    plan: dict[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    """Run the forward half once. Deterministic given its inputs."""
    trace = ["NOTES_SUBJECT_PINNED"]

    manifest = validate_manifest(manifest)
    sources_by_id = {s["source_id"]: s for s in manifest["sources"]}
    trace.append("SOURCE_INVENTORY")

    graph = validate_graph(graph, sources_by_id)
    ceilings = check_corroboration(graph, sources_by_id)
    trace.append("ASSERTIONS_COMPILED")

    # Every subject is compiled against one notes subject. Two layers pinned to
    # different commits would let a spec cite assertions from a tree the source
    # manifest never saw.
    for name, layer in (
        ("assertion graph", graph),
        ("system spec", spec),
        ("codeop plan", plan),
    ):
        if layer.get("notes_subject") != manifest["notes_subject"]:
            raise ContractError(
                f"{name} is pinned to a different notes subject than the source "
                "manifest; layers compiled from two trees cannot be traced to one"
            )

    open_unknowns = sorted(
        a["assertion_id"]
        for a in graph["assertions"]
        if a["verification_state"] == "UNKNOWN"
    )
    open_contradictions = sorted(c["contradiction_id"] for c in graph["contradictions"])
    trace.append("CONFLICTS_UNKNOWNS_SCHEDULED")

    cards = compile_cards(graph["assertions"], graph["contradictions"], grouping)
    card_graph = {
        "schema_version": "loopx/knowledge-card-graph/v1",
        "notes_subject": manifest["notes_subject"],
        "cards": cards,
    }
    validate_card_graph(card_graph)
    trace.append("CARDS_COMPILED")

    assertions_by_id = {a["assertion_id"]: a for a in graph["assertions"]}
    spec = validate_spec(spec, assertions_by_id, {c["canonical_key"] for c in cards})
    trace.append("SYSTEM_SPEC_EMITTED")

    requirement_ids = {r["requirement_id"] for r in spec["requirements"]}
    plan = validate_plan(plan, requirement_ids)
    trace.append("CODEOPS_PLANNED")

    rendered = render(plan, spec, output_root)
    trace.append("SCAFFOLD_RENDERED_IN_DISPOSABLE_TREE")

    gates = [
        {
            "name": "contract-shapes",
            "state": "PASS",
            "detail": "every layer validated against its schema",
        },
        {
            "name": "provenance-reachable",
            "state": "PASS",
            "detail": "every planned operation traces to an assertion and a locator",
        },
        {
            # Named rather than omitted. This leaf renders a candidate; it does
            # not execute the generated code, and a receipt that left this out
            # would read as though it had.
            "name": "generated-tests-executed",
            "state": "NOT_EXERCISED",
            "detail": (
                "the candidate scaffold is not executed by the compiler; running it "
                "is part of applying it, which is Human Admit"
            ),
        },
    ]
    trace.append("STATIC_TEST_GATES")

    receipt = emit_receipt(
        manifest["notes_subject"],
        manifest["compiler_identity"],
        plan,
        rendered,
        gates,
        {
            "open_unknowns": open_unknowns,
            "open_contradictions": open_contradictions,
            "uncovered_requirements": uncovered_requirements(plan, requirement_ids),
        },
    )
    trace.append("CANDIDATE_RECEIPT")

    return {
        "state_trace": trace,
        "card_graph": card_graph,
        "confidence_ceilings": ceilings,
        "receipt": receipt,
        # The idempotence handle. Two compiles of the same subject are compared
        # on this, not on wall-clock or on the receipt's file mtimes.
        "compile_digest": digest(
            {"cards": cards, "scaffold": rendered, "unresolved": receipt["unresolved"]}
        ),
    }
