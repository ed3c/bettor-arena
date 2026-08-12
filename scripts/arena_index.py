#!/usr/bin/env python3
"""Exact Git-index identities for live repositories and materialized trees."""

from __future__ import annotations

from pathlib import Path
import subprocess


class IndexError(ValueError):
    """Git index metadata is absent, malformed, or unstable."""


def parse_entries(raw: bytes, source: str) -> dict[str, dict[str, str]]:
    if not raw or not raw.endswith(b"\0"):
        raise IndexError(
            f"{source}: index manifest must be non-empty and NUL-terminated"
        )
    entries: dict[str, dict[str, str]] = {}
    for raw_entry in raw[:-1].split(b"\0"):
        metadata, separator, path_raw = raw_entry.partition(b"\t")
        if not separator:
            raise IndexError(f"{source}: index entry has no path separator")
        try:
            parts = metadata.decode("ascii").split()
            path = path_raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise IndexError(f"{source}: index entry encoding is invalid") from exc
        if len(parts) != 3:
            raise IndexError(f"{source}: index entry metadata drifted")
        mode, blob, stage = parts
        if stage != "0":
            raise IndexError(f"{source}: unmerged index entry is unstable: {path}")
        if path in entries:
            raise IndexError(f"{source}: duplicate index path: {path}")
        entries[path] = {"path": path, "mode": mode, "blob": blob}
    return entries


def git_entries(root: Path) -> dict[str, dict[str, str]]:
    process = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--stage", "-z"],
        check=False,
        capture_output=True,
    )
    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        raise IndexError(f"git ls-files --stage failed for {root}: {detail}")
    return parse_entries(process.stdout, f"Git index at {root}")


def load_entries(path: Path) -> dict[str, dict[str, str]]:
    return parse_entries(path.read_bytes(), str(path))
