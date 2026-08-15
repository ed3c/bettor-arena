#!/usr/bin/env python3
"""Control group: drive the public port as an outside caller would.

The selftest exercises the functions. This exercises the CLI -- argv shapes,
exit codes and the bytes that reach disk -- because a module whose library is
correct and whose entry point is not is still broken for everyone who uses it.

Every assertion is on an exit code or on emitted bytes, never on an internal
value, so it cannot pass merely by agreeing with the implementation.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

OK, BAD, USAGE = 0, 2, 64


def run(root: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(root / "scripts" / "hitl.py"), *argv],
        capture_output=True,
        text=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    root = parser.parse_args().root.resolve()
    good = root / "tests" / "fixtures" / "good"
    hollow = root / "tests" / "fixtures" / "hollow"
    failures: list[str] = []

    def expect(label: str, result: subprocess.CompletedProcess[str], code: int) -> None:
        if result.returncode != code:
            failures.append(
                f"{label}: expected exit {code}, got {result.returncode}; "
                f"stderr={result.stderr.strip()[:200]}"
            )

    expect("check", run(root, ["check", "--root", str(root)]), OK)
    expect("selftest", run(root, ["selftest", "--root", str(root)]), OK)
    expect(
        "validate-interrupt positive",
        run(root, ["validate-interrupt", "--interrupt", str(good / "interrupt.json")]),
        OK,
    )
    expect(
        "validate-checkpoint positive",
        run(
            root, ["validate-checkpoint", "--checkpoint", str(good / "checkpoint.json")]
        ),
        OK,
    )
    expect(
        "validate-decision positive",
        run(
            root,
            [
                "validate-decision",
                "--decision",
                str(good / "decision.json"),
                "--gate-classes",
                str(good / "gate-classes.json"),
            ],
        ),
        OK,
    )
    # Readable and wrong exits 2; absent exits 64. Absence is not a verdict.
    expect(
        "validate-decision hollow",
        run(
            root,
            [
                "validate-decision",
                "--decision",
                str(hollow / "decision.json"),
                "--gate-classes",
                str(good / "gate-classes.json"),
            ],
        ),
        BAD,
    )
    expect(
        "absent input",
        run(
            root,
            [
                "validate-decision",
                "--decision",
                str(good / "does-not-exist.json"),
                "--gate-classes",
                str(good / "gate-classes.json"),
            ],
        ),
        USAGE,
    )
    expect("unknown subcommand", run(root, ["not-a-command"]), USAGE)
    expect("no subcommand", run(root, []), USAGE)

    with tempfile.TemporaryDirectory() as tmp:
        envelope_path = Path(tmp) / "resume-envelope.json"
        expect(
            "resume",
            run(
                root,
                [
                    "resume",
                    "--interrupt",
                    str(good / "interrupt.json"),
                    "--decision",
                    str(good / "decision.json"),
                    "--state",
                    str(good / "state.json"),
                    "--gate-classes",
                    str(good / "gate-classes.json"),
                    "--observations",
                    str(good / "revalidation-observations.json"),
                    "--output",
                    str(envelope_path),
                ],
            ),
            OK,
        )
        if envelope_path.is_file():
            envelope = json.loads(envelope_path.read_text())
            checks = [
                (
                    "terminal_visibility",
                    "COMPLETED_WITH_EXCEPTION",
                    "a scoped exception must stay visibly different from a clean pass",
                ),
                (
                    "canonical_writer",
                    "LOOPX_LEDGER_REDUCER",
                    "the envelope must name the reducer as the only writer",
                ),
                (
                    "proposed_event",
                    "ADMIT_EXCEPTION",
                    "the envelope must propose the event the decision implies",
                ),
            ]
            for field, expected, why in checks:
                if envelope.get(field) != expected:
                    failures.append(
                        f"resume envelope {field}={envelope.get(field)!r}: {why}"
                    )
            if not envelope.get("exception_expires_at"):
                failures.append("resume envelope: the exception lost its expiry")
            if envelope.get("revalidated_gates") != ["gate-flaky-timing"]:
                failures.append(
                    "resume envelope: revalidated gates do not match the interrupt"
                )
        else:
            failures.append("resume wrote no envelope")

    if failures:
        for line in failures:
            print(f"loopx-strategy-hitl control RED: {line}", file=sys.stderr)
        return BAD
    print(
        "loopx-strategy-hitl control PASS: check=0 selftest=0 positives=0 hollow=2 "
        "absent=64 usage=64 envelope=COMPLETED_WITH_EXCEPTION"
    )
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
