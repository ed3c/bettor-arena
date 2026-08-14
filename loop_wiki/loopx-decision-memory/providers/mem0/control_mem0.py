#!/usr/bin/env python3
"""Physical control group. A projection on disk, a real delete, a real store check.

Two claims in #93 are about a *second store*, and a second store is where
in-memory reasoning stops being enough:

**A canonical delete does not delete anything in Mem0.** The index holds its own
copy, and that copy is what a retrieval returns. So this writes the projection
to disk, deletes the memory canonically, rebuilds, writes the new projection
back, and then reads the bytes off disk and searches them.

**An unavailable store is not an empty index.** Here the store is a real
directory: the control removes it and asks the availability probe, so the
`PROVIDER_UNAVAILABLE` path is reached because the filesystem said so rather
than because a flag was set.

Four controls:

1. before the delete, the statement is findable in the projection file --
   without it, control 2 passes because there was nothing to find;
2. after the canonical delete and rebuild, neither the statement nor a fragment
   of it is in the file;
3. a missing store directory yields PROVIDER_UNAVAILABLE, and the same query
   against a present store yields ANSWERED -- so control 3's refusal is
   attributable to the store rather than to the query;
4. two rebuilds of one log write relation-equivalent projections, so the
   equivalence check is not passing on identical bytes it never had to compare.

Exit: 0 all controls behaved, 2 one did not, 64 unusable environment.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
for _sub in ("scripts", "runtime"):
    sys.path.insert(0, str(BASE / _sub))

from memory import ContractError, digest, good_bundle  # noqa: E402

from dmr_pipeline import admit, delete  # noqa: E402
from mem0_projection import build, query, rebuild_equivalent  # noqa: E402

OK, BAD, USAGE = 0, 2, 64

OSS = {
    "mode": "OSS_SELF_HOSTED",
    "package_version": "mem0ai==0.1.9",
    "server_endpoint": None,
    "storage_identity": "local-dir",
    "embedding_identity": "bge-small-en-v1.5",
    "llm_identity": "none",
    "namespace": "bettor-arena",
}
POLICY = {
    "drop_fields": ["evidence_refs"],
    "policy_digest": digest({"drop": ["evidence_refs"]}),
}
NOW = "2026-08-16T10:00:00Z"


def store_availability(store: Path) -> str:
    """Ask the filesystem, not a flag."""
    return "AVAILABLE" if store.is_dir() else "UNAVAILABLE"


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    failures: list[str] = []

    try:
        proposal, decision = good_bundle()
    except Exception as exc:  # noqa: BLE001
        print(f"mem0 control FATAL: {exc}", file=sys.stderr)
        return USAGE

    statement = proposal["statement"]
    fragment = statement[: max(20, len(statement) // 2)]

    with tempfile.TemporaryDirectory(prefix="loopx-mem0-control-") as tmp:
        base = Path(tmp)
        store = base / "store"
        store.mkdir()
        index_file = store / "projection.json"

        log = admit([], proposal, decision)["log"]
        projection = build(log, OSS, POLICY, NOW)
        index_file.write_text(json.dumps(projection, indent=2), encoding="utf-8")

        # --- control 1: the content is in the index file --------------------
        before = index_file.read_text(encoding="utf-8")
        if statement not in before:
            failures.append(
                "the statement is not in the projection file before deletion; with "
                "nothing to remove, control 2 would pass vacuously"
            )

        # --- control 2: after a canonical delete, it is not -----------------
        removed = delete(
            log, proposal["canonical_key"], "ed3c", "2026-08-16T09:00:00Z", "req"
        )
        rebuilt = build(removed["log"], OSS, POLICY, "2026-08-16T12:00:00Z")
        index_file.write_text(json.dumps(rebuilt, indent=2), encoding="utf-8")
        after = index_file.read_text(encoding="utf-8")

        if statement in after:
            failures.append(
                "the removed statement is still in the projection file; a canonical "
                "delete does not reach the index, and the index is what a retrieval "
                "returns"
            )
        if fragment in after:
            failures.append(
                f"a {len(fragment)}-character fragment survived into the index file"
            )
        if rebuilt["record_count"] != 0:
            failures.append(
                f"the rebuilt projection still has {rebuilt['record_count']} record(s)"
            )

        # --- control 3: a real missing store --------------------------------
        present = query(projection, "boundary", store_availability(store))
        if present["state"] != "ANSWERED":
            failures.append(
                f"a query against a present store produced {present['state']}; "
                "control 3's refusal could then be blamed on the query"
            )
        shutil.rmtree(store)
        absent = query(projection, "boundary", store_availability(store))
        if absent["state"] != "PROVIDER_UNAVAILABLE":
            failures.append(
                f"a query against a removed store produced {absent['state']}, not "
                "PROVIDER_UNAVAILABLE"
            )
        if absent["hits"]:
            failures.append("an unavailable store returned hits")

        # --- control 4: two rebuilds agree on relations ---------------------
        try:
            first = rebuild_equivalent(log, projection, POLICY, "2026-08-16T13:00:00Z")
            second = rebuild_equivalent(log, projection, POLICY, "2026-08-16T14:00:00Z")
        except ContractError as exc:
            print(f"mem0 control FATAL: rebuild refused: {exc}", file=sys.stderr)
            return USAGE
        if not first["equivalent"] or not second["equivalent"]:
            failures.append("a rebuild from the same log was not equivalent")
        if first["rebuilt_relation_digest"] != second["rebuilt_relation_digest"]:
            failures.append("two rebuilds produced different relation digests")
        # The built_at timestamps differ, so a byte comparison would have failed
        # here -- which is the reason the check is on relations.
        if first["stored_relation_digest"] != projection["relation_digest"]:
            failures.append("the stored relation digest drifted")

    if failures:
        for line in failures:
            print(f"mem0 control RED: {line}", file=sys.stderr)
        return BAD

    print(
        json.dumps(
            {
                "module": "loopx-decision-memory/providers/mem0",
                "controls": [
                    "statement-is-in-the-projection-file-before-deletion",
                    "statement-and-fragment-absent-after-canonical-delete",
                    "removed-store-directory-yields-provider-unavailable",
                    "two-rebuilds-agree-on-relations-despite-different-timestamps",
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
