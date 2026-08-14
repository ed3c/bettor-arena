#!/usr/bin/env python3
"""Local/cloud parity: compare contract behaviour, and say NOT_EXERCISED honestly.

Parity here is not "both said PASS". Two adapters agreeing on an exit code while
disagreeing on residue, artifact digests or failure classification are not at
parity -- and the dimension that differs is exactly the one someone would later
rely on.

An adapter with no receipt is `NOT_EXERCISED`, never `PASS` and never `FAIL`.
That distinction is the whole reason this harness exists: a parity matrix that
renders absent adapters as blank invites the reading that they agreed.
"""

from __future__ import annotations

from typing import Any

from fabric_common import ContractError, exact_object, non_empty_str, require

# The dimensions #66 names. Compared field by field, because a single overall
# verdict would let one matching exit code hide four disagreements.
PARITY_DIMENSIONS = [
    "subject_identity",
    "filesystem_enforcement",
    "network_enforcement",
    "process_enforcement",
    "exit_behaviour",
    "artifact_digests",
    "cleanup_residue",
    "failure_classification",
]

# Deliberately excluded from parity: timing and resource observations. They are
# environment-specific, and a matrix that required them to match would either be
# permanently red or quietly rounded until it was meaningless.
OBSERVATION_ONLY_DIMENSIONS = ["startup_ms", "elapsed_ms", "resource_observations"]


def _dimension_values(receipt: dict[str, Any]) -> dict[str, Any]:
    return {
        "subject_identity": receipt["subject"],
        "filesystem_enforcement": receipt["enforcement_ceiling"]["filesystem"],
        "network_enforcement": (
            receipt["network"]["requested"],
            receipt["network"]["attested"],
        ),
        "process_enforcement": receipt["enforcement_ceiling"]["process_group"],
        "exit_behaviour": (
            receipt["execution"]["exit_code"],
            receipt["execution"]["timed_out"],
        ),
        "artifact_digests": [(a["path"], a["digest"]) for a in receipt["artifacts"]],
        "cleanup_residue": (
            receipt["cleanup"]["status"],
            receipt["cleanup"]["residue_paths"],
        ),
        "failure_classification": receipt["outcome"],
    }


def build_matrix(
    reference_adapter: str,
    receipts: dict[str, dict[str, Any]],
    declared_adapters: list[str],
) -> dict[str, Any]:
    """Compare every declared adapter against the reference one."""
    for name in declared_adapters:
        non_empty_str(name, "declared adapter")
    if reference_adapter not in declared_adapters:
        raise ContractError("the reference adapter must be among the declared adapters")
    if reference_adapter not in receipts:
        raise ContractError(
            f"no receipt for the reference adapter {reference_adapter!r}; parity "
            "cannot be measured against an adapter that did not run"
        )

    reference = _dimension_values(receipts[reference_adapter])
    rows = []
    for adapter in sorted(declared_adapters):
        if adapter not in receipts:
            rows.append(
                {
                    "adapter": adapter,
                    "state": "NOT_EXERCISED",
                    "dimensions": {d: "NOT_EXERCISED" for d in PARITY_DIMENSIONS},
                }
            )
            continue
        values = _dimension_values(receipts[adapter])
        dimensions = {
            d: ("MATCH" if values[d] == reference[d] else "DIFFERS")
            for d in PARITY_DIMENSIONS
        }
        differing = sorted(d for d, v in dimensions.items() if v == "DIFFERS")
        rows.append(
            {
                "adapter": adapter,
                "state": "PARITY" if not differing else "DIVERGENT",
                "dimensions": dimensions,
                "differing_dimensions": differing,
            }
        )

    exercised = [r for r in rows if r["state"] != "NOT_EXERCISED"]
    return {
        "schema_version": "loopx/runtime-parity-matrix/v1",
        "reference_adapter": reference_adapter,
        "declared_adapters": sorted(declared_adapters),
        "compared_dimensions": PARITY_DIMENSIONS,
        "observation_only_dimensions": OBSERVATION_ONLY_DIMENSIONS,
        "rows": rows,
        "exercised_count": len(exercised),
        "not_exercised_count": len(rows) - len(exercised),
        # Stated on the matrix itself. A green row for one adapter says nothing
        # about an adapter that never ran, and this is where that gets read.
        "claim_boundary": (
            "parity is claimed only for adapters with a receipt; NOT_EXERCISED "
            "rows are absent evidence, not agreement"
        ),
    }


def validate_matrix(value: Any) -> dict[str, Any]:
    matrix = exact_object(
        value,
        {
            "schema_version",
            "reference_adapter",
            "declared_adapters",
            "compared_dimensions",
            "observation_only_dimensions",
            "rows",
            "exercised_count",
            "not_exercised_count",
            "claim_boundary",
        },
        "parity matrix",
    )
    require(
        matrix["schema_version"] == "loopx/runtime-parity-matrix/v1",
        "parity matrix schema version drifted",
    )
    if matrix["compared_dimensions"] != PARITY_DIMENSIONS:
        raise ContractError("parity dimensions drifted from the declared set")
    for row in matrix["rows"]:
        if row["state"] not in {"PARITY", "DIVERGENT", "NOT_EXERCISED"}:
            raise ContractError(f"unknown parity state {row['state']!r}")
        if row["state"] == "NOT_EXERCISED" and set(row["dimensions"].values()) != {
            "NOT_EXERCISED"
        }:
            raise ContractError(
                f"adapter {row['adapter']!r} has no receipt but reports dimension "
                "verdicts; absent evidence may not be rendered as agreement"
            )
    return matrix
