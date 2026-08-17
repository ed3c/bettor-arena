#!/usr/bin/env python3
"""Planted misbehaving carrier used only by `run_live_lane.py --selftest`.

It emits a well-formed event stream and exits 0, but writes one file into the
leased worktree. A `READ_ONLY` request must therefore go RED at the gateway.
Keeping the plant in its own entry file means the production carrier carries no
selftest branch that a stray environment variable could flip.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from carrier import event, load_json, write_events

PLANTED = "loopx-91-planted-dirt.txt"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="planted read-only violation")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    request = load_json(args.request)
    (args.workspace / PLANTED).write_text("planted control\n", encoding="utf-8")
    write_events(
        args.events,
        [
            event(request, 0, "PROCESS_STARTED", "planted carrier started"),
            event(request, 1, "STDOUT", f"planted carrier wrote {PLANTED}"),
            event(request, 2, "PROCESS_EXIT", "planted carrier exited", exit_code=0),
        ],
    )
    print("planted carrier completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
