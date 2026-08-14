#!/usr/bin/env python3
"""Physical control group. Real trees, real writes, real checks afterwards.

Every other control in this module is a fixture mutation, and a fixture cannot
answer the one question that matters about the lease: does the code that writes
files actually stay inside it? A validator that rejects a bad path in a plan
proves nothing about the renderer, and the renderer is what touches the disk.

Four controls, in the order they have to run:

1. **clean** -- a normal render writes only under the leased root and leaves the
   surrounding tree untouched. Without this, a renderer that wrote nothing at all
   would pass controls 2-4 and prove nothing;
2. **relative escape** -- a target path of `../outside.py` is refused, and the
   file really is absent from the parent directory afterwards. Checked on disk,
   not from the exception;
3. **symlink escape** -- a symlink planted inside the output tree pointing at a
   directory outside it. Every string prefix check passes; the write would land
   outside. Only path resolution catches it;
4. **absolute escape** -- an absolute target path, which silently discards the
   root under `Path.__truediv__` and is the easiest of the three to write by
   accident.

Exit: 0 all controls behaved, 2 one did not, 64 unusable environment.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kc_common import BAD, OK, USAGE, ContractError, InputError, load_json  # noqa: E402
from kc_scaffold import render  # noqa: E402


def _fixtures(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    good = root / "tests/fixtures/good"
    return load_json(good / "codeop-plan.json"), load_json(good / "system-spec.json")


def _render_expecting_refusal(
    plan: dict[str, Any], spec: dict[str, Any], output_root: Path, label: str
) -> str | None:
    """Returns a failure description, or None if the render was refused."""
    try:
        render(plan, spec, output_root)
    except ContractError:
        return None
    except Exception as exc:  # noqa: BLE001
        return (
            f"{label} raised {type(exc).__name__}: {exc} -- that is a broken control, "
            "not a refusal; the escape was never measured"
        )
    return f"{label} was rendered instead of refused"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()

    try:
        base_plan, spec = _fixtures(args.root.resolve())
    except InputError as exc:
        print(f"knowledge control FATAL: {exc}", file=sys.stderr)
        return USAGE

    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="loopx-kc-control-") as tmp:
        base = Path(tmp)

        # --- control 1: a clean render must be clean, and must write ----------
        clean_root = base / "clean" / "candidate"
        sentinel = base / "clean" / "untouched.txt"
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text("original\n", encoding="utf-8")

        rendered = render(copy.deepcopy(base_plan), spec, clean_root)
        if not rendered["files"]:
            failures.append(
                "the clean render wrote no files; with nothing written, every escape "
                "control below would pass vacuously"
            )
        for entry in rendered["files"]:
            written = clean_root / entry["path"]
            if not written.is_file():
                failures.append(f"receipt names {entry['path']}, which is not on disk")
        outside = [
            path
            for path in (base / "clean").rglob("*")
            if path.is_file() and clean_root not in path.parents and path != sentinel
        ]
        if outside:
            failures.append(f"the clean render wrote outside its root: {outside}")
        if sentinel.read_text(encoding="utf-8") != "original\n":
            failures.append("the clean render modified a file outside its lease")

        # --- control 2: relative escape --------------------------------------
        escape_root = base / "relative" / "candidate"
        escape_root.mkdir(parents=True)
        plan = copy.deepcopy(base_plan)
        plan["operations"][0]["target"]["path"] = "../../outside.py"
        problem = _render_expecting_refusal(plan, spec, escape_root, "relative escape")
        if problem:
            failures.append(problem)
        # Asked of the filesystem, not of the exception. An exception raised
        # after the write would still leave the file there.
        if (base / "outside.py").exists() or (
            base / "relative" / "outside.py"
        ).exists():
            failures.append(
                "a refused relative escape still left a file outside the leased tree"
            )

        # --- control 3: symlink escape ---------------------------------------
        symlink_root = base / "symlinked" / "candidate"
        symlink_root.mkdir(parents=True)
        target = base / "symlinked" / "real-checkout"
        target.mkdir()
        try:
            (symlink_root / "generated").symlink_to(target, target_is_directory=True)
        except OSError as exc:
            print(
                f"knowledge control FATAL: cannot create symlink: {exc}",
                file=sys.stderr,
            )
            return USAGE
        problem = _render_expecting_refusal(
            copy.deepcopy(base_plan), spec, symlink_root, "symlink escape"
        )
        if problem:
            failures.append(problem)
        leaked = sorted(p.name for p in target.rglob("*") if p.is_file())
        if leaked:
            failures.append(
                f"a symlink inside the output tree let the render reach {leaked} in a "
                "directory outside the lease; a string prefix check would have called "
                "this clean"
            )

        # --- control 4: absolute path ----------------------------------------
        absolute_root = base / "absolute" / "candidate"
        absolute_root.mkdir(parents=True)
        plan = copy.deepcopy(base_plan)
        plan["operations"][0]["target"]["path"] = str(base / "absolute" / "escaped.py")
        problem = _render_expecting_refusal(
            plan, spec, absolute_root, "absolute escape"
        )
        if problem:
            failures.append(problem)
        if (base / "absolute" / "escaped.py").exists():
            failures.append(
                "an absolute target path was written outside the leased root; "
                "Path('/leased') / '/absolute' discards the left side silently"
            )

    if failures:
        for line in failures:
            print(f"knowledge control RED: {line}", file=sys.stderr)
        return BAD

    print(
        json.dumps(
            {
                "module": "loopx-knowledge-compiler",
                "controls": [
                    "clean-render-stays-inside-lease",
                    "relative-escape-refused-and-absent-on-disk",
                    "symlink-escape-refused-and-nothing-leaked",
                    "absolute-path-escape-refused",
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
