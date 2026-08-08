#!/usr/bin/env python3
"""Add a Google Drive document by REFERENCE and return its indexed text, as JSON.

    drive_fetch.py <notebook_id> <file_id> <title> [<wait_seconds>]
        ->  {"source_id", "title", "content"}

Why this is a separate file and not part of workflow.py: it runs under a
DIFFERENT interpreter. The `notebooklm` CLI is normally installed into its own
isolated environment (pipx / uv tool), so the repo's python cannot import the
library — workflow.py resolves the CLI's own interpreter off its shebang and
runs this file with that.

Why the library at all, when workflow.py otherwise only speaks to the CLI: the
CLI's `source add <url>` is an UNAUTHENTICATED web fetch, and it cannot reach a
Google Doc that requires sign-in. Measured, not assumed — every document linked
from the harvested sheet answers HTTP 401 to an anonymous request (a nonexistent
id answers 404, which is how "exists but gated" was told apart from "not there"),
and the CLI returns FAILED_PRECONDITION (gRPC 9) for each of them. The library's
`sources.add_drive` goes by Drive file id over the SIGNED-IN session, which
reaches exactly those documents. There is no CLI flag for it; that is the whole
reason this file exists.

Exit: 0 with JSON on stdout · 3 the library is not importable under this
interpreter · 4 Drive refused the file (not shared with this account, wrong id,
or not a native Doc). Distinct codes because they are repaired in different
places, and the caller turns each into its own named state.
"""

from __future__ import annotations

import asyncio
import json
import sys


async def _fetch(
    notebook_id: str, file_id: str, title: str, wait_seconds: float = 120.0
) -> dict:
    from notebooklm import NotebookLMClient
    from notebooklm.auth import AuthTokens
    from notebooklm.types import DriveMimeType

    auth = await AuthTokens.from_storage()
    async with NotebookLMClient(auth) as client:
        source = await client.sources.add_drive(
            notebook_id,
            file_id=file_id,
            title=title,
            mime_type=DriveMimeType.GOOGLE_DOC.value,
            wait=True,
            wait_timeout=wait_seconds,
        )
        fulltext = await client.sources.get_fulltext(notebook_id, source.id)
        return {
            "source_id": source.id,
            "title": fulltext.title or source.title,
            "content": fulltext.content or "",
        }


def main(argv: list[str]) -> int:
    if len(argv) not in (3, 4):
        print(__doc__.strip(), file=sys.stderr)
        return 64
    notebook_id, file_id, title = argv[0], argv[1], argv[2]
    wait_seconds = float(argv[3]) if len(argv) == 4 else 120.0
    try:
        import notebooklm  # noqa: F401
    except ImportError as exc:
        print(
            f"drive-fetch: the notebooklm library is not importable under "
            f"{sys.executable} — {exc}",
            file=sys.stderr,
        )
        return 3
    try:
        result = asyncio.run(_fetch(notebook_id, file_id, title, wait_seconds))
    except Exception as exc:  # noqa: BLE001 — the caller needs the reason, not the type
        print(
            f"drive-fetch: Drive refused {file_id} — {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 4
    # Nothing but JSON on stdout: the caller asserts purity, the same way it does
    # for the CLI, so a stray print here can never be parsed past.
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
