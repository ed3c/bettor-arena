#!/usr/bin/env python3
"""The CLI fallback, and the ceiling it cannot exceed.

When the server is unavailable there is still something useful to do: parse the
single file and report syntax errors. What there is *not* is a way to answer a
references query, because references are a whole-project question and a
single-file parser has one file.

So the fallback declares a capability ceiling and refuses queries above it,
rather than answering them badly. The failure this prevents is specific: a
`REFERENCES` query answered by a single-file fallback returns an empty list, and
an empty reference list reads as "this symbol is unused" -- which is the reading
someone acts on by deleting it.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from lsp_common import ContractError, non_empty_str

# What a single-file parse can honestly answer, and what it cannot.
CEILING = {
    "DIAGNOSTICS": "SINGLE_FILE_SYNTAX_ONLY",
    "SYMBOLS": "SINGLE_FILE_ONLY",
    "REFERENCES": "REFUSED_PROJECT_WIDE",
    "DEFINITION": "REFUSED_PROJECT_WIDE",
}

SUPPORTED_LANGUAGES = {"python"}


def capability(kind: str) -> str:
    if kind not in CEILING:
        raise ContractError(f"unknown query kind {kind!r}")
    return CEILING[kind]


def run(request: dict[str, Any], root: Path) -> dict[str, Any]:
    """Answer within the ceiling, or say why not. Never returns an empty win."""
    kind = request["kind"]
    ceiling = capability(kind)

    if ceiling.startswith("REFUSED"):
        return {
            "state": "UNKNOWN",
            "findings": [],
            "reason": (
                f"a single-file fallback cannot answer {kind}: it is a project-wide "
                "question and this has one file. An empty reference list reads as "
                "'this symbol is unused', which is the reading someone acts on"
            ),
            "capability_ceiling": ceiling,
        }

    if request["language"] not in SUPPORTED_LANGUAGES:
        return {
            "state": "UNKNOWN",
            "findings": [],
            "reason": f"the fallback parses {sorted(SUPPORTED_LANGUAGES)}, not "
            f"{request['language']}",
            "capability_ceiling": ceiling,
        }

    path = root / request["path"]
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "state": "UNKNOWN",
            "findings": [],
            "reason": f"cannot read {request['path']}: {exc}",
            "capability_ceiling": ceiling,
        }

    try:
        ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return {
            "state": "FINDINGS",
            "findings": [
                {
                    "line": exc.lineno or 0,
                    "column": exc.offset or 0,
                    "message": str(exc.msg),
                    "severity": "ERROR",
                    "source": "cli-fallback-parse",
                }
            ],
            "reason": "single-file parse found a syntax error",
            "capability_ceiling": ceiling,
        }

    return {
        "state": "CLEAN",
        "findings": [],
        # Stated in the reason, not only in the ceiling field: a CLEAN from here
        # means the file parses, and nothing about types, imports or references.
        "reason": (
            "the file parses. This is a syntax-only answer -- it says nothing about "
            "types, imports or anything outside this file"
        ),
        "capability_ceiling": ceiling,
    }


def validate_fallback_admission(value: Any) -> dict[str, Any]:
    """The fallback runs only when it has been admitted, with its ceiling recorded."""
    if not isinstance(value, dict):
        raise ContractError("fallback admission must be an object")
    if set(value) != {"admitted", "admitted_by", "ceiling_acknowledged"}:
        raise ContractError("fallback admission fields drifted")
    if value["admitted"] is not True:
        raise ContractError(
            "the CLI fallback was not admitted; falling back silently means a "
            "syntax-only answer arrives wearing the same shape as a full one"
        )
    non_empty_str(value["admitted_by"], "fallback.admitted_by")
    if value["ceiling_acknowledged"] != sorted(CEILING):
        raise ContractError(
            "the admission does not acknowledge every query kind's ceiling; admitting "
            "a fallback without knowing what it cannot answer is admitting a shape"
        )
    return value
