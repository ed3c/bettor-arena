#!/usr/bin/env python3
"""Compatibility entrypoint for the default-deny stateless MCP runtime.

The implementation lives in `mcp_runtime.py`; this file remains the stable path
used by `.mcp.json`, `.codex/config.toml`, loopctl wiring, and existing callers.
"""

from __future__ import annotations

from mcp_runtime import main


if __name__ == "__main__":
    raise SystemExit(main())
