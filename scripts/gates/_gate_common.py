"""_gate_common — shared plumbing for the scripts/gates/ checkers.

repo_root() was byte-identical across check_root_coupling / check_placement /
check_skill_pointers, and the selftest git-fixture builder was duplicated in
the first two; a fix in one copy silently missed the others. Shared here once.
The gates stay single-file invocable (`python3 scripts/gates/<gate>.py`):
sys.path[0] is this directory when a gate runs as a script, so a plain
`from _gate_common import …` resolves without packaging.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def repo_root(start: Path) -> Path | None:
    """Toplevel of the git work tree containing `start`, or None outside one."""
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def git_fixture(tmp: Path, files: dict[str, str], track: bool = True) -> Path:
    """Throwaway git repo at tmp/fixture with `files` written (and staged)."""
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
