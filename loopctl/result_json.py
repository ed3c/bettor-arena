#!/usr/bin/env python3
"""One machine-readable result for a loopctl invocation.

Everything arrives in the environment, so the shell never builds JSON by hand —
a wrapper that hand-rolls quoting produces output that parses until the day a
path contains a quote.

What it carries and why:
    exit        the target's own code, unchanged. 0 ok, 2 the loop's check
                failed, 64 usage or a FATAL. A caller that flattens these cannot
                tell a red gate from a crash, which is why they are never mapped.
    artifacts   the paths this run actually produced, scraped from the target's
                own PASS/receipt lines and reported repo-relative. A caller
                should not have to know where each loop writes.
    stdout/err  captured, truncated, and TRUNCATION IS DECLARED. A silently cut
                stream reads as a complete one, and the tail is where failures
                say what happened.

Truncation keeps the TAIL, not the head: a target that fails prints its reason
last, and a head-truncated log hides exactly the line worth reading.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

LIMIT = 8000
# Paths the loops announce on success. Anchored to the announcement rather than
# guessed from a directory listing, so an artifact from an earlier run is never
# reported as this run's.
PATTERNS = (
    re.compile(r"route_result=(\S+)"),
    re.compile(r"wiki_update_request=(\S+)"),
    re.compile(r"receipt=(\S+)"),
    re.compile(r"^proof\[\w+\] digest=(?P<digest>[0-9a-f]{64})", re.M),
)


def tail(text: str) -> tuple[str, bool]:
    if len(text) <= LIMIT:
        return text, False
    return text[-LIMIT:], True


def main() -> int:
    capture = Path(os.environ["LOOPCTL_CAPTURE"])
    root = os.environ["LOOPCTL_ROOT"].rstrip("/") + "/"
    out = (capture / "out").read_text(encoding="utf-8", errors="replace")
    err = (capture / "err").read_text(encoding="utf-8", errors="replace")

    artifacts, digest = [], None
    for pattern in PATTERNS:
        for match in pattern.finditer(out + "\n" + err):
            value = match.group(match.lastindex or 1)
            if pattern.groupindex.get("digest"):
                digest = value
                continue
            artifacts.append(value.replace(root, ""))

    out_text, out_cut = tail(out)
    err_text, err_cut = tail(err)
    result = {
        "schema_version": "bettor-arena-loopctl-result@1.0.0",
        "loop": os.environ["LOOPCTL_LOOP"],
        "mode": os.environ["LOOPCTL_MODE"],
        "target": os.environ["LOOPCTL_TARGET"],
        "exit": int(os.environ["LOOPCTL_EXIT"]),
        "ok": int(os.environ["LOOPCTL_EXIT"]) == 0,
        "artifacts": sorted(set(artifacts)),
        "proof_digest": digest,
        "stdout": out_text,
        "stdout_truncated": out_cut,
        "stderr": err_text,
        "stderr_truncated": err_cut,
        "exit_meaning": "0 ok · 2 the loop's own check failed · 64 usage, contract "
        "violation, or a FATAL from the target. Never re-mapped by this CLI.",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------- selftest


def _selftest() -> int:
    red = 0

    def case(name: str, got, want) -> None:
        nonlocal red
        if got != want:
            print(
                f"SELFTEST case failed — {name}: got {got!r}, want {want!r}",
                file=sys.stderr,
            )
            red = 1

    body, cut = tail("x" * (LIMIT + 50))
    case("oversize-is-cut", cut, True)
    case("cut-keeps-the-tail-length", len(body), LIMIT)
    # The tail, not the head: a failing target says why on its last line.
    tail_text, _ = tail("head" + "y" * LIMIT + "THE REASON")
    case("cut-keeps-the-end", tail_text.endswith("THE REASON"), True)
    case("small-is-untouched", tail("short"), ("short", False))

    line = "PASS: route_result=/repo/a/route-result.x.json wiki_update_request=/repo/b/request-x.json"
    found = []
    for pattern in PATTERNS:
        for match in pattern.finditer(line):
            if not pattern.groupindex.get("digest"):
                found.append(match.group(1).replace("/repo/", ""))
    case(
        "artifacts-scraped-from-the-announcement",
        sorted(found),
        ["a/route-result.x.json", "b/request-x.json"],
    )

    digests = [
        m.group("digest")
        for m in PATTERNS[-1].finditer("proof[micro] digest=" + "a" * 64 + " files=3")
    ]
    case("digest-scraped", digests, ["a" * 64])
    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        raise SystemExit(_selftest())
    raise SystemExit(main())
