#!/usr/bin/env python3
"""Queries and their results. Every result says which tree it came from.

A diagnostic without provenance is a claim about "the code" -- and there are five
worktrees. So every result carries the server identity, the workspace root, the
commit and tree it was indexed at, and how fresh that index is. `validate_result`
refuses a result whose subject does not match the request, which is the
cross-worktree control expressed as a shape rather than a review habit.

The other half is `answer_for`, which turns what the server did into one of the
five states without ever collapsing them. Its whole job is to keep "no
diagnostics" from meaning three different things.
"""

from __future__ import annotations

from typing import Any

from lsp_common import (
    ContractError,
    exact_object,
    non_empty_str,
    normalise_path,
    parse_time,
    sha256_ref,
    state_bears_evidence,
)
from lsp_pool import validate_server, validate_workspace

REQUEST_KEYS = {"request_id", "kind", "path", "language", "server", "workspace"}

QUERY_KINDS = ("DIAGNOSTICS", "REFERENCES", "DEFINITION", "SYMBOLS")

RESULT_KEYS = {
    "request_id",
    "state",
    "findings",
    "provenance",
    "reason",
}

PROVENANCE_KEYS = {
    "server_id",
    "version",
    "config_digest",
    "workspace_id",
    "repository",
    "root",
    "commit",
    "tree",
    "indexed_at",
    "index_freshness",
}

FRESHNESS = ("CURRENT", "STALE", "NOT_INDEXED")


def validate_request(value: Any, label: str = "request") -> dict[str, Any]:
    request = exact_object(value, REQUEST_KEYS, label)
    non_empty_str(request["request_id"], f"{label}.request_id")
    non_empty_str(request["language"], f"{label}.language")
    normalise_path(request["path"], f"{label}.path")
    if request["kind"] not in QUERY_KINDS:
        raise ContractError(f"{label}.kind must be one of {list(QUERY_KINDS)}")
    validate_server(request["server"], f"{label}.server")
    validate_workspace(request["workspace"], f"{label}.workspace")
    return request


def answer_for(
    request: dict[str, Any],
    server_exit: int | None,
    findings: list[dict[str, Any]],
    indexed: bool,
) -> tuple[str, str]:
    """What actually happened, as one of five states and a reason.

    Order matters. The server's own health is asked first, because a crashed
    server produces an empty findings list and so does a clean file -- and after
    they are both rendered as "no diagnostics" nobody can separate them again.
    """
    if server_exit is None:
        return (
            "SERVER_FAILED",
            "the server did not return; a crash produces no diagnostics and so does "
            "a clean file, and reporting both as zero errors makes them identical",
        )
    if server_exit != 0:
        return (
            "SERVER_FAILED",
            f"the server exited {server_exit}; its silence is about itself, not about "
            "the code",
        )
    if request["language"] not in request["server"]["languages"]:
        return (
            "UNKNOWN",
            f"{request['server']['server_id']} does not handle {request['language']}; "
            "nobody looked at this file, which is a different answer from finding "
            "nothing wrong with it",
        )
    if not indexed:
        return (
            "UNKNOWN",
            "the path is not in the server's index; an unindexed file reported as "
            "clean is a file nobody opened",
        )
    if findings:
        return ("FINDINGS", f"{len(findings)} finding(s) reported")
    return ("CLEAN", "the server indexed this path and reported nothing")


def build_result(
    request: dict[str, Any],
    slot: dict[str, Any],
    state: str,
    findings: list[dict[str, Any]],
    reason: str,
    freshness: str,
) -> dict[str, Any]:
    """Attach provenance to a result. There is no path that omits it."""
    if freshness not in FRESHNESS:
        raise ContractError(f"index_freshness must be one of {list(FRESHNESS)}")
    state_bears_evidence(state, "result.state")
    if state in {"UNKNOWN", "SERVER_FAILED"} and findings:
        raise ContractError(
            f"a {state} result carries {len(findings)} finding(s); if the server did "
            "not or could not look, whatever is in that list did not come from looking"
        )
    workspace = request["workspace"]
    return {
        "request_id": request["request_id"],
        "state": state,
        "findings": findings,
        "reason": reason,
        "provenance": {
            "server_id": slot["server"]["server_id"],
            "version": slot["server"]["version"],
            "config_digest": slot["server"]["config_digest"],
            "workspace_id": workspace["workspace_id"],
            "repository": workspace["repository"],
            "root": workspace["root"],
            "commit": workspace["commit"],
            "tree": workspace["tree"],
            "indexed_at": slot["indexed_at"],
            "index_freshness": freshness,
        },
    }


def validate_result(
    value: Any, request: dict[str, Any], label: str = "result"
) -> dict[str, Any]:
    result = exact_object(value, RESULT_KEYS, label)
    if result["request_id"] != request["request_id"]:
        raise ContractError(f"{label} answers a different request")
    state_bears_evidence(result["state"], f"{label}.state")
    non_empty_str(result["reason"], f"{label}.reason")

    provenance = exact_object(
        result["provenance"], PROVENANCE_KEYS, f"{label}.provenance"
    )
    sha256_ref(provenance["config_digest"], f"{label}.provenance.config_digest")
    parse_time(provenance["indexed_at"], f"{label}.provenance.indexed_at")
    if provenance["index_freshness"] not in FRESHNESS:
        raise ContractError(f"{label}.provenance.index_freshness is unknown")

    # The cross-worktree control, as a shape. A result whose provenance names a
    # different tree than the request is a result about someone else's code, and
    # it arrives looking exactly as authoritative as a correct one.
    workspace = request["workspace"]
    for field in ("workspace_id", "repository", "root", "commit", "tree"):
        if provenance[field] != workspace[field]:
            raise ContractError(
                f"{label}.provenance.{field} is {provenance[field]!r} but the request "
                f"asked about {workspace[field]!r}; this result describes a different "
                "tree and arrives looking exactly as authoritative as a correct one"
            )

    if (
        result["state"] in {"CLEAN", "FINDINGS"}
        and provenance["index_freshness"] != "CURRENT"
    ):
        raise ContractError(
            f"{label} claims {result['state']} from a {provenance['index_freshness']} "
            "index; the answer describes whatever was indexed, not what is there now"
        )
    if result["state"] == "CLEAN" and result["findings"]:
        raise ContractError(f"{label} is CLEAN with findings attached")
    if result["state"] == "FINDINGS" and not result["findings"]:
        raise ContractError(f"{label} is FINDINGS with nothing in it")
    return result


def to_code_truth_graph(result: dict[str, Any]) -> dict[str, Any]:
    """What the Code Truth Graph is handed. Provenance, never bare diagnostics."""
    if not state_bears_evidence(result["state"], "result.state"):
        return {
            "admitted": False,
            "state": result["state"],
            "reason": result["reason"],
            "evidence": "NONE",
        }
    return {
        "admitted": True,
        "state": result["state"],
        "findings": result["findings"],
        "provenance": result["provenance"],
        # Said on the way out, where the consumer reads it: a language server is
        # a tool that reads source. Its output is input to a graph, not a verdict.
        "authority": "EVIDENCE_INPUT_NOT_GATE_VERDICT",
    }
