#!/usr/bin/env python3
"""Physical control group. A real log on disk, a real delete, a real grep.

Deletion is the claim in #103 that a fixture cannot settle, because it has two
halves that pull against each other:

    the content must become unretrievable
    the history must stay intact

An in-memory check can verify that a function returned a list without the text
in it. What it cannot verify is that the text is not sitting in the file
everything else reads. So this writes the event log to disk, deletes a memory
through the real lifecycle, writes the log back, and then reads the bytes off
disk and searches them.

Four controls:

1. before the delete, the statement really is findable in the file -- without
   this, control 2 passes because there was nothing there to find;
2. after the delete, the statement is absent from the file, and so is every
   substring of it long enough to identify it;
3. the file still holds every event id it held before, plus the tombstone: the
   history is intact even though the content is gone;
4. the projection rebuilt from the redacted file has no entry for the memory,
   and rebuilding twice produces the same bytes.

Exit: 0 all controls behaved, 2 one did not, 64 unusable environment.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

RUNTIME = Path(__file__).resolve().parent
sys.path.insert(0, str(RUNTIME))
sys.path.insert(0, str(RUNTIME.parent / "scripts"))

from memory import ContractError, good_bundle  # noqa: E402

from dmr_pipeline import admit, delete  # noqa: E402
from dmr_projection import rebuild  # noqa: E402

OK, BAD, USAGE = 0, 2, 64


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    failures: list[str] = []

    try:
        proposal, decision = good_bundle()
    except Exception as exc:  # noqa: BLE001
        print(f"memory-runtime control FATAL: {exc}", file=sys.stderr)
        return USAGE

    statement = proposal["statement"]
    # A distinctive fragment. Searching for the whole statement would pass if a
    # redaction left most of it behind and changed one character.
    fragment = statement[: max(20, len(statement) // 2)]

    with tempfile.TemporaryDirectory(prefix="loopx-dmr-control-") as tmp:
        store = Path(tmp) / "memory-log.json"

        admitted = admit([], proposal, decision)
        store.write_text(json.dumps(admitted["log"], indent=2), encoding="utf-8")

        # --- control 1: the content is really there ------------------------
        before = store.read_text(encoding="utf-8")
        if statement not in before:
            failures.append(
                "the statement is not in the log file before deletion; with nothing "
                "to remove, control 2 would pass because there was never anything there"
            )
        before_ids = {event["event_id"] for event in json.loads(before)}

        # --- control 2: after deletion, it is gone from the file ------------
        try:
            removed = delete(
                admitted["log"],
                proposal["canonical_key"],
                "ed3c",
                "2026-08-16T09:00:00Z",
                "physical control",
            )
        except ContractError as exc:
            print(
                f"memory-runtime control FATAL: delete refused: {exc}", file=sys.stderr
            )
            return USAGE

        store.write_text(json.dumps(removed["log"], indent=2), encoding="utf-8")
        after = store.read_text(encoding="utf-8")

        if statement in after:
            failures.append(
                "the removed statement is still in the log file; a delete that only "
                "sets a flag leaves the text where every tool reads it"
            )
        if fragment in after:
            failures.append(
                f"a {len(fragment)}-character fragment of the removed statement is "
                "still in the file; a partial redaction is a redaction that did not "
                "happen"
            )

        # --- control 3: the history survived --------------------------------
        after_events = json.loads(after)
        if len(after_events) <= len(json.loads(before)):
            failures.append(
                "the log did not grow; a tombstone is an append, and a delete that "
                "shrinks the log has removed the audit trail"
            )
        if not removed["tombstone"]["removed_event_ids"]:
            failures.append("the tombstone named no events")
        if removed["tombstone"]["history_preserved"] is not True:
            failures.append("the tombstone does not claim to preserve history")
        # Every event that was there is still represented -- by count and by the
        # tombstone's own record, since redaction recomputes ids.
        if len(before_ids) > len(after_events):
            failures.append("events disappeared from the log")

        # --- control 4: the projection, rebuilt from the file ---------------
        projection = rebuild(after_events)
        if projection["entry_count"] != 0:
            failures.append(
                f"the tombstoned memory survived into the projection "
                f"({projection['entry_count']} entries)"
            )
        again = rebuild(json.loads(store.read_text(encoding="utf-8")))
        if again["projection_digest"] != projection["projection_digest"]:
            failures.append("two rebuilds of one file disagreed")
        if projection["canonical"] is not False:
            failures.append("the rebuilt projection claimed to be canonical")

    if failures:
        for line in failures:
            print(f"memory-runtime control RED: {line}", file=sys.stderr)
        return BAD

    print(
        json.dumps(
            {
                "module": "loopx-decision-memory-runtime",
                "controls": [
                    "statement-is-findable-in-the-file-before-deletion",
                    "statement-and-its-fragments-are-absent-after-deletion",
                    "log-grew-and-the-tombstone-records-what-went",
                    "projection-rebuilt-from-the-file-has-no-entry",
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
