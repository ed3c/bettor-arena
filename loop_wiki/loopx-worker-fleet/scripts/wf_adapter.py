#!/usr/bin/env python3
"""Adapters: tmux and Herdr. Neither of them knows whether a task passed.

This file exists to keep two specific sentences from ever being written down as
if they were evidence:

    "the tmux session is alive, so the Worker is running"
    "Herdr exited 0, so the gate passed"

A tmux session is a terminal that is still open. It survives the process that
was running in it, it survives that process failing, and it is a perfectly good
operator projection -- which is why the temptation exists. So `tmux_projection`
returns a state from a vocabulary that has no PASS in it at all: there is no
value it can carry that a reader could mistake for a task verdict.

Herdr is the same shape one layer up. Its exit code describes the queue
adapter's own run, not the workload's gates. `herdr_admission` cannot report
anything but NOT_EXERCISED unless the caller supplies an exact binary digest and
config digest from a canary -- and even then it reports admission of the
*adapter*, never of a task.
"""

from __future__ import annotations

from typing import Any

from wf_common import (
    ContractError,
    exact_object,
    non_empty_str,
    sha256_ref_or_none,
)

# Deliberately without PASS, FAIL or any verdict word. A projection reports what
# a terminal looks like; it has no vocabulary for whether work succeeded.
TMUX_STATES = ("SESSION_PRESENT", "SESSION_ABSENT", "SESSION_UNKNOWN")

PROJECTION_KEYS = {"session_name", "state", "pane_count", "attached"}

HERDR_KEYS = {"binary_digest", "config_digest", "canary_receipt", "exit_code"}

ADMISSION_STATES = ("NOT_EXERCISED", "ADAPTER_ADMITTED", "ADAPTER_REFUSED")


def tmux_projection(value: Any) -> dict[str, Any]:
    """An operator's view of a session. Never a Worker verdict."""
    projection = exact_object(value, PROJECTION_KEYS, "tmux projection")
    non_empty_str(projection["session_name"], "tmux projection.session_name")
    if projection["state"] not in TMUX_STATES:
        raise ContractError(
            f"tmux projection.state must be one of {list(TMUX_STATES)}; a session is "
            "a terminal that is still open -- it survives the process that was "
            "running in it, and it survives that process failing"
        )
    if not isinstance(projection["pane_count"], int) or projection["pane_count"] < 0:
        raise ContractError("tmux projection.pane_count must be a non-negative integer")
    if not isinstance(projection["attached"], bool):
        raise ContractError("tmux projection.attached must be a boolean")
    return {
        **projection,
        # Carried on the projection itself, where someone reading it will see it.
        "authority": "OPERATOR_PROJECTION_ONLY",
        "task_evidence": "NONE",
    }


def worker_state_from_tmux(projection: dict[str, Any]) -> str:
    """What a tmux projection tells you about the Worker. Deliberately: nothing.

    Present as a named function so the answer is written down once, here, rather
    than re-derived by whoever next has a session state and needs a Worker state.
    """
    tmux_projection(projection)
    return "NOT_OBSERVED"


def herdr_admission(value: Any) -> dict[str, Any]:
    """Adapter admission, which is not task admission and not a gate verdict."""
    herdr = exact_object(value, HERDR_KEYS, "herdr admission")
    binary = sha256_ref_or_none(herdr["binary_digest"], "herdr.binary_digest")
    config = sha256_ref_or_none(herdr["config_digest"], "herdr.config_digest")
    receipt = herdr["canary_receipt"]

    if binary is None or config is None or not receipt:
        # No exact binary, no exact config, or no canary receipt: the adapter has
        # not been exercised, and that is a different answer from "it failed".
        return {
            "state": "NOT_EXERCISED",
            "reason": (
                "an adapter admitted without an exact binary digest, config digest "
                "and canary receipt is admitted on its name"
            ),
            "authority": "ADAPTER_ONLY",
            "gate_evidence": "NONE",
        }

    non_empty_str(receipt, "herdr.canary_receipt")
    exit_code = herdr["exit_code"]
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        raise ContractError("herdr.exit_code must be an integer")

    state = "ADAPTER_ADMITTED" if exit_code == 0 else "ADAPTER_REFUSED"
    if state not in ADMISSION_STATES:
        raise ContractError(f"unknown admission state {state!r}")
    return {
        "state": state,
        "reason": f"canary {receipt} exited {exit_code}",
        # Said on the record every time, because the exit code is right there
        # next to it and zero is the most persuasive number in software.
        "authority": "ADAPTER_ONLY",
        "gate_evidence": "NONE",
    }


def refuse_adapter_as_verdict(field: str, value: Any) -> None:
    """Raise if an adapter observation is being used where a verdict belongs."""
    raise ContractError(
        f"{field} was set from an adapter observation ({value!r}). A tmux session "
        "being present and Herdr exiting zero are facts about adapters; a task "
        "verdict comes from the gates the task ran, and nothing else"
    )
