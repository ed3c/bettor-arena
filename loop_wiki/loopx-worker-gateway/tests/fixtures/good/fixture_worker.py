#!/usr/bin/env python3
"""Deterministic fixture process for LoopX Worker Gateway tests."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["success", "fail", "sleep", "spawn"], required=True)
    args = parser.parse_args()

    observation = {
        "schema_version": "loopx/fixture-worker-observation/v1",
        "host_id": os.environ.get("LOOPX_HOST_ID"),
        "request_id": os.environ.get("LOOPX_REQUEST_ID"),
        "task_id": os.environ.get("LOOPX_TASK_ID"),
        "skill_digest": os.environ.get("LOOPX_SKILL_DIGEST"),
        "context_digest": os.environ.get("LOOPX_CONTEXT_DIGEST"),
    }
    print(json.dumps(observation, sort_keys=True), flush=True)

    if args.mode == "success":
        print("fixture-success", flush=True)
        return 0
    if args.mode == "fail":
        print("fixture-failure", file=sys.stderr, flush=True)
        return 7
    if args.mode == "sleep":
        time.sleep(10)
        return 0
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    print(json.dumps({"spawned_pid": child.pid}), flush=True)
    time.sleep(30)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
