#!/usr/bin/env python3
"""Stage-1 validation: prove the landed LoopX foundation on exact current main.

Issue #90 asks for executable evidence that five mechanisms are really on the
default branch and really work there -- not that they worked on the branch they
were written on. Those are different claims, and this repository has already
been bitten by the difference: four squash merges left every child PR's head
commit unreachable from main while their contents were fully present.

So reachability here is proved by content, not by commit ancestry. For each
module the tree object at the PR head is compared against the tree at current
main; when they differ, every differing path is listed with the commit that
introduced the change, so a difference is either explained or visible.

Every suite is then executed against the current checkout. A suite that passed
in CI on a branch is not evidence about main.

Exit: 0 all evidence holds, 2 something disagreed, 64 unusable input.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

OK, BAD, USAGE = 0, 2, 64

# The five mechanisms, with the PR that delivered each and the head commit that
# PR was merged at. Pinned literally: deriving them from the current GitHub API
# would make this receipt depend on state that can change after it is written.
DELIVERIES = [
    {
        "module": "loopx-kernel",
        "pr": 74,
        "issue": 62,
        "head": "0731b667d0832c49b7844d7a2788c435518a654f",
        "merge_commit": "d194df1ad7a9e114dab1952d2be57fdf86b7b44d",
        "capability": "loopx.contracts/v1",
    },
    {
        "module": "loopx-ledger",
        "pr": 75,
        "issue": 63,
        "head": "8fa52730754c49da3128474423ddbc75007c5ae4",
        "merge_commit": "2fd05408f585f6b8999a7922d4995d8379795eb2",
        "capability": "loopx.ledger/v1",
    },
    {
        "module": "loopx-worker-gateway",
        "pr": 76,
        "issue": 64,
        "head": "4ebdfdfb0e20b9177b2e11834c49af41b3bbd228",
        "merge_commit": "c6c0a25f7c7f35d34d2530a37983058a65eadf1b",
        "capability": "loopx.worker-gateway/v1",
    },
    {
        "module": "loopx-decision-memory",
        "pr": 78,
        "issue": 42,
        "head": "1f0eb3acef73b9b22bf71f886a28b5363a09cc9c",
        "merge_commit": "489958df1bc1e0f5d8ccfed451a089001cef5419",
        "capability": "loopx.decision-memory/v1",
    },
    {
        "module": "code-truth-graph-v2",
        "pr": 79,
        "issue": 69,
        "head": "966e74fa11fac99b4a0eeb5cf8c7d80aeaa8d10c",
        "merge_commit": "437ad4004ced51ba2e2ee7c3253897c0fe61f8d2",
        "capability": "code-truth-graph.build/v2",
    },
]

# Authority ceilings. Each is a claim the foundation must NOT make; the receipt
# records where the refusal lives so a later reader can re-check it.
CEILINGS = [
    (
        "worker may not write canonical state",
        "loop_wiki/loopx-worker-gateway/contracts/AUTHORITY.md",
    ),
    (
        "memory admission is proposal-only until Human admit",
        "loop_wiki/loopx-decision-memory/contracts",
    ),
    (
        "graph is an evidence plane, not an authority",
        "loop_wiki/code-truth-graph-v2/contracts",
    ),
]


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


def tree_of(root: Path, rev: str, path: str) -> str | None:
    try:
        return git(root, "rev-parse", f"{rev}:{path}")
    except RuntimeError:
        return None


def content_reachability(root: Path, delivery: dict[str, Any]) -> dict[str, Any]:
    """Is the PR's module present on main, and if changed, changed by what?"""
    path = f"loop_wiki/{delivery['module']}"
    head_tree = tree_of(root, delivery["head"], path)
    main_tree = tree_of(root, "HEAD", path)

    if main_tree is None:
        return {"state": "ABSENT_FROM_MAIN", "path": path}
    if head_tree is None:
        return {"state": "ABSENT_AT_PR_HEAD", "path": path, "main_tree": main_tree}
    if head_tree == main_tree:
        return {
            "state": "IDENTICAL",
            "path": path,
            "tree": head_tree,
        }

    changed = [
        line
        for line in git(
            root, "diff", "--name-only", delivery["head"], "HEAD", "--", path
        ).splitlines()
        if line
    ]
    attributions = []
    unattributable = 0
    for rel in changed:
        commits = git(
            root, "log", "--format=%H %s", f"{delivery['head']}..HEAD", "--", rel
        ).splitlines()
        changed_by = [
            {"commit": line.split(" ", 1)[0], "subject": line.split(" ", 1)[1]}
            for line in commits
            if " " in line
        ]
        entry: dict[str, Any] = {
            "path": rel,
            "at_pr_head": tree_of(root, delivery["head"], rel) is not None
            or _blob_exists(root, delivery["head"], rel),
            "on_main": _blob_exists(root, "HEAD", rel),
        }
        if changed_by:
            entry["attribution"] = "ATTRIBUTED"
            entry["changed_by"] = changed_by
        else:
            # An empty log here is not "nothing changed" -- the diff already said
            # it did. The change happened on a branch that was squashed, so the
            # commit that made it is not in HEAD's history at all. Saying so is
            # the honest answer; an empty list would read as no change.
            entry["attribution"] = "UNATTRIBUTABLE_SQUASHED_HISTORY"
            entry["changed_by"] = []
            unattributable += 1
        attributions.append(entry)

    return {
        "state": "PRESENT_WITH_ATTRIBUTED_CHANGES",
        "path": path,
        "pr_head_tree": head_tree,
        "main_tree": main_tree,
        "changed_paths": attributions,
        "unattributable_count": unattributable,
    }


def _blob_exists(root: Path, rev: str, rel: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "cat-file", "-e", f"{rev}:{rel}"],
        capture_output=True,
    )
    return result.returncode == 0


def run_suite(root: Path, module: str) -> dict[str, Any]:
    suite = root / "loop_wiki" / module / "tests" / "run-all.sh"
    if not suite.is_file():
        return {"state": "ABSENT", "suite": str(suite.relative_to(root))}
    result = subprocess.run(
        ["sh", str(suite)], capture_output=True, text=True, cwd=str(root)
    )
    tail = [line for line in result.stdout.splitlines() if line.strip()][-6:]
    return {
        "state": "PASS" if result.returncode == 0 else "FAIL",
        "exit_code": result.returncode,
        "suite": str(suite.relative_to(root)),
        "reported": tail,
    }


def module_closure(root: Path, module: str) -> dict[str, Any]:
    manifest = root / ".arena" / "modules" / module / "module.json"
    if not manifest.is_file():
        return {"state": "ABSENT"}
    data = json.loads(manifest.read_text())
    missing = []
    for name, component in (data.get("components") or {}).items():
        for rel in component.get("paths", []):
            if not (root / rel).exists():
                missing.append(f"{name}:{rel}")
    return {
        "state": "COMPLETE" if not missing else "INCOMPLETE",
        "interface_version": data.get("interface_version"),
        "provides": data.get("provides"),
        "requires": data.get("requires"),
        "missing_paths": missing,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--observed-at", required=True)
    parser.add_argument(
        "--predecessor-receipt",
        required=True,
        help="how issue #82 was disposed; #90 requires it pinned",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()

    try:
        commit = git(root, "rev-parse", "HEAD")
        tree = git(root, "rev-parse", "HEAD^{tree}")
        dirty = git(root, "status", "--porcelain")
    except RuntimeError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE

    receipt: dict[str, Any] = {
        "schema_version": "bettor-arena/loopx-stage1-receipt/v1",
        "observed_at": args.observed_at,
        "subject": {
            "repository": "ed3c/bettor-arena",
            "commit": commit,
            "tree": tree,
            "worktree_clean": dirty == "",
        },
        "predecessor": {
            "issue": 82,
            "disposition": args.predecessor_receipt,
        },
        "reachability_method": (
            "content, not commit ancestry: four squash merges left every child "
            "PR head unreachable from main while their contents were present, so "
            "ancestry would report absent for a module that is fully landed"
        ),
        "deliveries": [],
        "authority_ceilings": [],
    }

    failures: list[str] = []

    for delivery in DELIVERIES:
        module = delivery["module"]
        reach = content_reachability(root, delivery)
        suite = run_suite(root, module)
        closure = module_closure(root, module)

        if reach["state"] in {"ABSENT_FROM_MAIN", "ABSENT_AT_PR_HEAD"}:
            failures.append(f"{module}: {reach['state']}")
        if suite["state"] != "PASS":
            failures.append(f"{module}: suite {suite['state']}")
        if closure["state"] != "COMPLETE":
            failures.append(
                f"{module}: closure {closure['state']} {closure.get('missing_paths')}"
            )

        receipt["deliveries"].append(
            {
                **{
                    k: delivery[k]
                    for k in (
                        "module",
                        "pr",
                        "issue",
                        "head",
                        "merge_commit",
                        "capability",
                    )
                },
                "reachability": reach,
                "suite": suite,
                "closure": closure,
            }
        )

    for claim, where in CEILINGS:
        path = root / where
        receipt["authority_ceilings"].append(
            {
                "claim": claim,
                "declared_in": where,
                "present": path.exists(),
            }
        )
        if not path.exists():
            failures.append(f"authority ceiling undocumented: {claim}")

    receipt["result"] = "PASS" if not failures else "FAIL"
    receipt["failures"] = failures

    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"WROTE {args.output}")
    else:
        sys.stdout.write(text)

    if failures:
        for line in failures:
            print(f"STAGE1-RED {line}", file=sys.stderr)
        return BAD
    print(
        f"PASS stage-1: {len(DELIVERIES)} mechanisms present on {commit[:8]}, "
        f"suites green, closures complete"
    )
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
