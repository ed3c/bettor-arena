#!/usr/bin/env python3
"""Stable compatibility entrypoint for the Bun/TypeScript stateless MCP runtime."""
from __future__ import annotations

import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
os.execvp("bun", ["bun", str(HERE / "mcp_runtime.ts"), *sys.argv[1:]])
