#!/usr/bin/env python3
"""Verify a loopback CDP browser without reading page or conversation content."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from urllib.parse import urlsplit
from urllib.request import urlopen


def main() -> int:
    endpoint = os.environ.get("DR_CDP_URL") or "http://127.0.0.1:9333"
    parsed = urlsplit(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        print("research CDP RED: endpoint must be loopback HTTP", file=sys.stderr)
        return 2
    try:
        with urlopen(endpoint.rstrip("/") + "/json/version", timeout=5) as response:
            document = json.loads(response.read())
    except Exception:
        print("research CDP RED: debugger metadata is unreachable", file=sys.stderr)
        return 2
    browser = document.get("Browser")
    websocket = document.get("webSocketDebuggerUrl")
    if not isinstance(browser, str) or not browser or not isinstance(websocket, str):
        print("research CDP RED: debugger metadata is incomplete", file=sys.stderr)
        return 2
    ws = urlsplit(websocket)
    if ws.scheme != "ws" or ws.hostname not in {"127.0.0.1", "localhost", "::1"}:
        print("research CDP RED: debugger websocket is not loopback", file=sys.stderr)
        return 2
    print(
        "PASS: research CDP reachable; browser_sha256="
        + hashlib.sha256(browser.encode()).hexdigest()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
