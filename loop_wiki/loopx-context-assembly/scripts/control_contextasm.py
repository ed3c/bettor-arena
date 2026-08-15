#!/usr/bin/env python3
"""Physical control group: real files on disk, real separate processes.

The in-process selftest compares objects the same process built. That proves the
comparison logic and nothing about the thing the comparison is for -- projections
are written to disk and read back by something else, and prefixes are rendered by
one process and cached by another.

So this group:

  * writes the six projections to real files, edits the law in one of them on
    disk, and checks the from-disk comparison turns red -- then restores the file
    and checks it turns green again, so the red is attributable to the edit
    rather than to the reader being broken;
  * renders the prefix in two separate interpreters under different
    PYTHONHASHSEED values and checks the bytes are identical. Set and dict
    iteration order is the classic way a prefix becomes unstable across
    processes, and it is invisible inside one.

Exits 0 or 2.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ca_common import BAD, OK, ContractError  # noqa: E402

HERE = Path(__file__).resolve().parent
PORT = HERE / "contextasm.py"


def run_port(*argv: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PORT), *argv],
        capture_output=True,
        text=True,
        check=False,
    )


def prefix_digest_in_subprocess(seed: str, reverse_tools: bool = False) -> str:
    """Render the prefix in a fresh interpreter with a given hash seed.

    `reverse_tools` hands the renderer the same tools in the opposite order. Two
    callers assembling the same IR will not agree on list order, and the prefix
    is the cache key -- so canonicalisation has to hold across a process
    boundary, not just inside one.
    """
    env = dict(os.environ, PYTHONHASHSEED=seed)
    code = (
        "import sys;sys.path.insert(0,%r)\n"
        "from ca_ir import render_prefix\n"
        "from ca_selftest import IR\n"
        "ir = dict(IR)\n"
        "if %r: ir['tools'] = list(reversed(ir['tools']))\n"
        "print(render_prefix(ir)['prefix_digest'])\n" % (str(HERE), reverse_tools)
    )
    done = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if done.returncode != 0:
        raise ContractError(
            f"rendering under PYTHONHASHSEED={seed} failed: {done.stderr.strip()}"
        )
    return done.stdout.strip()


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="loopx-ca-") as tmp:
        target = Path(tmp) / "projections"

        done = run_port(
            "emit", "--dir", str(target), "--output", str(Path(tmp) / "emit.json")
        )
        if done.returncode != 0:
            raise ContractError(f"emit failed: {done.stderr.strip()}")
        files = sorted(p.name for p in target.glob("*.md"))
        if len(files) != 6:
            raise ContractError(f"emit wrote {files}, expected six projections")
        checks += 1

        # 1. Clean: the law agrees across six real files.
        done = run_port(
            "verify", "--dir", str(target), "--output", str(Path(tmp) / "v1.json")
        )
        if done.returncode != 0:
            raise ContractError(
                f"a clean directory verified red: {done.stderr.strip()}"
            )
        checks += 1

        # 2. Edit the law in one file on disk. Nothing about the file is
        #    malformed; it just says something different from the other five.
        victim = target / "grok-build.md"
        original = victim.read_text(encoding="utf-8")
        if "never hand-edited" not in original:
            raise ContractError("the physical control could not find the line it edits")
        victim.write_text(
            original.replace("never hand-edited", "usually not hand-edited"),
            encoding="utf-8",
        )
        done = run_port("verify", "--dir", str(target))
        if done.returncode != BAD:
            raise ContractError(
                f"an edited law on disk exited {done.returncode}, expected {BAD}"
            )
        if "found by the thing it allowed" not in done.stderr:
            raise ContractError(
                f"the refusal named a different rule: {done.stderr.strip()}"
            )
        checks += 1

        # 3. Restore. A red that stays red after the cause is removed is a broken
        #    reader, not a detection.
        victim.write_text(original, encoding="utf-8")
        done = run_port("verify", "--dir", str(target))
        if done.returncode != 0:
            raise ContractError(
                f"the directory stayed red after the edit was reverted: {done.stderr.strip()}"
            )
        checks += 1

        # 4. A timestamp appended to a projection after it was written.
        victim.write_text(original + "\nrendered 2026-08-16T09:30\n", encoding="utf-8")
        done = run_port("verify", "--dir", str(target))
        if done.returncode != BAD or "changed after it was written" not in done.stderr:
            raise ContractError(
                f"a projection edited after rendering exited {done.returncode}: "
                f"{done.stderr.strip()}"
            )
        victim.write_text(original, encoding="utf-8")
        checks += 1

        # 5. An empty directory is unusable input, not a disagreement. Exit 64,
        #    because "nothing to compare" and "they disagree" are different
        #    answers and they render identically as a non-zero exit.
        done = run_port("verify", "--dir", str(Path(tmp) / "empty"))
        if done.returncode != 64:
            raise ContractError(
                f"an empty directory exited {done.returncode}, expected 64. Absence "
                "is not disagreement"
            )
        checks += 1

    # 6. Two separate interpreters, different hash seeds, identical prefix bytes.
    first = prefix_digest_in_subprocess("0")
    second = prefix_digest_in_subprocess("12345")
    if not first or first != second:
        raise ContractError(
            f"the prefix digest differs across processes: {first} vs {second}. Every "
            "request would be a cache miss, and nothing would error"
        )
    checks += 1

    # 7. A different caller, in a different process, holding the same tools in
    #    the opposite order.
    reordered = prefix_digest_in_subprocess("0", reverse_tools=True)
    if reordered != first:
        raise ContractError(
            f"a caller's tool order reached the prefix across a process boundary: "
            f"{reordered} vs {first}. Reordering tools would silently change the cache "
            "key, and the reorder is invisible in review"
        )
    checks += 1

    print(
        f"loopx-context-assembly physical control PASS: {checks} controls on real "
        f"files and separate processes (prefix {first[:19]}...)"
    )
    return OK


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"loopx-context-assembly physical control RED: {exc}", file=sys.stderr)
        raise SystemExit(BAD) from exc
