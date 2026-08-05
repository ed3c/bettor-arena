from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

from .engine import ContextPackError, RepositoryContextEngine


def _repository_root() -> Path:
    configured = os.environ.get("REPO_CONTEXT_ROOT")
    if configured:
        root = Path(configured)
        if not root.is_absolute():
            raise RuntimeError("REPO_CONTEXT_ROOT must be an absolute path")
        return root
    return Path.cwd()


engine = RepositoryContextEngine(_repository_root())
mcp = MCPServer(
    "repo-context-pack",
    version="0.1.0",
    instructions=(
        "Read-only Python evidence packs. Pass repository-relative paths only. "
        "Treat completeness=partial as a requirement to read source bodies before edits."
    ),
)


@mcp.tool()
def build_python_context_pack(
    relative_path: str,
    symbol: str | None = None,
    max_bytes: int = 16_000,
) -> dict[str, Any]:
    """Build a repo-bound, SHA-256 source-bound Python AST evidence pack."""

    try:
        return engine.build_python_context_pack(
            relative_path,
            symbol=symbol,
            max_bytes=max_bytes,
        )
    except ContextPackError as exc:
        raise ValueError(str(exc)) from exc


@mcp.tool()
def context_pack_status() -> dict[str, Any]:
    """Report the bounded server contract without exposing the absolute repository path."""

    return engine.status()


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
