#!/usr/bin/env python3
"""The optional simulator lane, and why it is absent by default.

`nektos/act` runs workflow steps locally. It is not a GitHub-hosted runner: the
image differs, the token permissions differ, the cache and artifact services are
absent or emulated, and nothing is billed. So it is admitted only with an exact
version and an exact image digest, and its results stay in their own lane --
never merged into the native-local lane, because a step that passed under act and
a step that passed under the repository's own script are two different claims.

Absent is the default and absent is a state, not a failure. `SIMULATOR_ABSENT`
means nothing was asked, which is different from asked-and-disagreed.
"""

from __future__ import annotations

from typing import Any

from cp_common import ContractError, digest, non_empty_str

SIMULATOR_STATES = ("SIMULATOR_ABSENT", "SIMULATOR_PINNED", "SIMULATOR_UNPINNED")

ADMISSION_KEYS = {"tool", "version", "image", "image_digest", "license"}


def absent(reason: str = "no simulator has been admitted") -> dict[str, Any]:
    return {
        "state": "SIMULATOR_ABSENT",
        "reason": reason,
        # The distinction that keeps an absent simulator from reading as a clean
        # simulator run: nothing ran, so nothing agreed.
        "results_admissible": False,
        "lane": "NONE",
    }


def admit(value: Any) -> dict[str, Any]:
    """Pin a simulator, or refuse. There is no partly-pinned admission."""
    if not isinstance(value, dict) or set(value) != ADMISSION_KEYS:
        raise ContractError(
            f"simulator admission fields drifted; expected {sorted(ADMISSION_KEYS)}. "
            "An admission missing its image digest names a tool, not a thing that ran"
        )
    for field in ADMISSION_KEYS:
        non_empty_str(value[field], f"simulator.{field}")
    if not value["image_digest"].startswith("sha256:"):
        raise ContractError(
            f"simulator.image_digest is {value['image_digest']!r}; an image tag can be "
            "repushed onto different contents, so a tag does not identify what ran"
        )
    return {
        "state": "SIMULATOR_PINNED",
        **value,
        "results_admissible": True,
        # Its own lane. Merging simulator results into the native-local lane
        # would make two different claims indistinguishable in the receipt.
        "lane": "SIMULATOR",
        "equivalent_to_hosted_runner": False,
        "admission_digest": digest(value),
    }


def require_separate_lanes(
    native: dict[str, Any], simulated: dict[str, Any] | None
) -> None:
    """Refuse a receipt that has folded the two lanes together."""
    if native.get("lane") not in (None, "NATIVE"):
        raise ContractError(
            f"the native local result is in lane {native.get('lane')!r}"
        )
    if simulated is None:
        return
    if simulated.get("lane") != "SIMULATOR":
        raise ContractError(
            "a simulator result is in the native lane. A step that passed under a "
            "simulator and a step that passed under the repository's own script are "
            "two different claims, and the receipt has to be able to say which"
        )
    if simulated.get("equivalent_to_hosted_runner"):
        raise ContractError(
            "a simulator result claims equivalence to a hosted runner. The image, the "
            "token permissions, the cache and artifact services and the billing all "
            "differ; a simulator answers whether the commands work, not whether the "
            "hosted run would pass"
        )
