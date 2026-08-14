#!/usr/bin/env python3
"""Positive properties plus one planted control per named failure in #105."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from nr_common import (
    ABSENCE_PROOF,
    RETRIEVAL_STATES,
    ContractError,
    digest,
    proves_absence,
)
from nr_index import (
    build_chunks,
    build_subject,
    check_freshness,
    coverage,
    validate_chunk,
    validate_policy,
    validate_subject,
)
from nr_openwiki import DERIVED_MARKER, admissible_as_evidence, validate_projection
from nr_pipeline import build, query
from nr_query import to_claim, validate_result

POLICY = {
    "chunk_max_chars": 200,
    "chunk_overlap_chars": 20,
    "embedding_model": "bge-small-en-v1.5",
    "embedding_dimensions": 384,
    "provider_id": "lancedb",
    "provider_version": "0.9.0",
}
CARDS = [
    {
        "canonical_key": "component:ledger-append",
        "title": "Ledger append",
        "summary": "Append is compare-and-set.",
        "verification_state": "CORROBORATED",
    }
]
EVIDENCE = [
    {
        "evidence_id": "ev-0001",
        "source_id": "talk",
        "card_key": "component:ledger-append",
        "locator": "sources/talk.vtt#t=00:00:01.000",
    },
    {
        "evidence_id": "ev-0002",
        "source_id": "paper",
        "card_key": None,
        "locator": "sources/paper.txt#page=1",
    },
]
TEXTS = {
    "ev-0001": "The ledger append is compare-and-set on state_revision.",
    "ev-0002": "The retention window is thirty days.",
}
MANIFEST_DIGEST = digest({"manifest": 1})


def _tree(root: Path) -> Path:
    (root / "sources").mkdir(parents=True, exist_ok=True)
    (root / "sources/talk.vtt").write_text(TEXTS["ev-0001"], encoding="utf-8")
    (root / "sources/paper.txt").write_text(TEXTS["ev-0002"], encoding="utf-8")
    return root


def _built(provider: bool = True) -> dict[str, Any]:
    return build(
        "ed3c/bettor-notes",
        "1a" * 20,
        "2b" * 20,
        MANIFEST_DIGEST,
        POLICY,
        CARDS,
        EVIDENCE,
        TEXTS,
        provider,
    )


def run_selftest(module_root: Path) -> tuple[int, int]:
    positives = 0
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="loopx-nr-selftest-") as tmp:
        root = _tree(Path(tmp) / "tree")
        built = _built()
        subject = built["index_subject"]
        validate_subject(subject)
        validate_projection(built["openwiki"])
        positives += 1

        # Every chunk keeps every identity it came from.
        for index, chunk in enumerate(built["chunks"]):
            validate_chunk(chunk, f"chunks[{index}]")
            if not chunk["locator"] or not chunk["evidence_id"]:
                raise ContractError("a chunk lost its provenance")
        positives += 1

        # A hit is a candidate with provenance, never a fact.
        answered = query(built, subject, "compare-and-set", root)
        validate_result(answered["micro"])
        if answered["micro"]["state"] != "HIT" or not answered["micro"]["hits"]:
            raise ContractError(f"the query produced {answered['micro']}")
        claim = to_claim(answered["micro"])
        if claim["is_fact"] or claim["is_gate_verdict"]:
            raise ContractError("a retrieval hit was admitted as a fact or a verdict")
        if claim["admitted_as"] != "RETRIEVAL_CANDIDATE":
            raise ContractError(f"a hit was admitted as {claim['admitted_as']}")
        positives += 1

        # Readback confirms the chunk text is in the source it cites.
        if [entry["state"] for entry in answered["readbacks"]] != ["CONFIRMED"]:
            raise ContractError(f"readback produced {answered['readbacks']}")
        positives += 1

        # A miss proves nothing, and every state agrees.
        missed = query(built, subject, "no-such-text-anywhere", root)
        if missed["micro"]["state"] != "MISS":
            raise ContractError(f"an absent term produced {missed['micro']['state']}")
        if set(ABSENCE_PROOF.values()) != {"NONE"}:
            raise ContractError(
                "some retrieval state claims to prove absence; a retrieval says "
                "something about an index and nothing about the world"
            )
        for state in RETRIEVAL_STATES:
            if proves_absence(state) != "NONE":
                raise ContractError(f"{state} claims to prove absence")
        positives += 1

        # The macro read works with no provider; only micro is lost.
        without = _built(provider=False)
        no_provider = query(without, without["index_subject"], "compare-and-set", root)
        if no_provider["macro"]["page_count"] != 1:
            raise ContractError("the OpenWiki projection needed a vector provider")
        if no_provider["micro"]["state"] != "PROVIDER_ABSENT":
            raise ContractError(
                f"a missing provider produced {no_provider['micro']['state']}; an "
                "empty list would have been indistinguishable from a miss"
            )
        if no_provider["micro"]["hits"]:
            raise ContractError("an absent provider returned hits")
        positives += 1

        # Subject drift and policy drift are separate answers.
        moved = build_subject(
            "ed3c/bettor-notes", "9f" * 20, "8e" * 20, MANIFEST_DIGEST, POLICY
        )
        if check_freshness(subject, moved)["state"] != "STALE_SUBJECT":
            raise ContractError("a moved commit was not reported as a stale subject")
        repolicied = build_subject(
            "ed3c/bettor-notes",
            "1a" * 20,
            "2b" * 20,
            MANIFEST_DIGEST,
            {**POLICY, "embedding_dimensions": 768},
        )
        if check_freshness(subject, repolicied)["state"] != "STALE_POLICY":
            raise ContractError(
                "a changed embedding dimension was not reported; an index built with "
                "one model and queried with another returns meaningless neighbours"
            )
        if check_freshness(None, subject)["state"] != "NOT_BUILT":
            raise ContractError("an unbuilt index was not reported as such")
        positives += 1

        # A stale index does not answer.
        stale_result = query(
            {**built, "index_subject": moved}, subject, "compare", root
        )
        if stale_result["micro"]["state"] != "NOT_INDEXED":
            raise ContractError(
                f"a stale index answered with {stale_result['micro']['state']}"
            )
        positives += 1

        # Uncovered evidence is UNKNOWN, not absent.
        partial = coverage(built["chunks"][:1], EVIDENCE)
        if (
            partial["uncovered_state"] != "UNKNOWN"
            or not partial["uncovered_evidence_ids"]
        ):
            raise ContractError("uncovered evidence was not reported as UNKNOWN")
        positives += 1

        # The OpenWiki projection is deterministic and refuses to be its own source.
        again = _built()
        if (
            again["openwiki"]["projection_digest"]
            != built["openwiki"]["projection_digest"]
        ):
            raise ContractError("two builds produced different OpenWiki projections")
        if again["build_digest"] != built["build_digest"]:
            raise ContractError("two builds disagreed")
        positives += 1

        # --- controls -------------------------------------------------------
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

        page_body = built["openwiki"]["pages"][0]["body"]
        expect(
            "openwiki-output-cited-as-its-own-evidence",
            "closes a circle nothing outside can break",
            lambda: admissible_as_evidence(page_body),
        )
        expect(
            "openwiki-copied-into-a-notes-file",
            "closes a circle nothing outside can break",
            # A different filename, the same marker: a path check would miss this.
            lambda: admissible_as_evidence(
                f"# My notes\n\n{page_body}", "notes/copied.md"
            ),
        )
        expect(
            "openwiki-declared-admissible",
            "a claim supporting itself",
            lambda: validate_projection(
                {**built["openwiki"], "admissible_as_evidence": True}
            ),
        )
        expect(
            "index-pinned-to-a-branch",
            "keeps answering after the notes",
            lambda: validate_subject({**subject, "ref_kind": "BRANCH"}),
        )
        expect(
            "chunk-overlap-swallows-the-chunk",
            "one paragraph would be retrieved as several",
            lambda: validate_policy({**POLICY, "chunk_overlap_chars": 200}),
        )
        expect(
            "unnamed-embedding-model",
            "embedding_model",
            lambda: validate_policy({**POLICY, "embedding_model": ""}),
        )
        expect(
            "result-claiming-to-prove-absence",
            "says something about an index",
            lambda: validate_result({**answered["micro"], "absence_proof": "PROVEN"}),
        )
        expect(
            "result-claiming-final-authority",
            "the final authority is",
            lambda: validate_result({**answered["micro"], "authority": "RETRIEVAL"}),
        )
        expect(
            "miss-carrying-hits",
            "is MISS and carries hits",
            lambda: validate_result(
                {**missed["micro"], "hits": answered["micro"]["hits"]}
            ),
        )
        expect(
            "hit-without-provenance",
            "a paragraph nobody can check",
            lambda: validate_result(
                {
                    **answered["micro"],
                    "hits": [
                        {
                            "chunk_id": "c",
                            "text": "t",
                            "provenance": {"source_id": "s"},
                        }
                    ],
                }
            ),
        )

        # A chunk whose source drifted must fail readback rather than pass.
        drifted_root = _tree(Path(tmp) / "drifted")
        (drifted_root / "sources/talk.vtt").write_text(
            "entirely different\n", encoding="utf-8"
        )
        try:
            query(built, subject, "compare-and-set", drifted_root)
        except ContractError as exc:
            if "the citation looks perfect" not in str(exc):
                failures.append(f"readback drift refused for the wrong reason: {exc}")
        else:
            failures.append(
                "a chunk citing text that is no longer in its source passed readback"
            )

        if DERIVED_MARKER not in page_body:
            failures.append("the generated page carries no derived marker")

        # Chunks must be deterministic for one policy.
        if build_chunks(EVIDENCE, TEXTS, POLICY) != build_chunks(
            EVIDENCE, TEXTS, POLICY
        ):
            failures.append("chunking is not deterministic")

    if failures:
        raise ContractError(
            "planted controls did not behave:\n  " + "\n  ".join(failures)
        )
    return positives, 12
