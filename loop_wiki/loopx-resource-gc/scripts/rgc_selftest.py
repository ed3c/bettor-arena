#!/usr/bin/env python3
"""Positive properties plus one planted control per named failure in #97.

Every run builds a real tree, because the rebuild proofs compare bytes on disk.
A fixture-only version of this suite would be testing the plan's arithmetic and
not the property the plan rests on.
"""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any, Callable

from rgc_common import ContractError, ResourceExhausted
from rgc_execute import validate_receipt
from rgc_fixtures import build_tree
from rgc_pipeline import run_gc

NAMES = ("resources", "rebuild-specs", "config")


def load_inputs(root: Path) -> dict[str, Any]:
    good = root / "tests/fixtures/good"
    return {
        name: json.loads((good / f"{name}.json").read_text(encoding="utf-8"))
        for name in NAMES
    }


def _run(
    inputs: dict[str, Any], root: Path, apply: bool = False, **observed
) -> dict[str, Any]:
    cfg = inputs["config"]
    return run_gc(
        cfg["root_id"],
        inputs["resources"],
        set(cfg["held_leases"]),
        set(cfg["live_subjects"]),
        inputs["rebuild-specs"],
        cfg["admitted"],
        cfg["authorized_by"],
        cfg["now"],
        cfg["max_age_s"],
        root,
        apply=apply,
        **observed,
    )


def _resource(inputs: dict[str, Any], rid: str) -> dict[str, Any]:
    for resource in inputs["resources"]:
        if resource["resource_id"] == rid:
            return resource
    raise KeyError(rid)


def _actions(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {action["resource_id"]: action for action in result["plan"]["actions"]}


# --- controls that must raise -------------------------------------------------


def _agent_authorizes_destruction(inputs: dict[str, Any]) -> None:
    inputs["config"]["authorized_by"] = "AGENT"


def _unknown_resource_class(inputs: dict[str, Any]) -> None:
    _resource(inputs, "cache-stale")["resource_class"] = "SOMETHING_NEW"


def _path_traversal(inputs: dict[str, Any]) -> None:
    _resource(inputs, "cache-stale")["path"] = "data/../../etc/passwd"


def _admit_a_resource_not_in_inventory(inputs: dict[str, Any]) -> None:
    inputs["config"]["admitted"] = sorted(
        [*inputs["config"]["admitted"], "ghost-resource"]
    )


def _rebuild_spec_without_a_command(inputs: dict[str, Any]) -> None:
    inputs["rebuild-specs"][0]["rebuild_argv"] = []


def _negative_bytes(inputs: dict[str, Any]) -> None:
    _resource(inputs, "cache-stale")["bytes"] = -1


RAISING: list[tuple[str, Callable[[dict[str, Any]], None], str]] = [
    (
        "agent-authorizes-destructive-cleanup",
        _agent_authorizes_destruction,
        "only ['HUMAN']",
    ),
    ("unknown-resource-class", _unknown_resource_class, "the vocabulary is closed"),
    ("path-traversal-in-a-resource", _path_traversal, "climb out of the root"),
    (
        "admit-a-resource-nobody-inventoried",
        _admit_a_resource_not_in_inventory,
        "would delete whatever later takes that name",
    ),
    (
        "rebuild-spec-with-no-command",
        _rebuild_spec_without_a_command,
        "not recreatable",
    ),
    ("negative-resource-size", _negative_bytes, "non-negative integer"),
]


# --- controls that must keep a resource ---------------------------------------


def _blocked_evidence_admitted(inputs: dict[str, Any]) -> None:
    inputs["config"]["admitted"] = sorted(
        [*inputs["config"]["admitted"], "blocked-conflict-12"]
    )


def _release_subject_admitted(inputs: dict[str, Any]) -> None:
    inputs["config"]["admitted"] = sorted(
        [*inputs["config"]["admitted"], "release-subject-tree"]
    )


def _dirty_worktree_admitted(inputs: dict[str, Any]) -> None:
    inputs["config"]["admitted"] = sorted(
        [*inputs["config"]["admitted"], "worktree-dirty"]
    )


def _leased_worktree_admitted(inputs: dict[str, Any]) -> None:
    inputs["config"]["admitted"] = sorted(
        [*inputs["config"]["admitted"], "worktree-leased"]
    )


def _wal_admitted(inputs: dict[str, Any]) -> None:
    inputs["config"]["admitted"] = sorted([*inputs["config"]["admitted"], "wal-0003"])


def _projection_with_no_proof(inputs: dict[str, Any]) -> None:
    inputs["rebuild-specs"] = [
        spec
        for spec in inputs["rebuild-specs"]
        if spec["resource_id"] != "vector-stale"
    ]


def _retention_clock_drift(inputs: dict[str, Any]) -> None:
    # The clock jumps backwards past every last-used time. Nothing is expired,
    # and nothing may be deleted -- a drifting clock must not delete, and must
    # not silently keep either, so this checks the conservative direction.
    inputs["config"]["now"] = "2026-06-01T00:00:00Z"


KEEPING: list[tuple[str, Callable[[dict[str, Any]], None], str, str]] = [
    (
        "blocked-evidence-admitted",
        _blocked_evidence_admitted,
        "blocked-conflict-12",
        "blocked conflict evidence",
    ),
    (
        "release-subject-admitted",
        _release_subject_admitted,
        "release-subject-tree",
        "not expired",
    ),
    (
        "dirty-worktree-admitted",
        _dirty_worktree_admitted,
        "worktree-dirty",
        "leased or dirty",
    ),
    (
        "leased-worktree-admitted",
        _leased_worktree_admitted,
        "worktree-leased",
        "leased or dirty",
    ),
    ("wal-admitted", _wal_admitted, "wal-0003", "immutable evidence"),
    (
        "projection-with-no-rebuild-proof",
        _projection_with_no_proof,
        "vector-stale",
        "no rebuild proof",
    ),
    ("clock-drifted-backwards", _retention_clock_drift, "cache-stale", "not expired"),
]


def run_selftest(module_root: Path) -> tuple[int, int]:
    base = load_inputs(module_root)
    positives = 0

    with tempfile.TemporaryDirectory(prefix="loopx-rgc-selftest-") as tmp:
        root = build_tree(Path(tmp) / "tree")
        result = _run(copy.deepcopy(base), root, apply=True)

        if result["state_trace"][-1] != "TOMBSTONE_RECEIPT_APPENDED":
            raise ContractError("the GC pass did not reach a tombstone receipt")
        positives += 1

        # The four proof states, all reached against a real tree.
        proofs = result["rebuild_proofs"]
        expected = {
            "vector-stale": "PROVEN",
            "cache-stale": "PROVEN",
            "graph-divergent": "DIVERGENT",
            "lsp-unprovable": "UNPROVABLE",
        }
        if proofs != expected:
            raise ContractError(f"rebuild proofs were {proofs}, expected {expected}")
        positives += 1

        # DIVERGENT is the one that gets skipped: the rebuild exits zero, so the
        # projection "is rebuildable" -- and what comes back is not what was there.
        actions = _actions(result)
        if actions["graph-divergent"]["action"] != "KEEP":
            raise ContractError(
                "a DIVERGENT projection was deleted; the rebuild works and does not "
                "reproduce this, so whatever the difference encoded is now gone"
            )
        positives += 1

        if actions["lsp-unprovable"]["action"] != "KEEP":
            raise ContractError("an UNPROVABLE projection was deleted")
        positives += 1

        # A Human admitted the ledger segment, and it is still kept.
        if actions["ledger-seg-0001"]["action"] != "KEEP":
            raise ContractError(
                "an admitted ledger segment was deleted; immutable evidence is not "
                "admittable, because deleting it destroys the record of why "
                "everything else was allowed"
            )
        positives += 1

        # Exactly the two proven ones went, and both left tombstones.
        removed = sorted(entry["resource_id"] for entry in result["receipt"]["removed"])
        if removed != ["cache-stale", "vector-stale"]:
            raise ContractError(f"removed {removed}")
        if len(result["receipt"]["tombstones"]) != 2:
            raise ContractError("a removal left no tombstone")
        validate_receipt(result["receipt"])
        positives += 1

        # And the disk agrees.
        for name in ("vector-stale", "cache-stale"):
            if (root / "data/resource-gc" / name).exists():
                raise ContractError(f"{name} was reported removed but is still on disk")
        for name in ("graph-divergent", "lsp-unprovable", "ledger-0001", "blocked-12"):
            if not (root / "data/resource-gc" / name).exists():
                raise ContractError(f"{name} was removed despite being kept")
        positives += 1

        # A resource with no timestamp is protected, not expired.
        if actions["artifact-no-timestamp"]["action"] != "KEEP":
            raise ContractError(
                "a resource with no last-used time was treated as expired; an unknown "
                "age is not an old age, and deleting on missing data deletes most "
                "confidently where it knows least"
            )
        positives += 1

        # A dry run touches nothing.
        dry_root = build_tree(Path(tmp) / "dry")
        dry = _run(copy.deepcopy(base), dry_root, apply=False)
        if dry["receipt"]["state"] != "DRY_RUN" or dry["receipt"]["removed"]:
            raise ContractError("a dry run removed something")
        if not (dry_root / "data/resource-gc/vector-stale").exists():
            raise ContractError("a dry run deleted a projection")
        positives += 1

        # Residue turns the pass red rather than being reported alongside PASS.
        residue_root = build_tree(Path(tmp) / "residue")
        try:
            _run(
                copy.deepcopy(base),
                residue_root,
                apply=True,
                live_processes={4242},
                claimed={"processes": [4242]},
            )
        except ContractError as exc:
            if "still held" not in str(exc):
                raise ContractError(
                    f"residue refused for the wrong reason: {exc}"
                ) from exc
        else:
            raise ContractError(
                "a run that left a process running reported success; a path can be "
                "gone while the process holding it is not"
            )
        positives += 1

        # Disk exhaustion is its own exception, not a failure and not a refusal.
        full_root = build_tree(Path(tmp) / "full")
        try:
            _run(copy.deepcopy(base), full_root, apply=True, free_bytes=0)
        except ResourceExhausted:
            pass
        except ContractError as exc:
            raise ContractError(
                f"disk exhaustion was reported as a contract failure: {exc}"
            ) from exc
        else:
            raise ContractError("a full disk was not reported at all")
        positives += 1

        failures = []
        for name, mutate, needle in RAISING:
            inputs = copy.deepcopy(base)
            mutate(inputs)
            trial = build_tree(Path(tmp) / f"raise-{name}")
            try:
                _run(inputs, trial)
            except ContractError as exc:
                if needle not in str(exc):
                    failures.append(
                        f"{name} was refused, but for the wrong reason: expected "
                        f"{needle!r}, got {exc}"
                    )
                continue
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    f"{name} raised {type(exc).__name__}: {exc} -- broken control"
                )
                continue
            failures.append(f"{name} was accepted")

        for name, mutate, resource_id, needle in KEEPING:
            inputs = copy.deepcopy(base)
            mutate(inputs)
            trial = build_tree(Path(tmp) / f"keep-{name}")
            try:
                trial_result = _run(inputs, trial)
            except Exception as exc:  # noqa: BLE001
                failures.append(
                    f"{name} raised {type(exc).__name__}: {exc} -- this control checks "
                    "that a resource is kept, so a refusal means it was never reached"
                )
                continue
            action = _actions(trial_result).get(resource_id)
            if action is None:
                failures.append(f"{name}: {resource_id} is not in the plan at all")
            elif action["action"] != "KEEP":
                failures.append(f"{name}: {resource_id} was selected for deletion")
            elif needle not in action["reason"]:
                failures.append(
                    f"{name}: {resource_id} was kept for the wrong reason: expected "
                    f"{needle!r}, got {action['reason']!r}"
                )

        if failures:
            raise ContractError(
                "planted controls did not behave:\n  " + "\n  ".join(failures)
            )

    return positives, len(RAISING) + len(KEEPING)
