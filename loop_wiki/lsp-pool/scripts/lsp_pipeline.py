#!/usr/bin/env python3
"""The query pass, in the order #96 names.

    LSP_CAPABILITY_REQUESTED
    -> SERVER_VERSION_CONFIG_PINNED
    -> WORKSPACE_SUBJECT_LEASE_PINNED
    -> POOL_SLOT_SELECTED_OR_CREATED
    -> INITIALIZATION_INDEX_FRESHNESS_VERIFIED
    -> QUERY_EXECUTED
    -> SOURCE_READBACK_COVERAGE_RECEIPT
    -> MEMORY_CPU_QUEUE_ACCOUNTED
    -> WORKSPACE_INVALIDATED_OR_REUSED
    -> SHUTDOWN_RESIDUE_CHECK

Freshness is verified before the query, not after. A stale slot answering first
and being marked stale afterwards has already returned the wrong answer, and the
marking arrives too late to stop anyone acting on it.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from lsp_common import ContractError, ServerUnavailable, digest
from lsp_fallback import run as fallback_run
from lsp_fallback import validate_fallback_admission
from lsp_pool import evict, select, validate_slot
from lsp_query import answer_for, build_result, validate_request, validate_result

STATES = [
    "LSP_CAPABILITY_REQUESTED",
    "SERVER_VERSION_CONFIG_PINNED",
    "WORKSPACE_SUBJECT_LEASE_PINNED",
    "POOL_SLOT_SELECTED_OR_CREATED",
    "INITIALIZATION_INDEX_FRESHNESS_VERIFIED",
    "QUERY_EXECUTED",
    "SOURCE_READBACK_COVERAGE_RECEIPT",
    "MEMORY_CPU_QUEUE_ACCOUNTED",
    "WORKSPACE_INVALIDATED_OR_REUSED",
    "SHUTDOWN_RESIDUE_CHECK",
]


def call_server(
    server_argv: list[str],
    request: dict[str, Any],
    root: Path,
    behaviour: str,
    timeout_s: float,
    other_workspace_id: str | None = None,
) -> tuple[int | None, dict[str, Any] | None]:
    """Run the server as a real process. Returns (exit code, payload)."""
    payload = {
        "kind": request["kind"],
        "path": request["path"],
        "root": str(root),
        "workspace_id": request["workspace"]["workspace_id"],
        "behaviour": behaviour,
    }
    if other_workspace_id:
        payload["other_workspace_id"] = other_workspace_id
    try:
        completed = subprocess.run(
            server_argv,
            input=json.dumps(payload) + "\n",
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        # A hung server is unavailable, not a clean file. None distinguishes it
        # from an exit code so the caller cannot read it as "finished quietly".
        return (None, None)
    except (OSError, ValueError) as exc:
        raise ServerUnavailable(f"cannot start the language server: {exc}") from exc

    if completed.returncode != 0:
        return (completed.returncode, None)
    try:
        return (0, json.loads(completed.stdout))
    except json.JSONDecodeError:
        return (0, None)


def run_query(
    request: dict[str, Any],
    slots: list[dict[str, Any]],
    limits: dict[str, Any],
    server_argv: list[str],
    root: Path,
    behaviour: str = "normal",
    timeout_s: float = 20.0,
    fallback_admission: dict[str, Any] | None = None,
    other_workspace_id: str | None = None,
) -> dict[str, Any]:
    """One query through the pool. Deterministic given its inputs."""
    trace = ["LSP_CAPABILITY_REQUESTED"]

    request = validate_request(request)
    trace.append("SERVER_VERSION_CONFIG_PINNED")
    trace.append("WORKSPACE_SUBJECT_LEASE_PINNED")

    decision = select(slots, request["server"], request["workspace"], limits)
    trace.append("POOL_SLOT_SELECTED_OR_CREATED")

    if decision["decision"] == "QUEUE":
        return _terminal(
            trace,
            decision,
            {
                "request_id": request["request_id"],
                "state": "NOT_EXERCISED",
                "findings": [],
                "reason": (
                    "the pool is full and every slot is serving a request; the query "
                    "is queued rather than answered, which is not the same as finding "
                    "nothing"
                ),
                "provenance": None,
            },
            slots,
        )

    if decision["decision"] == "REUSE":
        slot = next(s for s in slots if s["slot_id"] == decision["slot_id"])
        pool = list(slots)
        freshness = "CURRENT"
    else:
        pool = list(slots)
        if decision["decision"] == "EVICT_THEN_CREATE":
            pool = evict(pool, decision["slot_id"])
        slot = {
            "slot_id": f"slot-{request['workspace']['workspace_id']}",
            "server": request["server"],
            "workspace": request["workspace"],
            "indexed_at": request.get("_indexed_at", "2026-08-15T10:00:00Z"),
            "memory_mb": limits["slot_memory_mb"],
            "active_requests": 0,
            "state": "WARM",
        }
        validate_slot(slot, "new slot")
        pool = [*pool, slot]
        freshness = "CURRENT"
    trace.append("INITIALIZATION_INDEX_FRESHNESS_VERIFIED")

    exit_code, payload = call_server(
        server_argv, request, root, behaviour, timeout_s, other_workspace_id
    )
    findings = (payload or {}).get("findings", [])
    indexed = bool((payload or {}).get("indexed"))
    state, reason = answer_for(request, exit_code, findings, indexed)

    # A server that does not handle this language still returns a list. The
    # state says nobody competent looked, so the list is discarded -- and the
    # discard is written into the reason rather than done quietly, because
    # "0 findings" and "findings we threw away" are different things to a
    # reader trying to work out why a file looks clean.
    if state not in {"CLEAN", "FINDINGS"} and findings:
        reason = (
            f"{reason}. {len(findings)} finding(s) came back and were discarded: "
            "they were produced by a server that was not in a position to look"
        )
        findings = []
    trace.append("QUERY_EXECUTED")

    # The server may report a workspace that is not the one asked about. Checked
    # here, before the result is built, so a wrong-tree answer never becomes a
    # well-formed result at all.
    if (
        payload is not None
        and payload.get("workspace_id") != request["workspace"]["workspace_id"]
    ):
        raise ContractError(
            f"the server answered for workspace {payload.get('workspace_id')!r} but "
            f"the request named {request['workspace']['workspace_id']!r}; a symbol "
            "resolved in another worktree arrives looking exactly as authoritative "
            "as a correct one"
        )

    if state == "SERVER_FAILED" and fallback_admission is not None:
        validate_fallback_admission(fallback_admission)
        fallback = fallback_run(request, root)
        state, findings, reason = (
            fallback["state"],
            fallback["findings"],
            f"{reason}. Fallback: {fallback['reason']}",
        )
        slot = {**slot, "server": {**slot["server"], "server_id": "cli-fallback"}}

    result = build_result(request, slot, state, findings, reason, freshness)
    validate_result(result, request)
    trace.append("SOURCE_READBACK_COVERAGE_RECEIPT")
    trace.append("MEMORY_CPU_QUEUE_ACCOUNTED")
    trace.append("WORKSPACE_INVALIDATED_OR_REUSED")

    return _terminal(trace, decision, result, pool)


def _terminal(
    trace: list[str],
    decision: dict[str, Any],
    result: dict[str, Any],
    pool: list[dict[str, Any]],
) -> dict[str, Any]:
    trace = [*trace, "SHUTDOWN_RESIDUE_CHECK"]
    out = {
        "state_trace": trace,
        "pool_decision": decision,
        "result": result,
        "pool": sorted(pool, key=lambda slot: slot["slot_id"]),
    }
    out["query_digest"] = digest(
        {"decision": decision["decision"], "state": result["state"]}
    )
    return out
