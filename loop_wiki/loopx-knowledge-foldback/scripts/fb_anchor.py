#!/usr/bin/env python3
"""Code evidence anchors, and the reason a line number alone is not one.

An anchor that records `src/ledger.py:42` and nothing else is a citation that
stops being true the moment someone inserts a line above it. It does not break
loudly -- it keeps pointing at line 42, which is now a different line, and every
claim resting on it silently changes meaning.

So an anchor pins four things: the commit it was read at, the symbol it names,
the line range, and the **digest of the lines themselves**. Re-checking an anchor
against a tree compares that digest. If the code moved, the anchor is
`STALE_MOVED` and must be re-derived; if the content changed, it is
`STALE_CHANGED`. Neither is silently repaired, because a repaired anchor is
indistinguishable from one that was right all along.

An anchor may never cite a model summary. `MODEL_SUMMARY` is not in the accepted
kinds at all: a summary is a claim about evidence, and using it as its own
evidence closes a loop that no amount of confidence can open.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fb_common import (
    SHA40,
    ContractError,
    exact_object,
    non_empty_str,
    sha256_ref,
    text_digest,
    validate_evidence_class,
)

ANCHOR_KEYS = {
    "anchor_id",
    "kind",
    "path",
    "symbol",
    "line_start",
    "line_end",
    "commit",
    "content_digest",
    "evidence_class",
}

# MODEL_SUMMARY is absent on purpose, and this list is the only place that
# decides what may be cited.
ANCHOR_KINDS = {"SOURCE_LINES", "TEST_CASE", "RUNTIME_TRACE", "INTERFACE_SIGNATURE"}

ANCHOR_STATES = ("FRESH", "STALE_MOVED", "STALE_CHANGED", "ABSENT")


def validate_anchor(value: Any, label: str) -> dict[str, Any]:
    anchor = exact_object(value, ANCHOR_KEYS, label)
    non_empty_str(anchor["anchor_id"], f"{label}.anchor_id")
    non_empty_str(anchor["path"], f"{label}.path")
    non_empty_str(anchor["symbol"], f"{label}.symbol")

    if anchor["kind"] not in ANCHOR_KINDS:
        raise ContractError(
            f"{label}.kind must be one of {sorted(ANCHOR_KINDS)}; a model summary is "
            "a claim about evidence, and citing it as evidence closes a loop that "
            "cannot be opened by checking it again"
        )
    validate_evidence_class(anchor["evidence_class"], f"{label}.evidence_class")

    for field in ("line_start", "line_end"):
        value_ = anchor[field]
        if not isinstance(value_, int) or isinstance(value_, bool) or value_ < 1:
            raise ContractError(f"{label}.{field} must be a positive integer")
    if anchor["line_end"] < anchor["line_start"]:
        raise ContractError(f"{label}.line_end must not precede line_start")

    if SHA40.fullmatch(str(anchor["commit"])) is None:
        raise ContractError(
            f"{label}.commit must be a full 40-hex sha; an anchor without the commit "
            "it was read at cannot be re-checked against anything"
        )
    sha256_ref(anchor["content_digest"], f"{label}.content_digest")
    return anchor


def digest_lines(text: str, line_start: int, line_end: int) -> str:
    """Digest of the anchored lines, exactly as an anchor records them."""
    lines = text.splitlines(keepends=True)
    if line_end > len(lines):
        raise ContractError(
            f"lines {line_start}-{line_end} run past the end of the file "
            f"({len(lines)} lines); a range that does not exist cannot be anchored"
        )
    return text_digest("".join(lines[line_start - 1 : line_end]).encode("utf-8"))


def recheck(anchor: dict[str, Any], tree_root: Path) -> dict[str, Any]:
    """Re-read an anchor against a real tree and say what it is now.

    Returns a state, never a repair. `STALE_MOVED` is reported with the range
    where the content actually is, so a caller can re-derive the anchor
    deliberately -- but the re-derivation is a new anchor, not an edit to this
    one.
    """
    path = tree_root / anchor["path"]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {"anchor_id": anchor["anchor_id"], "state": "ABSENT", "found_at": None}

    lines = text.splitlines(keepends=True)
    span = anchor["line_end"] - anchor["line_start"] + 1

    if anchor["line_end"] <= len(lines):
        here = text_digest(
            "".join(lines[anchor["line_start"] - 1 : anchor["line_end"]]).encode(
                "utf-8"
            )
        )
        if here == anchor["content_digest"]:
            return {
                "anchor_id": anchor["anchor_id"],
                "state": "FRESH",
                "found_at": [anchor["line_start"], anchor["line_end"]],
            }

    # The content may still be in the file, just somewhere else. Saying so is the
    # difference between "this claim is stale" and "this claim is gone", and a
    # fold-back that could not tell them apart would either drop live evidence or
    # keep dead evidence.
    for start in range(1, len(lines) - span + 2):
        window = text_digest(
            "".join(lines[start - 1 : start + span - 1]).encode("utf-8")
        )
        if window == anchor["content_digest"]:
            return {
                "anchor_id": anchor["anchor_id"],
                "state": "STALE_MOVED",
                "found_at": [start, start + span - 1],
            }
    return {
        "anchor_id": anchor["anchor_id"],
        "state": "STALE_CHANGED",
        "found_at": None,
    }


def require_fresh(results: list[dict[str, Any]]) -> None:
    """Every anchor a patch rests on must still point at what it claimed.

    This is the control against fabricated line numbers: a patch built on an
    anchor whose content has moved is a patch citing lines that now say
    something else, and the citation looks perfectly well-formed.
    """
    stale = sorted(r["anchor_id"] for r in results if r["state"] != "FRESH")
    if stale:
        detail = ", ".join(
            f"{r['anchor_id']}={r['state']}" for r in results if r["state"] != "FRESH"
        )
        raise ContractError(
            f"anchors no longer point at the content they recorded: {detail}. Line "
            "numbers carried forward after the source moved are fabricated citations "
            "-- they stay well-formed and start meaning something else"
        )
    _ = stale
