#!/usr/bin/env python3
"""The change delta, and the join between code evidence and test/runtime evidence.

Two failures live here.

The first is a diff becoming knowledge on its own. Code changed; therefore the
system behaves this way. That inference is invisible in the output -- the card
says "TESTED" and nothing records that no test ever ran. So a claim may only
reach `TEST` or `RUNTIME` evidence class if the delta carries a receipt of that
kind covering the symbol in question.

The second is subtler: a test that exists but did not run. A test file appearing
in the diff is `STATIC` evidence that a test was written. Only an execution
receipt with a zero exit is `TEST` evidence that it passed.
"""

from __future__ import annotations

from typing import Any

from fb_anchor import validate_anchor
from fb_common import (
    ContractError,
    exact_object,
    iso_timestamp,
    non_empty_str,
    require,
    sha256_ref,
    validate_subject,
)

DELTA_KEYS = {
    "schema_version",
    "before",
    "after",
    "changed_files",
    "symbol_delta",
    "public_interface_delta",
    "test_executions",
    "runtime_observations",
    "anchors",
}

SYMBOL_DELTA_KEYS = {"symbol", "path", "change", "public"}
SYMBOL_CHANGES = {"ADDED", "REMOVED", "MODIFIED", "RENAMED"}

TEST_EXECUTION_KEYS = {
    "execution_id",
    "command",
    "exit_code",
    "covered_symbols",
    "output_digest",
    "ran_at",
}

RUNTIME_OBSERVATION_KEYS = {
    "observation_id",
    "environment",
    "observed_symbols",
    "receipt_digest",
    "observed_at",
    "adapter_attested",
}


def validate_delta(value: Any) -> dict[str, Any]:
    delta = exact_object(value, DELTA_KEYS, "change delta")
    require(
        delta["schema_version"] == "loopx/foldback-change-delta/v1",
        "change delta schema version drifted",
    )
    before = validate_subject(delta["before"], "change delta.before")
    after = validate_subject(delta["after"], "change delta.after")
    if before["commit"] == after["commit"]:
        raise ContractError(
            "before and after name the same commit; a fold-back with no change to "
            "fold back is a NOOP, not a delta"
        )
    if before["repository"] != after["repository"]:
        raise ContractError("before and after are different repositories")

    files = delta["changed_files"]
    if not isinstance(files, list) or not files:
        raise ContractError("change delta.changed_files must be a non-empty list")
    if files != sorted(files):
        raise ContractError("change delta.changed_files must be sorted")

    symbols = delta["symbol_delta"]
    if not isinstance(symbols, list):
        raise ContractError("change delta.symbol_delta must be a list")
    for index, value_ in enumerate(symbols):
        label = f"symbol_delta[{index}]"
        entry = exact_object(value_, SYMBOL_DELTA_KEYS, label)
        non_empty_str(entry["symbol"], f"{label}.symbol")
        non_empty_str(entry["path"], f"{label}.path")
        if entry["change"] not in SYMBOL_CHANGES:
            raise ContractError(
                f"{label}.change must be one of {sorted(SYMBOL_CHANGES)}"
            )
        if not isinstance(entry["public"], bool):
            raise ContractError(f"{label}.public must be a boolean")
        if entry["path"] not in files:
            raise ContractError(
                f"{label} names {entry['path']}, which is not in changed_files; a "
                "symbol delta in an unchanged file did not come from this diff"
            )

    # A public interface delta must be backed by a symbol delta marked public.
    # Otherwise the two lists can disagree, and whichever one a reader consults
    # first becomes the truth.
    interfaces = delta["public_interface_delta"]
    if not isinstance(interfaces, list) or interfaces != sorted(interfaces):
        raise ContractError("change delta.public_interface_delta must be a sorted list")
    public_symbols = {s["symbol"] for s in symbols if s["public"]}
    undeclared = sorted(set(interfaces) - public_symbols)
    if undeclared:
        raise ContractError(
            f"public interface delta names {undeclared} with no public symbol delta "
            "to match; the two lists would disagree and whichever is read first wins"
        )

    executions = delta["test_executions"]
    if not isinstance(executions, list):
        raise ContractError("change delta.test_executions must be a list")
    for index, value_ in enumerate(executions):
        label = f"test_executions[{index}]"
        execution = exact_object(value_, TEST_EXECUTION_KEYS, label)
        non_empty_str(execution["execution_id"], f"{label}.execution_id")
        non_empty_str(execution["command"], f"{label}.command")
        sha256_ref(execution["output_digest"], f"{label}.output_digest")
        iso_timestamp(execution["ran_at"], f"{label}.ran_at")
        if not isinstance(execution["exit_code"], int):
            raise ContractError(f"{label}.exit_code must be an integer")
        covered = execution["covered_symbols"]
        if not isinstance(covered, list) or covered != sorted(covered) or not covered:
            raise ContractError(
                f"{label}.covered_symbols must be a sorted non-empty list"
            )

    observations = delta["runtime_observations"]
    if not isinstance(observations, list):
        raise ContractError("change delta.runtime_observations must be a list")
    for index, value_ in enumerate(observations):
        label = f"runtime_observations[{index}]"
        observation = exact_object(value_, RUNTIME_OBSERVATION_KEYS, label)
        non_empty_str(observation["observation_id"], f"{label}.observation_id")
        non_empty_str(observation["environment"], f"{label}.environment")
        sha256_ref(observation["receipt_digest"], f"{label}.receipt_digest")
        iso_timestamp(observation["observed_at"], f"{label}.observed_at")
        observed = observation["observed_symbols"]
        if (
            not isinstance(observed, list)
            or observed != sorted(observed)
            or not observed
        ):
            raise ContractError(
                f"{label}.observed_symbols must be a sorted non-empty list"
            )
        # A runtime observation nobody's adapter attested is a report of a run
        # that may never have happened. It is not weaker runtime evidence; it is
        # not runtime evidence.
        if observation["adapter_attested"] is not True:
            raise ContractError(
                f"{label} is not adapter-attested; an unattested runtime report is a "
                "claim that something ran, which is exactly what runtime evidence is "
                "supposed to establish"
            )

    anchors = delta["anchors"]
    if not isinstance(anchors, list) or not anchors:
        raise ContractError("change delta.anchors must be a non-empty list")
    seen: set[str] = set()
    for index, anchor in enumerate(anchors):
        validated = validate_anchor(anchor, f"anchors[{index}]")
        if validated["anchor_id"] in seen:
            raise ContractError(f"duplicate anchor_id {validated['anchor_id']!r}")
        seen.add(validated["anchor_id"])
        if validated["commit"] not in {before["commit"], after["commit"]}:
            raise ContractError(
                f"anchors[{index}] was read at a commit that is neither the before "
                "nor the after subject; it belongs to a diff this delta does not cover"
            )
    return delta


def supported_classes(delta: dict[str, Any], symbol: str) -> set[str]:
    """Which evidence classes this delta can actually support for one symbol.

    STATIC is available whenever the symbol appears in the diff. TEST needs a
    passing execution that covered it. RUNTIME needs an attested observation of
    it. Nothing here derives one from another -- that is the whole point.
    """
    classes: set[str] = set()
    if any(entry["symbol"] == symbol for entry in delta["symbol_delta"]):
        classes.add("STATIC")
    for execution in delta["test_executions"]:
        if symbol in execution["covered_symbols"] and execution["exit_code"] == 0:
            classes.add("TEST")
    for observation in delta["runtime_observations"]:
        if symbol in observation["observed_symbols"]:
            classes.add("RUNTIME")
    return classes


def require_supported(delta: dict[str, Any], symbol: str, claimed: str) -> None:
    available = supported_classes(delta, symbol)
    if claimed not in available:
        raise ContractError(
            f"a patch claims {claimed} evidence for {symbol!r}, but this delta only "
            f"supports {sorted(available) or ['nothing']}. A diff shows what the "
            "source says; it does not show what it does, and a static change "
            "recorded as observed behaviour cannot be told apart afterwards"
        )
