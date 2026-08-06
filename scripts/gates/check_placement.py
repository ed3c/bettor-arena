#!/usr/bin/env python3
"""check_placement — every tracked root-level item must map to an ARCHITECTURE.md §2 slot.

Mechanizes the placement contract (ARCHITECTURE.md §2: no slot = amend the map
first, then land the file). Parses the root-level entries of the §2 fenced
tree block and compares them against the actual root-level items of
`git ls-files`. An undeclared root item fails loud; a declared slot with no
file yet is fine (planned slots land in later slices).

Exit codes: 0 clean · 2 undeclared root items · 64 usage, not a git work
tree, or ARCHITECTURE.md missing/slotless. --selftest: 0 green · 1 red,
using throwaway git fixtures with positive and negative controls.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ARCH_REL = "ARCHITECTURE.md"
ENTRY_RE = re.compile(r"^[├└]──\s+(\S+)")


def repo_root(start: Path) -> Path | None:
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def declared_slots(text: str) -> set[str] | None:
    """Root-level slot names from the first fenced block in §2; None if absent."""
    section = re.search(r"^## §2.*?\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if section is None:
        return None
    block = re.search(r"^```[^\n]*\n(.*?)^```", section.group(1), re.M | re.S)
    if block is None:
        return None
    slots = set()
    for line in block.group(1).splitlines():
        m = ENTRY_RE.match(line)
        if m:
            slots.add(m.group(1).rstrip("/"))
    return slots or None


def actual_root_items(root: Path) -> set[str]:
    out = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    return {p.split("/", 1)[0] for p in out.split("\0") if p}


def run(start: Path) -> int:
    root = repo_root(start)
    if root is None:
        print("check_placement: not inside a git work tree", file=sys.stderr)
        return 64
    print(f"check_placement: scanning repo root {root}")
    arch = root / ARCH_REL
    if not arch.is_file():
        print(
            f"check_placement: {ARCH_REL} missing — no placement contract to check against",
            file=sys.stderr,
        )
        return 64
    slots = declared_slots(arch.read_text(encoding="utf-8"))
    if slots is None:
        print(
            f"check_placement: no §2 tree block with root entries in {ARCH_REL}",
            file=sys.stderr,
        )
        return 64
    unmapped = sorted(actual_root_items(root) - slots)
    if unmapped:
        for name in unmapped:
            print(f"UNPLACED {name}", file=sys.stderr)
        print(
            f"FAIL: {len(unmapped)} tracked root item(s) have no {ARCH_REL} §2 slot "
            "(amend the map first, then land the file)",
            file=sys.stderr,
        )
        return 2
    print("PASS: every tracked root item maps to a §2 slot")
    return 0


# ---------------------------------------------------------------- selftest

ARCH_FIXTURE = """# fixture SSOT

## §2 放置契約

```
fixture/
├── ARCHITECTURE.md    # ssot
├── a.md               # doc
├── src/               # code
│   └── nested/        # nested entries must not count as root slots
└── planned/           # declared slot, no files yet — must stay green
```

## §3 other section
"""


def _fixture(tmp: Path, files: dict[str, str]) -> Path:
    repo = tmp / "fixture"
    repo.mkdir(parents=True)
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    return repo


def _selftest() -> int:
    base = {ARCH_REL: ARCH_FIXTURE, "a.md": "doc\n", "src/nested/x.py": "pass\n"}
    cases = []
    with tempfile.TemporaryDirectory() as td:
        cases.append(("clean", run(_fixture(Path(td), base)), 0))
    with tempfile.TemporaryDirectory() as td:
        rogue = dict(base, **{"rogue.txt": "undeclared\n"})
        cases.append(("undeclared-root-item", run(_fixture(Path(td), rogue)), 2))
    with tempfile.TemporaryDirectory() as td:
        cases.append(("arch-missing", run(_fixture(Path(td), {"a.md": "doc\n"})), 64))
    with tempfile.TemporaryDirectory() as td:
        slotless = dict(base, **{ARCH_REL: "# no tree block here\n## §2 empty\n"})
        cases.append(("arch-slotless", run(_fixture(Path(td), slotless)), 64))
    with tempfile.TemporaryDirectory() as td:
        cases.append(("not-a-repo", run(Path(td)), 64))
    # Anchoring control: invoked as a subprocess from a foreign repo's cwd, the
    # gate must still scan its OWN repo (the one holding this script), not cwd's.
    with tempfile.TemporaryDirectory() as td:
        foreign = _fixture(Path(td), {"a.md": "doc\n"})  # no ARCH here on purpose
        own = repo_root(Path(__file__).resolve().parent)
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve())],
            cwd=str(foreign),
            text=True,
            capture_output=True,
        )
        first = proc.stdout.splitlines()[0] if proc.stdout else "<no output>"
        anchored = own is not None and str(own) in first and str(foreign) not in first
        if not anchored:
            print(
                f"SELFTEST anchoring detail — own={own} first line: {first}",
                file=sys.stderr,
            )
        cases.append(("external-cwd-scans-own-repo", 0 if anchored else 1, 0))

    red = [
        f"{name}: got {got}, want {want}" for name, got, want in cases if got != want
    ]
    for line in red:
        print(f"SELFTEST case failed — {line}", file=sys.stderr)
    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return 0 if not red else 1


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return _selftest()
    if argv:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    return run(Path(__file__).resolve().parent)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
