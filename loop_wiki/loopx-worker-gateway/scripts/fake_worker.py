#!/usr/bin/env python3
# ruff: noqa: F401,F403,F405  # this module family composes through star imports; the names ruff reads as unused are deliberate re-exports the downstream modules import through.
"""Deterministic fixture Worker used only by LoopX Gateway controls."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

from gateway_common import digest, load_json, write_json_atomic


def event(
    request: dict[str, Any],
    sequence: int,
    kind: str,
    payload: dict[str, Any],
    visibility: str = "EXTERNAL",
) -> dict[str, Any]:
    value = {
        "schema_version": "loopx/worker-event/v1",
        "event_id": f"fixture-event-{sequence}",
        "request_id": request["request_id"],
        "host_id": request["host_id"],
        "sequence": sequence,
        "occurred_at": f"2026-08-14T00:00:0{sequence}Z",
        "kind": kind,
        "visibility": visibility,
        "payload": payload,
        "content_digest": None,
    }
    raw = copy.deepcopy(value)
    raw.pop("content_digest")
    value["content_digest"] = digest(raw)
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    request = load_json(args.request)
    args.output.mkdir(parents=True, exist_ok=True)
    events = [
        event(
            request,
            0,
            "PROCESS_STARTED",
            {
                "message": "fixture Worker started",
                "exit_code": None,
                "tool": None,
                "artifact_ref": None,
                "cleanup_state": None,
            },
        ),
    ]
    if request["task"]["mode"] == "EDIT":
        target = args.workspace / request["workspace"]["writable_paths"][0]
        if target.suffix:
            target.parent.mkdir(parents=True, exist_ok=True)
        else:
            target.mkdir(parents=True, exist_ok=True)
            target = target / "result.txt"
        target.write_text("fixture Worker output\n", encoding="utf-8")
    events.append(
        event(
            request,
            1,
            "STDOUT",
            {
                "message": "fixture Worker completed",
                "exit_code": None,
                "tool": None,
                "artifact_ref": None,
                "cleanup_state": None,
            },
        )
    )
    events.append(
        event(
            request,
            2,
            "PROCESS_EXIT",
            {
                "message": "fixture Worker exited",
                "exit_code": 0,
                "tool": None,
                "artifact_ref": None,
                "cleanup_state": None,
            },
        )
    )
    args.events.parent.mkdir(parents=True, exist_ok=True)
    args.events.write_text(
        "\n".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            for item in events
        )
        + "\n",
        encoding="utf-8",
    )
    print("fixture Worker completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
