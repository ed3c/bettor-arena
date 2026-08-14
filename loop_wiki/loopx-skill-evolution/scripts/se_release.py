#!/usr/bin/env python3
"""The candidate release receipt, and what Bettor is not allowed to do with it.

Two boundaries, and they are different from each other:

**Bettor does not edit the canonical Skill body.** A winning experiment produces
a *versioned candidate release* addressed to `skills-shared`. Editing the shared
body in place from here would make the consumer the author, and the next repo to
consume it would find content nobody released.

**A fixture result does not unlock a live capability.** Every receipt records
what was actually exercised. `FIXTURE_ONLY` evidence produces a release whose
`capability_state` is `NOT_UNLOCKED`, and no argument to this module can change
that -- there is no parameter for it.

Rejected and inconclusive results get receipts too. A rejection that leaves no
artifact is a rejection nobody can find when the same candidate is proposed
again, and the second proposal will look new.
"""

from __future__ import annotations

from typing import Any

from se_common import (
    ContractError,
    digest,
    exact_object,
    iso_timestamp,
    non_empty_str,
    sha256_ref,
)

RECEIPT_SCHEMA = "loopx/skill-evolution-receipt/v1"

EVIDENCE_KINDS = ("FIXTURE_ONLY", "LIVE_EXERCISED")

PROJECTION_KEYS = {"host_id", "projection_digest", "canonical_digest", "derivation"}


def validate_projection(value: Any, label: str) -> dict[str, Any]:
    projection = exact_object(value, PROJECTION_KEYS, label)
    non_empty_str(projection["host_id"], f"{label}.host_id")
    sha256_ref(projection["projection_digest"], f"{label}.projection_digest")
    sha256_ref(projection["canonical_digest"], f"{label}.canonical_digest")
    if projection["derivation"] not in {"GENERATED_FROM_CANONICAL", "HAND_WRITTEN"}:
        raise ContractError(
            f"{label}.derivation must be GENERATED_FROM_CANONICAL or HAND_WRITTEN"
        )
    # A projection that differs from canonical is fine -- host projections are
    # supposed to differ. What is not fine is differing without recording which
    # canonical content it was derived from, because then nobody can tell a
    # deliberate projection from a stale copy.
    if (
        projection["derivation"] == "GENERATED_FROM_CANONICAL"
        and projection["projection_digest"] == projection["canonical_digest"]
    ):
        raise ContractError(
            f"{label} claims to be generated from canonical yet has the identical "
            "digest; either it is a copy rather than a projection, or the derivation "
            "never ran"
        )
    return projection


def build_receipt(
    experiment: dict[str, Any],
    decision: dict[str, Any],
    evidence_kind: str,
    projections: list[dict[str, Any]],
    at: str,
) -> dict[str, Any]:
    if evidence_kind not in EVIDENCE_KINDS:
        raise ContractError(f"evidence_kind must be one of {list(EVIDENCE_KINDS)}")
    iso_timestamp(at, "receipt.at")
    for index, projection in enumerate(projections):
        validate_projection(projection, f"projections[{index}]")

    outcome = decision["outcome"]
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "experiment_id": experiment["experiment_id"],
        "subject": experiment["subject"],
        "execution_contract": experiment["execution_contract"],
        "arm_digests": sorted(
            (
                {"arm": arm["arm"], "content_digest": arm["content_digest"]}
                for arm in experiment["arms"]
            ),
            key=lambda entry: entry["arm"],
        ),
        "dev_case_set_digest": experiment["dev_case_set_digest"],
        "sealed_holdout_seal": experiment["sealed_holdout"]["seal"],
        "mutation_suite_digest": experiment["mutation_suite"]["suite_digest"],
        "decision": decision,
        "evidence_kind": evidence_kind,
        # There is no code path that sets this to unlocked on fixture evidence.
        "capability_state": (
            "UNLOCKED_PENDING_ADMIT"
            if evidence_kind == "LIVE_EXERCISED" and outcome == "CANDIDATE"
            else "NOT_UNLOCKED"
        ),
        "host_projections": sorted(projections, key=lambda p: p["host_id"]),
        "recorded_at": at,
        # Where the change goes. Not into this repository's copy.
        "proposed_release": (
            {
                "target_repository": "skills-shared",
                "skill_id": experiment["subject"]["skill_id"],
                "supersedes_release": experiment["subject"]["skill_release"],
                "state": "PROPOSED_AWAITING_ADMIT",
            }
            if outcome == "CANDIDATE"
            else None
        ),
        "canonical_mutation": "NONE_PERFORMED",
        "consumer_binding_update": "SEPARATE_LEAF_NOT_PERFORMED",
        "admit_required": True,
        "authority": "PROPOSES",
    }
    receipt["receipt_digest"] = digest(
        {k: v for k, v in receipt.items() if k != "receipt_digest"}
    )
    return receipt


def validate_receipt(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError("receipt must be an object")
    if value.get("schema_version") != RECEIPT_SCHEMA:
        raise ContractError("receipt schema version drifted")
    if value.get("canonical_mutation") != "NONE_PERFORMED":
        raise ContractError(
            "the receipt records a canonical mutation; Bettor consumes immutable "
            "Skill releases and does not edit the shared body -- doing so makes the "
            "consumer the author, and the next repo finds content nobody released"
        )
    if value.get("consumer_binding_update") != "SEPARATE_LEAF_NOT_PERFORMED":
        raise ContractError(
            "the receipt records a consumer binding update; rebinding Bettor to a new "
            "release is a separate Human-admitted leaf, and folding it in here would "
            "promote a release the downstream consumer has not revalidated"
        )
    if value.get("admit_required") is not True:
        raise ContractError("a candidate release receipt must require Human Admit")

    if (
        value.get("evidence_kind") == "FIXTURE_ONLY"
        and value.get("capability_state") != "NOT_UNLOCKED"
    ):
        raise ContractError(
            "fixture-only evidence may not unlock a capability; a harness that passed "
            "against synthetic inputs has said nothing about a live host"
        )
    if (
        value.get("decision", {}).get("outcome") != "CANDIDATE"
        and value.get("proposed_release") is not None
    ):
        raise ContractError(
            "a release is proposed for an outcome that is not CANDIDATE"
        )

    recomputed = digest({k: v for k, v in value.items() if k != "receipt_digest"})
    if value.get("receipt_digest") != recomputed:
        raise ContractError("receipt digest does not match its content")
    return value
