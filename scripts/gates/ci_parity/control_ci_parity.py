#!/usr/bin/env python3
"""Physical control group: a real local command, a real exit code, real drift.

Everything in the selftest compares dictionaries the same process built. That
proves the comparison and nothing about the thing being compared -- a local
result is supposed to come from a command that actually ran, and the failure this
gate exists for is a local green that was never a real green.

So this group writes a real script to disk, runs it as a subprocess, and builds
the local result from its **actual exit code**. Then it edits the script so the
command genuinely fails and checks the verdict moves PARITY -> DIVERGED -- and
puts it back and checks it returns to PARITY, so the DIVERGED is attributable to
the planted drift rather than to the runner being broken.

It also inventories every workflow file in the real repository, because the
completeness check in cp_index is worth nothing against fixtures written to
satisfy it.

Exits 0 or 2.
"""

from __future__ import annotations

import stat
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cp_common import BAD, OK, ContractError  # noqa: E402
from cp_index import inventory  # noqa: E402
from cp_parity import compare, local_result, remote_result  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
HEAD = "d" * 40

GREEN = "#!/bin/sh\nexit 0\n"
RED = "#!/bin/sh\necho 'the gate disagreed' >&2\nexit 2\n"

REMOTE = {
    "workflow": "probe.yml",
    "commit": HEAD,
    "jobs": {"probe": "success"},
    "run_id": 1,
    "runner": "ubuntu-latest",
}


def run_local(script: Path) -> str:
    """Run the real script and report what it actually did."""
    done = subprocess.run([str(script)], capture_output=True, text=True, check=False)
    if done.returncode not in (0, 2):
        raise ContractError(
            f"the local command exited {done.returncode}, which is neither ok nor a "
            f"checked disagreement: {done.stderr.strip()}"
        )
    return "PASS" if done.returncode == 0 else "FAIL"


def verdict_for(script: Path) -> str:
    outcome = run_local(script)
    local = local_result(
        {
            "workflow": "probe.yml",
            "commit": HEAD,
            "jobs": {"probe": outcome},
            "runner": "local-native",
        }
    )
    return compare(local, remote_result(REMOTE), HEAD, ["probe"])["verdict"]


def main() -> int:
    checks = 0

    with tempfile.TemporaryDirectory(prefix="cp-control-") as tmp:
        script = Path(tmp) / "local_gate.sh"
        script.write_text(GREEN, encoding="utf-8")
        script.chmod(script.stat().st_mode | stat.S_IXUSR)

        # 1. A real green command against a real recorded green run.
        if verdict_for(script) != "PARITY":
            raise ContractError(
                "a genuinely green local command did not produce PARITY"
            )
        checks += 1

        # 2. Plant the drift. The remote receipt is untouched: only the local
        #    side changed, which is exactly the shape of a local/remote drift.
        script.write_text(RED, encoding="utf-8")
        if verdict_for(script) != "DIVERGED":
            raise ContractError(
                "a local command that really failed still compared as agreement; the "
                "local result is not coming from the command's exit code"
            )
        checks += 1

        # 3. Restore. A verdict that stays DIVERGED after the drift is removed is
        #    a broken runner, not a detection.
        script.write_text(GREEN, encoding="utf-8")
        if verdict_for(script) != "PARITY":
            raise ContractError(
                "the verdict stayed DIVERGED after the drift was reverted"
            )
        checks += 1

        # 4. A command that exits with something the contract does not define.
        script.write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
        try:
            run_local(script)
        except ContractError as exc:
            if "neither ok nor a checked disagreement" not in str(exc):
                raise ContractError(
                    f"an undefined exit code was refused by another rule: {exc}"
                ) from exc
        else:
            raise ContractError("an undefined exit code was accepted as a result")
        checks += 1

        # 5. A missing command is unusable input, not a failing gate. Without
        #    this split, deleting the local script reads as the gate passing
        #    nothing rather than as the gate being gone.
        missing = Path(tmp) / "not-there.sh"
        try:
            subprocess.run([str(missing)], capture_output=True, check=False)
        except OSError:
            checks += 1
        else:
            raise ContractError("a missing local command did not raise")

    # 6. Every workflow in the real repository, inventoried for real. The
    #    completeness check is worth nothing against fixtures written to satisfy
    #    it, and these files were written by hand over many commits.
    workflows = sorted((ROOT / ".github/workflows").glob("*.yml"))
    if len(workflows) < 10:
        raise ContractError(
            f"only {len(workflows)} workflow files found; expected the real set"
        )
    unpinned: dict[str, list[str]] = {}
    total_actions = 0
    for path in workflows:
        surface = inventory(path)
        total_actions += surface["action_count"]
        if surface["unpinned_actions"]:
            unpinned[path.name] = surface["unpinned_actions"]
    if unpinned:
        raise ContractError(
            f"workflows in this repository use unpinned actions: {unpinned}. A tag can "
            "be moved onto different code without the reference changing"
        )
    checks += 1

    # 7. The clean result above is only evidence if the detector can produce a
    #    dirty one. Every workflow in the tree is pinned, so a detector that
    #    reported nothing and a detector that saw nothing look identical -- this
    #    writes a real file with a tag reference and requires it to be caught.
    with tempfile.TemporaryDirectory(prefix="cp-dirty-") as tmp:
        dirty = Path(tmp) / "dirty.yml"
        dirty.write_text(
            "name: Dirty\n"
            "on:\n  push:\n    branches: [main]\n"
            "jobs:\n"
            "  probe:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n",
            encoding="utf-8",
        )
        found = inventory(dirty)["unpinned_actions"]
        if found != ["actions/checkout@v4"]:
            raise ContractError(
                f"a workflow with a tag reference reported {found}. The clean result "
                "above says nothing unless the detector can produce a dirty one"
            )
    checks += 1

    # 8. Same argument for the completeness check. Every real workflow here uses
    #    bare job keys, so the check has never had anything to catch -- and a
    #    guard that has never fired is indistinguishable from one that cannot.
    #    A quoted job key is valid YAML and this reader does not understand it;
    #    the correct answer is to refuse the file, not to return the steps it did
    #    manage to attribute.
    with tempfile.TemporaryDirectory(prefix="cp-quoted-") as tmp:
        quoted = Path(tmp) / "quoted.yml"
        quoted.write_text(
            "name: Quoted\n"
            "on:\n  push:\n    branches: [main]\n"
            "jobs:\n"
            '  "build":\n'
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@" + "1" * 40 + "\n",
            encoding="utf-8",
        )
        try:
            inventory(quoted)
        except ContractError as exc:
            if "NOT_INVENTORIED" not in str(exc):
                raise ContractError(
                    f"an unattributable workflow was refused by another rule: {exc}"
                ) from exc
        else:
            raise ContractError(
                "a workflow this reader cannot fully attribute was inventoried anyway. "
                "A short list and a complete list look exactly the same"
            )
    checks += 1

    print(
        f"ci-parity physical control PASS: {checks} controls on a real command and "
        f"{len(workflows)} real workflow files ({total_actions} pinned actions)"
    )
    return OK


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"ci-parity physical control RED: {exc}", file=sys.stderr)
        raise SystemExit(BAD) from exc
