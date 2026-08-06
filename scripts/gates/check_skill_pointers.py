#!/usr/bin/env python3
"""check_skill_pointers — skill content exists once; host entries are pointers.

Mechanizes the S5 skills-SSOT contract (ARCHITECTURE.md §2): `.agents/skills/`
is the host-neutral single home of skill content; `.claude/skills/` holds only
symlinks that resolve into `.agents/skills/` or a module-owned skill home
(`kb-ingest/skill`). Checks, against tracked+untracked-visible files:

1. every `.claude/skills/` entry is a symlink resolving inside
   `.agents/skills/` or `kb-ingest/skill` (no real files, no escapes);
2. no symlink under `.agents/skills/` resolves back into `.claude/` (content
   must never live behind a host entry);
3. repo-wide, no two real SKILL.md files share the same skill-directory name
   (a residual copy of a skill re-creates the dual-home drift S5 removed).

Exit codes: 0 clean · 2 pointer contract violated · 64 usage / not a git
work tree / expected dirs missing. --selftest: 0 green · 1 red, throwaway
git fixtures with positive and negative (injected residual copy) controls.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from _gate_common import repo_root

CLAUDE_SKILLS_REL = ".claude/skills"
AGENTS_SKILLS_REL = ".agents/skills"
ALLOWED_TARGET_RELS = (AGENTS_SKILLS_REL, "kb-ingest/skill")


def visible_paths(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-co", "--exclude-standard", "-z"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    return [p for p in out.split("\0") if p]


def _resolves_inside(link: Path, root: Path, allowed_rels: tuple[str, ...]) -> bool:
    real = Path(os.path.realpath(link))
    return any(
        real == (root / rel / link.name) or real.is_relative_to(root / rel)
        for rel in allowed_rels
    )


def run(start: Path) -> int:
    root = repo_root(start)
    if root is None:
        print("check_skill_pointers: not inside a git work tree", file=sys.stderr)
        return 64
    print(f"check_skill_pointers: scanning repo root {root}")
    claude_skills = root / CLAUDE_SKILLS_REL
    agents_skills = root / AGENTS_SKILLS_REL
    if not claude_skills.is_dir() or not agents_skills.is_dir():
        print(
            f"check_skill_pointers: {CLAUDE_SKILLS_REL} or {AGENTS_SKILLS_REL} "
            "missing — no pointer contract surface",
            file=sys.stderr,
        )
        return 64

    violations: list[str] = []

    # 1: every host entry is a symlink resolving into an allowed content home
    for entry in sorted(claude_skills.iterdir()):
        if entry.name == ".gitignore":
            continue
        if not entry.is_symlink():
            violations.append(
                f"REAL-ENTRY {CLAUDE_SKILLS_REL}/{entry.name} "
                "(host entries must be symlinks, zero content copies)"
            )
            continue
        if not _resolves_inside(entry, root, ALLOWED_TARGET_RELS):
            violations.append(
                f"ESCAPED-LINK {CLAUDE_SKILLS_REL}/{entry.name} -> {os.readlink(entry)} "
                f"(must resolve inside {' or '.join(ALLOWED_TARGET_RELS)})"
            )

    # 2: content home must not point back into the host tree
    for dirpath, dirnames, filenames in os.walk(agents_skills):
        for name in dirnames + filenames:
            p = Path(dirpath) / name
            if p.is_symlink():
                real = Path(os.path.realpath(p))
                if real.is_relative_to(root / ".claude"):
                    rel = p.relative_to(root)
                    violations.append(
                        f"BACK-LINK {rel} -> {os.readlink(p)} "
                        "(content must not live behind a host entry)"
                    )

    # 3: no two real SKILL.md files under a same-named skill directory
    by_dirname: dict[str, list[str]] = {}
    for rel in visible_paths(root):
        parts = rel.split("/")
        if (
            parts[-1] == "SKILL.md"
            and len(parts) >= 2
            and not (root / rel).is_symlink()
        ):
            by_dirname.setdefault(parts[-2], []).append(rel)
    for dirname, rels in sorted(by_dirname.items()):
        if len(rels) > 1:
            violations.append(
                f"DUPLICATE-SKILL {dirname}: {' | '.join(sorted(rels))} "
                "(skill content must exist exactly once)"
            )

    if violations:
        for line in violations:
            print(line, file=sys.stderr)
        print(f"FAIL: {len(violations)} skill pointer violation(s)", file=sys.stderr)
        return 2
    print("PASS: host skill entries are pointers; content exists once")
    return 0


# ---------------------------------------------------------------- selftest


def _fixture(tmp: Path) -> Path:
    repo = tmp / "fixture"
    (repo / ".agents/skills/foo").mkdir(parents=True)
    (repo / ".agents/skills/foo/SKILL.md").write_text("foo content\n", encoding="utf-8")
    (repo / "kb-ingest/skill").mkdir(parents=True)
    (repo / "kb-ingest/skill/SKILL.md").write_text("wiki content\n", encoding="utf-8")
    (repo / ".claude/skills").mkdir(parents=True)
    os.symlink("../../.agents/skills/foo", repo / ".claude/skills/foo")
    os.symlink("../../kb-ingest/skill", repo / ".claude/skills/repo-wiki-converge")
    os.symlink("../../kb-ingest/skill", repo / ".agents/skills/repo-wiki-converge")
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    return repo


def _selftest() -> int:
    cases = []
    with tempfile.TemporaryDirectory() as td:
        cases.append(("clean", run(_fixture(Path(td))), 0))
    with tempfile.TemporaryDirectory() as td:
        repo = _fixture(Path(td))  # injected residual copy: dual-home drift
        (repo / ".claude/skills/foo").unlink()
        (repo / ".claude/skills/foo").mkdir()
        (repo / ".claude/skills/foo/SKILL.md").write_text(
            "stale copy\n", encoding="utf-8"
        )
        cases.append(("residual-copy-red", run(repo), 2))
    with tempfile.TemporaryDirectory() as td:
        repo = _fixture(Path(td))  # link escaping the allowed content homes
        (repo / "elsewhere").mkdir()
        (repo / "elsewhere/SKILL.md").write_text("outside\n", encoding="utf-8")
        (repo / ".claude/skills/foo").unlink()
        os.symlink("../../elsewhere", repo / ".claude/skills/foo")
        cases.append(("escaped-link-red", run(repo), 2))
    with tempfile.TemporaryDirectory() as td:
        repo = _fixture(Path(td))  # content home pointing back into the host tree
        (repo / ".claude/skills/bar-home").mkdir()
        (repo / ".claude/skills/bar-home/SKILL.md").write_text(
            "host-side\n", encoding="utf-8"
        )
        os.symlink("../../.claude/skills/bar-home", repo / ".agents/skills/bar")
        cases.append(("back-link-red", run(repo), 2))
    with tempfile.TemporaryDirectory() as td:
        repo = _fixture(Path(td))  # same-named copy far from either skills tree
        (repo / "vendor/foo").mkdir(parents=True)
        (repo / "vendor/foo/SKILL.md").write_text("far copy\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        cases.append(("far-duplicate-red", run(repo), 2))
    with tempfile.TemporaryDirectory() as td:
        repo = _fixture(Path(td))
        import shutil

        shutil.rmtree(repo / ".claude/skills")
        cases.append(("surface-missing", run(repo), 64))
    with tempfile.TemporaryDirectory() as td:
        cases.append(("not-a-repo", run(Path(td)), 64))

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
