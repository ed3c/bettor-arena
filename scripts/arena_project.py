#!/usr/bin/env python3
"""Compatibility shim for the Bun + TypeScript project bootstrapper."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys


script = Path(__file__).with_suffix(".ts")
bun = shutil.which("bun")
if bun is None:
    print("project-bootstrap FATAL: bun is required", file=sys.stderr)
    raise SystemExit(64)
os.execv(bun, [bun, str(script), *sys.argv[1:]])
