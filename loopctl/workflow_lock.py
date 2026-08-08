#!/usr/bin/env python3
"""The workflow's file manifest: what a CLI traversal is actually made of.

    workflow_lock.py build <repo> <out>     assemble the manifest from the proof receipts
    workflow_lock.py touched <repo> <lock>  print staged paths that are in the manifest
    workflow_lock.py --selftest

The manifest is not written by hand and is not a second list to keep in sync. It
is assembled from the three proof receipts at the current commit, which already
record every path a traversal walked and what kind it was — deterministic harness
or the documents the probabilistic lane reads. Deriving it means the manifest
cannot describe a workflow different from the one the proofs measured.

Kinds are carried through rather than flattened. "Something in the workflow
changed" is too coarse to act on: a changed harness script means the mechanism
moved, a changed context document means the prompt the model reads moved, and a
changed surface means the external promise moved. They fail differently and the
lineage trailer says which.

Absence is FATAL, never an empty manifest: a lock built from no receipts would
declare that nothing belongs to the workflow, and every later check would pass
by covering nothing.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

LOOPS = ("macro", "micro", "openwiki", "container", "policy")


def _receipt(repo: Path, loop: str, short: str) -> Path | None:
    """The receipt describing the CURRENT tree, clean or dirty.

    Preferring the clean stamp unconditionally lets a receipt from an earlier
    tree-state answer for a freshly re-proved dirty one — the lock then describes
    a workflow nobody is holding, and a newly covered file never reaches the
    manifest, so the lineage hook stays silent about a change it should sense.
    Found here after the identical defect was fixed in compare_control.py: one
    instance repaired is not the class repaired.
    """
    dirty = bool(
        subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "status",
                "--porcelain",
                "--",
                ".",
                ":(exclude)data/proof-workflow/",
            ],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    )
    names = (
        (f"{loop}-{short}-dirty.json", f"{loop}-{short}.json")
        if dirty
        else (f"{loop}-{short}.json", f"{loop}-{short}-dirty.json")
    )
    for name in names:
        candidate = repo / "data" / "proof-workflow" / name
        if candidate.is_file():
            return candidate
    return None


def commit_bytes(repo: Path, path: str, worktree_sha: str) -> tuple[str, str]:
    """The hash of what a commit would carry for this path, and where it came from.

    Concurrency, not pedantry. The receipts hash the WORKING TREE — correctly, since
    that is what ran — but a commit carries the INDEX, and anything edited between a
    proof and its commit made the lock describe bytes nobody was committing. The gate
    then refused with an error that read like the committer's mistake. Reading the
    index instead closes that window: someone else's unstaged edit cannot move this,
    and only `git add` can, which is the committer's own act.

    Order still matters and is stated where it is needed: stage first, then lock,
    then stage the lock. Falls back to HEAD for a workflow file that is tracked but
    not staged, and only then to the worktree — each labelled, so a reader never has
    to guess which one answered.
    """
    for args, origin in (
        (["rev-parse", f":{path}"], "index"),
        (["rev-parse", f"HEAD:{path}"], "head"),
    ):
        blob = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
        ).stdout.strip()
        if blob:
            content = subprocess.run(
                ["git", "-C", str(repo), "cat-file", "blob", blob],
                capture_output=True,
                check=False,
            ).stdout
            return hashlib.sha256(content).hexdigest(), origin
    # Untracked runtime evidence: only the working tree has it, and the receipt
    # already hashed exactly those bytes.
    return worktree_sha, "worktree"


def build(repo: Path) -> dict:
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    short = head[:12]
    tag = subprocess.run(
        ["git", "-C", str(repo), "tag", "--points-at", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.split()

    files: dict[str, dict] = {}
    sources: dict[str, str] = {}
    for loop in LOOPS:
        receipt = _receipt(repo, loop, short)
        if receipt is None:
            raise SystemExit(
                f"workflow-lock FATAL: no {loop} proof receipt at {short}. A manifest built "
                "from missing receipts would declare that nothing belongs to the workflow, "
                "and every check downstream would pass by covering nothing. "
                "Run `sh loopctl/loopctl.sh <loop> prove` for each loop first."
            )
        data = json.loads(receipt.read_text(encoding="utf-8"))
        sources[loop] = receipt.name
        for step in data["steps"]:
            path = step.get("path")
            if not path or path == "-" or not step.get("sha256"):
                continue
            digest, origin = commit_bytes(repo, path, step["sha256"])
            files.setdefault(
                path,
                {
                    "sha256": digest,
                    "hash_source": origin,
                    "kind": step["kind"],
                    "loop": loop,
                },
            )

    # Cycle guard. The lock is DERIVED from these receipts, so a proof that hashed
    # the lock would make the receipt depend on a file that depends on the receipt:
    # every rebuild would move both and neither would ever settle. It is excluded
    # by a note in the macro proof today, and this refuses to let a future step
    # reintroduce it silently — a self-referential manifest looks green while
    # never converging.
    for self_ref in ("loopctl/workflow.lock",):
        if self_ref in files:
            raise SystemExit(
                f"workflow-lock FATAL: {self_ref} appears in a proof receipt. The lock is "
                "built from those receipts, so hashing it there is a cycle: the digest "
                "would depend on a file that depends on the digest, and no rebuild would "
                "ever settle. Remove that step, or record it with prove_note instead."
            )

    canonical = "".join(
        f"{p} {files[p]['kind']} {files[p]['sha256']}\n" for p in sorted(files)
    )
    return {
        "schema_version": "bettor-arena-workflow-lock@1.0.0",
        "workflow_commit": head,
        "workflow_tags": tag,
        "built_from": sources,
        "counts": {
            kind: sum(1 for f in files.values() if f["kind"] == kind)
            for kind in sorted({f["kind"] for f in files.values()})
        },
        "workflow_digest": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "files": {p: files[p] for p in sorted(files)},
    }


def staged(repo: Path) -> list[str]:
    out = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMR",
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line for line in out.splitlines() if line.strip()]


def touched(lock: dict, paths: list[str]) -> list[tuple[str, str, str]]:
    """Staged paths that are part of the workflow, with the kind and loop each belongs to."""
    return [
        (p, lock["files"][p]["kind"], lock["files"][p]["loop"])
        for p in paths
        if p in lock["files"]
    ]


def main(argv: list[str]) -> int:
    if argv[:1] == ["--selftest"]:
        return _selftest()
    if len(argv) < 3:
        print(__doc__.strip(), file=sys.stderr)
        return 64
    cmd, repo, target = argv[0], Path(argv[1]), Path(argv[2])
    if cmd == "build":
        lock = build(repo)
        target.write_text(
            json.dumps(lock, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(
            f"workflow-lock: {len(lock['files'])} file(s) {lock['counts']} "
            f"digest={lock['workflow_digest'][:12]} commit={lock['workflow_commit'][:12]}"
            + (f" tags={lock['workflow_tags']}" if lock["workflow_tags"] else "")
        )
        return 0
    if cmd == "touched":
        if not target.is_file():
            print(f"workflow-lock FATAL: no lock at {target}", file=sys.stderr)
            return 64
        lock = json.loads(target.read_text(encoding="utf-8"))
        for path, kind, loop in touched(lock, staged(repo)):
            print(f"{kind}\t{loop}\t{path}")
        return 0
    print(__doc__.strip(), file=sys.stderr)
    return 64


# ---------------------------------------------------------------- selftest


def _selftest() -> int:
    red = 0

    def case(name: str, got, want) -> None:
        nonlocal red
        if got != want:
            print(
                f"SELFTEST case failed — {name}: got {got}, want {want}",
                file=sys.stderr,
            )
            red = 1

    lock = {
        "files": {
            "a/harness.sh": {"sha256": "x", "kind": "harness", "loop": "macro"},
            "b/prompt.md": {"sha256": "y", "kind": "context", "loop": "openwiki"},
        }
    }
    case(
        "in-manifest-is-reported",
        touched(lock, ["a/harness.sh", "unrelated.txt"]),
        [("a/harness.sh", "harness", "macro")],
    )
    case("outside-manifest-is-silent", touched(lock, ["unrelated.txt"]), [])
    # The kind must survive: "the workflow changed" cannot tell a moved mechanism
    # from a moved prompt, and those are repaired differently.
    case(
        "kind-and-loop-survive",
        touched(lock, ["b/prompt.md"]),
        [("b/prompt.md", "context", "openwiki")],
    )
    print("SELFTEST " + ("GREEN" if not red else "RED"))
    return red


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
