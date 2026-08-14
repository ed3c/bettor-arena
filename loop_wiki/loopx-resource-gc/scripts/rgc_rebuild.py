#!/usr/bin/env python3
"""Rebuild proof. A projection may be deleted only after it has been rebuilt.

This is the part of #97 that cannot be answered with a configuration flag. "This
index is rebuildable" is a claim about the future, and the only honest way to
check it is to rebuild the thing now, next to the original, and compare bytes.

Three distinct outcomes, and collapsing any two of them loses the case that
matters:

    PROVEN          rebuilt, and byte-identical to what is on disk
    DIVERGENT       rebuilt, and different -- the rebuild works but does not
                    reproduce this; deleting means losing the difference
    UNPROVABLE      could not rebuild at all (no source, no command, it failed)

Only PROVEN admits deletion. DIVERGENT is the one people skip: the rebuild
command ran and exited zero, so the projection "is rebuildable" -- but what comes
back is not what was there, and whatever the difference encoded is gone.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from rgc_common import (
    ContractError,
    exact_object,
    non_empty_str,
    text_digest,
)

PROOF_STATES = ("PROVEN", "DIVERGENT", "UNPROVABLE")

SPEC_KEYS = {"resource_id", "path", "rebuild_argv", "source_paths", "timeout_ms"}


def validate_spec(value: Any, label: str) -> dict[str, Any]:
    spec = exact_object(value, SPEC_KEYS, label)
    non_empty_str(spec["resource_id"], f"{label}.resource_id")
    non_empty_str(spec["path"], f"{label}.path")
    argv = spec["rebuild_argv"]
    if (
        not isinstance(argv, list)
        or not argv
        or not all(isinstance(part, str) and part for part in argv)
    ):
        raise ContractError(
            f"{label}.rebuild_argv must be a non-empty list of strings; a projection "
            "with no rebuild command is not recreatable, whatever its class says"
        )
    sources = spec["source_paths"]
    if not isinstance(sources, list) or not sources or sources != sorted(sources):
        raise ContractError(f"{label}.source_paths must be a sorted non-empty list")
    timeout = spec["timeout_ms"]
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout < 1:
        raise ContractError(f"{label}.timeout_ms must be a positive integer")
    return spec


def _tree_digest(root: Path) -> str:
    """A digest over the file names and contents under root."""
    entries = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            entries.append(
                (path.relative_to(root).as_posix(), text_digest(path.read_bytes()))
            )
    return text_digest(repr(entries).encode("utf-8"))


def prove(spec: dict[str, Any], root: Path) -> dict[str, Any]:
    """Rebuild this projection beside the original and compare. Never deletes."""
    validate_spec(spec, f"rebuild spec {spec.get('resource_id')!r}")
    original = root / spec["path"]
    if not original.exists():
        return {
            "resource_id": spec["resource_id"],
            "state": "UNPROVABLE",
            "reason": f"{spec['path']} is not on disk, so there is nothing to compare",
            "original_digest": None,
            "rebuilt_digest": None,
        }

    for source in spec["source_paths"]:
        if not (root / source).exists():
            return {
                "resource_id": spec["resource_id"],
                "state": "UNPROVABLE",
                "reason": (
                    f"source {source!r} is absent, so this projection cannot be "
                    "rebuilt after deletion -- deleting it would be one-way"
                ),
                "original_digest": None,
                "rebuilt_digest": None,
            }

    original_digest = (
        _tree_digest(original)
        if original.is_dir()
        else text_digest(original.read_bytes())
    )

    with tempfile.TemporaryDirectory(prefix="loopx-rgc-rebuild-") as tmp:
        scratch = Path(tmp) / "rebuilt"
        scratch.parent.mkdir(parents=True, exist_ok=True)
        argv = [
            part.replace("{OUTPUT}", str(scratch)).replace("{ROOT}", str(root))
            for part in spec["rebuild_argv"]
        ]
        try:
            completed = subprocess.run(
                argv,
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=spec["timeout_ms"] / 1000,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return {
                "resource_id": spec["resource_id"],
                "state": "UNPROVABLE",
                "reason": f"the rebuild command could not run: {exc}",
                "original_digest": original_digest,
                "rebuilt_digest": None,
            }

        if completed.returncode != 0:
            return {
                "resource_id": spec["resource_id"],
                "state": "UNPROVABLE",
                "reason": (
                    f"the rebuild exited {completed.returncode}: "
                    f"{completed.stderr.strip()[:200]}"
                ),
                "original_digest": original_digest,
                "rebuilt_digest": None,
            }
        if not scratch.exists():
            return {
                "resource_id": spec["resource_id"],
                "state": "UNPROVABLE",
                "reason": (
                    "the rebuild exited zero and produced nothing; an exit code is "
                    "not an artifact, and this is the case a returncode check misses"
                ),
                "original_digest": original_digest,
                "rebuilt_digest": None,
            }

        rebuilt_digest = (
            _tree_digest(scratch)
            if scratch.is_dir()
            else text_digest(scratch.read_bytes())
        )
        shutil.rmtree(scratch, ignore_errors=True)

    if rebuilt_digest != original_digest:
        return {
            "resource_id": spec["resource_id"],
            "state": "DIVERGENT",
            "reason": (
                "the rebuild succeeded but does not reproduce what is on disk; the "
                "projection is recreatable in general and this particular content is "
                "not, so deleting it loses whatever the difference encodes"
            ),
            "original_digest": original_digest,
            "rebuilt_digest": rebuilt_digest,
        }
    return {
        "resource_id": spec["resource_id"],
        "state": "PROVEN",
        "reason": "rebuilt beside the original and byte-identical",
        "original_digest": original_digest,
        "rebuilt_digest": rebuilt_digest,
    }


def admits_deletion(proof: dict[str, Any]) -> bool:
    if proof["state"] not in PROOF_STATES:
        raise ContractError(f"unknown rebuild proof state {proof['state']!r}")
    return proof["state"] == "PROVEN"
