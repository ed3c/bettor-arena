#!/usr/bin/env python3
"""Carrier entry for the issue-91 Claude Code live lane.

The frozen Worker Gateway invokes this file as the adapter entry with the
fixed argv `--request/--workspace/--events/--output`. This process launches
exactly one host turn inside the detached worktree the gateway leased, writes
the raw host output under the gateway output root and emits a
`loopx/worker-event/v1` stream whose terminal `PROCESS_EXIT` carries this
process's own exit code.

It observes; it never classifies. `OBSERVED_SUCCESS`, Gate verdicts, LoopX
state and Human Admit are outside this process by construction.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from gateway_common import digest, load_json  # noqa: E402

CARRIER_ID = "issue-91-live-lane"
CARRIER_TIMEOUT_S = 300
STUB_HOST = "fixture-host"
LIVE_HOST = "claude-code"
# Names the host must never inherit from the surrounding agent session: they
# would let an outer Claude Code/Codex process leak identity or budget into the
# carried turn. The gateway already passes only the request env allowlist; this
# is the second, local drop.
SCRUB = re.compile(r"^(?:CLAUDECODE|CLAUDE_CODE_.*|ANTHROPIC_.*|CODEX_.*|AI_AGENT)$")
STUB_SOURCE = (
    "import hashlib,json,sys;"
    "print(json.dumps({'stub_carrier':True,"
    "'note':'no host binary was launched',"
    "'prompt_sha256':hashlib.sha256(sys.argv[1].encode()).hexdigest()},"
    "sort_keys=True))"
)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def event(
    request: dict[str, Any],
    sequence: int,
    kind: str,
    message: str,
    exit_code: int | None = None,
) -> dict[str, Any]:
    value = {
        "schema_version": "loopx/worker-event/v1",
        "event_id": f"carrier-{sequence}-{kind.lower()}",
        "request_id": request["request_id"],
        "host_id": request["host_id"],
        "sequence": sequence,
        "occurred_at": now_utc(),
        "kind": kind,
        "visibility": "EXTERNAL",
        "payload": {
            "message": message,
            "exit_code": exit_code,
            "tool": None,
            "artifact_ref": None,
            "cleanup_state": None,
        },
        "content_digest": None,
    }
    raw = copy.deepcopy(value)
    raw.pop("content_digest")
    value["content_digest"] = digest(raw)
    return value


def write_events(path: Path, events: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            for item in events
        )
        + "\n",
        encoding="utf-8",
    )


def resolve_prompt(request: dict[str, Any], workspace: Path) -> str:
    """Return the single prompt line whose bytes match `task.prompt_ref`.

    The leased worktree is searched first. The source checkout is the fallback
    for a prompt that is still uncommitted; either way the file only counts
    when its digest equals the digest the gateway already bound.
    """
    ref = request["task"]["prompt_ref"]
    source_root = Path(__file__).resolve().parents[3]
    for base in (workspace, source_root):
        candidate = base / ref["path"]
        if not candidate.is_file():
            continue
        raw = candidate.read_bytes()
        if "sha256:" + hashlib.sha256(raw).hexdigest() != ref["digest"]:
            continue
        text = raw.decode("utf-8").strip()
        if not text or "\n" in text:
            raise ValueError("carrier prompt must be exactly one non-empty line")
        return text
    raise ValueError(f"no digest-matching prompt found for {ref['path']}")


def carrier_argv(request: dict[str, Any], prompt: str) -> list[str]:
    if request["host_id"] == STUB_HOST:
        return [sys.executable, "-c", STUB_SOURCE, prompt]
    if request["host_id"] != LIVE_HOST:
        raise ValueError(f"this carrier serves only {LIVE_HOST} and {STUB_HOST}")
    return [
        "claude",
        "-p",
        prompt,
        "--output-format",
        "json",
        "--tools",
        "",
        "--disable-slash-commands",
        "--no-session-persistence",
        "--max-budget-usd",
        "1",
    ]


def launch(argv: list[str], workspace: Path, output: Path) -> tuple[int, str]:
    env = {key: value for key, value in os.environ.items() if not SCRUB.fullmatch(key)}
    try:
        completed = subprocess.run(
            argv,
            cwd=str(workspace),
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=CARRIER_TIMEOUT_S,
            check=False,
            start_new_session=True,
        )
        stdout, stderr, code = completed.stdout, completed.stderr, completed.returncode
        note = "host process exited"
    except FileNotFoundError:
        stdout, stderr, code = b"", b"", 127
        note = f"host binary not found on PATH: {argv[0]}"
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or b""
        stderr = exc.stderr or b""
        code = 124
        note = f"host process exceeded {CARRIER_TIMEOUT_S}s and was terminated"
    output.mkdir(parents=True, exist_ok=True)
    (output / "carrier-stdout.bin").write_bytes(stdout)
    (output / "carrier-stderr.bin").write_bytes(stderr)
    summary = {
        "carrier": CARRIER_ID,
        "binary": Path(argv[0]).name,
        "exit_code": code,
        "note": note,
        "stdout_bytes": len(stdout),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_bytes": len(stderr),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return code, (
        f"host={summary['binary']} exit={code} "
        f"stdout_bytes={summary['stdout_bytes']} "
        f"stdout_sha256={summary['stdout_sha256']}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="issue-91 live-lane carrier")
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    request = load_json(args.request)
    events = [
        event(request, 0, "PROCESS_STARTED", f"carrier {CARRIER_ID} started"),
    ]
    try:
        prompt = resolve_prompt(request, args.workspace)
        code, observation = launch(
            carrier_argv(request, prompt), args.workspace, args.output
        )
    except (ValueError, OSError) as exc:
        code, observation = 64, f"carrier refused to launch: {exc}"
        print(f"FATAL: {observation}", file=sys.stderr)
    events.append(event(request, 1, "STDOUT", observation))
    events.append(event(request, 2, "PROCESS_EXIT", "carrier exited", exit_code=code))
    write_events(args.events, events)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
