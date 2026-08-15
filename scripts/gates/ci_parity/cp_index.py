#!/usr/bin/env python3
"""Inventory the workflow surface, and refuse to report a short list.

This reads the line-anchored facts it needs -- `uses:`, `runs-on:`, `jobs:`,
`permissions:`, `concurrency:`, the `on:` trigger types -- rather than parsing
YAML. That is deliberate: PyYAML is not in the standard library and is not
guaranteed on a `setup-python` runner, and a gate that cannot run in the
environment it guards is worse than one with a narrower reader.

The narrower reader has one failure mode that matters. An inventory fails in one
direction: a step it did not attribute is a step nobody ever hears about, and a
short list and a complete list look exactly the same. So `inventory` counts every
`uses:` and `runs-on:` line in the file independently of how it attributed them,
and refuses the whole file as NOT_INVENTORIED if the two counts disagree. It
never returns what it managed to understand.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cp_common import (
    ACTION_REF,
    FULL_SHA,
    GITHUB_ONLY,
    MUTABLE_RUNNERS,
    ContractError,
    InputError,
    digest,
)

USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(?P<ref>\S+)")
RUNS_ON = re.compile(r"^\s*runs-on:\s*(?P<label>\S+)")
JOB = re.compile(r"^  (?P<name>[A-Za-z0-9_-]+):\s*$")
TOP_KEY = re.compile(r"^(?P<name>[a-z_-]+):")


def read_workflow(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"cannot read workflow {path}: {exc}") from exc


def action_identity(ref: str) -> dict[str, Any]:
    """Pin an action reference, or say plainly that it is unpinnable."""
    match = ACTION_REF.match(ref)
    if match is None:
        # A local or docker action. It has an identity, but not this kind.
        return {"ref": ref, "name": ref, "pinned": False, "kind": "LOCAL_OR_DOCKER"}
    name, rev = match.group("name"), match.group("ref")
    pinned = FULL_SHA.fullmatch(rev) is not None
    return {
        "ref": ref,
        "name": name,
        "rev": rev,
        "pinned": pinned,
        "kind": "REMOTE_ACTION",
    }


def inventory(path: Path) -> dict[str, Any]:
    """Every job, step action and runner in one workflow file.

    Refuses rather than under-reports; see the module docstring.
    """
    text = read_workflow(path)
    lines = text.splitlines()

    jobs: dict[str, dict[str, Any]] = {}
    current: str | None = None
    in_jobs = False
    attributed_uses = 0
    attributed_runners = 0

    for line in lines:
        top = TOP_KEY.match(line)
        if top:
            in_jobs = top.group("name") == "jobs"
            current = None
            continue
        if not in_jobs:
            continue
        job = JOB.match(line)
        if job:
            current = job.group("name")
            jobs[current] = {"name": current, "actions": [], "runners": []}
            continue
        if current is None:
            continue
        uses = USES.match(line)
        if uses:
            jobs[current]["actions"].append(action_identity(uses.group("ref")))
            attributed_uses += 1
            continue
        runs = RUNS_ON.match(line)
        if runs:
            jobs[current]["runners"].append(runs.group("label"))
            attributed_runners += 1

    # The completeness check. Counted over the raw file, independently of the
    # attribution above, so a step the block reader missed cannot vanish.
    total_uses = sum(1 for line in lines if USES.match(line))
    total_runners = sum(1 for line in lines if RUNS_ON.match(line))
    if attributed_uses != total_uses or attributed_runners != total_runners:
        raise ContractError(
            f"{path.name} is NOT_INVENTORIED: attributed {attributed_uses}/{total_uses} "
            f"actions and {attributed_runners}/{total_runners} runners. An inventory "
            "that returns what it understood is indistinguishable from a complete one, "
            "so this reports nothing rather than a short list"
        )
    if not jobs:
        raise ContractError(f"{path.name} declares no jobs")

    unpinned = [
        action["ref"]
        for job in jobs.values()
        for action in job["actions"]
        if action["kind"] == "REMOTE_ACTION" and not action["pinned"]
    ]
    mutable = sorted(
        {
            label
            for job in jobs.values()
            for label in job["runners"]
            if label in MUTABLE_RUNNERS
        }
    )

    return {
        "workflow": path.name,
        "jobs": {name: job for name, job in sorted(jobs.items())},
        "job_count": len(jobs),
        "action_count": total_uses,
        "unpinned_actions": sorted(unpinned),
        # Recorded, not refused. The image behind `ubuntu-latest` moves, and that
        # is what GitHub provides -- so a parity claim about runner behaviour is
        # bounded by it rather than pretending the runner was pinned.
        "unpinnable_runners": mutable,
        "triggers": triggers(text),
        "declares_permissions": bool(re.search(r"^permissions:", text, re.MULTILINE)),
        "declares_concurrency": bool(re.search(r"^concurrency:", text, re.MULTILINE)),
        "surface_digest": digest(
            {
                "jobs": {
                    name: {
                        "actions": [a["ref"] for a in job["actions"]],
                        "runners": job["runners"],
                    }
                    for name, job in sorted(jobs.items())
                }
            }
        ),
    }


def triggers(text: str) -> dict[str, Any]:
    """The events that can bill a run, and the pull_request types among them."""
    events = sorted(
        set(
            re.findall(r"^  (pull_request|push|workflow_dispatch):", text, re.MULTILINE)
        )
    )
    if (
        re.search(r"^  workflow_dispatch:\s*$", text, re.MULTILINE) is None
        and "workflow_dispatch" in text
    ):
        events = sorted(set(events + ["workflow_dispatch"]))
    types_match = re.search(r"types:\s*\[([^\]]*)\]", text)
    types = (
        sorted(part.strip() for part in types_match.group(1).split(",") if part.strip())
        if types_match
        else []
    )
    return {"events": events, "pull_request_types": types}


def require_pinned(surface: dict[str, Any]) -> None:
    if surface["unpinned_actions"]:
        raise ContractError(
            f"{surface['workflow']} uses unpinned actions {surface['unpinned_actions']}. "
            "A tag can be moved onto different code without the reference changing, so "
            "the receipt would name an identity that no longer selects what ran"
        )


def build_index(root: Path, declared: list[dict[str, Any]]) -> dict[str, Any]:
    """Index the declared required workflows against their local equivalents."""
    entries = []
    for entry in declared:
        path = root / entry["workflow"]
        if not path.exists():
            raise ContractError(
                f"the index declares {entry['workflow']}, which is not in the tree. A "
                "declared-but-absent workflow is the one state an index cannot detect "
                "by reading itself"
            )
        surface = inventory(path)
        require_pinned(surface)
        covered = set(entry["local_covers"])
        # Checked first, and deliberately. A GitHub-only surface is never a job
        # name, so the unknown-job check below would catch it too -- with a
        # message saying the workflow does not declare that job, which is true
        # and useless. Nothing local can be evidence about billing or token
        # permissions, and that is the sentence worth printing.
        overreach = covered & set(GITHUB_ONLY)
        if overreach:
            raise ContractError(
                f"{entry['workflow']}: local coverage claims {sorted(overreach)}, which "
                "no local run can observe"
            )
        unknown = covered - set(surface["jobs"])
        if unknown:
            raise ContractError(
                f"{entry['workflow']}: the local equivalent claims to cover jobs "
                f"{sorted(unknown)}, which the workflow does not declare"
            )
        entries.append(
            {
                **entry,
                "surface": surface,
                "uncovered_jobs": sorted(set(surface["jobs"]) - covered),
            }
        )

    # Every workflow in the tree, so a required one that was never declared shows
    # up as a hole rather than as silence.
    present = sorted(p.name for p in (root / ".github/workflows").glob("*.yml"))
    declared_names = {Path(entry["workflow"]).name for entry in declared}
    return {
        "entries": entries,
        "workflows_in_tree": len(present),
        "declared": sorted(declared_names),
        "undeclared": sorted(set(present) - declared_names),
        "index_digest": digest(
            [entry["surface"]["surface_digest"] for entry in entries]
        ),
    }
