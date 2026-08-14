#!/usr/bin/env python3
"""Control group: drive the public port as an outside caller would.

The selftest exercises the functions. This exercises the CLI -- argv shapes,
exit codes and emitted bytes -- because a module whose library is correct and
whose entry point is not is still broken for everyone who uses it.

It also runs the one claim that cannot be made from inside a function call: that
the projection is byte-identical across two separate processes. A determinism
check inside one interpreter would pass even if the result depended on hash
seeding or dict insertion order.
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
        [sys.executable, str(root / "scripts" / "observability.py"), *argv],
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
        "validate-policy positive",
        run(root, ["validate-policy", "--policy", str(good / "redaction-policy.json")]),
        OK,
    )
    expect(
        "validate-request positive",
        run(root, ["validate-request", "--request", str(good / "action-request.json")]),
        OK,
    )
    # Readable and wrong exits 2; absent exits 64. Absence is not a verdict.
    expect(
        "hollow ledger rebuild",
        run(
            root,
            [
                "rebuild",
                "--ledger",
                str(hollow / "ledger.json"),
                "--policy",
                str(good / "redaction-policy.json"),
                "--projection",
                str(good / "projection.json"),
            ],
        ),
        BAD,
    )
    expect(
        "absent input",
        run(root, ["validate-policy", "--policy", str(good / "does-not-exist.json")]),
        USAGE,
    )
    expect("unknown subcommand", run(root, ["not-a-command"]), USAGE)
    expect("no subcommand", run(root, []), USAGE)

    with tempfile.TemporaryDirectory() as tmp:
        first = Path(tmp) / "a.json"
        second = Path(tmp) / "b.json"
        for out in (first, second):
            expect(
                f"project -> {out.name}",
                run(
                    root,
                    [
                        "project",
                        "--ledger",
                        str(good / "ledger.json"),
                        "--policy",
                        str(good / "redaction-policy.json"),
                        "--output",
                        str(out),
                    ],
                ),
                OK,
            )
        if first.is_file() and second.is_file():
            # Two separate processes, compared as bytes. Determinism asserted
            # inside one interpreter would survive a dependency on hash seeding.
            if first.read_bytes() != second.read_bytes():
                failures.append(
                    "two projections of the same ledger differ across processes; "
                    "rebuild-from-ledger cannot be claimed"
                )
            emitted = json.loads(first.read_text())
            if emitted.get("authority") != "PROJECTION_ONLY":
                failures.append("projection does not state PROJECTION_ONLY authority")
            if emitted.get("canonical_writer") != "LOOPX_LEDGER_REDUCER":
                failures.append("projection names a writer other than the reducer")
            redacted = [
                env for env in emitted["envelopes"] if env["redaction"]["removed_paths"]
            ]
            if not redacted:
                failures.append(
                    "no envelope recorded a removed path; the fixture plants a token, "
                    "so either redaction or its self-reporting is not working"
                )
            for env in emitted["envelopes"]:
                if "ghp_" in json.dumps(env):
                    failures.append(
                        f"envelope {env['ledger']['sequence']} still carries a "
                        "secret-shaped value"
                    )
        else:
            failures.append("project wrote no output")

        proposal = Path(tmp) / "proposal.json"
        expect(
            "admit-request",
            run(
                root,
                [
                    "admit-request",
                    "--request",
                    str(good / "action-request.json"),
                    "--state",
                    str(good / "state.json"),
                    "--projection",
                    str(good / "projection.json"),
                    "--output",
                    str(proposal),
                ],
            ),
            OK,
        )
        if proposal.is_file():
            emitted = json.loads(proposal.read_text())
            if emitted.get("outcome") != "FORWARDED_TO_REDUCER":
                failures.append(
                    "a console request must be forwarded, never resolved: "
                    f"outcome={emitted.get('outcome')!r}"
                )
            if emitted.get("canonical_writer") != "LOOPX_LEDGER_REDUCER":
                failures.append("proposal names a writer other than the reducer")
        else:
            failures.append("admit-request wrote no proposal")

    if failures:
        for line in failures:
            print(f"loopx-observability control RED: {line}", file=sys.stderr)
        return BAD
    print(
        "loopx-observability control PASS: check=0 selftest=0 positives=0 hollow=2 "
        "absent=64 usage=64 cross-process-deterministic outcome=FORWARDED_TO_REDUCER"
    )
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
