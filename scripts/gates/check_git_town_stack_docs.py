#!/usr/bin/env python3
"""Zero-network Stack governance verifier; never executes Git Town. Exit 0/2/64."""

import argparse
import copy
import json
import re
import sys
from pathlib import Path

MAIN = "ea8c4a101bcf44ffe54c78ef53da583afa9efad2"
SCHEMA = "bettor-arena/stack-pr-index/v1"
SKILL = {
    "repository": "ed3c/skills-shared",
    "commit": "c5750720d960a228a0d9419f28125c09d064e3e1",
    "blob": "eb2d915bca3e8a3938625f7d33a10fae95a15769",
    "path": "skills/git-town-stacked-pr-worker/SKILL.md",
    "reference_state": "PINNED",
    "selection_state": "NOT_SELECTED",
}
GIT_TOWN = {
    "binary_state": "ABSENT",
    "configuration_state": "ABSENT",
    "live_sync_state": "NOT_EXERCISED",
    "publication_state": "NOT_EXERCISED",
    "human_admit": "NOT_PERFORMED",
}
FILES = """README.md AGENTS.md CLAUDE.md docs/README.md docs/INDEX.md docs/git/README.md docs/git/REPO_PROFILE.md docs/git/STACKED_PRS.md docs/git/WORKER_PROTOCOL.md docs/git/GIT_TOWN_ADMISSION.md docs/git/stack-prs.index.schema.json docs/git/stack-prs.index.json docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md docs/architecture/STATE_MACHINES.md docs/architecture/agent-entrypoints.contract.json docs/traceability/STACK_PR_INDEX.md .arena/contexts/macro.json""".split()
MARK = {
    "README.md": [
        "Git Town Stacked-PR governance",
        "Directory → State Machine ownership",
        "RESOLVED_BY_HUMAN",
    ],
    "AGENTS.md": [
        "## Git Town Stacked-PR Worker route",
        SKILL["path"],
        "## Completion contract",
    ],
    "CLAUDE.md": ["docs/git/REPO_PROFILE.md", SKILL["path"], "Claude Code 不得"],
    "docs/git/README.md": ["## State Machine", "## Data flow", "Human Admit boundary"],
    "docs/git/REPO_PROFILE.md": [
        "binary_state: ABSENT",
        "configuration_state: ABSENT",
        "one_worker_one_worktree: true",
        "## Rollback boundary",
    ],
    "docs/git/STACKED_PRS.md": [
        "PR #75",
        "MERGED_TO_MAIN",
        "PR #76",
        "PR #77",
        "RESOLVED_BY_HUMAN",
        "issue #80",
    ],
    "docs/git/WORKER_PROTOCOL.md": [
        "## Worker State Machine",
        "## Conflict protocol",
        "## Rollback boundary",
    ],
    "docs/git/GIT_TOWN_ADMISSION.md": [
        "not currently admitted",
        ".git-town.toml",
        "## Unblock criteria",
    ],
    "docs/architecture/DIRECTORY_STATE_MACHINE_MAP.md": [
        "docs/git/",
        "Git Town Stack State Machine",
    ],
    "docs/architecture/STATE_MACHINES.md": [
        "Git Town Stacked-PR worker State Machine",
        "MERGED_TO_PARENT",
    ],
    "docs/traceability/STACK_PR_INDEX.md": [
        "Canonical shared Git Town method",
        "PR #75",
        "PR #76",
        "PR #77",
        "issue #80",
    ],
}
# Home roots are assembled at runtime so this gate does not flag its own source,
# the same way check_root_coupling.py does it.
_HOME = "|".join(
    a + b for a, b in (("/Use", "rs/"), ("/ho", "me/"), ("[A-Za-z]:\\\\Use", "rs\\\\"))
)
BAD = [
    re.compile(x)
    for x in [
        r"<[A-Z][A-Z0-9_ -]{2,}>",
        r"(^|[\s`'\"])(" + _HOME + r")",
        r"https://[^/\s:@]+:[^/\s@]+@",
        r"\b(?:ghp_|github_pat_|sk-)[A-Za-z0-9_]{20,}\b",
    ]
]
HEX = re.compile(r"^[0-9a-f]{40}$")


class Fatal(Exception):
    pass


def read(p):
    try:
        return p.read_text(encoding="utf-8")
    except OSError as e:
        raise Fatal(f"unreadable {p}: {e}")


def obj(s, name):
    try:
        v = json.loads(s)
    except json.JSONDecodeError as e:
        raise Fatal(f"invalid JSON {name}: {e}")
    if not isinstance(v, dict):
        raise Fatal(f"object required: {name}")
    return v


def load(root):
    missing = [x for x in FILES if not (root / x).is_file()]
    if missing:
        raise Fatal("missing " + ", ".join(missing))
    docs = {x: read(root / x) for x in FILES}
    return {
        "docs": docs,
        "index": obj(docs["docs/git/stack-prs.index.json"], "index"),
        "entry": obj(
            docs["docs/architecture/agent-entrypoints.contract.json"], "entry"
        ),
        "macro": obj(docs[".arena/contexts/macro.json"], "macro"),
        "config": (root / ".git-town.toml").exists() or (root / ".git-town").exists(),
        "shadow": (
            root / ".agents/skills/git-town-stacked-pr-worker/SKILL.md"
        ).exists(),
    }


def nodes(d):
    return [
        n
        for s in d.get("stacks", [])
        if isinstance(s, dict)
        for n in s.get("nodes", [])
        if isinstance(n, dict)
    ]


def find(a, key, val):
    return next((x for x in a if x.get(key) == val), None)


def validate(v):
    e = []
    docs = v["docs"]
    d = v["index"]
    for f, ms in MARK.items():
        e += [f"MARKER {f}: {m}" for m in ms if m not in docs[f]]
    for f, s in docs.items():
        if any(x.search(s) for x in BAD):
            e.append("UNSAFE " + f)
    if v["config"]:
        e.append("FALSE CONFIG")
    if v["shadow"]:
        e.append("SHADOW SKILL")
    r = d.get("repository", {})
    if d.get("schema") != SCHEMA:
        e.append("SCHEMA")
    if (
        r.get("full_name"),
        r.get("repository_id"),
        r.get("default_branch"),
        r.get("observed_main_sha"),
    ) != ("ed3c/bettor-arena", 1330387399, "main", MAIN):
        e.append("REPO/MAIN")
    if d.get("shared_skill") != SKILL:
        e.append("SKILL")
    if d.get("git_town") != GIT_TOWN:
        e.append("GIT TOWN ADMISSION")
    a = nodes(d)
    ids = [x.get("id") for x in a]
    br = [x.get("branch") for x in a if x.get("branch") not in (None, "NOT_CREATED")]
    if len(ids) != len(set(ids)):
        e.append("DUP ID")
    if len(br) != len(set(br)):
        e.append("DUP BRANCH")
    for x in a:
        h = x.get("observed_head_sha")
        rb = x.get("rollback_subject")
        if h is not None and not HEX.fullmatch(str(h)):
            e.append("HEAD")
        if not HEX.fullmatch(str(rb)):
            e.append("ROLLBACK")
        if any(
            not isinstance(p, str) or Path(p).is_absolute() or ".." in Path(p).parts
            for p in x.get("path_roots", [])
        ):
            e.append("PATH")
    p = find(a, "pr", 75)
    q = find(a, "issue", 80)
    if not p or (p.get("publication_state"), p.get("main_presence")) != (
        "MERGED_TO_MAIN",
        "ON_MAIN",
    ):
        e.append("PR75")
    if not q or (
        q.get("branch"),
        q.get("base_branch"),
        q.get("relation"),
        q.get("main_presence"),
    ) != ("feat/git-town-stack-governance-v1", "main", "TRUE_CHILD", "NOT_ON_MAIN"):
        e.append("ISSUE80")
    # The duplicate is settled: #76 landed, #77 was closed as a superseded second
    # implementation of the same module. The pair still has to be named -- an
    # index that simply forgot the duplicate would look identical to one where it
    # was resolved -- so the assertion moves from "blocked" to "resolved this way".
    x = find(a, "pr", 76)
    if not x or (
        x.get("issue"),
        x.get("publication_state"),
        x.get("main_presence"),
    ) != (64, "MERGED_TO_MAIN", "ON_MAIN"):
        e.append("DUP PR")
    x = find(a, "pr", 77)
    if not x or (x.get("issue"), x.get("relation"), x.get("publication_state")) != (
        64,
        "HISTORICAL",
        "SUPERSEDED_CANDIDATE",
    ):
        e.append("DUP PR")
    c = next(
        (
            x
            for x in d.get("conflicts", [])
            if isinstance(x, dict) and set(x.get("prs", [])) == {76, 77}
        ),
        None,
    )
    if not c or (c.get("type"), c.get("state"), c.get("authority")) != (
        "DUPLICATE_ACTIVE_TERMINAL",
        "RESOLVED_BY_HUMAN",
        "HUMAN",
    ):
        e.append("CONFLICT")
    if c and not c.get("resolution"):
        e.append("CONFLICT RESOLUTION")
    human = set(d.get("human_owned_operations", []))
    for x in (
        "semantic conflict resolution",
        "remote publication",
        "merge ship close or delete",
        "promotion",
        "rollback",
    ):
        if x not in human:
            e.append("HUMAN")
    for z in (v["entry"].get("canonical_documents", []), v["macro"].get("common", [])):
        for x in (
            "docs/git/README.md",
            "docs/git/REPO_PROFILE.md",
            "docs/git/STACKED_PRS.md",
            "docs/git/stack-prs.index.json",
        ):
            if x not in z:
                e.append("ROUTE")
    return e


def check(root):
    return validate(load(root))


def selftest(v):
    if validate(v):
        raise Fatal("positive failed " + repr(validate(v)))

    def ix(x):
        return x["index"]

    muts = [
        lambda x: x.__setitem__("config", True),
        lambda x: find(nodes(ix(x)), "pr", 75).__setitem__(
            "main_presence", "NOT_ON_MAIN"
        ),
        lambda x: ix(x).__setitem__("conflicts", []),
        lambda x: [
            s.__setitem__("nodes", [n for n in s["nodes"] if n.get("issue") != 80])
            for s in ix(x)["stacks"]
        ],
        lambda x: x["docs"].__setitem__(
            "docs/git/REPO_PROFILE.md",
            x["docs"]["docs/git/REPO_PROFILE.md"] + "<MAIN_BRANCH>",
        ),
        lambda x: x["docs"].__setitem__(
            "docs/git/REPO_PROFILE.md",
            x["docs"]["docs/git/REPO_PROFILE.md"] + "https://u:p@example.invalid/r",
        ),
        lambda x: find(nodes(ix(x)), "pr", 74)["path_roots"].append("../x"),
        lambda x: x["docs"].__setitem__(
            "AGENTS.md",
            x["docs"]["AGENTS.md"].replace("## Completion contract", "## gone"),
        ),
        lambda x: ix(x)["repository"].__setitem__("observed_main_sha", "0" * 40),
        lambda x: x.__setitem__("shadow", True),
        lambda x: find(nodes(ix(x)), "pr", 79).__setitem__(
            "branch", find(nodes(ix(x)), "pr", 78)["branch"]
        ),
        lambda x: ix(x)["shared_skill"].__setitem__("selection_state", "SELECTED"),
        lambda x: ix(x).__setitem__("git_town", {"binary_state": "ADMITTED"}),
    ]
    for i, m in enumerate(muts, 1):
        q = copy.deepcopy(v)
        m(q)
        if not validate(q):
            raise Fatal(f"mutation {i} survived")
    print(f"SELFTEST PASS Git Town Stack governance: 1 positive, {len(muts)} mutations")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    r = a.root.resolve()
    try:
        v = load(r)
        if a.selftest:
            selftest(v)
            return 0
        e = validate(v)
    except Fatal as x:
        print("git-town-stack FATAL:", x, file=sys.stderr)
        return 64
    if e:
        for x in e:
            print("GIT-TOWN-STACK-RED", x, file=sys.stderr)
        return 2
    print(
        "PASS Git Town Stack governance: profile, routes, DAG, conflict and Human boundaries"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
