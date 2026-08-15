#!/usr/bin/env python3
"""Positive properties plus one planted control per named failure in #93."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[2]
for sub in ("scripts", "runtime"):
    sys.path.insert(0, str(BASE / sub))

from memory import ContractError, digest, good_bundle  # noqa: E402

from dmr_pipeline import admit, delete  # noqa: E402
from mem0_authority import (  # noqa: E402
    LADDER,
    RANK,
    outranks,
    resolve,
    validate_writeback,
    writeback_proposal,
)
from mem0_identity import (  # noqa: E402
    evidence_applies_to,
    provider_state,
    require_same_mode,
    validate_identity,
)
from mem0_lifecycle import (  # noqa: E402
    delete_and_verify,
    export_scope,
    namespace_leak,
    substring_residue,
)
from mem0_projection import build, query, rebuild_equivalent, validate_projection  # noqa: E402

OSS = {
    "mode": "OSS_SELF_HOSTED",
    "package_version": "mem0ai==0.1.9",
    "server_endpoint": None,
    "storage_identity": "qdrant:local:collection-a",
    "embedding_identity": "bge-small-en-v1.5",
    "llm_identity": "none",
    "namespace": "bettor-arena",
}
MANAGED = {
    "mode": "MANAGED_SERVICE",
    "package_version": None,
    "server_endpoint": "https://api.mem0.ai",
    "storage_identity": "managed",
    "embedding_identity": "managed",
    "llm_identity": "managed",
    "namespace": "bettor-arena",
}
POLICY = {
    "drop_fields": ["evidence_refs"],
    "policy_digest": digest({"drop": ["evidence_refs"]}),
}
NOW = "2026-08-16T10:00:00Z"


def _log() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    proposal, decision = good_bundle()
    return admit([], proposal, decision)["log"], proposal


def run_selftest(root: Path) -> tuple[int, int]:
    positives = 0
    failures: list[str] = []
    log, proposal = _log()

    projection = build(log, OSS, POLICY, NOW)
    validate_projection(projection)
    if (
        projection["canonical"] is not False
        or projection["authority"] != "PROJECTION_ONLY"
    ):
        raise ContractError("the projection claimed authority")
    positives += 1

    # The redaction policy actually drops.
    if "evidence_refs" in projection["records"][0]:
        raise ContractError("the pinned redaction policy did not drop its field")
    positives += 1

    # Rebuild equivalence is on relations, and says so.
    eq = rebuild_equivalent(log, projection, POLICY, "2026-08-16T11:00:00Z")
    if not eq["equivalent"] or eq["comparison"] != "RELATION_EQUIVALENT":
        raise ContractError(f"rebuild reported {eq}")
    if "bytes" not in eq["note"]:
        raise ContractError("the rebuild note does not say what was not compared")
    positives += 1

    # An unavailable provider is not an empty result.
    answered = query(projection, "boundary", "AVAILABLE")
    down = query(projection, "boundary", "UNAVAILABLE")
    if answered["state"] != "ANSWERED" or not answered["hits"]:
        raise ContractError(f"an available query produced {answered}")
    if down["state"] != "PROVIDER_UNAVAILABLE":
        raise ContractError(
            f"an unavailable provider produced {down['state']}; an empty list from a "
            "store that is down looks exactly like one from a store with nothing to say"
        )
    if down["hits"]:
        raise ContractError("an unavailable provider returned hits")
    positives += 1

    # Every hit carries provenance including the mode that produced it.
    provenance = answered["hits"][0]["provenance"]
    for field in ("namespace", "source_event_id", "policy_digest", "mode"):
        if not provenance.get(field):
            raise ContractError(f"a hit is missing provenance.{field}")
    positives += 1

    # The four-rung ladder, in order.
    if list(LADDER)[-2:] != ["MEM0_PROJECTION", "MODEL_SUMMARY"]:
        raise ContractError(f"the ladder ends {list(LADDER)[-2:]}")
    if not outranks("MEMORY", "MEM0_PROJECTION"):
        raise ContractError("an admitted memory does not outrank a retrieval")
    if not outranks("MEM0_PROJECTION", "MODEL_SUMMARY"):
        raise ContractError("a retrieval does not outrank a model summary")
    if not outranks("SOURCE", "MODEL_SUMMARY"):
        raise ContractError("source does not outrank a model summary")
    resolution = resolve(
        [
            {"rung": "MODEL_SUMMARY", "statement": "model", "ref": "m"},
            {"rung": "MEM0_PROJECTION", "statement": "index", "ref": "p"},
            {"rung": "MEMORY", "statement": "admitted", "ref": "e"},
            {"rung": "SOURCE", "statement": "code", "ref": "s"},
        ]
    )
    if resolution["rung"] != "SOURCE" or resolution["answer"] != "code":
        raise ContractError(f"the ladder resolved to {resolution}")
    if not resolution["projection_was_overridden"]:
        raise ContractError("the overridden projection result was not named")
    positives += 1

    # Writeback is a proposal and says it wrote nothing.
    wb = writeback_proposal(answered["hits"], proposal["canonical_key"], "a claim")
    validate_writeback(wb)
    if wb["written"] is not False or not wb["requires_human_admit"]:
        raise ContractError("the writeback claimed to have written")
    positives += 1

    # Mode evidence does not widen, in either direction.
    if evidence_applies_to(OSS) != ("OSS_SELF_HOSTED",):
        raise ContractError("OSS evidence widened")
    if evidence_applies_to(MANAGED) != ("MANAGED_SERVICE",):
        raise ContractError("managed evidence widened")
    positives += 1

    # A canonical delete leaves nothing retrievable in the rebuilt index.
    statement = proposal["statement"]
    removed = delete(
        log, proposal["canonical_key"], "ed3c", "2026-08-16T09:00:00Z", "req"
    )
    verified = delete_and_verify(
        removed["log"], OSS, POLICY, digest(statement), statement[:24], NOW
    )
    if verified["state"] != "CLEAN" or verified["content_retrievable"]:
        raise ContractError(f"content survived into the index: {verified}")
    if verified["record_count"] != 0:
        raise ContractError("a tombstoned memory stayed in the projection")
    positives += 1

    # The fragment check finds what a digest check would miss.
    partial = build(log, OSS, POLICY, NOW)
    if not substring_residue(partial, statement[:24]):
        raise ContractError(
            "the fragment scan found nothing while the content was present; it would "
            "then report a partial copy as clean"
        )
    positives += 1

    # No cross-namespace records, and an export names its scope.
    if namespace_leak(projection, "bettor-arena"):
        raise ContractError("the projection carried another namespace's records")
    scope = export_scope(projection, "ed3c", NOW)["scope"]
    if scope != "namespace:bettor-arena":
        raise ContractError(f"the export scope is {scope}")
    positives += 1

    # --- controls -----------------------------------------------------------
    def expect(name: str, needle: str, call) -> None:
        try:
            call()
        except ContractError as exc:
            if needle not in str(exc):
                failures.append(f"{name} refused for the wrong reason: {exc}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{name} raised {type(exc).__name__}: {exc}")
        else:
            failures.append(f"{name} was accepted")

    expect(
        "managed-benchmark-read-as-oss-evidence",
        "describes the service that produced it",
        lambda: require_same_mode(MANAGED, "OSS_SELF_HOSTED"),
    )
    expect(
        "oss-benchmark-read-as-managed-evidence",
        "describes the service that produced it",
        lambda: require_same_mode(OSS, "MANAGED_SERVICE"),
    )
    expect(
        "self-hosted-with-a-hosted-endpoint",
        "describe that service",
        lambda: validate_identity({**OSS, "server_endpoint": "https://api.mem0.ai"}),
    )
    expect(
        "self-hosted-without-a-pinned-version",
        "whatever was installed that day",
        lambda: validate_identity({**OSS, "package_version": None}),
    )
    expect(
        "unnamed-embedding",
        "cannot be rebuilt into the same index",
        lambda: validate_identity({**OSS, "embedding_identity": ""}),
    )
    expect(
        "projection-promoted-to-canonical",
        "makes the vector store the record",
        lambda: validate_projection({**projection, "canonical": True}),
    )
    expect(
        "writeback-that-wrote",
        "makes the vector store an author",
        lambda: validate_writeback({**wb, "written": True}),
    )
    expect(
        "writeback-without-admission",
        "does not require admission",
        lambda: validate_writeback({**wb, "requires_human_admit": False}),
    )
    expect(
        "writeback-from-no-hits",
        "wearing a retrieval's clothes",
        lambda: writeback_proposal([], "k", "s"),
    )
    expect(
        "unavailable-reported-as-a-pass",
        "an unreachable store reported as a passing query",
        lambda: provider_state("PASS", "availability"),
    )
    expect(
        "cross-namespace-read",
        "another project's memories with this project's provenance",
        lambda: namespace_leak(projection, "other-project"),
    )
    expect(
        "projection-built-under-an-unrecorded-policy",
        "cannot be compared",
        lambda: build(log, OSS, {"drop_fields": []}, NOW),
    )

    if "MEM0_PROJECTION" in RANK and RANK["MEM0_PROJECTION"] < RANK["MEMORY"]:
        failures.append("the projection outranks admitted memory")

    if failures:
        raise ContractError(
            "planted controls did not behave:\n  " + "\n  ".join(failures)
        )
    return positives, 12
