#!/usr/bin/env python3
"""Positive properties, and one planted control per named failure.

Every control asserts on the substring its own rule raises. A control that only
checks "something was refused" passes when a different guard fires first, which
makes it a control over nothing -- and it stays green while the rule it was
written for is deleted.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable

from ca_common import SAMPLE_HOST_PATH, ContractError, normative_region
from ca_ir import canonical_tools, render_prefix, render_suffix, tool_order_digest, trim
from ca_pipeline import assemble, require_prefix_stable
from ca_project import (
    HOSTS,
    cache_observation,
    law_matrix,
    project,
    require_law_agreement,
    require_same_environment,
)

LAW = (
    "An agent proposes; a human admits. No gate verdict is written by a model.\n"
    "Generated files are rendered, never hand-edited.\n"
    "ABSENT, NOT_IMPLEMENTED and NOT_EXERCISED are never promoted to PASS."
)

IR: dict[str, Any] = {
    "schema_version": "loopx/prompt-ir/v1",
    "system_law": LAW,
    "skill_identity": "repository-procedure@1.4.0",
    "tools": [
        {"name": "Read", "description": "read a file", "schema_digest": "sha256:a1"},
        {"name": "Bash", "description": "run a command", "schema_digest": "sha256:b2"},
        {"name": "Edit", "description": "edit a file", "schema_digest": "sha256:c3"},
        {"name": "Grep", "description": "search a tree", "schema_digest": "sha256:d4"},
    ],
    "dynamic": {
        "todo": ["land the context assembler", "advance the terminal queue"],
        "evidence_anchors": [
            "ev-0001 loop_wiki/loopx-context-assembly/scripts/ca_ir.py#L130-L168",
            "ev-0002 loop_wiki/loopx-context-assembly/scripts/ca_project.py#L70-L106",
        ],
        "admitted_memory": [
            "memory-1f2e: generated projections are rendered before every push",
            "memory-77ab: a cache hit rate is scoped to one host, model and provider",
        ],
    },
    "budget": {"max_bytes": 4096, "max_items": 32},
}


def _ir(**overrides: Any) -> dict[str, Any]:
    value = copy.deepcopy(IR)
    value.update(copy.deepcopy(overrides))
    return value


def _dynamic(**overrides: Any) -> dict[str, Any]:
    value = copy.deepcopy(IR)
    value["dynamic"].update(copy.deepcopy(overrides))
    return value


def control(label: str, expect: str, action: Callable[[], Any]) -> None:
    """Run an action that must be refused, and check *which* rule refused it."""
    try:
        action()
    except ContractError as exc:
        if expect not in str(exc):
            raise ContractError(
                f"control {label!r} was refused, but by a different rule: {exc}. A "
                f"control that only checks 'something was refused' passes when a "
                f"neighbouring guard fires and stays green while its own rule is deleted"
            ) from exc
        return
    raise ContractError(f"control {label!r} was not refused")


def positive_properties() -> int:
    checks = 0

    result = assemble(IR)
    if result["state_trace"][-1] != "REGRESSION_EVAL":
        raise ContractError("the assembly did not reach REGRESSION_EVAL")
    checks += 1

    if [p["host"] for p in result["projections"]] != sorted(HOSTS):
        raise ContractError("one IR did not render all six host projections")
    checks += 1

    # The law survives every wrapper.
    laws = {normative_region(p["text"], p["host"]) for p in result["projections"]}
    if len(laws) != 1 or laws.pop().strip() != LAW:
        raise ContractError("a projection changed the normative law")
    checks += 1

    if result["law_matrix"]["distinct_law_digests"] != 1:
        raise ContractError("the law matrix reported divergence on an agreeing set")
    checks += 1

    # Presentation does differ -- otherwise the comparison above proves nothing.
    if len({p["projection_digest"] for p in result["projections"]}) != len(HOSTS):
        raise ContractError(
            "the six projections are byte-identical, so the law comparison would "
            "hold even if a renderer edited the law"
        )
    checks += 1

    if [t["name"] for t in canonical_tools(IR["tools"])] != [
        "Bash",
        "Edit",
        "Grep",
        "Read",
    ]:
        raise ContractError("tool order is not canonical")
    checks += 1

    # Order is part of the prefix bytes, so it must move the digest.
    reordered = _ir(tools=list(reversed(IR["tools"])))
    if tool_order_digest(reordered["tools"]) != tool_order_digest(IR["tools"]):
        raise ContractError("canonicalisation did not absorb a caller's tool order")
    if render_prefix(reordered)["prefix_digest"] != render_prefix(IR)["prefix_digest"]:
        raise ContractError("a caller's tool order leaked into the cached prefix")
    checks += 1

    # A schema change with the same order is the same problem from the other side.
    changed = copy.deepcopy(IR)
    changed["tools"][0]["schema_digest"] = "sha256:ff"
    if tool_order_digest(changed["tools"]) == tool_order_digest(IR["tools"]):
        raise ContractError("a tool schema change did not move the order digest")
    checks += 1

    require_prefix_stable(result, assemble(IR))
    checks += 1

    if not result["suffix"]["budget_report"]["complete"]:
        raise ContractError("a suffix inside its budget reported as trimmed")
    checks += 1

    # Under a budget that cannot hold everything, anchors survive and the drop is
    # named. A silent trim is the failure this section exists for.
    tight = _ir(budget={"max_bytes": 260, "max_items": 32})
    report = render_suffix(tight)["budget_report"]
    if report["complete"] or not report["dropped"]:
        raise ContractError("a trimmed suffix reported as complete")
    if report["evidence_anchors_dropped"] != 0:
        raise ContractError("an evidence anchor was dropped to fit the budget")
    if len(report["kept"]["evidence_anchors"]) != len(
        IR["dynamic"]["evidence_anchors"]
    ):
        raise ContractError("the budget lost an evidence anchor")
    checks += 1

    if "No evidence anchor was dropped" not in render_suffix(tight)["text"]:
        raise ContractError("the trimmed suffix did not say what it dropped")
    checks += 1

    observation = cache_observation(
        {
            "host": "claude",
            "model": "opus-5",
            "provider": "anthropic",
            "prefix_digest": result["prefix"]["prefix_digest"],
            "hits": 17,
            "misses": 3,
        }
    )
    if (
        observation["universal_claim"]
        or observation["applies_to"] != "SINGLE_HOST_MODEL_PROVIDER"
    ):
        raise ContractError("a cache observation was recorded as a universal claim")
    require_same_environment(observation, "claude", "opus-5", "anthropic")
    checks += 1

    # A host subset is not an agreement -- see the missing-host control below.
    subset = assemble(IR, hosts=list(HOSTS))
    if subset["law_matrix"]["missing_hosts"]:
        raise ContractError("a full projection reported missing hosts")
    checks += 1

    if trim(IR)["kept"]["evidence_anchors"] != IR["dynamic"]["evidence_anchors"]:
        raise ContractError("trim reordered or altered the evidence anchors")
    checks += 1

    return checks


def controls() -> int:
    prefix = render_prefix(IR)
    suffix = render_suffix(IR)
    good = [project(host, prefix, suffix) for host in HOSTS]

    def diverged() -> list[dict[str, Any]]:
        # One renderer softened one line of the law. The projections still render,
        # still validate, and now say different things.
        other = copy.deepcopy(good)
        edited = _ir(system_law=LAW.replace("never hand-edited", "rarely hand-edited"))
        other[3] = project("grok-build", render_prefix(edited), suffix)
        return other

    cases: list[tuple[str, str, Callable[[], Any]]] = [
        (
            "timestamp in the cacheable prefix",
            "only symptom is the bill",
            lambda: render_prefix(
                _ir(skill_identity="procedure@1.4.0 built 2026-08-16T09:30")
            ),
        ),
        (
            "run id in the cacheable prefix",
            "only symptom is the bill",
            lambda: render_prefix(_ir(system_law=LAW + "\nrun_id is carried forward.")),
        ),
        (
            "private reasoning in the prefix",
            "read by every later session",
            lambda: render_prefix(
                _ir(system_law=LAW + "\nEmit your chain-of-thought.")
            ),
        ),
        (
            "host path in the suffix",
            "the dynamic suffix contains",
            lambda: render_suffix(_dynamic(todo=[f"read {SAMPLE_HOST_PATH}"])),
        ),
        (
            "credential in the suffix",
            "the dynamic suffix contains",
            lambda: render_suffix(_dynamic(admitted_memory=["api_key=sk-live-0"])),
        ),
        (
            "text edited after it was scanned",
            "no longer exists",
            lambda: project(
                "codex",
                {**prefix, "text": prefix["text"] + "run_id: 8f21\n"},
                suffix,
            ),
        ),
        (
            "evidence anchors alone exceed the budget",
            "budget has to grow or the task has to shrink",
            lambda: trim(_ir(budget={"max_bytes": 40, "max_items": 32})),
        ),
        (
            "the law diverged between hosts",
            "found by the thing it allowed",
            lambda: require_law_agreement(law_matrix(diverged())),
        ),
        (
            "a host was never projected",
            "absence is the state a hand-maintained prompt drifts in",
            lambda: require_law_agreement(law_matrix(good[:5])),
        ),
        (
            "a cache receipt read as evidence about another host",
            "none of which are shared here",
            lambda: require_same_environment(
                cache_observation(
                    {
                        "host": "claude",
                        "model": "opus-5",
                        "provider": "anthropic",
                        "prefix_digest": prefix["prefix_digest"],
                        "hits": 1,
                        "misses": 0,
                    }
                ),
                "grok-build",
                "grok-4",
                "xai",
            ),
        ),
        (
            "cache observation without its environment",
            "cache observation fields drifted",
            lambda: cache_observation({"hits": 1, "misses": 0}),
        ),
        (
            "IR field drift",
            "IR fields drifted",
            lambda: assemble({k: v for k, v in IR.items() if k != "budget"}),
        ),
        (
            "duplicate tool names",
            "duplicate names",
            lambda: assemble(_ir(tools=IR["tools"] + [copy.deepcopy(IR["tools"][0])])),
        ),
        (
            "tool schema digest missing",
            "fields drifted",
            lambda: assemble(_ir(tools=[{"name": "Read", "description": "read"}])),
        ),
        (
            "no delimited normative region",
            "always fail or be dropped",
            lambda: normative_region("# Skill: procedure\n\nno markers here", "probe"),
        ),
        (
            "an empty normative region",
            "empty normative region",
            lambda: normative_region(
                "<!-- loopx:normative-law:begin --><!-- loopx:normative-law:end -->",
                "probe",
            ),
        ),
        (
            "an unknown host",
            "unknown host",
            lambda: project("gemini", prefix, suffix),
        ),
        (
            "a budget of zero bytes",
            "must be a positive integer",
            lambda: assemble(_ir(budget={"max_bytes": 0, "max_items": 32})),
        ),
        (
            "no tools at all",
            "non-empty list",
            lambda: assemble(_ir(tools=[])),
        ),
    ]

    for label, expect, action in cases:
        control(label, expect, action)
    return len(cases)


def run_selftest(root: Path) -> tuple[int, int]:
    return positive_properties(), controls()
