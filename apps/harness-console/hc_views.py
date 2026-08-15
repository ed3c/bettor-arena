#!/usr/bin/env python3
"""The eight views, as bounded data. No HTML, no socket, no browser.

This is the view *model* layer. Rendering is NOT_IMPLEMENTED and says so -- what
is here is the thing a renderer would render, which is also the thing that can be
checked: that each view is bounded, that it is derived only from the projection,
and that none of them can show a gate as passing or an exception as an ordinary
completion.

Bounded matters more than it sounds. An unbounded diff or an unbounded log is how
a console becomes the place a secret is persisted at scale, and it is also how a
UI stops responding on the one task anyone needed to look at. Every view truncates
and every view says it truncated -- a truncated list that does not say so is a
shorter list, and a shorter list looks complete.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(
    0, str(Path(__file__).resolve().parents[2] / "packages/harness-console-contracts")
)

from hc_vocab import (  # noqa: E402
    RENDER_STATE,
    VIEWS,
    ContractError,
    digest,
    find_unredacted,
)

# Per-view caps. Small on purpose: the console is for looking at one subject, and
# a view that can render ten thousand rows is a view that will be asked to.
LIMITS = {
    "thread_task_graph": 200,
    "gate_evidence_inspector": 100,
    "diagnostics_panel": 100,
    "git_diff_viewer": 50,
    "quota_retry_panel": 50,
    "provenance_panel": 100,
    "receipt_links": 50,
}

# Bytes of diff text any single entry may carry.
DIFF_BYTES = 4096


def _bounded(items: list[Any], view: str) -> dict[str, Any]:
    limit = LIMITS[view]
    kept = items[:limit]
    return {
        "items": kept,
        "shown": len(kept),
        "total": len(items),
        # Stated, always, including when nothing was dropped. A field that only
        # appears when it is interesting is a field nobody looks for.
        "truncated": len(items) > limit,
        "limit": limit,
    }


def thread_task_graph(projection: dict[str, Any]) -> dict[str, Any]:
    """Task topology with parent links, and the exception state kept separate."""
    tasks = list(projection["tasks"].values())
    view = _bounded(tasks, "thread_task_graph")
    by_state: dict[str, int] = {}
    for task in tasks:
        by_state[task["state"]] = by_state.get(task["state"], 0) + 1
    return {
        **view,
        "counts_by_state": dict(sorted(by_state.items())),
        # Counted on its own line. Folded into `COMPLETED` it disappears, and the
        # summary that hides it is the one a reader trusts.
        "completed_with_exception": by_state.get("COMPLETED_WITH_EXCEPTION", 0),
        "completed_clean": by_state.get("COMPLETED", 0),
    }


def gate_evidence_inspector(projection: dict[str, Any]) -> dict[str, Any]:
    """Gate verdicts exactly as the ledger recorded them."""
    gates = projection["gates"]
    view = _bounded(gates, "gate_evidence_inspector")
    verdicts: dict[str, int] = {}
    for gate in gates:
        verdicts[gate["verdict"]] = verdicts.get(gate["verdict"], 0) + 1
    return {
        **view,
        "counts_by_verdict": dict(sorted(verdicts.items())),
        # The console displays a verdict. It has no code path that writes one, and
        # this field is here so a receipt built from this view says so too.
        "may_write_verdict": False,
    }


def diagnostics_panel(projection: dict[str, Any]) -> dict[str, Any]:
    return _bounded(projection["diagnostics"], "diagnostics_panel")


def git_diff_viewer(projection: dict[str, Any]) -> dict[str, Any]:
    """Diffs, truncated per entry as well as per list."""
    trimmed = []
    for entry in projection["diffs"]:
        text = str(entry.get("patch", ""))
        encoded = text.encode("utf-8")
        trimmed.append(
            {
                **entry,
                "patch": text
                if len(encoded) <= DIFF_BYTES
                else encoded[:DIFF_BYTES].decode("utf-8", "ignore"),
                "patch_bytes": len(encoded),
                "patch_truncated": len(encoded) > DIFF_BYTES,
            }
        )
    return _bounded(trimmed, "git_diff_viewer")


def quota_retry_panel(projection: dict[str, Any]) -> dict[str, Any]:
    return _bounded(projection["quota"], "quota_retry_panel")


def provenance_panel(projection: dict[str, Any]) -> dict[str, Any]:
    return _bounded(projection["provenance"], "provenance_panel")


def hitl_dialog(projection: dict[str, Any]) -> dict[str, Any]:
    """What the dialog can offer. The closed set, plus the bindings it will carry."""
    from hc_vocab import CONSOLE_MAY, CONSOLE_MAY_NOT

    return {
        "available_actions": sorted(CONSOLE_MAY),
        "refused_actions": sorted(CONSOLE_MAY_NOT),
        "binds_ledger_head": projection["ledger_head"],
        "binds_state_revision": projection["state_revision"],
        "requires_signature": True,
        # A dialog that can be opened on a gapped projection is a dialog that
        # drafts a decision about history it did not show.
        "draftable": projection["completeness"] == "COMPLETE",
        "reason": (
            "ready"
            if projection["completeness"] == "COMPLETE"
            else f"projection is missing events {projection['missing_sequences']}"
        ),
    }


def receipt_links(projection: dict[str, Any]) -> dict[str, Any]:
    """Stack, host and runtime receipts, as references rather than copies."""
    links = [
        {"kind": entry.get("kind"), "ref": entry.get("ref")}
        for entry in projection["provenance"]
        if entry.get("ref")
    ]
    return _bounded(links, "receipt_links")


BUILDERS = {
    "thread_task_graph": thread_task_graph,
    "gate_evidence_inspector": gate_evidence_inspector,
    "diagnostics_panel": diagnostics_panel,
    "git_diff_viewer": git_diff_viewer,
    "quota_retry_panel": quota_retry_panel,
    "provenance_panel": provenance_panel,
    "hitl_dialog": hitl_dialog,
    "receipt_links": receipt_links,
}


def render(projection: dict[str, Any]) -> dict[str, Any]:
    """Every view, built from the projection and nothing else."""
    missing = sorted(set(VIEWS) - set(BUILDERS))
    if missing:
        raise ContractError(
            f"views {missing} are declared and have no builder. A declared view with no "
            "builder is a screen nobody opened, and it is indistinguishable from one "
            "that renders empty"
        )
    views = {name: BUILDERS[name](projection) for name in sorted(VIEWS)}

    leaks = find_unredacted(views)
    if leaks:
        raise ContractError(
            f"the rendered views contain {leaks}. This is the last point before a "
            "screen or a cache"
        )

    return {
        "schema_version": "loopx/console-views/v1",
        "ledger_head": projection["ledger_head"],
        "state_revision": projection["state_revision"],
        "completeness": projection["completeness"],
        "views": views,
        "view_count": len(views),
        # There is no HTML here, no websocket and no browser. Carried on the
        # output so the claim travels with anything built from it.
        "render_state": RENDER_STATE,
        "authority": "READ_ONLY_PROJECTION",
        "views_digest": digest(views),
    }
