#!/usr/bin/env python3
"""Physical control group. Real processes, real process groups, real workspaces.

Two of #94's failures cannot be answered by a fixture, because both are about
what is still true on the machine after the fleet thinks it is finished:

**Descendants outliving a timeout.** A Worker that spawns a child and is then
killed leaves the child running. The parent's exit status says nothing about it,
and the fleet's own records will say the task ended. So this starts a real
process that starts a real child, kills the parent's process group, and asks the
operating system whether anything in that group is still alive.

**Orphan recovery deleting live work.** The GC's job is to remove workspaces
nobody owns, and its worst failure is removing one somebody does. So this builds
four real directories -- clean, dirty, leased, and unreadable -- and checks the
plan for each, then runs the executor with `apply=True` and looks at the disk.

Five controls:

1. a clean leaseless workspace is proposed for removal, never auto-removed;
2. a dirty workspace is kept, and is still there after apply;
3. a leased workspace is kept, and is still there after apply;
4. an unreadable workspace is kept -- "cannot tell" is not "safe to delete";
5. a killed process group takes its descendants with it, verified by asking the
   OS rather than by trusting the parent's exit code.

Exit: 0 all controls behaved, 2 one did not, 64 unusable environment.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from wf_cleanup import descendants_alive, execute, inventory, plan  # noqa: E402
from wf_common import BAD, OK, USAGE  # noqa: E402

# A parent that starts a child and then waits. If the group kill only reaches the
# parent, the child stays alive and `descendants_alive` will say so.
SPAWNER = """
import subprocess, sys, time
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
print(child.pid, flush=True)
time.sleep(120)
"""


def _workspace(root: Path, name: str, *, dirty: bool = False) -> Path:
    path = root / name
    path.mkdir(parents=True, exist_ok=True)
    (path / ".worker-scaffold").write_text("scaffold\n", encoding="utf-8")
    if dirty:
        (path / ".worker-dirty").write_text("uncommitted\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.parse_args()

    failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="loopx-fleet-control-") as tmp:
        base = Path(tmp)
        workspaces = base / "workspaces"
        workspaces.mkdir()

        _workspace(workspaces, "clean-leaseless")
        _workspace(workspaces, "dirty", dirty=True)
        _workspace(workspaces, "leased")
        unreadable = _workspace(workspaces, "unreadable")

        leases = [
            {
                "lease_id": "lease-live",
                "worker_id": "worker-a",
                "task_id": "task-a",
                "branch": "feat/x",
                "worktree_path": "leased",
                "path_globs": ["loop_wiki/x/**"],
                "granted_at": "2026-08-15T10:00:00Z",
                "expires_at": "2026-08-15T12:00:00Z",
                "heartbeat_interval_s": 300,
                "state": "ACTIVE",
            }
        ]

        # Made genuinely unreadable, so the "cannot tell" branch is reached by
        # the filesystem rather than by a flag the test sets.
        original_mode = unreadable.stat().st_mode
        os.chmod(unreadable, 0o000)
        try:
            entries = inventory(workspaces, leases, "checkouts/owner-live")
        finally:
            os.chmod(unreadable, original_mode)

        by_path = {entry["path"]: entry for entry in entries}
        expected = {
            "clean-leaseless": "PROPOSED_REQUIRES_HUMAN",
            "dirty": "KEEP_DIRTY",
            "leased": "KEEP_ACTIVE_LEASE",
        }
        for name, want in expected.items():
            got = by_path.get(name, {}).get("disposition")
            if got != want:
                failures.append(f"{name} classified {got}, expected {want}")

        # Running as root defeats a 0o000 chmod, and a control that quietly
        # passes because the check could not be performed is worse than one that
        # fails. Reported rather than skipped.
        unreadable_state = by_path.get("unreadable", {}).get("disposition")
        if unreadable_state != "KEEP_UNREADABLE":
            if os.geteuid() == 0:
                print(
                    "fleet control NOTE: running as root, so the unreadable "
                    "workspace was readable and control 4 could not be exercised",
                    file=sys.stderr,
                )
                return USAGE
            failures.append(
                f"an unreadable workspace classified {unreadable_state}, not "
                "KEEP_UNREADABLE; a GC that treats 'cannot tell' as 'safe to delete' "
                "deletes exactly what it cannot see"
            )

        # A default plan removes nothing at all.
        default = plan(entries)
        if default["removable_count"] != 0:
            failures.append(
                f"a default GC plan marked {default['removable_count']} workspace(s) "
                "removable; a scheduled run must propose, not delete"
            )

        # A human admitting the clean one makes exactly that one removable, and
        # admitting a kept one is refused rather than honoured.
        admitted = plan(entries, ["clean-leaseless"])
        if admitted["removable_count"] != 1:
            failures.append(
                f"admitting one workspace made {admitted['removable_count']} removable"
            )
        for name in ("dirty", "leased"):
            try:
                plan(entries, [name])
            except Exception as exc:  # noqa: BLE001
                if "cannot be admitted for removal" not in str(exc):
                    failures.append(
                        f"admitting {name} refused for the wrong reason: {exc}"
                    )
            else:
                failures.append(
                    f"{name} was admitted for removal; admitting past the reason a "
                    "workspace is kept makes the check decorative"
                )

        result = execute(admitted, apply=True)
        if [entry["path"] for entry in result["removed"]] != ["clean-leaseless"]:
            failures.append(f"apply removed {result['removed']}")
        for name in ("dirty", "leased", "unreadable"):
            if not (workspaces / name).exists():
                failures.append(f"{name} was removed despite being kept")
        if (workspaces / "clean-leaseless").exists():
            failures.append(
                "the admitted workspace was reported removed but is on disk"
            )

        # --- control 5: the process group -----------------------------------
        script = base / "spawner.py"
        script.write_text(SPAWNER, encoding="utf-8")
        parent = subprocess.Popen(
            [sys.executable, str(script)],
            stdout=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            child_pid = int(parent.stdout.readline().strip())
        except (ValueError, AttributeError):
            parent.kill()
            print(
                "fleet control FATAL: the spawner did not report a child",
                file=sys.stderr,
            )
            return USAGE

        pgid = os.getpgid(parent.pid)
        if not descendants_alive(pgid):
            failures.append(
                "the process group was reported empty while the Worker was running; "
                "with nothing alive, the kill below would prove nothing"
            )

        os.killpg(pgid, signal.SIGKILL)
        parent.wait(timeout=10)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and descendants_alive(pgid):
            time.sleep(0.05)

        if descendants_alive(pgid):
            failures.append("the process group still has members after the group kill")
        # Asked of the OS about the child specifically, not inferred from the
        # parent's exit status -- which is what a fleet would otherwise record.
        try:
            os.kill(child_pid, 0)
        except ProcessLookupError:
            pass
        except PermissionError:
            failures.append(f"child {child_pid} still exists after the group kill")
        else:
            failures.append(
                f"child {child_pid} outlived the group kill; a timeout that leaves "
                "descendants shows up later as a machine with no free CPU while the "
                "fleet says the task ended"
            )

    if failures:
        for line in failures:
            print(f"fleet control RED: {line}", file=sys.stderr)
        return BAD

    print(
        json.dumps(
            {
                "module": "loopx-worker-fleet",
                "controls": [
                    "clean-leaseless-workspace-is-proposed-not-removed",
                    "dirty-workspace-kept-and-still-on-disk-after-apply",
                    "leased-workspace-kept-and-still-on-disk-after-apply",
                    "unreadable-workspace-kept-because-cannot-tell-is-not-safe",
                    "group-kill-takes-descendants-verified-against-the-os",
                ],
                "state": "PASS",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
