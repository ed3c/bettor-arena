#!/usr/bin/env python3
"""Which tracked files under proof_workflow/ no proof hashes.

    harness_coverage.py <repo>     0 all covered or declared · 2 something is not
    harness_coverage.py --selftest

Coverage means a proof receipt at THIS commit carries the path as a hashed step.
A `note` carrying the path counts as DECLARED, not covered — the distinction the
comparator already makes, kept identical here so the two cannot disagree about
what a declaration means.

Receipts are read for the current commit only. An older receipt would report
coverage the present tree does not have, which is the same stale-stamp failure
that has bitten twice elsewhere in this repo.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def tracked(repo: Path, prefix: str) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(repo), "ls-files", prefix],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return sorted(line for line in out.splitlines() if line.strip())


def coverage(repo: Path) -> tuple[set[str], set[str]]:
    """(hashed, declared) paths from every proof receipt at this commit."""
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()[:12]
    hashed: set[str] = set()
    declared: set[str] = set()
    receipts = repo / "data" / "proof-workflow"
    for path in sorted(receipts.glob(f"*-{head}*.json")):
        # control-* receipts describe a control run, not a traversal; counting
        # them would let a control vouch for coverage it never measured.
        if path.name.startswith("control-"):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for step in data.get("steps", []):
            target = step.get("path")
            if not target or target == "-":
                continue
            if step.get("kind") == "note":
                declared.add(target)
            elif step.get("sha256"):
                hashed.add(target)
    return hashed, declared


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    if not argv:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    repo = Path(argv[0])
    hashed, declared = coverage(repo)
    if not hashed:
        print(
            "harness-coverage FATAL: no proof receipt at this commit carries any hashed "
            "path. Everything would read as uncovered, which is not the same as the "
            "harness being unmeasured — stamp the proofs first.",
            file=sys.stderr,
        )
        return 64
    files = tracked(repo, "proof_workflow/")
    uncovered = [f for f in files if f not in hashed and f not in declared]
    for f in files:
        state = (
            "covered" if f in hashed else ("declared" if f in declared else "UNCOVERED")
        )
        print(f"{state:9} {f}")
    if uncovered:
        print(
            f"harness-coverage: {len(uncovered)} file(s) hashed by no proof — a change "
            "to them would move no digest and the lineage hook would stay silent",
            file=sys.stderr,
        )
        return 2
    return 0


# ---------------------------------------------------------------- selftest


def _selftest() -> int:
    red = 0

    def case(name: str, got, want) -> None:
        nonlocal red
        if got != want:
            print(
                f"SELFTEST case failed — {name}: got {got!r}, want {want!r}",
                file=sys.stderr,
            )
            red = 1

    import tempfile

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        (repo / "proof_workflow").mkdir()
        (repo / "data" / "proof-workflow").mkdir(parents=True)
        for name in ("a.sh", "b.sh", "c.sh"):
            (repo / "proof_workflow" / name).write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "-c",
                "user.email=t@t",
                "-c",
                "user.name=t",
                "commit",
                "-qm",
                "fixture",
            ],
            check=True,
        )
        head = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()[:12]
        (repo / "data" / "proof-workflow" / f"x-{head}.json").write_text(
            json.dumps(
                {
                    "steps": [
                        {
                            "kind": "harness",
                            "path": "proof_workflow/a.sh",
                            "sha256": "s",
                        },
                        {"kind": "note", "path": "proof_workflow/b.sh", "sha256": None},
                        {"kind": "harness", "path": "-", "sha256": None},
                    ]
                }
            ),
            encoding="utf-8",
        )
        hashed, declared = coverage(repo)
        case("hashed-step-counts-as-covered", "proof_workflow/a.sh" in hashed, True)
        # A declaration is not coverage — the same rule the comparator uses.
        case(
            "note-counts-as-declared-not-covered",
            "proof_workflow/b.sh" in hashed,
            False,
        )
        case("note-is-declared", "proof_workflow/b.sh" in declared, True)
        case("uncovered-is-detected", main([str(repo)]), 2)

        # A control receipt must not vouch for coverage it never measured.
        (repo / "data" / "proof-workflow" / f"control-x-{head}.json").write_text(
            json.dumps(
                {
                    "steps": [
                        {
                            "kind": "harness",
                            "path": "proof_workflow/c.sh",
                            "sha256": "s",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        hashed, _ = coverage(repo)
        case("control-receipt-does-not-count", "proof_workflow/c.sh" in hashed, False)

        # Cover the rest and it goes green — a checker that can only ever fail is
        # as useless as one that can only ever pass.
        (repo / "data" / "proof-workflow" / f"y-{head}.json").write_text(
            json.dumps(
                {
                    "steps": [
                        {
                            "kind": "harness",
                            "path": "proof_workflow/c.sh",
                            "sha256": "s",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        case("all-covered-is-green", main([str(repo)]), 0)

    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
