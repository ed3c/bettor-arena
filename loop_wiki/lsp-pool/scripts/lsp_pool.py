#!/usr/bin/env python3
"""The pool: which server may serve which workspace, and when a slot goes stale.

Two workspaces may share a server slot only when every dimension of the slot
matches: server id, version, config digest **and** the workspace subject. The
subject is in that list deliberately. A slot keyed only on server identity is
the sharing everyone wants -- one process, five worktrees, one index -- and it is
exactly how a symbol from another worktree comes back looking authoritative.

Staleness is not a timer. A slot is stale the moment its workspace's commit or
tree moves, because the index it holds describes bytes that are no longer there.
Reusing it returns results about the previous commit with no marking of any kind.
"""

from __future__ import annotations

from typing import Any

from lsp_common import (
    SHA40,
    ContractError,
    exact_object,
    non_empty_str,
    parse_time,
    positive_int,
    sha256_ref,
)

SERVER_KEYS = {"server_id", "version", "config_digest", "languages", "multi_root"}

WORKSPACE_KEYS = {"workspace_id", "repository", "root", "commit", "tree", "lease_id"}

SLOT_KEYS = {
    "slot_id",
    "server",
    "workspace",
    "indexed_at",
    "memory_mb",
    "active_requests",
    "state",
}

SLOT_STATES = ("WARM", "INDEXING", "STALE", "EVICTING", "SHUT_DOWN")


def validate_server(value: Any, label: str) -> dict[str, Any]:
    server = exact_object(value, SERVER_KEYS, label)
    non_empty_str(server["server_id"], f"{label}.server_id")
    non_empty_str(server["version"], f"{label}.version")
    sha256_ref(server["config_digest"], f"{label}.config_digest")
    languages = server["languages"]
    if (
        not isinstance(languages, list)
        or not languages
        or languages != sorted(languages)
    ):
        raise ContractError(f"{label}.languages must be a sorted non-empty list")
    if not isinstance(server["multi_root"], bool):
        raise ContractError(
            f"{label}.multi_root must be a boolean; whether one process may serve "
            "several workspaces is a property of the server protocol, not a "
            "configuration preference"
        )
    return server


def validate_workspace(value: Any, label: str) -> dict[str, Any]:
    workspace = exact_object(value, WORKSPACE_KEYS, label)
    for field in ("workspace_id", "repository", "root", "lease_id"):
        non_empty_str(workspace[field], f"{label}.{field}")
    for field in ("commit", "tree"):
        if SHA40.fullmatch(str(workspace[field])) is None:
            raise ContractError(f"{label}.{field} must be a full 40-hex sha")
    return workspace


def validate_slot(value: Any, label: str) -> dict[str, Any]:
    slot = exact_object(value, SLOT_KEYS, label)
    non_empty_str(slot["slot_id"], f"{label}.slot_id")
    validate_server(slot["server"], f"{label}.server")
    validate_workspace(slot["workspace"], f"{label}.workspace")
    parse_time(slot["indexed_at"], f"{label}.indexed_at")
    positive_int(slot["memory_mb"], f"{label}.memory_mb")
    if slot["state"] not in SLOT_STATES:
        raise ContractError(f"{label}.state must be one of {list(SLOT_STATES)}")
    active = slot["active_requests"]
    if not isinstance(active, int) or isinstance(active, bool) or active < 0:
        raise ContractError(f"{label}.active_requests must be a non-negative integer")
    return slot


def compatible(
    slot: dict[str, Any], server: dict[str, Any], workspace: dict[str, Any]
) -> list[str]:
    """Every reason this slot cannot serve this request. All of them, not the first."""
    reasons = []
    for field in ("server_id", "version", "config_digest"):
        if slot["server"][field] != server[field]:
            reasons.append(
                f"{field} differs ({slot['server'][field]} vs {server[field]})"
            )

    held = slot["workspace"]
    if held["workspace_id"] != workspace["workspace_id"]:
        # Sharing across workspaces is only legal if the server says so, and even
        # then the repository must match: a multi-root server holding two
        # repositories will happily resolve a symbol from the wrong one.
        if not slot["server"]["multi_root"]:
            reasons.append(
                f"slot holds workspace {held['workspace_id']} and this server is not "
                "multi-root; one index answering for two trees returns symbols from "
                "whichever it happened to load"
            )
        elif held["repository"] != workspace["repository"]:
            reasons.append(
                f"slot holds repository {held['repository']}, request is for "
                f"{workspace['repository']}; a multi-root server crossing repositories "
                "resolves a name to whichever definition it saw first"
            )
    else:
        # Same workspace id, so the only question is whether the bytes moved.
        for field in ("commit", "tree"):
            if held[field] != workspace[field]:
                reasons.append(
                    f"workspace {field} moved from {held[field][:8]} to "
                    f"{workspace[field][:8]}; the index describes bytes that are no "
                    "longer there, and reusing it answers about the previous commit"
                )
    return reasons


def select(
    slots: list[dict[str, Any]],
    server: dict[str, Any],
    workspace: dict[str, Any],
    limits: dict[str, Any],
) -> dict[str, Any]:
    """Pick a slot, or say what has to happen instead. Never mutates the pool."""
    validate_server(server, "request.server")
    validate_workspace(workspace, "request.workspace")
    for index, slot in enumerate(slots):
        validate_slot(slot, f"slots[{index}]")

    usable = [slot for slot in slots if slot["state"] == "WARM"]
    refusals = []
    for slot in usable:
        reasons = compatible(slot, server, workspace)
        if not reasons:
            return {"decision": "REUSE", "slot_id": slot["slot_id"], "reasons": []}
        refusals.append({"slot_id": slot["slot_id"], "reasons": reasons})

    live = [slot for slot in slots if slot["state"] in {"WARM", "INDEXING"}]
    memory = sum(slot["memory_mb"] for slot in live)
    if len(live) >= limits["max_slots"]:
        return _needs_room(
            slots,
            f"pool is at its slot ceiling ({limits['max_slots']})",
            refusals,
        )
    if memory + limits["slot_memory_mb"] > limits["max_memory_mb"]:
        return _needs_room(
            slots,
            f"pool would exceed {limits['max_memory_mb']}MB "
            f"({memory} in use, {limits['slot_memory_mb']} requested)",
            refusals,
        )
    return {"decision": "CREATE", "slot_id": None, "reasons": refusals}


def _needs_room(
    slots: list[dict[str, Any]], why: str, refusals: list[dict[str, Any]]
) -> dict[str, Any]:
    """Find something evictable, or queue. An active request is never evictable."""
    idle = [
        slot
        for slot in slots
        if slot["state"] in {"WARM", "STALE"} and slot["active_requests"] == 0
    ]
    if idle:
        # Oldest index first, and among equals by slot_id so the choice is
        # reproducible. A pool that evicts by dict order evicts differently on
        # every run and no test of it means anything.
        victim = sorted(idle, key=lambda slot: (slot["indexed_at"], slot["slot_id"]))[0]
        return {
            "decision": "EVICT_THEN_CREATE",
            "slot_id": victim["slot_id"],
            "reasons": [*refusals, {"pool": why}],
        }
    return {
        "decision": "QUEUE",
        "slot_id": None,
        "reasons": [
            *refusals,
            {
                "pool": (
                    f"{why}, and every slot has an active request. Evicting one would "
                    "kill a query someone is waiting on, which turns a capacity "
                    "problem into a wrong answer"
                )
            },
        ],
    }


def evict(slots: list[dict[str, Any]], slot_id: str) -> list[dict[str, Any]]:
    """Remove a slot, refusing if it is serving anything."""
    for slot in slots:
        if slot["slot_id"] != slot_id:
            continue
        if slot["active_requests"] > 0:
            raise ContractError(
                f"slot {slot_id} has {slot['active_requests']} active request(s); "
                "evicting it kills a query someone is waiting on, and the caller sees "
                "a failure that looks like it came from their code"
            )
        return [entry for entry in slots if entry["slot_id"] != slot_id]
    raise ContractError(f"slot {slot_id} is not in the pool")
