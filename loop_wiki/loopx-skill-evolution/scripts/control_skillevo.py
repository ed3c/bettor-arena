#!/usr/bin/env python3
"""Physical control group. Real files, real payload bytes, a real subprocess.

The sealed-holdout claim is the one this module lives or dies on, and it is the
one a fixture cannot answer: a fixture can assert that `runner_payload` omits
`expected`, but the question is whether the bytes a runner actually receives
contain the answer. So this writes the cases to disk, builds the payload, writes
*that* to disk, and greps the resulting file.

Five controls:

1. **the answers are on disk** -- the holdout file really does contain them.
   Without this, every leak check below passes because there was nothing to
   leak, and the whole group would be green and empty;
2. **the payload file does not contain any answer** -- checked by reading the
   bytes back off disk, not by inspecting the object in memory;
3. **an answer embedded in a prompt is caught** -- the field whitelist allows
   `prompt`, so field-level separation cannot see this one and only the content
   scan can;
4. **a runner subprocess given only the payload cannot produce the answers** --
   it is handed the payload file and asked to print anything that looks like an
   answer; it finds nothing, because the answers are not in the file it was
   given;
5. **the same subprocess given the holdout file finds them immediately** -- so
   control 4's silence is attributable to the payload, not to a broken probe.

Exit: 0 all controls behaved, 2 one did not, 64 unusable environment.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from se_cases import (  # noqa: E402
    build_run_input,
    runner_payload,
    scan_payload_for_leaks,
)
from se_common import BAD, OK, USAGE, ContractError, InputError, load_json  # noqa: E402

# A runner stand-in. It gets one file and reports every answer-shaped string it
# can find, which is exactly what a leaky payload would hand a real model.
PROBE = """
import json, sys
data = json.loads(open(sys.argv[1]).read())
needles = json.loads(open(sys.argv[2]).read())
blob = json.dumps(data)
print(json.dumps(sorted(n for n in needles if n in blob)))
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    root = parser.parse_args().root.resolve()

    try:
        good = root / "tests/fixtures/good"
        dev = load_json(good / "dev-cases.json")
        holdout = load_json(good / "holdout-cases.json")
    except InputError as exc:
        print(f"skill-evolution control FATAL: {exc}", file=sys.stderr)
        return USAGE

    failures: list[str] = []
    answers = [case["expected"] for case in holdout]

    with tempfile.TemporaryDirectory(prefix="loopx-se-control-") as tmp:
        base = Path(tmp)
        probe = base / "probe.py"
        probe.write_text(PROBE, encoding="utf-8")
        needles = base / "needles.json"
        needles.write_text(json.dumps(answers), encoding="utf-8")

        # --- control 1: the answers exist and are findable --------------------
        holdout_file = base / "holdout.json"
        holdout_file.write_text(json.dumps(holdout), encoding="utf-8")
        blob = holdout_file.read_text(encoding="utf-8")
        missing = [answer for answer in answers if answer not in blob]
        if missing:
            failures.append(
                f"the holdout file does not contain {len(missing)} of its own answers; "
                "with nothing to leak, every check below would pass vacuously"
            )

        # --- control 2: the payload on disk carries none of them --------------
        payload_file = base / "payload.json"
        payload_file.write_text(
            json.dumps(build_run_input(dev, holdout)), encoding="utf-8"
        )
        payload_blob = payload_file.read_text(encoding="utf-8")
        leaked = [answer for answer in answers if answer in payload_blob]
        if leaked:
            failures.append(
                f"{len(leaked)} holdout answer(s) are present in the payload file the "
                "runner receives"
            )
        if "expected" in json.dumps(list(json.loads(payload_blob)[0].keys())):
            failures.append("the payload carries an `expected` field")

        # --- control 3: an answer hidden inside an allowed field --------------
        poisoned = [dict(case) for case in dev]
        poisoned[0]["prompt"] = f"{poisoned[0]['prompt']} e.g. {answers[0]}"
        found = scan_payload_for_leaks([runner_payload(c) for c in poisoned], holdout)
        if not found:
            failures.append(
                "an answer embedded in a prompt was not detected; the field whitelist "
                "allows `prompt`, so nothing else in this module would have seen it"
            )
        try:
            build_run_input(poisoned, holdout)
        except ContractError:
            pass
        else:
            failures.append("build_run_input accepted a payload with a leaked answer")

        # --- control 4/5: a real subprocess, given each file in turn ----------
        def ask(path: Path) -> list[str]:
            completed = subprocess.run(
                [sys.executable, str(probe), str(path), str(needles)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if completed.returncode != 0:
                raise ContractError(f"probe failed: {completed.stderr.strip()}")
            return json.loads(completed.stdout)

        try:
            from_payload = ask(payload_file)
            from_holdout = ask(holdout_file)
        except (ContractError, subprocess.SubprocessError) as exc:
            print(f"skill-evolution control FATAL: {exc}", file=sys.stderr)
            return USAGE

        if from_payload:
            failures.append(f"a runner given only the payload recovered {from_payload}")
        if len(from_holdout) != len(answers):
            failures.append(
                f"the same runner given the holdout file recovered "
                f"{len(from_holdout)} of {len(answers)} answers; control 4's silence "
                "cannot be attributed to the payload if the probe cannot find answers "
                "that are there"
            )

    if failures:
        for line in failures:
            print(f"skill-evolution control RED: {line}", file=sys.stderr)
        return BAD

    print(
        json.dumps(
            {
                "module": "loopx-skill-evolution",
                "controls": [
                    "holdout-file-really-contains-its-answers",
                    "payload-file-on-disk-contains-none",
                    "answer-embedded-in-an-allowed-field-is-caught",
                    "subprocess-given-the-payload-recovers-nothing",
                    "same-subprocess-given-the-holdout-recovers-everything",
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
