#!/usr/bin/env python3
"""The Prompt IR, the stable prefix, and the bounded suffix.

One IR, six projections. The split that matters is not stylistic:

    prefix   system law, Skill identity, ordered tool schemas
    suffix   the current Todo, the evidence, the admitted memory

The prefix is what a prompt cache keys on, byte for byte. Anything in it that
varies between requests turns every request into a miss -- and nothing errors,
nothing warns, and the only symptom is the bill. So `render_prefix` scans its own
output for volatile patterns and refuses, rather than trusting that the fields it
was given are stable.

Tool order is canonicalised and digested together with the schemas. Reordering
tools changes the prefix bytes, so it changes the cache key; without a digest
that moves with it, the reorder is invisible in review and expensive in
production.

The suffix has a budget, and overflow is *reported*. An evidence anchor dropped
silently is the failure that turns a cited claim into an uncited one, and the
claim still reads as cited.
"""

from __future__ import annotations

from typing import Any

from ca_common import (
    NORMATIVE_CLOSE,
    NORMATIVE_OPEN,
    ContractError,
    digest,
    find_forbidden,
    find_volatile,
    non_empty_str,
    positive_int,
    require,
    text_digest,
)

IR_KEYS = {
    "schema_version",
    "system_law",
    "skill_identity",
    "tools",
    "dynamic",
    "budget",
}

TOOL_KEYS = {"name", "description", "schema_digest"}

DYNAMIC_KEYS = {"todo", "evidence_anchors", "admitted_memory"}

BUDGET_KEYS = {"max_bytes", "max_items"}

# Suffix sections in the order they are rendered, and the order they are dropped
# in when the budget runs out -- last first. Evidence anchors are never dropped;
# see trim().
SUFFIX_ORDER = ("evidence_anchors", "todo", "admitted_memory")


def validate_tool(value: Any, label: str) -> dict[str, Any]:
    tool = exact_tool(value, label)
    non_empty_str(tool["name"], f"{label}.name")
    non_empty_str(tool["description"], f"{label}.description")
    non_empty_str(tool["schema_digest"], f"{label}.schema_digest")
    return tool


def exact_tool(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != TOOL_KEYS:
        raise ContractError(f"{label} fields drifted; expected {sorted(TOOL_KEYS)}")
    return value


def validate_ir(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != IR_KEYS:
        missing = sorted(IR_KEYS - set(value or {}))
        extra = sorted(set(value or {}) - IR_KEYS)
        raise ContractError(f"IR fields drifted; missing={missing}, extra={extra}")
    require(
        value["schema_version"] == "loopx/prompt-ir/v1", "IR schema version drifted"
    )
    non_empty_str(value["system_law"], "ir.system_law")
    non_empty_str(value["skill_identity"], "ir.skill_identity")

    tools = value["tools"]
    if not isinstance(tools, list) or not tools:
        raise ContractError("ir.tools must be a non-empty list")
    names = [
        validate_tool(tool, f"ir.tools[{index}]")["name"]
        for index, tool in enumerate(tools)
    ]
    if len(names) != len(set(names)):
        raise ContractError("ir.tools has duplicate names")

    dynamic = value["dynamic"]
    if not isinstance(dynamic, dict) or set(dynamic) != DYNAMIC_KEYS:
        raise ContractError(
            f"ir.dynamic fields drifted; expected {sorted(DYNAMIC_KEYS)}"
        )
    for key in DYNAMIC_KEYS:
        if not isinstance(dynamic[key], list):
            raise ContractError(f"ir.dynamic.{key} must be a list")

    budget = value["budget"]
    if not isinstance(budget, dict) or set(budget) != BUDGET_KEYS:
        raise ContractError(f"ir.budget fields drifted; expected {sorted(BUDGET_KEYS)}")
    positive_int(budget["max_bytes"], "ir.budget.max_bytes")
    positive_int(budget["max_items"], "ir.budget.max_items")
    return value


def canonical_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One order, always. Sorted by name so the prefix bytes cannot drift."""
    return sorted(tools, key=lambda tool: tool["name"])


def tool_order_digest(tools: list[dict[str, Any]]) -> str:
    """Digest over the order and the schemas together.

    Both, because they fail together: reordering changes the prefix bytes and so
    the cache key, and a schema change with the same order is the same problem
    from the other direction.
    """
    return digest(
        [
            {"name": tool["name"], "schema_digest": tool["schema_digest"]}
            for tool in canonical_tools(tools)
        ]
    )


def render_prefix(ir: dict[str, Any]) -> dict[str, Any]:
    """The cacheable prefix. Refuses to contain anything that varies."""
    validate_ir(ir)
    tools = canonical_tools(ir["tools"])

    lines = [
        NORMATIVE_OPEN,
        ir["system_law"].strip(),
        NORMATIVE_CLOSE,
        "",
        f"# Skill: {ir['skill_identity']}",
        "",
        "## Tools",
        "",
    ]
    for tool in tools:
        lines.append(
            f"- `{tool['name']}` — {tool['description']} [{tool['schema_digest']}]"
        )
    text = "\n".join(lines) + "\n"

    volatile = find_volatile(text)
    if volatile:
        raise ContractError(
            f"the stable prefix contains {volatile}. A prompt cache keys on the prefix "
            "byte for byte: one value that varies turns every request into a miss, "
            "and nothing errors -- the only symptom is the bill"
        )
    forbidden = find_forbidden(text)
    if forbidden:
        raise ContractError(
            f"the stable prefix contains {forbidden}; a prompt projection is written "
            "to disk, attached to receipts and read by every later session"
        )

    return {
        "text": text,
        "prefix_digest": text_digest(text),
        "tool_order_digest": tool_order_digest(tools),
        "tool_names": [tool["name"] for tool in tools],
    }


def trim(ir: dict[str, Any]) -> dict[str, Any]:
    """Fit the dynamic sections into the budget, and say what did not fit.

    Evidence anchors are never dropped. A claim whose anchor was trimmed still
    reads as cited, and the citation is the part a reader checks -- so when the
    anchors alone exceed the budget the assembler refuses rather than choosing
    which evidence to lose.
    """
    validate_ir(ir)
    dynamic = ir["dynamic"]
    budget = ir["budget"]

    anchors = dynamic["evidence_anchors"]
    anchor_bytes = len("\n".join(map(str, anchors)).encode("utf-8"))
    if anchor_bytes > budget["max_bytes"]:
        raise ContractError(
            f"the evidence anchors alone are {anchor_bytes} bytes against a "
            f"{budget['max_bytes']} budget. Dropping one would leave a claim that "
            "still reads as cited, so the budget has to grow or the task has to shrink"
        )

    kept: dict[str, list[Any]] = {"evidence_anchors": list(anchors)}
    dropped: dict[str, int] = {}
    used = anchor_bytes
    items = len(anchors)

    for section in SUFFIX_ORDER[1:]:
        kept[section] = []
        for entry in dynamic[section]:
            size = len(str(entry).encode("utf-8")) + 1
            if used + size > budget["max_bytes"] or items + 1 > budget["max_items"]:
                dropped[section] = dropped.get(section, 0) + 1
                continue
            kept[section].append(entry)
            used += size
            items += 1

    return {
        "kept": kept,
        "dropped": dropped,
        "bytes_used": used,
        "items_used": items,
        "budget": dict(budget),
        # Both numbers on the record. A suffix that fit and a suffix that was cut
        # to fit are different situations, and they render identically.
        "complete": not dropped,
        "evidence_anchors_dropped": 0,
    }


def render_suffix(ir: dict[str, Any]) -> dict[str, Any]:
    """The bounded dynamic suffix, with its overflow recorded."""
    fitted = trim(ir)
    kept = fitted["kept"]
    lines: list[str] = ["## Evidence", ""]
    lines += [f"- {anchor}" for anchor in kept["evidence_anchors"]]
    lines += ["", "## Todo", ""]
    lines += [f"- {entry}" for entry in kept["todo"]]
    lines += ["", "## Admitted memory", ""]
    lines += [f"- {entry}" for entry in kept["admitted_memory"]]
    if fitted["dropped"]:
        lines += [
            "",
            "> Budget reached. Dropped: "
            + ", ".join(
                f"{count} {name}" for name, count in sorted(fitted["dropped"].items())
            )
            + ". No evidence anchor was dropped.",
        ]
    text = "\n".join(lines) + "\n"

    forbidden = find_forbidden(text)
    if forbidden:
        raise ContractError(f"the dynamic suffix contains {forbidden}")

    return {
        "text": text,
        "suffix_digest": text_digest(text),
        "budget_report": fitted,
    }
