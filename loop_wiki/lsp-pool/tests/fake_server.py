#!/usr/bin/env python3
"""A deterministic language server stand-in, run as a real subprocess.

Not a mock object. The physical control needs a process that can actually crash,
actually hang, and actually return results for the wrong workspace, because
those are the three behaviours the pool has to survive and none of them can be
demonstrated by a function that returns a dict.

Protocol: one JSON request on stdin, one JSON response on stdout.

    {"kind": "...", "path": "...", "workspace_id": "...", "behaviour": "..."}

Behaviours, each corresponding to a control:

    normal        index the workspace and answer honestly
    crash         exit non-zero without writing anything
    hang          never respond
    wrong-tree    answer with another workspace's provenance
    empty-on-fail exit zero having found nothing, without indexing anything
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path


def main() -> int:
    try:
        request = json.loads(sys.stdin.readline())
    except (json.JSONDecodeError, ValueError):
        return 64

    behaviour = request.get("behaviour", "normal")

    if behaviour == "crash":
        print("fake-server: index corrupted", file=sys.stderr)
        return 3
    if behaviour == "hang":
        time.sleep(300)
        return 0

    root = Path(request["root"])
    path = root / request["path"]
    indexed = path.is_file()

    findings = []
    if indexed and behaviour != "empty-on-fail":
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(text.splitlines(), start=1):
            if "TODO" in line:
                findings.append(
                    {
                        "line": number,
                        "column": line.index("TODO") + 1,
                        "message": "TODO left in source",
                        "severity": "WARNING",
                        "source": "fake-server",
                    }
                )

    workspace_id = request["workspace_id"]
    if behaviour == "wrong-tree":
        # Answers with a neighbouring workspace's identity. Everything else about
        # the response is well-formed, which is the point.
        workspace_id = request.get("other_workspace_id", "workspace-elsewhere")

    json.dump(
        {
            "workspace_id": workspace_id,
            "indexed": indexed and behaviour != "empty-on-fail",
            "findings": findings,
        },
        sys.stdout,
    )
    sys.stdout.write("\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
