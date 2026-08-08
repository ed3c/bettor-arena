#!/usr/bin/env python3
"""Validate the local repo-wiki-converge port of langchain-ai/openwiki.

This is a perception gate. It proves the skill's claims are backed by runnable
local assets rather than prose: the official prompt assets exist and are
machine-generated (not hand-edited), the deterministic post-processing runs, the
three review subagents' read boundaries actually hold, and the RepoDoc ingest
lane still accepts a wiki.

Run:  python3 <module>/check_repo_wiki_converge.py   (from anywhere; paths resolve off __file__)
Exit: 0 pass · 1 fail · 3 fatal (cannot tell — see below)

Two roots, deliberately distinct. MODULE_ROOT is this directory: everything the module
can prove about itself resolves from it, so the module survives being copied to another
repo under another name at another depth. HOST_ROOT is the checkout the module is
installed in, and only host-profile checks may touch it. Collapsing the two -- which is
what parents[1] used to do -- is what pinned this lane to one repo at one depth.

There is deliberately NO third root here. The machine-global shared-skills checkout holds
the judge-loop skill that runs on top of this port (see HOST_SKILL_NAME); where that name
resolves is the shared registry's contract. Asserting it from this gate would make a
module that must survive `cp` into any repo depend on a checkout no repo owns.

Exit 3 is not a worse 1. It means the gate could not establish what it was supposed to
check (no host declaration, unparseable declaration, unknown profile name, no git
worktree). Those must never collapse into "fail" or, worse, into a silent pass: a
forgotten configuration would otherwise read as "this host legitimately has no such
profile" and the check would disappear while the banner stayed green.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parent


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def fatal(msg: str) -> None:
    """The gate cannot establish what it was asked to check. Never degrade this to fail()."""
    print(f"FATAL: {msg}", file=sys.stderr)
    raise SystemExit(3)


def _git_root(flag: str) -> Path | None:
    """Ask git for a root, or None outside a work tree."""
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(MODULE_ROOT),
                "rev-parse",
                "--path-format=absolute",
                flag,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    path = Path(result.stdout.strip()).resolve()
    # --git-common-dir points at the .git directory; its parent is the main work tree.
    return path.parent if flag == "--git-common-dir" else path


def _host_root() -> Path:
    """The checkout this module is installed in.

    Explicit override first, then git. Never falls back to cwd or to a parent-of-module
    guess: a wrong host root would make host-profile assertions check the wrong tree and
    report green, which is the failure this whole split exists to prevent.
    """
    override = os.environ.get("REPO_WIKI_HOST_ROOT")
    if override:
        path = Path(override).expanduser().resolve()
        if not path.is_dir():
            fatal(f"REPO_WIKI_HOST_ROOT is not a directory: {path}")
        return path
    root = _git_root("--show-toplevel")
    if root is None:
        fatal(
            f"{MODULE_ROOT} is not inside a git work tree, so the host root cannot be "
            "established. Set REPO_WIKI_HOST_ROOT to declare it explicitly."
        )
    return root


KNOWN_PROFILES = ("repodoc", "host-skill-links", "skill-bettor-layout")
PROFILE_DECLARATION = MODULE_ROOT / "host-profile.json"


def _load_profiles() -> tuple[str, ...]:
    """Which host profiles this installation declares.

    Every failure mode here is FATAL rather than an empty list. "The declaration is
    missing/broken/misspelled" and "this host genuinely has no profiles" must not produce
    the same outcome, or a typo silently retires a check while the banner still says PASS.
    """
    if not PROFILE_DECLARATION.exists():
        fatal(
            f"{PROFILE_DECLARATION.name} not found in {MODULE_ROOT}. Every installation must "
            "declare its host profiles explicitly; a copy in a fresh repo declares "
            '{"profiles": []} and still gets the full core gate.'
        )
    try:
        declared = json.loads(PROFILE_DECLARATION.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fatal(f"{PROFILE_DECLARATION.name} is unreadable: {exc}")
    profiles = declared.get("profiles") if isinstance(declared, dict) else None
    if not isinstance(profiles, list) or any(not isinstance(p, str) for p in profiles):
        fatal(f'{PROFILE_DECLARATION.name} must contain a "profiles" list of strings')
    unknown = sorted(set(profiles) - set(KNOWN_PROFILES))
    if unknown:
        fatal(
            f"{PROFILE_DECLARATION.name} declares unknown profile(s) {unknown}; "
            f"known: {list(KNOWN_PROFILES)}"
        )
    return tuple(dict.fromkeys(profiles))


PROFILES = _load_profiles()
HOST_ROOT = _host_root() if PROFILES else MODULE_ROOT

# A linked worktree has its own toplevel but shares the main tree's git dir, so committed docs
# naming the main tree's absolute paths are still correct there. Deriving the main root (rather
# than hardcoding one) keeps host-profile needles satisfiable inside a worktree without weakening
# them.
ALLOWED_ROOTS = tuple(
    dict.fromkeys([HOST_ROOT, *(r for r in (_git_root("--git-common-dir"),) if r)])
)
ALLOWED_ROOT_PREFIXES = tuple(f"{root}/" for root in ALLOWED_ROOTS)

# Assembled at runtime so this file never contains a literal match for what it scans for.
HOME_ROOT_MARKERS = tuple(a + b for a, b in (("/Use", "rs/"), ("/ho", "me/")))
_PATH_END_CHARS = " \t\n\"'`)]>,;"


def foreign_home_paths(text: str) -> list[str]:
    """Home-rooted absolute paths in `text` that sit under no allowed checkout root.

    Derived from ALLOWED_ROOTS instead of a hardcoded list of known machine roots:
    a hardcoded list only flags roots it has already heard of, goes stale the moment
    the module lands on a new machine, and a stale list is a scan that silently
    stopped scanning. Here "foreign" means exactly "not this installation's own
    checkout (or its main worktree)", which is the assertion the stale-root check
    was always trying to make.
    """
    hits: list[str] = []
    for marker in HOME_ROOT_MARKERS:
        idx = text.find(marker)
        while idx != -1:
            if not any(
                text.startswith(prefix, idx) for prefix in ALLOWED_ROOT_PREFIXES
            ):
                end = idx
                while end < len(text) and text[end] not in _PATH_END_CHARS:
                    end += 1
                hits.append(text[idx:end])
            idx = text.find(marker, idx + 1)
    return sorted(set(hits))


KB = MODULE_ROOT
# The operating manual ships inside the module: installing is `cp` the module plus one
# symlink per host skill directory, and the manual's paths stay module-relative so they
# survive the copy. Host skill locations are a host concern and live behind a profile.
SKILL_DIR = KB / "skill"
SKILL = SKILL_DIR / "SKILL.md"
MODULE = SKILL_DIR / "modules" / "official-port-map.md"
# The host name this module answers to. Renamed from `repo-wiki-converge` by human ruling
# (2026-08-08): that name belongs to the judge-loop skill in the shared skills checkout,
# which sits ON TOP of this port (its S0 runs this very gate). Two layers, two names.
# Where the shared name points is the shared registry's contract, not this gate's — a
# module that asserted it would stop being copyable into a repo that has no such checkout.
HOST_SKILL_NAME = "openwiki-port"
HOST_SKILL_LINKS = [
    HOST_ROOT / ".agents" / "skills" / HOST_SKILL_NAME,
    HOST_ROOT / ".claude" / "skills" / HOST_SKILL_NAME,
]
INDEXING = HOST_ROOT / "indexing"

OW = KB / "openwiki"  # upstream bytes ONLY — enforced by check_official_purity()
PORT = KB / "port"  # everything skill-bettor added

# The seven machine-generated prompt assets. Each must carry the verbatim markers
# and the generator's do-not-edit banner.
PROMPT_ASSETS = [
    OW / "init.system.md",
    OW / "update.system.md",
    OW / "user.init.md",
    OW / "user.update.md",
    OW / "subagents" / "skeleton-critic.md",
    OW / "subagents" / "question-finder.md",
    OW / "subagents" / "answer-verifier.md",
]

# Core: what the module is, provable from MODULE_ROOT alone. These run on every install.
CORE_FILES = [
    PROFILE_DECLARATION,
    SKILL,
    MODULE,
    PORT / "README.md",
    PORT / "sync_prompts.py",
    PORT / "host-runtime.md",
    PORT / "repodoc-extension.md",
    PORT / "openwiki_post.py",
    PORT / "openwiki_subagent.sh",
    KB / "engine-baseline.md",
    KB / "mastery-ladder.md",
    KB / "setup-repo.sh",
    *PROMPT_ASSETS,
]

# Host profiles: what the surrounding checkout must look like. Only run when declared.
PROFILE_FILES = {
    "repodoc": [
        INDEXING / "ingest_repodoc_cli.py",
        INDEXING / "repodoc.py",
        INDEXING / "store.py",
        INDEXING / "tests" / "fixtures" / "repowiki" / "quickstart.md",
    ],
    "skill-bettor-layout": [
        KB / "setup-prototype.sh",
    ],
}

# The manual must name the module's own entry points, so a reader who follows it reaches
# real files. Needles are module-relative: nothing here may assume a host directory name.
CORE_TEXT: dict[Path, list[str]] = {
    SKILL: [
        "check_repo_wiki_converge.py",
        "Stateful Workflow",
        "port/sync_prompts.py",
        "port/openwiki_post.py",
        "port/openwiki_subagent.sh",
    ],
    MODULE: [
        "port/sync_prompts.py",
        "PRESERVED_EXTENSION_FIELDS",
    ],
}

PROFILE_TEXT = {
    "repodoc": {
        INDEXING / "repodoc.py": [
            '_SOURCE = {"source": "skill-bettor"}',
            'COLLECTION_REPODOCS = "skill_bettor_repodocs"',
        ],
        INDEXING / "store.py": [
            "SKILL_BETTOR_GRAPH_PATH",
            "SKILL_BETTOR_VECTOR_DB",
            "VectorStore requires chromadb",
        ],
    },
    "skill-bettor-layout": {
        SKILL: [
            "python3 -m indexing.ingest_repodoc_cli",
        ],
        MODULE: [
            # The commit the retired assets last existed in — this repo's history, not the
            # module's, so it cannot be asserted anywhere else.
            "b8d076a",
        ],
        # The defaults must be DERIVED from the module's own checkout, not name a
        # machine: a literal root in these scripts is exactly what the stale-root
        # scan below exists to reject.
        KB / "setup-repo.sh": [
            "SKILL_BETTOR_REPO_ROOT",
            "--show-toplevel",
            '"$HOST_ROOT/repo"',
        ],
        KB / "setup-prototype.sh": [
            "SKILL_BETTOR_PROTOTYPE_ROOT",
            "--show-toplevel",
            '"$HOST_ROOT/prototype"',
        ],
    },
}

# Stale-root scanning is a host concern: it asks whether committed docs name a checkout that
# is not this one. With no host profile there is no such expectation to violate.
PROFILE_NO_OLD_ABSOLUTE_PATHS = {
    "skill-bettor-layout": [
        SKILL,
        MODULE,
        KB / "setup-repo.sh",
        KB / "setup-prototype.sh",
    ],
}

CORE_EXECUTABLES = [PORT / "openwiki_subagent.sh", KB / "setup-repo.sh"]
PROFILE_EXECUTABLES = {"skill-bettor-layout": [KB / "setup-prototype.sh"]}


def rel(path: Path) -> str:
    """Shortest readable form: module-relative when inside the module, else host-relative."""
    for base in (MODULE_ROOT, HOST_ROOT):
        try:
            return str(path.relative_to(base))
        except ValueError:
            continue
    return str(path)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        fail(f"{rel(path)} is not utf-8: {exc}")


def run(argv: list[str], cwd: Path = MODULE_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def check_files() -> None:
    expected = [*CORE_FILES]
    executables = [*CORE_EXECUTABLES]
    for profile in PROFILES:
        expected += PROFILE_FILES.get(profile, [])
        executables += PROFILE_EXECUTABLES.get(profile, [])
    missing = [rel(p) for p in expected if not p.exists()]
    if missing:
        fail(f"missing required local assets: {missing}")
    for path in executables:
        if not os.access(path, os.X_OK):
            fail(f"{rel(path)} must be executable")


def check_skill_symlink() -> None:
    """Every host entry for HOST_SKILL_NAME must be a symlink into the module, never a copy.

    Two copies previously drifted apart through a botched find-and-replace, which is why
    this is a link check and not a diff: a diff passes right up until someone edits one
    side, whereas there is only ever one file to edit here.

    The name is `openwiki-port`, not `repo-wiki-converge` (human ruling 2026-08-08). The
    earlier name collided with the shared judge-loop skill that runs ON TOP of this port,
    and a project-level directory outranks the user-level one on both hosts — so the
    collision did not duplicate that skill, it replaced it. Splitting the names is what
    lets both checks be true at once; asserting where the OTHER name points is the shared
    registry's job, and doing it here would make this module require a checkout it does
    not own.
    """
    target = SKILL_DIR.resolve()
    for link in HOST_SKILL_LINKS:
        if not link.is_symlink() or link.resolve() != target:
            fail(f"{rel(link)} must be a symlink to {rel(SKILL_DIR)}")


def check_text_contracts() -> None:
    contracts: dict[Path, list[str]] = {**CORE_TEXT}
    stale_scan: list[Path] = []
    for profile in PROFILES:
        for path, needles in PROFILE_TEXT.get(profile, {}).items():
            contracts.setdefault(path, []).extend(needles)
        stale_scan += PROFILE_NO_OLD_ABSOLUTE_PATHS.get(profile, [])

    for path, needles in contracts.items():
        text = read(path)
        missing = [needle for needle in needles if needle not in text]
        if missing:
            fail(f"{rel(path)} missing required text: {missing}")

    for path in stale_scan:
        stale_roots = foreign_home_paths(read(path))
        if stale_roots:
            fail(
                f"{rel(path)} contains home-rooted absolute path(s) outside the allowed "
                f"checkout roots {[str(root) for root in ALLOWED_ROOTS]}: {stale_roots}"
            )


def check_official_purity() -> None:
    """kb-ingest/openwiki/ holds upstream bytes and nothing else.

    Marker comments inside a file are not enough on their own: the moment a
    hand-written appendix, a generator, or a scratch note lands in that directory,
    "this directory is exactly upstream" stops being checkable by inspection and
    `sync_prompts.py --check` stops being a complete statement about it. The
    boundary is therefore a directory boundary, and this is what enforces it.
    Anything skill-bettor adds belongs in kb-ingest/port/.
    """
    expected = {p.relative_to(OW).as_posix() for p in PROMPT_ASSETS}
    found = {p.relative_to(OW).as_posix() for p in OW.rglob("*") if p.is_file()}
    intruders = sorted(found - expected)
    if intruders:
        fail(
            f"kb-ingest/openwiki/ must contain ONLY the {len(expected)} generated upstream assets; "
            f"found non-official file(s): {intruders}. Move them to kb-ingest/port/."
        )
    if found != expected:
        fail(
            f"kb-ingest/openwiki/ is missing generated asset(s): {sorted(expected - found)}"
        )


def check_prompt_assets() -> None:
    """The port's central claim: prompt text is upstream's, verbatim and regenerable."""
    for path in PROMPT_ASSETS:
        text = read(path)
        shown = rel(path)
        for needle in (
            "DO NOT EDIT BY HAND",
            "<!-- OPENWIKI-OFFICIAL:BEGIN -->",
            "<!-- OPENWIKI-OFFICIAL:END -->",
            "upstream: langchain-ai/openwiki @",
        ):
            if needle not in text:
                fail(
                    f"{shown} is missing {needle!r} — regenerate with {rel(PORT / 'sync_prompts.py')}"
                )
        body = text.split("<!-- OPENWIKI-OFFICIAL:BEGIN -->", 1)[1]
        # An unresolved {PLACEHOLDER} would be shipped to the model as literal text.
        # User-prompt templates keep theirs on purpose; system prompts must have none.
        if "system.md" in path.name:
            import re

            leftover = re.findall(r"\{[A-Z][A-Z_]{3,}\}", body)
            if leftover:
                fail(
                    f"{shown} has unresolved placeholders {sorted(set(leftover))} — extend PLACEHOLDERS in sync_prompts.py"
                )

    init = read(OW / "init.system.md")
    # Spot-check that this really is the official init prompt and not a re-summarized one.
    # These three lines are exactly what the retired distilled workflow had dropped or inverted.
    for needle in (
        "Do not document every file or target a page count",
        "invoke the 'skeleton_critic' subagent",
        "'wiki_question_finder' and 'wiki_answer_verifier' subagents",
        "Do not draft wiki prose until every planned substantive page has an evidence brief",
    ):
        if needle not in init:
            fail(
                f"init.system.md does not look like the official prompt (missing: {needle!r})"
            )

    update = read(OW / "update.system.md")
    if "do not target a page count or page length" not in update:
        fail("update.system.md does not look like the official prompt")


def check_selftests() -> None:
    for script in (PORT / "openwiki_post.py", PORT / "sync_prompts.py"):
        result = run([sys.executable, str(script), "--selftest"])
        if result.returncode != 0 or "selftest ok" not in result.stdout:
            fail(f"{rel(script)} --selftest failed:\n{result.stdout}")


def check_subagent_boundaries() -> None:
    """Prove the three read boundaries hold, against the hardest case.

    The target here has a COMMITTED openwiki/, so a naive "the wiki is untracked
    anyway" assumption would pass while the real boundary leaked.
    """
    script = PORT / "openwiki_subagent.sh"
    with tempfile.TemporaryDirectory(prefix="repo-wiki-converge-") as tmp:
        target = Path(tmp) / "target"
        (target / "src").mkdir(parents=True)
        (target / "openwiki").mkdir()
        (target / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
        (target / "openwiki" / "quickstart.md").write_text(
            "---\ntype: Playbook\n---\n\n# Quickstart\n", encoding="utf-8"
        )
        for argv in (
            ["init", "-q"],
            ["add", "-A"],
            ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "init"],
        ):
            if run(["git", "-C", str(target), *argv], cwd=target).returncode != 0:
                fail("could not build the boundary-test fixture repository")
        (target / "openwiki" / "_skeleton.md").write_text(
            "- page: overview.md\n", encoding="utf-8"
        )

        env = {**os.environ, "OPENWIKI_DRY_RUN": "1"}
        seen = {}
        for role in ("finder", "critic", "verifier"):
            result = subprocess.run(
                ["bash", str(script), role, str(target)],
                input="payload\n",
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if result.returncode != 0:
                fail(f"{role} dry-run failed:\n{result.stdout}")
            seen[role] = result.stdout

        if "openwiki" in seen["finder"].split("sandbox top level:")[1]:
            fail(
                "BOUNDARY LEAK: the question finder can see the generated wiki\n"
                + seen["finder"]
            )
        if "src" in seen["verifier"].split("sandbox top level:")[1]:
            fail(
                "BOUNDARY LEAK: the answer verifier can see repository source\n"
                + seen["verifier"]
            )
        critic_sandbox = seen["critic"].split("sandbox top level:")[1]
        if "src" not in critic_sandbox or "openwiki" not in critic_sandbox:
            fail(
                "the skeleton critic must see both repository source and the skeleton\n"
                + seen["critic"]
            )

        worktrees = run(["git", "-C", str(target), "worktree", "list"]).stdout
        if worktrees.count("\n") != 1:
            fail(f"disposable worktrees were not cleaned up:\n{worktrees}")


def check_repodoc_ingest_dry_run() -> None:
    # `python3 -m indexing.…` needs the host checkout on the import path, not the module dir.
    fixture = INDEXING / "tests" / "fixtures" / "repowiki"
    with tempfile.TemporaryDirectory(prefix="repo-wiki-converge-") as tmp:
        graph = Path(tmp) / "graph.json"
        result = run(
            [
                sys.executable,
                "-m",
                "indexing.ingest_repodoc_cli",
                str(fixture),
                "--dry-run",
                "--graph",
                str(graph),
            ],
            cwd=HOST_ROOT,
        )
    if result.returncode != 0:
        fail(f"RepoDoc dry-run ingest failed:\n{result.stdout}")
    if (
        "RepoDoc=6" not in result.stdout
        or "[dry-run] no changes written." not in result.stdout
    ):
        fail(f"RepoDoc dry-run did not report expected fixture shape:\n{result.stdout}")


# Host-profile checks, run only when the installation declares them.
PROFILE_CHECKS = {
    "repodoc": [check_repodoc_ingest_dry_run],
    # Separate from skill-bettor-layout on purpose: "the host exposes this skill as a symlink
    # into the module" is true of any host that installs it, whereas the layout profile asserts
    # this repo's own repo//prototype/ conventions. Fused, no other host could adopt the link
    # discipline without also inheriting conventions that are none of its business.
    "host-skill-links": [check_skill_symlink],
}


def main() -> int:
    # Core: true of the module wherever it is installed.
    check_files()
    check_text_contracts()
    check_official_purity()
    check_prompt_assets()
    check_selftests()
    check_subagent_boundaries()

    for profile in PROFILES:
        for check in PROFILE_CHECKS.get(profile, []):
            check()

    declared = ", ".join(PROFILES) if PROFILES else "none (core only)"
    skipped = [p for p in KNOWN_PROFILES if p not in PROFILES]
    print(
        "PASS: repo-wiki-converge official-openwiki port "
        "(openwiki/ pure upstream · prompt assets verbatim · post-passes self-tested · "
        "read boundaries proven)"
    )
    print(f"      module={MODULE_ROOT}")
    print(f"      host profiles run: {declared}")
    if skipped:
        # Naming what did NOT run keeps a narrowed gate from reading as a full one.
        print(
            f"      host profiles NOT declared (their checks did not run): {', '.join(skipped)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
