#!/usr/bin/env python3
"""Positive properties, and one planted control per failure named in #98.

Every control asserts on the substring its own rule raises. A control that only
checks "something was refused" passes when a neighbouring guard fires first, and
stays green while the rule it was written for is deleted.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable

from cp_common import GITHUB_ONLY, STATES, ContractError, find_secrets
from cp_index import action_identity, build_index, inventory, triggers
from cp_parity import (
    compare,
    local_result,
    normalize_conclusion,
    publication_decision,
    remote_result,
)
from cp_policy import billing_decision, materialize_payload, require_decided
from cp_simulator import absent, admit, require_separate_lanes

HEAD = "a" * 40
OLDER = "b" * 40

LOCAL = {
    "workflow": "modular-contracts.yml",
    "commit": HEAD,
    "jobs": {"contracts": "PASS"},
    "runner": "local-native",
}

REMOTE = {
    "workflow": "modular-contracts.yml",
    "commit": HEAD,
    "jobs": {"contracts": "success"},
    "run_id": 31836185958,
    "runner": "ubuntu-latest",
}

TRIGGERS = {
    "events": ["pull_request", "push", "workflow_dispatch"],
    "pull_request_types": ["ready_for_review"],
}

PAYLOAD = {
    "event": "pull_request",
    "action": "ready_for_review",
    "ref": "refs/pull/129/head",
    "head_sha": HEAD,
    "draft": False,
}

ADMISSION = {
    "tool": "nektos/act",
    "version": "0.2.82",
    "image": "catthehacker/ubuntu:act-latest",
    "image_digest": "sha256:" + "c" * 64,
    "license": "MIT",
}


def _local(**overrides: Any) -> dict[str, Any]:
    value = copy.deepcopy(LOCAL)
    value.update(copy.deepcopy(overrides))
    return value


def _remote(**overrides: Any) -> dict[str, Any]:
    value = copy.deepcopy(REMOTE)
    value.update(copy.deepcopy(overrides))
    return value


def control(label: str, expect: str, action: Callable[[], Any]) -> None:
    try:
        action()
    except ContractError as exc:
        if expect not in str(exc):
            raise ContractError(
                f"control {label!r} was refused, but by a different rule: {exc}. A "
                "control that only checks 'something was refused' passes when a "
                "neighbouring guard fires and stays green while its own rule is deleted"
            ) from exc
        return
    raise ContractError(f"control {label!r} was not refused")


def positive_properties(root: Path) -> int:
    checks = 0
    local = local_result(LOCAL)
    remote = remote_result(REMOTE)

    # Both sides, same head, full coverage.
    receipt = compare(local, remote, HEAD, ["contracts"])
    if receipt["verdict"] != "PARITY":
        raise ContractError(f"a full agreeing comparison produced {receipt['verdict']}")
    checks += 1

    # The claim that must never round up, on every receipt.
    if receipt["local_proxies_remote"] or local["proxies_remote"]:
        raise ContractError("a local result was recorded as proxying the remote")
    checks += 1

    if list(receipt["github_only_surfaces"]) != list(GITHUB_ONLY):
        raise ContractError("the GitHub-only surface list drifted out of a receipt")
    checks += 1

    # No remote at all: the ordinary case before publication.
    absent_remote = compare(local, None, HEAD, ["contracts"])
    if absent_remote["verdict"] != "NOT_EXERCISED":
        raise ContractError(
            f"a local-only comparison produced {absent_remote['verdict']}; a local "
            "green with nothing to compare against is not a verified head"
        )
    checks += 1

    # A remote run at an older commit is not evidence about this head.
    stale = compare(local, remote_result(_remote(commit=OLDER)), HEAD, ["contracts"])
    if stale["verdict"] != "NOT_EXERCISED":
        raise ContractError(f"an older GitHub run produced {stale['verdict']}")
    checks += 1

    # Real disagreement.
    diverged = compare(
        local_result(_local(jobs={"contracts": "PASS"})),
        remote_result(_remote(jobs={"contracts": "failure"})),
        HEAD,
        ["contracts"],
    )
    if diverged["verdict"] != "DIVERGED":
        raise ContractError(
            f"a local PASS against a remote failure produced {diverged['verdict']}"
        )
    checks += 1

    # A job that ran remotely with no local equivalent leaves the verdict PARTIAL.
    partial = compare(
        local_result(_local(jobs={"contracts": "PASS"})),
        remote_result(_remote(jobs={"contracts": "success", "audit": "success"})),
        HEAD,
        ["contracts"],
    )
    if partial["verdict"] != "PARTIAL":
        raise ContractError(f"an uncompared remote job produced {partial['verdict']}")
    if not any("not compared" in finding for finding in partial["findings"]):
        raise ContractError("a PARTIAL verdict did not say what went uncompared")
    checks += 1

    # Every non-pass conclusion keeps its own name.
    for conclusion, expected in (
        ("skipped", "SKIPPED"),
        ("cancelled", "CANCELLED"),
        ("action_required", "ACTION_REQUIRED"),
        ("neutral", "NEUTRAL"),
        ("timed_out", "FAIL"),
    ):
        if normalize_conclusion(conclusion, "probe") != expected:
            raise ContractError(
                f"{conclusion} normalized to something other than {expected}"
            )
    checks += 1

    # A skipped job is not agreement, even against a local PASS.
    skipped = compare(
        local,
        remote_result(_remote(jobs={"contracts": "skipped"})),
        HEAD,
        ["contracts"],
    )
    if skipped["verdict"] != "DIVERGED":
        raise ContractError(
            f"a skipped remote job against a local PASS produced {skipped['verdict']}"
        )
    checks += 1

    # Cancellation is the one that hides: concurrency can remove the only run.
    cancelled = compare(
        local,
        remote_result(_remote(jobs={"contracts": "cancelled"})),
        HEAD,
        ["contracts"],
    )
    if cancelled["verdict"] != "DIVERGED":
        raise ContractError("a cancelled remote run was read as agreement")
    checks += 1

    decision = publication_decision(receipt)
    if (
        not decision["may_claim_remote_verified"]
        or decision["owner"] != "HUMAN_OR_TRUSTED_OPERATOR"
    ):
        raise ContractError("the publication decision drifted")
    if publication_decision(absent_remote)["may_claim_remote_verified"]:
        raise ContractError("a NOT_EXERCISED verdict permitted a remote-verified claim")
    checks += 1

    # The simulator is absent by default, and absent admits nothing.
    if absent()["results_admissible"]:
        raise ContractError("an absent simulator admitted results")
    pinned = admit(ADMISSION)
    if pinned["equivalent_to_hosted_runner"] or pinned["lane"] != "SIMULATOR":
        raise ContractError("a pinned simulator claimed hosted-runner equivalence")
    require_separate_lanes({"lane": "NATIVE"}, pinned)
    checks += 1

    materialized = materialize_payload(PAYLOAD, TRIGGERS)
    if not materialized["would_fire"]:
        raise ContractError("a valid payload was not materialized")
    checks += 1

    # Billing arithmetic, against the real unit.
    cost = billing_decision(
        {"a": 7.0, "b": 9.0, "c": 12.0, "d": 6.0},
        grouped=False,
        reason="fault localisation per gate family",
    )
    if cost["split_billed_minutes"] != 4 or cost["merged_billed_minutes"] != 1:
        raise ContractError(f"billing arithmetic drifted: {cost}")
    if cost["overhead_minutes"] != 3 or len(cost["sub_minute_jobs"]) != 4:
        raise ContractError("the sub-minute overhead was not reported")
    require_decided(cost)
    checks += 1

    # The real workflow surface in this repository.
    surface = inventory(root / ".github/workflows/modular-contracts.yml")
    if surface["unpinned_actions"]:
        raise ContractError(
            f"the required workflow has unpinned actions: {surface['unpinned_actions']}"
        )
    if "ubuntu-latest" not in surface["unpinnable_runners"]:
        raise ContractError("a mutable runner label was not recorded as unpinnable")
    if surface["triggers"]["pull_request_types"] != ["ready_for_review"]:
        raise ContractError(
            f"the required workflow's pull_request types read as "
            f"{surface['triggers']['pull_request_types']}"
        )
    checks += 1

    if not surface["declares_permissions"] or not surface["declares_concurrency"]:
        raise ContractError(
            "the required workflow's permissions or concurrency went unread"
        )
    checks += 1

    if action_identity("actions/checkout@v4")["pinned"]:
        raise ContractError("a tag reference was recorded as pinned")
    if not action_identity("actions/checkout@" + "1" * 40)["pinned"]:
        raise ContractError("a full-SHA reference was not recorded as pinned")
    checks += 1

    if triggers("on:\n  push:\n    branches: [main]\n")["events"] != ["push"]:
        raise ContractError("trigger extraction drifted")
    checks += 1

    if not find_secrets("token: ghp_" + "a" * 32):
        raise ContractError("a credential shape passed the receipt scanner")
    if find_secrets("the run_id is 31836185958 and the head is " + HEAD):
        raise ContractError("ordinary receipt content was flagged as a credential")
    checks += 1

    if STATES[-1] != "PUBLICATION_POLICY_DECISION" or len(STATES) != 9:
        raise ContractError("the state sequence drifted")
    checks += 1

    return checks


def controls(root: Path) -> int:
    local = local_result(LOCAL)
    cases: list[tuple[str, str, Callable[[], Any]]] = [
        (
            "local PASS proxying remote PASS",
            "says nothing about the hosted runner",
            lambda: _require_parity(compare(local, None, HEAD, ["contracts"])),
        ),
        (
            "old GitHub SHA proxying current head",
            "fact about older code",
            lambda: _require_parity(
                compare(
                    local, remote_result(_remote(commit=OLDER)), HEAD, ["contracts"]
                )
            ),
        ),
        (
            "a local result at the wrong commit",
            "two different programs",
            lambda: compare(
                local_result(_local(commit=OLDER)),
                remote_result(REMOTE),
                HEAD,
                ["contracts"],
            ),
        ),
        (
            "skipped represented as PASS",
            "not a pass",
            lambda: normalize_conclusion("success_but_skipped", "probe"),
        ),
        (
            "a GitHub state this gate does not know",
            "An unknown conclusion is not a pass",
            lambda: remote_result(_remote(jobs={"contracts": "queued"})),
        ),
        (
            "a local run borrowing a remote-only state",
            "no local counterpart",
            lambda: local_result(_local(jobs={"contracts": "SKIPPED"})),
        ),
        (
            "a short SHA as the head",
            "must be a full 40-character commit SHA",
            lambda: compare(local, remote_result(REMOTE), "abc1234", ["contracts"]),
        ),
        (
            "a remote result with no run id",
            "fields drifted",
            lambda: remote_result({k: v for k, v in REMOTE.items() if k != "run_id"}),
        ),
        (
            "event payload the workflow could not fire on",
            "could not have happened",
            lambda: materialize_payload({**PAYLOAD, "event": "schedule"}, TRIGGERS),
        ),
        (
            "pull_request type the workflow does not declare",
            "draft-first a requirement rather than a preference",
            lambda: materialize_payload({**PAYLOAD, "action": "synchronize"}, TRIGGERS),
        ),
        (
            "a draft payload claiming the ready transition",
            "draft -> ready transition",
            lambda: materialize_payload({**PAYLOAD, "draft": True}, TRIGGERS),
        ),
        (
            "a mutable action tag",
            "moved onto different code",
            # Written to a temporary tree rather than tracked. A fixture workflow
            # in .github/workflows is a workflow: GitHub would read it, and an
            # unpinned action would be a real one.
            lambda: build_index(*_unpinned_fixture()),
        ),
        (
            "a simulator admitted without an image digest",
            "names a tool, not a thing that ran",
            lambda: admit({k: v for k, v in ADMISSION.items() if k != "image_digest"}),
        ),
        (
            "a simulator pinned to a mutable image tag",
            "repushed onto different contents",
            lambda: admit({**ADMISSION, "image_digest": "act-latest"}),
        ),
        (
            "simulator results folded into the native lane",
            "two different claims",
            lambda: require_separate_lanes(
                {"lane": "NATIVE"}, {**admit(ADMISSION), "lane": "NATIVE"}
            ),
        ),
        (
            "a simulator claiming hosted-runner equivalence",
            "not whether the hosted run would pass",
            lambda: require_separate_lanes(
                {"lane": "NATIVE"},
                {**admit(ADMISSION), "equivalent_to_hosted_runner": True},
            ),
        ),
        (
            "sub-minute jobs split with no recorded decision",
            "not having answered is not",
            lambda: require_decided(
                billing_decision(
                    {"a": 5.0, "b": 6.0, "c": 7.0, "d": 8.0}, grouped=False, reason=" "
                )
            ),
        ),
        (
            "a credential in a tracked receipt",
            "read by every later session",
            lambda: compare(
                local_result(_local(runner="local-native token=ghp_" + "a" * 32)),
                remote_result(REMOTE),
                HEAD,
                ["contracts"],
            ),
        ),
        (
            "local coverage claiming a job the workflow does not declare",
            "which the workflow does not declare",
            lambda: build_index(
                root,
                [
                    {
                        "workflow": ".github/workflows/modular-contracts.yml",
                        "local_covers": ["nope"],
                    }
                ],
            ),
        ),
        (
            "local coverage claiming a GitHub-only surface",
            "local coverage claims",
            lambda: build_index(
                root,
                [
                    {
                        "workflow": ".github/workflows/modular-contracts.yml",
                        "local_covers": ["BILLING"],
                    }
                ],
            ),
        ),
        (
            "an index entry for a workflow that is not there",
            "cannot detect by reading itself",
            lambda: build_index(
                root, [{"workflow": ".github/workflows/absent.yml", "local_covers": []}]
            ),
        ),
    ]
    for label, expect, action in cases:
        control(label, expect, action)
    return len(cases)


UNPINNED_WORKFLOW = """name: Probe
on:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  probe:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo probe
"""


def _unpinned_fixture() -> tuple[Path, list[dict[str, Any]]]:
    """A throwaway tree carrying one workflow with a tag reference."""
    import tempfile

    tmp = Path(tempfile.mkdtemp(prefix="cp-unpinned-"))
    (tmp / ".github/workflows").mkdir(parents=True)
    (tmp / ".github/workflows/probe.yml").write_text(
        UNPINNED_WORKFLOW, encoding="utf-8"
    )
    return tmp, [{"workflow": ".github/workflows/probe.yml", "local_covers": ["probe"]}]


def _require_parity(receipt: dict[str, Any]) -> None:
    """Force the verdict to be read as a parity claim, so the refusal is visible."""
    if receipt["verdict"] != "PARITY":
        raise ContractError(
            f"the verdict is {receipt['verdict']}, not PARITY: "
            + "; ".join(receipt["findings"])
        )


def run_selftest(root: Path) -> tuple[int, int]:
    return positive_properties(root), controls(root)
