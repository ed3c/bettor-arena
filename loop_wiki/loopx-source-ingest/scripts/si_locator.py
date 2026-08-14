#!/usr/bin/env python3
"""Locators parsed out of captured bytes. Nothing here computes one.

Every function in this file reads. There is no code path that produces a
timestamp from a word count, a page number from a position, or a bounding box
from an assumption -- and that is deliberate rather than incidental: a module
that *could* estimate will, on the day the parse fails and someone needs the
pipeline to finish.

When the bytes do not contain a locator, the answer is a gap. `parse_vtt` on a
file with no cues returns no cues; it does not distribute the text evenly across
a guessed duration.

`speakers_are_not_sources` is here rather than in the corroboration layer because
this is where the temptation appears: a transcript with two speakers looks like
two voices agreeing. It is one recording, one upload, one dependency key.
"""

from __future__ import annotations

import re
from typing import Any

from si_common import (
    VTT_CUE,
    ADMISSIBLE_ORIGIN,
    ContractError,
    non_empty_str,
)

SPEAKER = re.compile(r"^<v\s+([^>]+)>|^([A-Z][A-Za-z .'-]{1,30}):\s")
PDF_PAGE_MARKER = re.compile(r"^===\s*PAGE\s+(\d+)\s*===$")


def parse_vtt(text: str) -> list[dict[str, Any]]:
    """Cues, with their real timestamps. A file with no cues yields none."""
    cues: list[dict[str, Any]] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = VTT_CUE.match(line.strip())
        if match is None:
            continue
        start = f"{match.group(1)}:{match.group(2)}:{match.group(3)}.{match.group(4)}"
        end = f"{match.group(5)}:{match.group(6)}:{match.group(7)}.{match.group(8)}"
        body = []
        for follow in lines[index + 1 :]:
            if not follow.strip() or VTT_CUE.match(follow.strip()):
                break
            body.append(follow)
        cues.append(
            {
                "start": start,
                "end": end,
                "text": "\n".join(body).strip(),
                "speaker": _speaker(body),
                # Recorded on every cue, because the field is what separates a
                # parsed timestamp from a plausible one.
                "locator_origin": ADMISSIBLE_ORIGIN,
                "source_line": index + 1,
            }
        )
    return cues


def _speaker(body: list[str]) -> str | None:
    for line in body:
        match = SPEAKER.match(line.strip())
        if match:
            return (match.group(1) or match.group(2)).strip()
    return None


def parse_pdf_pages(text: str) -> list[dict[str, Any]]:
    """Pages present in the captured text. A missing page is simply not here.

    The extraction format marks pages explicitly. A page that was not extracted
    produces no record at all, which is the point: representing an absent page
    as an observed empty one is the failure #104 names.
    """
    pages: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for index, line in enumerate(text.splitlines(), start=1):
        match = PDF_PAGE_MARKER.match(line.strip())
        if match:
            if current:
                pages.append(current)
            current = {
                "page": int(match.group(1)),
                "text": "",
                "locator_origin": ADMISSIBLE_ORIGIN,
                "source_line": index,
            }
            continue
        if current is not None:
            current["text"] = (current["text"] + "\n" + line).strip()
    if current:
        pages.append(current)
    return pages


def missing_pages(pages: list[dict[str, Any]], declared_page_count: int) -> list[int]:
    """Declared pages with no extracted record. Reported, never filled in."""
    present = {page["page"] for page in pages}
    return sorted(set(range(1, declared_page_count + 1)) - present)


OCR_KEYS = {"text", "artifact_digest", "box", "locator_origin"}


def validate_ocr(value: Any, label: str) -> dict[str, Any]:
    """OCR text needs the artifact it came from and where on it.

    Text without a box is text somebody read off a picture and typed. The box is
    what makes it checkable by a second reader.
    """
    if not isinstance(value, dict) or set(value) != OCR_KEYS:
        raise ContractError(f"{label} fields drifted; expected {sorted(OCR_KEYS)}")
    non_empty_str(value["text"], f"{label}.text")
    non_empty_str(value["artifact_digest"], f"{label}.artifact_digest")

    box = value["box"]
    if (
        not isinstance(box, list)
        or len(box) != 4
        or not all(isinstance(n, int) and n >= 0 for n in box)
    ):
        raise ContractError(
            f"{label}.box must be four non-negative integers; OCR text without a "
            "region is text somebody read off a picture, and nobody else can check it"
        )
    if value["locator_origin"] != ADMISSIBLE_ORIGIN:
        raise ContractError(
            f"{label}.locator_origin is {value['locator_origin']!r}; an OCR box that "
            "was assumed points at a region nobody looked at"
        )
    return value


def speakers_are_not_sources(
    cues: list[dict[str, Any]], dependency_key: str
) -> dict[str, Any]:
    """Speakers in one transcript, and the single dependency key they share.

    Two people agreeing in one recording is one recording. Counting them as two
    corroborating sources raises a confidence ceiling on a single upload.
    """
    speakers = sorted({cue["speaker"] for cue in cues if cue.get("speaker")})
    return {
        "speakers": speakers,
        "speaker_count": len(speakers),
        "dependency_key": dependency_key,
        "independent_sources": 1,
        "note": (
            "one recording, one upload, one dependency key. Speakers inside it are "
            "not independent sources, however many of them there are"
        ),
    }
