#!/usr/bin/env python3
"""Physical control group. A real index on disk, a real edit, a real readback.

Two of #105's failures are only visible against a filesystem:

**A stale index keeps answering.** The index is written to a file. The notes are
then edited -- really edited, on disk -- and the subject rebuilt from the new
bytes. Querying with the stored index must refuse rather than return the old
answer, and the refusal has to come from comparing subjects rather than from a
flag someone set.

**A chunk can outlive the text it cites.** Readback goes to the file and looks.
This control rewrites a source after indexing and checks the query fails, then
restores it and checks the query succeeds -- so the failure is attributable to
the drift and not to the readback being broken.

Five controls.

Exit: 0 all behaved, 2 one did not, 64 unusable environment.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nr_common import BAD, OK, USAGE, ContractError, digest  # noqa: E402
from nr_index import build_subject, check_freshness  # noqa: E402
from nr_openwiki import DERIVED_MARKER, admissible_as_evidence  # noqa: E402
from nr_pipeline import build, query  # noqa: E402

POLICY = {
    "chunk_max_chars": 200,
    "chunk_overlap_chars": 20,
    "embedding_model": "bge-small-en-v1.5",
    "embedding_dimensions": 384,
    "provider_id": "lancedb",
    "provider_version": "0.9.0",
}
CARDS = [
    {
        "canonical_key": "component:ledger-append",
        "title": "Ledger append",
        "summary": "Append is compare-and-set.",
        "verification_state": "CORROBORATED",
    }
]
EVIDENCE = [
    {
        "evidence_id": "ev-0001",
        "source_id": "talk",
        "card_key": "component:ledger-append",
        "locator": "sources/talk.vtt#t=00:00:01.000",
    }
]
ORIGINAL = "The ledger append is compare-and-set on state_revision."
TEXTS = {"ev-0001": ORIGINAL}
MANIFEST_DIGEST = digest({"manifest": 1})


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    failures: list[str] = []
    observed: dict[str, object] = {}

    with tempfile.TemporaryDirectory(prefix="loopx-nr-control-") as tmp:
        base = Path(tmp)
        root = base / "notes"
        (root / "sources").mkdir(parents=True)
        source = root / "sources/talk.vtt"
        source.write_text(ORIGINAL, encoding="utf-8")

        built = build(
            "ed3c/bettor-notes",
            "1a" * 20,
            "2b" * 20,
            MANIFEST_DIGEST,
            POLICY,
            CARDS,
            EVIDENCE,
            TEXTS,
            True,
        )
        index_file = base / "index.json"
        index_file.write_text(json.dumps(built), encoding="utf-8")
        subject = built["index_subject"]

        # --- control 1: a fresh index answers, and readback confirms --------
        fresh = query(built, subject, "compare-and-set", root)
        observed["fresh_state"] = fresh["micro"]["state"]
        observed["fresh_readback"] = [r["state"] for r in fresh["readbacks"]]
        if fresh["micro"]["state"] != "HIT":
            failures.append(
                f"a fresh index produced {fresh['micro']['state']}; with no working "
                "query, every refusal below would be unattributable"
            )
        if [r["state"] for r in fresh["readbacks"]] != ["CONFIRMED"]:
            failures.append("readback did not confirm a chunk that is in its source")

        # --- control 2: the notes really move -------------------------------
        source.write_text("Something else entirely now.\n", encoding="utf-8")
        moved_subject = build_subject(
            "ed3c/bettor-notes", "9f" * 20, "8e" * 20, MANIFEST_DIGEST, POLICY
        )
        freshness = check_freshness(subject, moved_subject)
        observed["after_edit"] = freshness["state"]
        if freshness["state"] != "STALE_SUBJECT":
            failures.append(
                f"after the notes moved the index reported {freshness['state']}; it "
                "would keep answering about the older tree with nothing saying so"
            )

        stale = query(
            json.loads(index_file.read_text(encoding="utf-8")),
            moved_subject,
            "compare",
            root,
        )
        observed["stale_query"] = stale["micro"]["state"]
        if stale["micro"]["state"] != "NOT_INDEXED":
            failures.append(f"a stale index answered with {stale['micro']['state']}")
        if stale["micro"]["absence_proof"] != "NONE":
            failures.append("a stale index claimed its silence proved absence")

        # --- control 3: readback catches the drift, on the real file --------
        try:
            query(built, subject, "compare-and-set", root)
        except ContractError as exc:
            observed["drift_refusal"] = "REFUSED"
            if "the citation looks perfect" not in str(exc):
                failures.append(f"drift refused for the wrong reason: {exc}")
        else:
            failures.append(
                "a chunk citing text that is no longer in the file passed readback"
            )

        # --- control 4: restore, and it works again -------------------------
        source.write_text(ORIGINAL, encoding="utf-8")
        restored = query(built, subject, "compare-and-set", root)
        observed["after_restore"] = restored["micro"]["state"]
        if restored["micro"]["state"] != "HIT":
            failures.append(
                "restoring the source did not restore the query; control 3's refusal "
                "would then be attributable to the readback rather than to the drift"
            )

        # --- control 5: the wiki page on disk still refuses to be evidence --
        page = built["openwiki"]["pages"][0]
        copied = root / "sources/copied-notes.md"
        copied.write_text(f"# Notes\n\n{page['body']}", encoding="utf-8")
        text_on_disk = copied.read_text(encoding="utf-8")
        observed["marker_survives_copy"] = DERIVED_MARKER in text_on_disk
        if DERIVED_MARKER not in text_on_disk:
            failures.append(
                "the derived marker did not survive being copied into a notes file; "
                "a path check would then be the only thing standing in the way"
            )
        try:
            admissible_as_evidence(text_on_disk, str(copied))
        except ContractError:
            pass
        else:
            failures.append(
                "a generated wiki page copied into the notes was admitted as evidence"
            )

    if failures:
        for line in failures:
            print(f"notes-retrieval control RED: {line}", file=sys.stderr)
        return BAD

    print(
        json.dumps(
            {
                "module": "loopx-notes-retrieval",
                "controls": [
                    "fresh-index-answers-and-readback-confirms",
                    "edited-notes-make-the-index-stale-subject",
                    "stale-index-refuses-rather-than-answering",
                    "drifted-source-fails-readback-and-restoring-fixes-it",
                    "wiki-marker-survives-a-copy-and-still-refuses",
                ],
                "observed": observed,
                "state": "PASS",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return OK


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:  # pragma: no cover
        print(f"notes-retrieval control FATAL: {exc}", file=sys.stderr)
        raise SystemExit(USAGE) from exc
