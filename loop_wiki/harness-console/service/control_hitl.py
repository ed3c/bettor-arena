#!/usr/bin/env python3
"""Physical control group: real files, real processes, a real cache to corrupt.

The selftest compares structures one process built. The failures #99 names happen
between processes and on disk: a UI cache that has drifted from the ledger, a
request signed in one place and verified in another, a backend that is simply
not there.

So this group:

  * writes the projection to a real file -- the UI cache -- edits it on disk, and
    checks the rebuild comparison catches the drift, then restores it and checks
    the comparison goes green again, so the red is attributable to the edit;
  * signs a request in one interpreter and verifies it in another, because a
    signature that depends on in-process state is not a signature;
  * points the port at a backend that is not there and checks it exits 64 and not
    2. A missing backend is absence, and LoopX correctness does not depend on
    whether a console could load;
  * deletes the projection entirely and rebuilds it from the events, byte for
    byte.

Exits 0 or 2.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "contracts"))

from hc_vocab import BAD, OK, ContractError  # noqa: E402
from hitl_selftest import DRAFT, EVENTS, HEAD, KEY, KEY_ID  # noqa: E402

PORT = HERE / "hitlapi.py"
ROOT = HERE.parents[2]


def run_port(*argv: str, key: str | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop("HITL_SIGNER_KEY", None)
    if key is not None:
        env["HITL_SIGNER_KEY"] = key
    return subprocess.run(
        [sys.executable, str(PORT), *argv, "--root", str(ROOT)],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def verify_in_subprocess(request_path: Path, projection_path: Path, key: str) -> dict:
    """Verify a signature in an interpreter that never saw the signing process."""
    done = run_port(
        "submit",
        "--in",
        str(request_path),
        "--projection",
        str(projection_path),
        key=key,
    )
    if done.returncode not in (0, BAD):
        raise ContractError(f"submit exited {done.returncode}: {done.stderr.strip()}")
    return json.loads(done.stdout)


def main() -> int:
    checks = 0
    key_text = KEY.decode()

    with tempfile.TemporaryDirectory(prefix="hc-control-") as tmp:
        work = Path(tmp)
        events = work / "events.json"
        events.write_text(json.dumps(EVENTS), encoding="utf-8")
        cache = work / "ui-cache.json"

        done = run_port(
            "project", "--events", str(events), "--head", HEAD, "--output", str(cache)
        )
        if done.returncode != 0:
            raise ContractError(f"project failed: {done.stderr.strip()}")
        original = cache.read_text(encoding="utf-8")
        checks += 1

        # 1. Delete the cache entirely and rebuild it. Byte for byte, or the UI
        #    database is holding something no event produced.
        rebuilt = work / "rebuilt.json"
        cache.unlink()
        run_port(
            "project", "--events", str(events), "--head", HEAD, "--output", str(rebuilt)
        )
        if rebuilt.read_text(encoding="utf-8") != original:
            raise ContractError(
                "rebuilding the projection from the same events produced different bytes; "
                "something in the UI database was not derived from an event"
            )
        cache.write_text(original, encoding="utf-8")
        checks += 1

        # 2. Corrupt the cache on disk. Nothing about the file is malformed -- a
        #    task simply says COMPLETED where the ledger says
        #    COMPLETED_WITH_EXCEPTION, which is what a drifted UI database looks
        #    like and exactly what renders identically.
        drifted = json.loads(original)
        drifted["tasks"]["t2"]["state"] = "COMPLETED"
        cache.write_text(
            json.dumps(drifted, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if json.loads(cache.read_text(encoding="utf-8")) == json.loads(original):
            raise ContractError("the planted drift did not change the cache")
        fresh = run_port(
            "project",
            "--events",
            str(events),
            "--head",
            HEAD,
            "--output",
            str(work / "fresh.json"),
        )
        if fresh.returncode != 0:
            raise ContractError("could not rebuild for comparison")
        if json.loads((work / "fresh.json").read_text(encoding="utf-8")) == json.loads(
            cache.read_text(encoding="utf-8")
        ):
            raise ContractError(
                "a cache showing COMPLETED where the ledger says COMPLETED_WITH_EXCEPTION "
                "compared equal to a fresh rebuild"
            )
        checks += 1

        # 3. Restore. A comparison that stays red after the drift is removed is a
        #    broken comparison, not a detection.
        cache.write_text(original, encoding="utf-8")
        if json.loads((work / "fresh.json").read_text(encoding="utf-8")) != json.loads(
            cache.read_text(encoding="utf-8")
        ):
            raise ContractError(
                "the cache stayed different after the drift was reverted"
            )
        checks += 1

        # 4. Draft, sign and verify across three separate interpreters.
        draft_in = work / "draft-in.json"
        draft_in.write_text(json.dumps(DRAFT), encoding="utf-8")
        drafted = work / "drafted.json"
        done = run_port(
            "draft",
            "--request",
            str(draft_in),
            "--projection",
            str(cache),
            "--output",
            str(drafted),
        )
        if done.returncode != 0:
            raise ContractError(f"draft failed: {done.stderr.strip()}")

        signed = work / "signed.json"
        done = run_port(
            "sign",
            "--in",
            str(drafted),
            "--key-id",
            KEY_ID,
            "--output",
            str(signed),
            key=key_text,
        )
        if done.returncode != 0:
            raise ContractError(f"sign failed: {done.stderr.strip()}")
        if key_text in signed.read_text(encoding="utf-8"):
            raise ContractError(
                "the signer key was written into the signed request on disk"
            )
        checks += 1

        outcome = verify_in_subprocess(signed, cache, key_text)
        if outcome["outcome"] != "ACCEPTED":
            raise ContractError(
                f"a valid signed request was rejected: {outcome.get('reason')}"
            )
        if outcome["mutated"] or outcome["gate_verdict_written"]:
            raise ContractError("acceptance mutated state or wrote a gate verdict")
        checks += 1

        # 5. The same request against a projection whose ledger has moved.
        moved_events = work / "moved.json"
        moved_events.write_text(
            json.dumps(
                EVENTS
                + [
                    {
                        "sequence": 12,
                        "kind": "ATTEMPT_STARTED",
                        "task_id": "t1",
                        "payload": {},
                    }
                ]
            ),
            encoding="utf-8",
        )
        moved = work / "moved-projection.json"
        run_port(
            "project",
            "--events",
            str(moved_events),
            "--head",
            HEAD,
            "--output",
            str(moved),
        )
        stale = verify_in_subprocess(signed, moved, key_text)
        if stale["outcome"] != "REJECTED" or "state revision" not in stale["reason"]:
            raise ContractError(
                f"a stale request was {stale['outcome']}: {stale.get('reason')}"
            )
        checks += 1

        # 6. A different key, in a different process.
        wrong = verify_in_subprocess(signed, cache, "a-completely-different-signer-key")
        if wrong["outcome"] != "REJECTED" or "different key" not in wrong["reason"]:
            raise ContractError(
                f"a request verified under the wrong key was {wrong['outcome']}"
            )
        checks += 1

        # 7. No key at all. Absence, not refusal: exit 64, because an
        #    unconfigured operator and a decision that disagreed are different
        #    answers and both are non-zero.
        done = run_port("submit", "--in", str(signed), "--projection", str(cache))
        if done.returncode != 64:
            raise ContractError(
                f"a missing signer key exited {done.returncode}, expected 64. An "
                "unconfigured operator is not a rejected decision"
            )
        checks += 1

        # 8. The backend is not there. LoopX correctness cannot depend on whether
        #    a console could load its projection.
        done = run_port("views", "--projection", str(work / "does-not-exist.json"))
        if done.returncode != 64:
            raise ContractError(
                f"an absent projection exited {done.returncode}, expected 64. A backend "
                "outage is absence, and absence is not a checked invariant disagreeing"
            )
        checks += 1

        # 9. There is no subcommand that merges, promotes or rolls back. Asking
        #    for one is unusable input, and it stays that way.
        for forbidden in ("merge", "promote", "rollback", "force-skip", "mark-pass"):
            done = run_port(forbidden)
            if done.returncode != 64:
                raise ContractError(
                    f"the port answered {forbidden!r} with exit {done.returncode}; the "
                    "console has no such route"
                )
        checks += 1

    print(
        f"harness-console physical control PASS: {checks} controls on a real cache and "
        f"separate processes for signing and verification"
    )
    return OK


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"harness-console physical control RED: {exc}", file=sys.stderr)
        raise SystemExit(BAD) from exc
