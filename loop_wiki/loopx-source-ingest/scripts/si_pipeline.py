#!/usr/bin/env python3
"""The ingest pass, in the order #104 names.

    SOURCE_DECLARED
    -> ACCESS_RIGHTS_DESTINATION_AUTHORIZED
    -> RAW_ARTIFACT_CAPTURED_OR_BLOCKED
    -> CONTENT_DIGESTED
    -> TYPE_DEPENDENCY_KEY_CLASSIFIED
    -> LOCATORS_EXTRACTED
    -> TRANSCRIPT_FRAME_CODE_NORMALIZED
    -> EVIDENCE_MANIFEST_EMITTED
    -> NOTES_REPO_COMMIT_TREE_PINNED
    -> QUALITY_INJECTION_GAP_GATES
    -> READY_FOR_KNOWLEDGE_COMPILATION

The policy snapshot is taken before any source byte is read and compared after
every source has been processed. That comparison is the only thing standing
between "source content is data" as a principle and as a property.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from si_capture import bears_evidence, capture
from si_common import ContractError, digest
from si_injection import assert_no_policy_effect, quarantine, scan, validate_quarantine
from si_locator import (
    missing_pages,
    parse_pdf_pages,
    parse_vtt,
    speakers_are_not_sources,
)
from si_manifest import build_evidence, build_manifest

STATES = [
    "SOURCE_DECLARED",
    "ACCESS_RIGHTS_DESTINATION_AUTHORIZED",
    "RAW_ARTIFACT_CAPTURED_OR_BLOCKED",
    "CONTENT_DIGESTED",
    "TYPE_DEPENDENCY_KEY_CLASSIFIED",
    "LOCATORS_EXTRACTED",
    "TRANSCRIPT_FRAME_CODE_NORMALIZED",
    "EVIDENCE_MANIFEST_EMITTED",
    "NOTES_REPO_COMMIT_TREE_PINNED",
    "QUALITY_INJECTION_GAP_GATES",
    "READY_FOR_KNOWLEDGE_COMPILATION",
]


def _policy_snapshot(declarations: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rights_state": sorted(d["rights_state"] for d in declarations),
        "destination_authorized": sorted(
            str(d["destination_authorized"]) for d in declarations
        ),
        "dependency_key": sorted(d["dependency_key"] for d in declarations),
    }


def ingest(
    subject: dict[str, Any],
    declarations: list[dict[str, Any]],
    artifacts: dict[str, str | None],
    root: Path,
    at: str,
    declared_page_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Run one ingest. Deterministic given its inputs and the files it reads."""
    trace = ["SOURCE_DECLARED"]

    # Taken before a single source byte is read.
    before_policy = _policy_snapshot(declarations)
    trace.append("ACCESS_RIGHTS_DESTINATION_AUTHORIZED")

    captures = [
        capture(declaration, root, artifacts.get(declaration["source_id"]), at)
        for declaration in declarations
    ]
    trace.append("RAW_ARTIFACT_CAPTURED_OR_BLOCKED")
    trace.append("CONTENT_DIGESTED")
    trace.append("TYPE_DEPENDENCY_KEY_CLASSIFIED")

    evidence: list[dict[str, Any]] = []
    findings: dict[str, list[dict[str, Any]]] = {}
    transcripts: dict[str, Any] = {}
    page_gaps: dict[str, list[int]] = {}

    for record in captures:
        if not bears_evidence(record):
            continue
        text = (root / record["artifact_path"]).read_text(
            encoding="utf-8", errors="replace"
        )

        # Wrapped before anything else touches it.
        wrapped = quarantine(text, record["source_id"])
        validate_quarantine(wrapped)
        findings[record["source_id"]] = scan(text)

        if record["source_type"] in {"VTT", "SRT", "YOUTUBE_TRANSCRIPT"}:
            cues = parse_vtt(text)
            transcripts[record["source_id"]] = speakers_are_not_sources(
                cues, record["dependency_key"]
            )
            for cue in cues:
                evidence.append(
                    build_evidence(
                        record,
                        f"{record['locator_base']}#t={cue['start']}",
                        cue["text"],
                        cue["locator_origin"],
                    )
                )
        elif record["source_type"] in {"PDF_PAGE", "PDF_FIGURE"}:
            pages = parse_pdf_pages(text)
            declared = (declared_page_counts or {}).get(record["source_id"])
            if declared:
                page_gaps[record["source_id"]] = missing_pages(pages, declared)
            for page in pages:
                evidence.append(
                    build_evidence(
                        record,
                        f"{record['locator_base']}#page={page['page']}",
                        page["text"],
                        page["locator_origin"],
                    )
                )
        else:
            # Line-addressed text. The locator is the line range that was read.
            lines = text.splitlines()
            evidence.append(
                build_evidence(
                    record,
                    f"{record['locator_base']}#L1-L{max(1, len(lines))}",
                    text,
                    "READ_FROM_ARTIFACT",
                )
            )
    trace.append("LOCATORS_EXTRACTED")
    trace.append("TRANSCRIPT_FRAME_CODE_NORMALIZED")

    manifest = build_manifest(subject, captures, evidence, findings, at)
    trace.append("EVIDENCE_MANIFEST_EMITTED")
    trace.append("NOTES_REPO_COMMIT_TREE_PINNED")

    # After every source has been read. If any of them moved a decision field,
    # a document was followed as an instruction.
    assert_no_policy_effect(
        before_policy,
        _policy_snapshot(declarations),
        [f for group in findings.values() for f in group],
    )
    trace.append("QUALITY_INJECTION_GAP_GATES")
    trace.append("READY_FOR_KNOWLEDGE_COMPILATION")

    return {
        "state_trace": trace,
        "captures": captures,
        "manifest": manifest,
        "transcripts": transcripts,
        "missing_pages": {k: v for k, v in page_gaps.items() if v},
        "ingest_digest": digest(
            {"manifest": manifest["manifest_digest"], "captures": len(captures)}
        ),
    }


def require_ready(result: dict[str, Any]) -> None:
    if result["manifest"]["state"] != "READY_FOR_KNOWLEDGE_COMPILATION":
        raise ContractError(
            f"the manifest is {result['manifest']['state']}; compiling knowledge from "
            "a manifest with no evidence would produce claims with nothing under them"
        )
