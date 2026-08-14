#!/usr/bin/env python3
"""Independent public-port control for LoopX Contract v1.

This control does not import the validator. It executes the public argv surface
as a child process and checks the observable exit/stdout/stderr contract:

  0  valid contract bundle
  2  checked contract disagreement
 64  invalid invocation or unreadable input
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Sequence

EXIT_PASS = 0
EXIT_FAIL = 2
EXIT_USAGE = 64


class ControlFailure(RuntimeError):
    """The public port did not exhibit its declared behavior."""


def run(argv: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env={"PATH": str(Path(sys.executable).parent) + ":/usr/local/bin:/usr/bin:/bin"},
    )


def expect(
    result: subprocess.CompletedProcess[str],
    *,
    code: int,
    stdout_marker: str | None = None,
    stderr_marker: str | None = None,
    label: str,
) -> None:
    if result.returncode != code:
        raise ControlFailure(
            f"{label}: expected exit {code}, observed {result.returncode}; "
            f"stdout={result.stdout[-500:]!r}; stderr={result.stderr[-500:]!r}"
        )
    if stdout_marker is not None and stdout_marker not in result.stdout:
        raise ControlFailure(f"{label}: missing stdout marker {stdout_marker!r}")
    if stderr_marker is not None and stderr_marker not in result.stderr:
        raise ControlFailure(f"{label}: missing stderr marker {stderr_marker!r}")


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ControlFailure(f"fixture root is not an object: {path}")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="LoopX kernel module root",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    validator = root / "scripts" / "check_contracts.py"
    good_path = root / "tests" / "fixtures" / "good" / "bundle.json"
    if not validator.is_file() or not good_path.is_file():
        print("FATAL: validator or positive fixture is absent", file=sys.stderr)
        return EXIT_USAGE

    command = [sys.executable, str(validator)]
    try:
        positive = run([*command, "--bundle", str(good_path)], root)
        expect(
            positive,
            code=EXIT_PASS,
            stdout_marker="loopx-contracts PASS:",
            label="positive bundle",
        )

        selftest = run([*command, "--selftest"], root)
        expect(
            selftest,
            code=EXIT_PASS,
            stdout_marker="1 positive, 1 hollow, 16 mutations",
            label="mutation matrix",
        )

        with tempfile.TemporaryDirectory(prefix="loopx-contract-control.") as temp:
            bad = copy.deepcopy(load_json(good_path))
            bad["gate_definitions"][0]["execution"]["shell"] = "python -m compileall ."
            bad_path = Path(temp) / "raw-shell.json"
            bad_path.write_text(
                json.dumps(bad, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                encoding="utf-8",
            )
            negative = run([*command, "--bundle", str(bad_path)], root)
            expect(
                negative,
                code=EXIT_FAIL,
                stderr_marker="loopx-contracts RED:",
                label="raw-shell negative",
            )

        missing = run(
            [*command, "--bundle", str(root / "tests" / "fixtures" / "ABSENT.json")],
            root,
        )
        expect(
            missing,
            code=EXIT_USAGE,
            stderr_marker="FATAL:",
            label="missing input",
        )

        invalid_invocation = run(
            [*command, "--bundle", str(good_path), "--selftest"], root
        )
        expect(
            invalid_invocation,
            code=EXIT_USAGE,
            stderr_marker="mutually exclusive",
            label="invalid invocation",
        )

        print(
            "loopx-contracts control PASS: "
            "positive=0 mutation-matrix=0 checked-negative=2 missing=64 invocation=64"
        )
        return EXIT_PASS
    except subprocess.TimeoutExpired as exc:
        print(f"FATAL: control timed out: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FATAL: control input/runtime error: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except ControlFailure as exc:
        print(f"loopx-contracts control RED: {exc}", file=sys.stderr)
        return EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
