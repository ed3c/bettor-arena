#!/usr/bin/env python3
"""Physical control group: real repositories, a real remote, real refs to move.

Git Town is not installed here, so this proves nothing about Git Town. It proves
the guard rails, which is the part that has to hold around a program nobody in
this repository has read -- and the only way to know a guard rail holds is to
drive something through it.

So every invariant gets both cases, in a real repository with a real bare remote:

  * a bounded local change: refs stay put, remote untouched, invariants hold;
  * a push: the remote refs move, and REMOTE_REF_MOVED fires -- read from the
    remote repository itself, not from the local remote-tracking cache;
  * main moved: PROTECTED_REF_MOVED fires;
  * a file outside the lease edited: OUT_OF_LEASE_DIFF fires;
  * conflict markers committed into a file with a clean `git status`:
    SILENT_CONFLICT_MARKERS fires;
  * a real `.orig` left on disk: RESIDUE_LEFT fires;
  * a real rebase stopped mid-conflict: OPERATION_IN_FLIGHT fires;
  * the rollback branch moved: the rollback subject refuses.

Each dirty case is followed by the clean one again, so a red is attributable to
what was planted rather than to the checker having broken.

Exits 0 or 2.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gt_admit import admit, modes_for, probe, require_mode_allowed  # noqa: E402
from gt_common import BAD, OK, ContractError  # noqa: E402
from gt_fixture import build, run  # noqa: E402
from gt_invariants import (  # noqa: E402
    compare,
    refs,
    require_rollback_intact,
    rollback_subject,
    snapshot,
)

# Built from parts rather than typed, for the same reason gt_common builds them
# that way: a source file containing the literal seven characters is flagged by
# every tool that scans for conflicts, including this repository's own gates.
MARKERS = (
    ("<" * 7) + " ours\nmine\n" + ("=" * 7) + "\ntheirs\n" + (">" * 7) + " theirs\n"
)


def main() -> int:
    checks = 0

    with tempfile.TemporaryDirectory(prefix="gt-control-") as tmp:
        fx = build(Path(tmp))
        repo, remote, lease = fx["repo"], fx["remote"], fx["lease"]

        base = snapshot(repo, remote, lease)
        rollback = rollback_subject(repo, remote, lease)
        if not base["local_refs"] or not base["remote_refs"]:
            raise ContractError(
                "the fixture produced no refs; nothing below would check anything"
            )
        if (
            base["dirty"]
            or base["residue"]
            or base["in_flight"]
            or base["conflict_markers"]
        ):
            raise ContractError(f"the fixture started unclean: {base}")
        checks += 1

        # 1. A bounded local change inside the lease. Everything holds.
        (repo / "leased" / "one.txt").write_text("one, edited\n", encoding="utf-8")
        run(repo, "add", "-A")
        run(repo, "commit", "-m", "leased: bounded change")
        bounded = snapshot(repo, remote, lease)
        result = compare(base, bounded, lease)
        if not result["held"]:
            raise ContractError(
                f"a bounded in-lease commit violated {result['violations']}"
            )
        require_rollback_intact(rollback, repo, remote, lease)
        checks += 1

        # 2. A real push. The remote moves and the invariant reads it from the
        #    remote repository, not from the local tracking cache.
        run(repo, "push", "origin", "HEAD")
        pushed = snapshot(repo, remote, lease)
        result = compare(base, pushed, lease)
        if any(v["rule"] == "REMOTE_REF_MOVED" for v in result["violations"]) is False:
            raise ContractError("a real push did not trip REMOTE_REF_MOVED")
        checks += 1

        # 2b. A push from somewhere else entirely. The remote moves and this
        #     repository's remote-tracking cache does not, because nothing here
        #     fetched. A checker reading the local cache sees nothing; the
        #     question --no-push asks is about the remote, and this is the case
        #     where the two answers differ.
        import subprocess as sp2

        # Its own baseline. Against `base`, the earlier local push would carry
        # the detection -- the cache moved then, so a cache-reading checker still
        # reports a difference and this control passes while checking nothing.
        pre_second = snapshot(repo, remote, lease)
        cache_before = refs(repo, "refs/remotes")

        second = Path(tmp) / "second"
        sp2.run(
            ["git", "clone", str(remote), str(second)], capture_output=True, check=True
        )
        run(second, "config", "user.name", "other")
        run(second, "config", "user.email", "other@invalid")
        (second / "leased" / "elsewhere.txt").write_text(
            "from another clone\n", encoding="utf-8"
        )
        run(second, "add", "-A")
        run(second, "commit", "-m", "second clone: publish")
        run(second, "push", "origin", "HEAD:main")

        elsewhere = snapshot(repo, remote, lease)
        if refs(repo, "refs/remotes") != cache_before:
            raise ContractError(
                "this repository fetched between the two snapshots; the cache case is no "
                "longer distinguishable from the remote case"
            )
        if not any(
            v["rule"] == "REMOTE_REF_MOVED"
            for v in compare(pre_second, elsewhere, lease)["violations"]
        ):
            raise ContractError(
                "the remote moved from another clone and went undetected. The checker is "
                "reading this repository's remote-tracking cache, which does not move when "
                "somebody else pushes -- and does move when nobody pushed at all"
            )
        checks += 1

        # 3. Protected ref moved.
        run(repo, "checkout", "main")
        (repo / "leased" / "main.txt").write_text("main moved\n", encoding="utf-8")
        run(repo, "add", "-A")
        run(repo, "commit", "-m", "main: moved")
        moved = snapshot(repo, remote, lease)
        if not any(
            v["rule"] == "PROTECTED_REF_MOVED"
            for v in compare(base, moved, lease)["violations"]
        ):
            raise ContractError("moving main did not trip PROTECTED_REF_MOVED")
        run(repo, "reset", "--hard", base["local_refs"]["refs/heads/main"])
        checks += 1

        # 4. Out of lease.
        run(repo, "checkout", fx["stack"][-1])
        (repo / "outside.txt").write_text(
            "changed outside the lease\n", encoding="utf-8"
        )
        run(repo, "add", "-A")
        run(repo, "commit", "-m", "outside: changed")
        outside = snapshot(repo, remote, lease)
        if not any(
            v["rule"] == "OUT_OF_LEASE_DIFF"
            for v in compare(base, outside, lease)["violations"]
        ):
            raise ContractError(
                "editing outside the lease did not trip OUT_OF_LEASE_DIFF"
            )
        checks += 1

        # 5. Conflict markers committed, with a clean `git status`. The dangerous
        #    case: the operation finished and the markers look like code.
        (repo / "leased" / "one.txt").write_text(MARKERS + "\n", encoding="utf-8")
        run(repo, "add", "-A")
        run(repo, "commit", "-m", "leased: markers committed")
        marked = snapshot(repo, remote, lease)
        if marked["dirty"]:
            raise ContractError("the marker case is only interesting with a clean tree")
        if not any(
            v["rule"] == "SILENT_CONFLICT_MARKERS"
            for v in compare(base, marked, lease)["violations"]
        ):
            raise ContractError(
                "committed conflict markers with a clean status went undetected"
            )
        checks += 1

        # 6. Real residue on disk.
        (repo / "leased" / "one.txt.orig").write_text("left behind\n", encoding="utf-8")
        residual = snapshot(repo, remote, lease)
        if not any(
            v["rule"] == "RESIDUE_LEFT"
            for v in compare(base, residual, lease)["violations"]
        ):
            raise ContractError("a real .orig on disk did not trip RESIDUE_LEFT")
        (repo / "leased" / "one.txt.orig").unlink()
        checks += 1

        # 7. A real rebase stopped in the middle. Not simulated: two branches
        #    genuinely edit the same line, and git stops.
        run(repo, "checkout", "main")
        (repo / "leased" / "clash.txt").write_text("main version\n", encoding="utf-8")
        run(repo, "add", "-A")
        run(repo, "commit", "-m", "main: clash")
        run(repo, "checkout", "-b", "clashing", base["local_refs"]["refs/heads/main"])
        (repo / "leased" / "clash.txt").write_text("branch version\n", encoding="utf-8")
        run(repo, "add", "-A")
        run(repo, "commit", "-m", "branch: clash")
        import subprocess as sp

        sp.run(
            ["git", "-C", str(repo), "rebase", "main"], capture_output=True, check=False
        )
        stopped = snapshot(repo, remote, lease)
        if not stopped["in_flight"]:
            raise ContractError(
                "a genuine conflicting rebase did not leave an in-flight marker; the "
                "detector is looking in the wrong place"
            )
        if not any(
            v["rule"] == "OPERATION_IN_FLIGHT"
            for v in compare(base, stopped, lease)["violations"]
        ):
            raise ContractError("a stopped rebase did not trip OPERATION_IN_FLIGHT")
        sp.run(
            ["git", "-C", str(repo), "rebase", "--abort"],
            capture_output=True,
            check=False,
        )
        checks += 1

        # 8. The rollback subject drifts. Not by the branch moving forward --
        #    that is what a sync does and the rollback is still available -- but
        #    by a reset that puts the recorded commit out of reach, which is what
        #    a force-push does and after which the rollback restores something
        #    nobody chose.
        run(repo, "checkout", rollback["branch"])
        run(repo, "reset", "--hard", base["local_refs"]["refs/heads/main"])
        try:
            require_rollback_intact(rollback, repo, remote, lease)
        except ContractError as exc:
            if "restores something nobody chose" not in str(exc):
                raise ContractError(
                    f"rollback drift was refused by another rule: {exc}"
                ) from exc
        else:
            raise ContractError("a moved rollback branch was accepted as intact")
        checks += 1

        # 9. Back to the start. A checker that stays red after everything is
        #    reverted is broken, not observant.
        run(repo, "checkout", "main")
        for branch in ("clashing",):
            run(repo, "branch", "-D", branch)
        run(repo, "reset", "--hard", base["local_refs"]["refs/heads/main"])
        run(repo, "checkout", fx["stack"][-1])
        run(
            repo, "reset", "--hard", base["local_refs"][f"refs/heads/{fx['stack'][-1]}"]
        )
        run(repo, "clean", "-fd")
        run(repo, "push", "--force", "origin", f"HEAD:{fx['stack'][-1]}")
        # The second clone moved the remote's main; put it back too, or the
        # restore is only partial and the final comparison would be red for a
        # reason that has nothing to do with the checker.
        run(
            repo,
            "push",
            "--force",
            "origin",
            f"{base['local_refs']['refs/heads/main']}:main",
        )
        restored = snapshot(repo, remote, lease)
        result = compare(base, restored, lease)
        if not result["held"]:
            raise ContractError(
                f"the repository was restored and the checker is still red: "
                f"{result['violations']}"
            )
        require_rollback_intact(rollback, repo, remote, lease)
        checks += 1

    # 10. The admission on this machine, which is absence.
    found = probe()
    if found["state"] != "EXECUTABLE_ABSENT":
        raise ContractError(
            f"git-town reports {found['state']} on this machine; the receipts in this "
            "module say EXECUTABLE_ABSENT and would now be describing a different world"
        )
    if modes_for("EXECUTABLE_ABSENT"):
        raise ContractError("an absent executable unlocked a mode")
    checks += 1

    # 11. No mode is reachable under absence, and the refusal names why.
    result = admit(found, ADMISSION, PROFILE, live_local_reviewed=True)
    if result["state"] != "EXECUTABLE_ABSENT":
        raise ContractError(
            f"a human review promoted an absent executable to {result['state']}"
        )
    try:
        require_mode_allowed(result, "sync_local_no_push")
    except ContractError as exc:
        if "has not admitted" not in str(exc):
            raise ContractError(f"the mode refusal named another rule: {exc}") from exc
    else:
        raise ContractError("a sync mode was available with no executable present")
    checks += 1

    print(
        f"git-town runtime physical control PASS: {checks} controls on real repositories "
        f"with a real bare remote (executable {found['state']})"
    )
    return OK


ADMISSION = {
    "tool": "git-town",
    "version": "21.1.0",
    "sha256": "sha256:" + "0" * 64,
    "provenance": "https://github.com/git-town/git-town/releases/tag/v21.1.0",
    "license": "MIT",
    "sbom_ref": "data/git-town/sbom-21.1.0.json",
}

PROFILE = {
    "main_branch": "main",
    "perennial_branches": [],
    "push_hook": False,
    "sync_strategy": "rebase",
    "ship_strategy": "api",
}


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"git-town runtime physical control RED: {exc}", file=sys.stderr)
        raise SystemExit(BAD) from exc
