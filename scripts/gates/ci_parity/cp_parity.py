#!/usr/bin/env python3
"""The comparison, and the four things it is allowed to conclude.

`PARITY` is a claim about two observations. The function that produces it takes
both sides and has no default: there is no code path where a local result alone
becomes PARITY, because that is the failure the whole module is built against --
a green local run standing in for a run that was never billed.

The exact-head rule is the same shape. A remote run at an older SHA is a fact
about older code; comparing it against a local run at the current head is
comparing two different programs and reporting agreement.

`PARTIAL` is not a weak `PARITY`. It means some surface was compared and agreed
and some was never compared at all, and the reason it is a separate word is that
"mostly verified" and "verified" get written the same way in a summary.
"""

from __future__ import annotations

from typing import Any

from cp_common import (
    CONCLUSIONS,
    GITHUB_ONLY,
    NOT_EVIDENCE,
    ContractError,
    digest,
    full_sha,
    non_empty_str,
    require_clean_receipt,
)

LOCAL_KEYS = {"workflow", "commit", "jobs", "runner"}
REMOTE_KEYS = {"workflow", "commit", "jobs", "run_id", "runner"}


def normalize_conclusion(value: Any, label: str) -> str:
    """Map a GitHub conclusion onto the vocabulary, refusing unknown ones.

    An unknown conclusion is refused rather than defaulted. Defaulting it to
    something safe-sounding is how a new GitHub state gets read as a pass for
    however long it takes anyone to notice.
    """
    if value not in CONCLUSIONS:
        raise ContractError(
            f"{label} reports conclusion {value!r}, which this gate does not know. "
            f"Known: {sorted(CONCLUSIONS)}. An unknown conclusion is not a pass"
        )
    return CONCLUSIONS[value]


def local_result(value: Any) -> dict[str, Any]:
    """A local run. Note what it does not have: a run_id, because nothing billed."""
    if not isinstance(value, dict) or set(value) != LOCAL_KEYS:
        raise ContractError(
            f"local result fields drifted; expected {sorted(LOCAL_KEYS)}"
        )
    non_empty_str(value["workflow"], "local.workflow")
    full_sha(value["commit"], "local.commit")
    jobs = value["jobs"]
    if not isinstance(jobs, dict) or not jobs:
        raise ContractError("local.jobs must be a non-empty object")
    for name, outcome in jobs.items():
        if outcome not in ("PASS", "FAIL"):
            raise ContractError(
                f"local job {name!r} reported {outcome!r}. A local run either ran the "
                "command or did not; GitHub's skipped, cancelled and action_required "
                "have no local counterpart, and borrowing them here would let a local "
                "state answer a question only the remote can answer"
            )
    return {
        **value,
        "side": "LOCAL",
        "billed": False,
        # Stated on the record rather than left to the reader. This is the claim
        # every summary wants to round up.
        "proxies_remote": False,
        "result_digest": digest(value),
    }


def remote_result(value: Any) -> dict[str, Any]:
    """An actual GitHub run at an actual commit."""
    if not isinstance(value, dict) or set(value) != REMOTE_KEYS:
        raise ContractError(
            f"remote result fields drifted; expected {sorted(REMOTE_KEYS)}"
        )
    non_empty_str(value["workflow"], "remote.workflow")
    full_sha(value["commit"], "remote.commit")
    non_empty_str(str(value["run_id"]), "remote.run_id")
    jobs = value["jobs"]
    if not isinstance(jobs, dict) or not jobs:
        raise ContractError("remote.jobs must be a non-empty object")
    normalized = {
        name: normalize_conclusion(outcome, f"remote job {name!r}")
        for name, outcome in jobs.items()
    }
    return {
        **value,
        "jobs": normalized,
        "side": "REMOTE",
        "billed": True,
        "result_digest": digest(value),
    }


def compare(
    local: dict[str, Any],
    remote: dict[str, Any] | None,
    head: str,
    covered_jobs: list[str],
) -> dict[str, Any]:
    """Compare one workflow's two sides at one head.

    `remote=None` is the ordinary case before publication, and it is the case
    this function exists to answer honestly.
    """
    full_sha(head, "head")
    findings: list[str] = []

    if local["commit"] != head:
        raise ContractError(
            f"the local result is at {local['commit'][:12]} but the head is "
            f"{head[:12]}. Comparing them would report agreement between two "
            "different programs"
        )

    if remote is None:
        return verdict(
            "NOT_EXERCISED",
            head,
            local,
            None,
            covered_jobs,
            [
                "no GitHub run at this head has been ingested. The local run says the "
                "commands succeed on this machine; it says nothing about the hosted "
                "runner, and it did not bill anything"
            ],
        )

    if remote["commit"] != head:
        return verdict(
            "NOT_EXERCISED",
            head,
            local,
            remote,
            covered_jobs,
            [
                f"the GitHub run is at {remote['commit'][:12]}, not the head "
                f"{head[:12]}. An older run is a fact about older code, and reusing it "
                "here is the cheapest way to claim the current head was verified"
            ],
        )

    # Only jobs the local equivalent actually claims to cover can be compared.
    # Everything else is uncompared, and uncompared is not agreement.
    compared: dict[str, Any] = {}
    for name in sorted(covered_jobs):
        left = local["jobs"].get(name)
        right = remote["jobs"].get(name)
        if left is None or right is None:
            findings.append(
                f"job {name!r} is claimed as locally covered but is missing from the "
                f"{'local' if left is None else 'remote'} result"
            )
            continue
        if right in NOT_EVIDENCE:
            findings.append(
                f"job {name!r} concluded {right} on GitHub. That is not a failure and "
                "not a pass -- it is the absence of a result, and a cancelled run is "
                "the one that hides hardest because concurrency can remove the only "
                "run at this head"
            )
            compared[name] = {"local": left, "remote": right, "agrees": False}
            continue
        compared[name] = {"local": left, "remote": right, "agrees": left == right}
        if left != right:
            findings.append(f"job {name!r}: local {left}, GitHub {right}")

    uncovered = sorted(set(remote["jobs"]) - set(covered_jobs))
    if uncovered:
        findings.append(
            f"jobs {uncovered} ran on GitHub with no local equivalent; they were not "
            "compared"
        )

    if not compared:
        state = "NOT_EXERCISED"
    elif any(not entry["agrees"] for entry in compared.values()):
        state = "DIVERGED"
    elif uncovered or len(compared) < len(remote["jobs"]):
        state = "PARTIAL"
    else:
        state = "PARITY"

    return verdict(state, head, local, remote, covered_jobs, findings, compared)


def verdict(
    state: str,
    head: str,
    local: dict[str, Any],
    remote: dict[str, Any] | None,
    covered_jobs: list[str],
    findings: list[str],
    compared: dict[str, Any] | None = None,
) -> dict[str, Any]:
    receipt = {
        "schema_version": "loopx/ci-parity-receipt/v1",
        "verdict": state,
        "head": head,
        "local": local,
        "remote": remote,
        "compared_jobs": compared or {},
        "covered_jobs": sorted(covered_jobs),
        # Never compared, by construction rather than by omission. Writing the
        # list into every receipt is what stops "the workflow passed" from being
        # read as a statement about permissions or billing.
        "github_only_surfaces": list(GITHUB_ONLY),
        "findings": findings,
        "local_proxies_remote": False,
        "receipt_digest": digest(
            {"state": state, "head": head, "compared": compared or {}}
        ),
    }
    require_clean_receipt(receipt, "the parity receipt")
    return receipt


def publication_decision(receipt: dict[str, Any]) -> dict[str, Any]:
    """What the verdict permits. Never the merge itself.

    A PARITY verdict says two observations agreed. It does not say the change is
    good, and it does not authorise publication, merge, rerun or billing
    recovery -- those stay with a human, and a gate that returned "may merge"
    would be writing a verdict it has no standing to write.
    """
    state = receipt["verdict"]
    return {
        "verdict": state,
        "may_claim_remote_verified": state == "PARITY",
        "must_publish_to_learn_more": state in ("NOT_EXERCISED", "PARTIAL"),
        "blocks_publication": False,
        "owner": "HUMAN_OR_TRUSTED_OPERATOR",
        "reason": (
            "publication, workflow rerun, merge and billing recovery are Human-owned. "
            "This gate reports what was compared and what was not"
        ),
    }
