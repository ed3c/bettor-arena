#!/usr/bin/env python3
"""check_credential_hygiene — tracked files must carry no credential material.

Why this gate exists: during the migration a review agent ran `git credential
fill` and wrote its output to a file. The file was transient and the token has
since been rotated, but the class of failure — a secret materialized into a
file that a commit could then publish — is exactly what an open-source repo
cannot afford. This gate hunts the SHAPES that credential material takes, so
the failure is caught at the boundary instead of after a push.

It deliberately does NOT read any credential store: a gate that fetches secrets
to check for secrets reproduces the incident it exists to prevent.

Prose that merely discusses credentials is not material, so the patterns match
assignment/serialization shapes (`password=<value>`, a key block header, a bare
long hex token assigned to a token-ish name), never the words themselves.

Allowlist: scripts/gates/credential_hygiene_allowlist.txt, same one-entry-per-
line contract as the root-coupling ledger (path or prefix, then a reason).

Exit codes: 0 clean · 2 material found · 64 usage or not a git work tree.
Selftest: --selftest builds throwaway git fixtures and proves the gate can
fail; exits 0 green, 1 red.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from _gate_common import git_fixture, repo_root  # noqa: E402

ALLOWLIST_REL = "scripts/gates/credential_hygiene_allowlist.txt"

# Assembled from fragments so this file never contains a literal specimen of
# what it hunts (same convention as check_root_coupling.py).
PATTERNS = (
    ("password-assignment", re.compile(r"\bpass" + r"word\s*[=:]\s*\S{6,}")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRI" + r"VATE KEY-----")),
    ("bearer-token", re.compile(r"\bBea" + r"rer\s+[A-Za-z0-9._\-]{20,}")),
    (
        "token-assignment",
        re.compile(
            r"\b(?:to" + r"ken|secret|api[_-]?key)\s*[=:]\s*['\"]?[A-Za-z0-9]{24,}"
        ),
    ),
)
# Placeholders are how documentation shows a shape without carrying a value.
PLACEHOLDER = re.compile(
    r"<[^>\n]+>|\$\{?[A-Z_]+\}?|x{8,}|\.{3}|EXAMPLE|PLACEHOLDER|redacted", re.I
)


def load_allowlist(root: Path) -> list[str]:
    path = root / ALLOWLIST_REL
    if not path.is_file():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            entries.append(line.split()[0])
    return entries


def allowed(rel: str, entries: list[str]) -> bool:
    return any(rel == e or (e.endswith("/") and rel.startswith(e)) for e in entries)


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    return [p for p in out.split("\0") if p]


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    entries = load_allowlist(root)
    for rel in tracked_files(root):
        if rel == ALLOWLIST_REL or allowed(rel, entries):
            continue
        try:
            text = (root / rel).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for name, pattern in PATTERNS:
                if pattern.search(line) and not PLACEHOLDER.search(line):
                    findings.append(f"{rel}:{lineno} [{name}]")
    return findings


def run(start: Path) -> int:
    # Anchored on this script's own location, not cwd: a mis-anchored call must
    # not scan (and green-light) some other repository.
    root = repo_root(Path(__file__).resolve().parent)
    if root is None:
        print("check_credential_hygiene: not inside a git work tree", file=sys.stderr)
        return 64
    print(f"check_credential_hygiene: scanning repo root {root}")
    findings = scan(root)
    if findings:
        for finding in findings:
            print(f"CREDENTIAL-MATERIAL {finding}", file=sys.stderr)
        print(
            f"FAIL: {len(findings)} tracked line(s) look like credential material "
            f"(declare a reviewed false positive in {ALLOWLIST_REL})",
            file=sys.stderr,
        )
        return 2
    print("PASS: no credential material in tracked files")
    return 0


# ---------------------------------------------------------------- selftest


def _fixture(tmp: Path, files: dict[str, str]) -> Path:
    return git_fixture(tmp, files)


def _scan_only(repo: Path) -> int:
    """Fixture verdict without the script-anchored root (fixtures are not this repo)."""
    return 2 if scan(repo) else 0


def _selftest() -> int:
    secret = "pass" + "word=hunter2supersecret"
    key = "-----BEGIN RSA PRI" + "VATE KEY-----"
    cases = []
    with tempfile.TemporaryDirectory() as td:
        clean = _fixture(
            Path(td), {"doc.md": "The password is stored in the keychain.\n"}
        )
        cases.append(("prose-mentioning-credentials-is-clean", _scan_only(clean), 0))
    with tempfile.TemporaryDirectory() as td:
        dirty = _fixture(Path(td), {"conf.env": f"{secret}\n"})
        cases.append(("password-assignment", _scan_only(dirty), 2))
    with tempfile.TemporaryDirectory() as td:
        keyed = _fixture(Path(td), {"id_rsa": f"{key}\nMIIEow==\n"})
        cases.append(("private-key-block", _scan_only(keyed), 2))
    with tempfile.TemporaryDirectory() as td:
        placeholder = _fixture(
            Path(td), {"README.md": "run with pass" + "word=<your-password>\n"}
        )
        cases.append(("placeholder-is-not-material", _scan_only(placeholder), 0))
    with tempfile.TemporaryDirectory() as td:
        declared = _fixture(
            Path(td),
            {
                "traces/old.log": f"{secret}\n",
                ALLOWLIST_REL: "traces/ reviewed-historical-fixture\n",
            },
        )
        cases.append(("allowlisted", _scan_only(declared), 0))

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
    return run(Path.cwd())


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
