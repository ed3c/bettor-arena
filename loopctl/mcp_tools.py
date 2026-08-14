#!/usr/bin/env python3
"""Stable compatibility entrypoint for the Bun/TypeScript MCP tool generator."""

from __future__ import annotations

import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
os.execvp("bun", ["bun", str(HERE / "mcp_tools.ts"), *sys.argv[1:]])
