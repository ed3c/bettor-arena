#!/usr/bin/env python3
"""The assembly pass, in the order #95 names.

    PROMPT_IR_SUBJECT_PINNED
    -> STATIC_PREFIX_FRAGMENTS_RESOLVED
    -> TOOL_SCHEMA_ORDER_CANONICALIZED
    -> TASK_RELEVANT_KNOWLEDGE_SELECTED
    -> HOT_WARM_MEMORY_BUDGETED
    -> DYNAMIC_SUFFIX_RENDERED
    -> HOST_PROJECTION_EMITTED
    -> PREFIX_SUFFIX_DIGESTS_RECORDED
    -> CACHE_CONTEXT_RECEIPT
    -> REGRESSION_EVAL

The prefix is rendered once and reused across all six projections. Rendering it
per host would let one renderer's wrapper leak into the cached region, which is
the difference between a cache that works and a cache that looks like it does.
"""

from __future__ import annotations

from typing import Any

from ca_common import ContractError, digest
from ca_ir import render_prefix, render_suffix, tool_order_digest, validate_ir
from ca_project import HOSTS, law_matrix, project, require_law_agreement

STATES = [
    "PROMPT_IR_SUBJECT_PINNED",
    "STATIC_PREFIX_FRAGMENTS_RESOLVED",
    "TOOL_SCHEMA_ORDER_CANONICALIZED",
    "TASK_RELEVANT_KNOWLEDGE_SELECTED",
    "HOT_WARM_MEMORY_BUDGETED",
    "DYNAMIC_SUFFIX_RENDERED",
    "HOST_PROJECTION_EMITTED",
    "PREFIX_SUFFIX_DIGESTS_RECORDED",
    "CACHE_CONTEXT_RECEIPT",
    "REGRESSION_EVAL",
]


def assemble(ir: dict[str, Any], hosts: list[str] | None = None) -> dict[str, Any]:
    """Assemble every projection from one IR. Deterministic in its input."""
    trace = ["PROMPT_IR_SUBJECT_PINNED"]
    validate_ir(ir)

    # Rendered once, shared by every host. Per-host rendering would let a
    # wrapper leak into the cached region.
    prefix = render_prefix(ir)
    trace.append("STATIC_PREFIX_FRAGMENTS_RESOLVED")
    trace.append("TOOL_SCHEMA_ORDER_CANONICALIZED")
    trace.append("TASK_RELEVANT_KNOWLEDGE_SELECTED")

    suffix = render_suffix(ir)
    trace.append("HOT_WARM_MEMORY_BUDGETED")
    trace.append("DYNAMIC_SUFFIX_RENDERED")

    targets = sorted(hosts or HOSTS)
    projections = [project(host, prefix, suffix) for host in targets]
    trace.append("HOST_PROJECTION_EMITTED")
    trace.append("PREFIX_SUFFIX_DIGESTS_RECORDED")

    matrix = law_matrix(projections)
    require_law_agreement(matrix)
    trace.append("CACHE_CONTEXT_RECEIPT")
    trace.append("REGRESSION_EVAL")

    return {
        "state_trace": trace,
        "prefix": prefix,
        "suffix": suffix,
        "projections": projections,
        "law_matrix": matrix,
        "tool_order_digest": tool_order_digest(ir["tools"]),
        # One number a caller can compare across runs without reading anything.
        "assembly_digest": digest(
            {
                "prefix": prefix["prefix_digest"],
                "suffix": suffix["suffix_digest"],
                "projections": [p["projection_digest"] for p in projections],
            }
        ),
    }


def require_prefix_stable(first: dict[str, Any], second: dict[str, Any]) -> None:
    """Two assemblies of one IR must produce the same prefix bytes."""
    if first["prefix"]["prefix_digest"] != second["prefix"]["prefix_digest"]:
        raise ContractError(
            "two assemblies of one IR produced different prefixes. Every request "
            "would be a cache miss, and nothing would error -- the only symptom is "
            "the bill"
        )
