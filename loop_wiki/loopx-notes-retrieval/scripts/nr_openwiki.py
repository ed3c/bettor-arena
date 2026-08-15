#!/usr/bin/env python3
"""The static OpenWiki projection: navigation, and the circle it must not close.

An OpenWiki page is generated from cards and evidence. It summarises, it links,
it gives a person somewhere to start. What it must never do is become an input
to the thing that generated it -- a summary cited as evidence for the claim it
summarises is a claim supporting itself, and every rebuild makes the circle
tighter rather than looser.

So every generated page carries `is_derived: true` and the digest of what it was
derived from, and `admissible_as_evidence` refuses any path that carries this
projection's own marker. The check is on the content, because a page that has
been copied into a notes file loses its filename and keeps its marker.

The projection is deterministic: same cards, same evidence, same bytes. That is
what makes "delete and rebuild" a safe operation rather than a hopeful one.
"""

from __future__ import annotations

from typing import Any

from nr_common import ContractError, digest, non_empty_str, text_digest

# Written into every generated page. A page that lost its filename keeps this.
DERIVED_MARKER = "<!-- loopx:openwiki-derived-projection -->"

PAGE_KEYS = {"path", "title", "body", "derived_from", "is_derived", "body_digest"}


def render_page(card: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    """One page from one card. Deterministic in its inputs."""
    non_empty_str(card.get("canonical_key", ""), "card.canonical_key")
    cited = sorted(evidence, key=lambda record: record["evidence_id"])

    lines = [
        DERIVED_MARKER,
        "",
        f"# {card['title']}",
        "",
        "> Generated from cards and evidence. This page is a projection: it is a",
        "> place to start, and it is not evidence for anything it says.",
        "",
        card.get("summary", ""),
        "",
        "## Evidence",
        "",
    ]
    for record in cited:
        lines.append(
            f"- `{record['evidence_id']}` — {record['locator']} "
            f"(source `{record['source_id']}`)"
        )
    lines += [
        "",
        "## Epistemic status",
        "",
        f"- {card.get('verification_state', 'UNVERIFIED')}",
    ]
    body = "\n".join(lines) + "\n"

    return {
        "path": f"wiki/{card['canonical_key'].replace(':', '/')}.md",
        "title": card["title"],
        "body": body,
        "derived_from": {
            "card_key": card["canonical_key"],
            "evidence_ids": [record["evidence_id"] for record in cited],
        },
        "is_derived": True,
        "body_digest": text_digest(body.encode("utf-8")),
    }


def build_projection(
    cards: list[dict[str, Any]],
    evidence_by_card: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    pages = [
        render_page(card, evidence_by_card.get(card["canonical_key"], []))
        for card in sorted(cards, key=lambda card: card["canonical_key"])
    ]
    projection = {
        "schema_version": "loopx/openwiki-projection/v1",
        "pages": pages,
        "page_count": len(pages),
        "navigation": sorted(
            ({"path": page["path"], "title": page["title"]} for page in pages),
            key=lambda entry: entry["path"],
        ),
        "is_derived": True,
        "admissible_as_evidence": False,
        "authority": "NAVIGATION_ONLY",
    }
    projection["projection_digest"] = digest(
        {k: v for k, v in projection.items() if k != "projection_digest"}
    )
    return projection


def validate_projection(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != (
        "loopx/openwiki-projection/v1"
    ):
        raise ContractError("OpenWiki projection schema version drifted")
    if value.get("admissible_as_evidence") is not False:
        raise ContractError(
            "the OpenWiki projection claims to be admissible as evidence; a summary "
            "cited as evidence for the claim it summarises is a claim supporting "
            "itself, and every rebuild tightens the circle"
        )
    if value.get("authority") != "NAVIGATION_ONLY":
        raise ContractError("OpenWiki authority drifted from navigation")
    for index, page in enumerate(value.get("pages", [])):
        if set(page) != PAGE_KEYS:
            raise ContractError(f"pages[{index}] fields drifted")
        if page["is_derived"] is not True:
            raise ContractError(f"pages[{index}] does not declare itself derived")
        if DERIVED_MARKER not in page["body"]:
            raise ContractError(
                f"pages[{index}] has no derived marker in its body; a page copied into "
                "a notes file loses its filename and keeps its content"
            )
        if page["body_digest"] != text_digest(page["body"].encode("utf-8")):
            raise ContractError(f"pages[{index}] body digest does not match its body")
    recomputed = digest({k: v for k, v in value.items() if k != "projection_digest"})
    if value.get("projection_digest") != recomputed:
        raise ContractError("OpenWiki projection digest does not match its content")
    return value


def admissible_as_evidence(text: str, label: str = "source text") -> None:
    """Refuse text that is this projection's own output.

    Checked on the content rather than the path. A generated page copied into a
    notes file arrives with a new name and the same marker, and the name is what
    a path check would look at.
    """
    if DERIVED_MARKER in text:
        raise ContractError(
            f"{label} carries the OpenWiki derived marker; this is generated output "
            "being offered as evidence for what generated it. The page summarises the "
            "cards -- citing it back closes a circle nothing outside can break"
        )
