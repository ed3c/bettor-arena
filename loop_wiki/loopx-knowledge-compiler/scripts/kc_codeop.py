#!/usr/bin/env python3
"""Layer 5 -- CodeOp IR. Every operation says what it touches and what undoes it.

A CodeOp without a precondition applies to a tree it never looked at. A CodeOp
without a rollback is a one-way door. A CodeOp without an exact target selector
is a suggestion, and something downstream will have to guess where it goes.

The interface-version rule is the other half: an operation that changes a public
symbol must carry an explicit version decision. Not because the compiler knows
what the right version bump is -- it does not -- but because a scaffold that
quietly alters a public interface is a breaking change that arrives looking like
an addition.
"""

from __future__ import annotations

from typing import Any

from kc_common import (
    ContractError,
    exact_object,
    non_empty_str,
    require,
)

INTENTS = {"CREATE", "UPDATE", "DELETE", "RENAME"}
VERSION_DECISIONS = {"NONE", "PATCH", "MINOR", "MAJOR"}

CODEOP_KEYS = {
    "op_id",
    "intent",
    "target",
    "precondition",
    "expected_diff_shape",
    "validation",
    "rollback",
    "requirement_ids",
    "public_interface_change",
    "version_decision",
    "provenance",
}

TARGET_KEYS = {"path", "selector_kind", "selector"}
PRECONDITION_KEYS = {"kind", "expression"}
DIFF_KEYS = {"added_symbols", "removed_symbols", "renamed_symbols", "max_changed_files"}
VALIDATION_KEYS = {"command", "expect_exit_code"}
ROLLBACK_KEYS = {"kind", "detail"}
PROVENANCE_KEYS = {"assertion_ids", "source_ids", "locators"}

PLAN_KEYS = {"schema_version", "notes_subject", "operations", "output_lease"}
LEASE_KEYS = {"lease_id", "output_root", "writable_paths"}


def validate_codeop(
    value: Any, label: str, requirement_ids: set[str]
) -> dict[str, Any]:
    op = exact_object(value, CODEOP_KEYS, label)
    non_empty_str(op["op_id"], f"{label}.op_id")
    if op["intent"] not in INTENTS:
        raise ContractError(f"{label}.intent must be one of {sorted(INTENTS)}")

    target = exact_object(op["target"], TARGET_KEYS, f"{label}.target")
    non_empty_str(target["path"], f"{label}.target.path")
    if target["selector_kind"] not in {"FILE", "SYMBOL", "REGION"}:
        raise ContractError(
            f"{label}.target.selector_kind must be FILE, SYMBOL or REGION"
        )
    if target["selector_kind"] != "FILE":
        non_empty_str(target["selector"], f"{label}.target.selector")

    precondition = exact_object(
        op["precondition"], PRECONDITION_KEYS, f"{label}.precondition"
    )
    if precondition["kind"] not in {"PATH_ABSENT", "PATH_PRESENT", "DIGEST_EQUALS"}:
        raise ContractError(
            f"{label}.precondition.kind must be PATH_ABSENT, PATH_PRESENT or "
            "DIGEST_EQUALS; an operation with no stated precondition applies to a "
            "tree it never checked"
        )
    non_empty_str(precondition["expression"], f"{label}.precondition.expression")

    # CREATE onto an existing path is an overwrite wearing the wrong intent.
    if op["intent"] == "CREATE" and precondition["kind"] != "PATH_ABSENT":
        raise ContractError(
            f"{label} is a CREATE with precondition {precondition['kind']}; a create "
            "that does not require the path to be absent overwrites whatever is there"
        )

    diff = exact_object(
        op["expected_diff_shape"], DIFF_KEYS, f"{label}.expected_diff_shape"
    )
    for field in ("added_symbols", "removed_symbols", "renamed_symbols"):
        if not isinstance(diff[field], list) or diff[field] != sorted(diff[field]):
            raise ContractError(
                f"{label}.expected_diff_shape.{field} must be a sorted list"
            )
    if not isinstance(diff["max_changed_files"], int) or diff["max_changed_files"] < 1:
        raise ContractError(
            f"{label}.expected_diff_shape.max_changed_files must be a positive int; "
            "an unbounded diff shape accepts any diff, including the wrong one"
        )

    validation = exact_object(op["validation"], VALIDATION_KEYS, f"{label}.validation")
    non_empty_str(validation["command"], f"{label}.validation.command")
    if not isinstance(validation["expect_exit_code"], int):
        raise ContractError(f"{label}.validation.expect_exit_code must be an int")

    rollback = exact_object(op["rollback"], ROLLBACK_KEYS, f"{label}.rollback")
    if rollback["kind"] not in {"DELETE_CREATED", "RESTORE_DIGEST", "RENAME_BACK"}:
        raise ContractError(
            f"{label}.rollback.kind must be DELETE_CREATED, RESTORE_DIGEST or "
            "RENAME_BACK; an operation nobody can undo is applied on faith"
        )
    non_empty_str(rollback["detail"], f"{label}.rollback.detail")

    ids = op["requirement_ids"]
    if not isinstance(ids, list) or not ids:
        raise ContractError(
            f"{label} serves no requirement; code planned without a requirement was "
            "not derived from the notes"
        )
    for requirement_id in ids:
        if requirement_id not in requirement_ids:
            raise ContractError(f"{label} cites unknown requirement {requirement_id!r}")

    if op["version_decision"] not in VERSION_DECISIONS:
        raise ContractError(
            f"{label}.version_decision must be one of {sorted(VERSION_DECISIONS)}"
        )
    changes_interface = bool(op["public_interface_change"])
    if changes_interface and op["version_decision"] == "NONE":
        raise ContractError(
            f"{label} changes a public interface with version_decision NONE; a "
            "scaffold that alters a published symbol without a version decision "
            "ships a breaking change that reads like an addition"
        )
    if diff["removed_symbols"] and not changes_interface:
        raise ContractError(
            f"{label} removes symbols {diff['removed_symbols']} but does not declare "
            "a public interface change; a removal is only private if someone said so"
        )

    # Provenance survives into the operation, so a generated symbol can be
    # traced back to the line of notes it came from without re-running anything.
    provenance = exact_object(op["provenance"], PROVENANCE_KEYS, f"{label}.provenance")
    for field in ("assertion_ids", "source_ids", "locators"):
        if not isinstance(provenance[field], list) or not provenance[field]:
            raise ContractError(
                f"{label}.provenance.{field} must be a non-empty list; a generated "
                "symbol with no trace back to a source is indistinguishable from one "
                "the model remembered"
            )
    return op


def validate_plan(value: Any, requirement_ids: set[str]) -> dict[str, Any]:
    plan = exact_object(value, PLAN_KEYS, "codeop plan")
    require(
        plan["schema_version"] == "loopx/knowledge-codeop-plan/v1",
        "codeop plan schema version drifted",
    )

    lease = exact_object(plan["output_lease"], LEASE_KEYS, "codeop plan.output_lease")
    non_empty_str(lease["lease_id"], "output_lease.lease_id")
    non_empty_str(lease["output_root"], "output_lease.output_root")
    if not isinstance(lease["writable_paths"], list) or not lease["writable_paths"]:
        raise ContractError("output_lease.writable_paths must be a non-empty list")
    if lease["writable_paths"] != sorted(lease["writable_paths"]):
        raise ContractError("output_lease.writable_paths must be sorted")

    operations = plan["operations"]
    if not isinstance(operations, list) or not operations:
        raise ContractError("codeop plan.operations must be a non-empty list")

    seen: set[str] = set()
    for index, op in enumerate(operations):
        validated = validate_codeop(op, f"operations[{index}]", requirement_ids)
        if validated["op_id"] in seen:
            raise ContractError(f"duplicate op_id {validated['op_id']!r}")
        seen.add(validated["op_id"])

        # The lease is checked here as well as at render time. Catching it in the
        # plan means the escape never gets as far as a filesystem call.
        path = validated["target"]["path"]
        if not any(
            path == w or path.startswith(w.rstrip("/") + "/")
            for w in lease["writable_paths"]
        ):
            raise ContractError(
                f"operations[{index}] targets {path!r}, outside the leased writable "
                f"paths {lease['writable_paths']}; a scaffold that writes outside its "
                "lease edits a tree it was never granted"
            )
    return plan


def uncovered_requirements(
    plan: dict[str, Any], requirement_ids: set[str]
) -> list[str]:
    """Requirements with no operation. Reported, not raised.

    A spec may legitimately outrun its scaffold -- the point is that the gap is
    named in the receipt rather than absent from it.
    """
    served = {rid for op in plan["operations"] for rid in op["requirement_ids"]}
    return sorted(requirement_ids - served)
