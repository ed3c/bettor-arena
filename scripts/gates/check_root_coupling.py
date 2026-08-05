#!/usr/bin/env python3
"""check_root_coupling — tracked files must not embed absolute home-root paths.

The repo's open-source contract is "clone anywhere and every gate runs".
Absolute home roots (the macOS, Linux, and Windows per-user directory
prefixes; see PATTERNS) in tracked files silently re-couple the tree to
one machine. This gate scans
git-tracked files only (untracked local state is allowed to be dirty) and
fails loud on any hit not declared in the allowlist ledger.

Allowlist: scripts/gates/root_coupling_allowlist.txt — one entry per line:
    <repo-relative path or prefix ending in /> <reason>
Historical evidence files are declared there, never rewritten: rewriting
evidence is forging evidence.

Exit codes: 0 clean · 2 violations · 64 usage or not a git work tree.
Selftest: --selftest builds throwaway git fixtures and proves the gate can
fail (a green that was never seen red is not evidence).

The scan patterns are assembled from fragments so this file's own source
never contains a literal match for what it hunts.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Assembled at runtime so the gate does not flag its own source.
PATTERNS = tuple(a + b for a, b in (("/Use", "rs/"), ("/ho", "me/"), ("C:\\Use", "rs\\")))
ALLOWLIST_REL = "scripts/gates/root_coupling_allowlist.txt"


def repo_root(start: Path) -> Path | None:
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        text=True, capture_output=True)
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        text=True, capture_output=True, check=True).stdout
    return [p for p in out.split("\0") if p]


def load_allowlist(root: Path) -> list[str]:
    path = root / ALLOWLIST_REL
    if not path.is_file():
        return []
    prefixes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        prefixes.append(line.split()[0])
    return prefixes


def allowed(rel: str, prefixes: list[str]) -> bool:
    return any(rel == p or (p.endswith("/") and rel.startswith(p)) for p in prefixes)


def scan(root: Path) -> list[str]:
    """Return 'path:line' for every tracked-file line embedding a home root."""
    violations: list[str] = []
    prefixes = load_allowlist(root)
    for rel in tracked_files(root):
        if rel == ALLOWLIST_REL or allowed(rel, prefixes):
            continue
        try:
            text = (root / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue  # binary or deleted-from-worktree: not a text coupling surface
        for lineno, line in enumerate(text.splitlines(), 1):
            if any(p in line for p in PATTERNS):
                violations.append(f"{rel}:{lineno}")
    return violations


def run(start: Path) -> int:
    root = repo_root(start)
    if root is None:
        print("check_root_coupling: not inside a git work tree", file=sys.stderr)
        return 64
    violations = scan(root)
    if violations:
        for v in violations:
            print(f"ROOT-COUPLING {v}", file=sys.stderr)
        print(f"FAIL: {len(violations)} tracked line(s) embed an absolute home root "
              f"(declare historical evidence in {ALLOWLIST_REL})", file=sys.stderr)
        return 2
    print("PASS: no absolute home roots in tracked files")
    return 0


# ---------------------------------------------------------------- selftest

def _fixture(tmp: Path, files: dict[str, str], track: bool = True) -> Path:
    repo = tmp / "fixture"
    repo.mkdir(parents=True)
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    if track:
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    return repo


def _selftest() -> int:
    bad = PATTERNS[0] + "someone/x"  # a violating line, assembled not literal
    cases = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        clean = _fixture(tmp / "a", {"doc.md": "relative/path only\n"})
        cases.append(("clean", run(clean), 0))
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        dirty = _fixture(tmp / "b", {"doc.md": f"points at {bad}\n"})
        cases.append(("tracked-violation", run(dirty), 2))
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        declared = _fixture(tmp / "c", {
            "traces/old.md": f"evidence {bad}\n",
            ALLOWLIST_REL: "traces/ historical-evidence\n"})
        cases.append(("allowlisted", run(declared), 0))
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        untracked = _fixture(tmp / "d", {"doc.md": f"local {bad}\n"}, track=False)
        cases.append(("untracked-ignored", run(untracked), 0))
    with tempfile.TemporaryDirectory() as td:
        cases.append(("not-a-repo", run(Path(td)), 64))

    red = [f"{name}: got {got}, want {want}" for name, got, want in cases if got != want]
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
    return run(Path.cwd())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
