#!/usr/bin/env python3
"""Physical control group. Real files, real edits, real re-anchoring.

The fabricated-line-number failure is the one control in this module that a
fixture cannot honestly answer. A fixture can hand `recheck` the answer
`STALE_MOVED` and watch the pipeline refuse, but that tests the refusal, not the
detection -- and detection is the part that has to work on a file nobody
annotated.

So this builds a real source file, records a real anchor over real lines, then
edits the file the four ways code actually changes, and asks `recheck` what it
finds each time:

1. **untouched** -- the anchor is FRESH. Without this, a detector that returned
   STALE for everything would pass controls 2-4 and be useless in practice;
2. **lines inserted above** -- the anchored code is byte-identical but now lives
   ten lines down. The old line numbers still resolve, and they resolve to
   something else. This is the failure: the citation stays well-formed and
   quietly starts meaning a different thing;
3. **the anchored code itself edited** -- STALE_CHANGED, and no `found_at`,
   because it is not anywhere;
4. **the file deleted** -- ABSENT, which is not the same answer as either.

Exit: 0 all controls behaved, 2 one did not, 64 unusable environment.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fb_anchor import digest_lines, recheck, require_fresh  # noqa: E402
from fb_common import BAD, OK, ContractError  # noqa: E402

SOURCE = """import time


def retry_interval(attempt):
    # The anchored region starts here.
    if attempt < 1:
        raise ValueError("attempt must be positive")
    return 5.0


def unrelated(x):
    return x + 1
"""

ANCHOR_START, ANCHOR_END = 4, 8


def _anchor(root: Path, commit: str) -> dict[str, object]:
    text = (root / "src/retry.py").read_text(encoding="utf-8")
    return {
        "anchor_id": "an-retry",
        "kind": "SOURCE_LINES",
        "path": "src/retry.py",
        "symbol": "retry_interval",
        "line_start": ANCHOR_START,
        "line_end": ANCHOR_END,
        "commit": commit,
        "content_digest": digest_lines(text, ANCHOR_START, ANCHOR_END),
        "evidence_class": "STATIC",
    }


def _tree(base: Path, name: str, body: str) -> Path:
    root = base / name
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src/retry.py").write_text(body, encoding="utf-8")
    return root


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="loopx-fb-control-") as tmp:
        base = Path(tmp)
        before = _tree(base, "before", SOURCE)
        anchor = _anchor(before, "1a" * 20)

        # --- control 1: an untouched tree must be FRESH ----------------------
        state = recheck(anchor, before)
        if state["state"] != "FRESH":
            failures.append(
                f"an unchanged file reported {state['state']}; a detector that is "
                "stale for everything would pass every control below and catch "
                "nothing in practice"
            )
        if state["found_at"] != [ANCHOR_START, ANCHOR_END]:
            failures.append(f"FRESH anchor reported found_at={state['found_at']}")

        # --- control 2: the code moved, byte for byte ------------------------
        moved = _tree(base, "moved", "\n" * 10 + SOURCE)
        state = recheck(anchor, moved)
        if state["state"] != "STALE_MOVED":
            failures.append(
                f"code shifted ten lines down reported {state['state']}; the old line "
                "numbers still resolve, they just resolve to something else, and a "
                "citation that stays well-formed while changing meaning is the whole "
                "failure"
            )
        elif state["found_at"] != [ANCHOR_START + 10, ANCHOR_END + 10]:
            failures.append(
                f"moved content found at {state['found_at']}, expected "
                f"{[ANCHOR_START + 10, ANCHOR_END + 10]}"
            )
        # And the thing now sitting at the old line numbers is not what was cited.
        shifted_text = (moved / "src/retry.py").read_text(encoding="utf-8")
        if (
            digest_lines(shifted_text, ANCHOR_START, ANCHOR_END)
            == anchor["content_digest"]
        ):
            failures.append(
                "the old line range still digests to the anchored content; this "
                "control cannot demonstrate movement"
            )

        # --- control 3: the anchored code itself changed ---------------------
        edited = _tree(base, "edited", SOURCE.replace("return 5.0", "return 1.0"))
        state = recheck(anchor, edited)
        if state["state"] != "STALE_CHANGED":
            failures.append(
                f"edited anchored code reported {state['state']}, not STALE_CHANGED"
            )
        elif state["found_at"] is not None:
            failures.append(
                "STALE_CHANGED reported a location for content that is gone"
            )

        # --- control 4: the file is not there --------------------------------
        state = recheck(anchor, base / "absent")
        if state["state"] != "ABSENT":
            failures.append(
                f"a missing file reported {state['state']}; absence and staleness are "
                "different answers and a caller must be able to tell them apart"
            )

        # --- the gate itself: a stale anchor must stop a fold-back -----------
        try:
            require_fresh([recheck(anchor, moved)])
        except ContractError:
            pass
        else:
            failures.append("require_fresh admitted a moved anchor")
        try:
            require_fresh([recheck(anchor, before)])
        except ContractError as exc:
            failures.append(f"require_fresh rejected a fresh anchor: {exc}")

    if failures:
        for line in failures:
            print(f"foldback control RED: {line}", file=sys.stderr)
        return BAD

    print(
        json.dumps(
            {
                "module": "loopx-knowledge-foldback",
                "controls": [
                    "untouched-tree-is-fresh",
                    "shifted-code-is-stale-moved-with-its-new-range",
                    "edited-code-is-stale-changed-with-no-location",
                    "missing-file-is-absent",
                    "require-fresh-refuses-moved-and-admits-fresh",
                ],
                "state": "PASS",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
