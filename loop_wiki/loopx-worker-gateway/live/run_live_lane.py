#!/usr/bin/env python3
"""Drive the issue-91 Claude Code live lane through the frozen Worker Gateway.

Modes:

```text
--selftest   planted controls; each one must go RED
--dry-run    the whole chain with the stub carrier; must go green end to end
--live       the single admitted Claude Code turn
```

The gateway in `../scripts` is frozen and is reused as-is: it leases the
detached worktree, executes the carrier, enforces the read-only and output
budgets, cleans up and writes the receipt. This runner owns the request, the
adapter selection, the post-run verification the gateway cannot do to itself
(receipt/event bytes against the frozen JSON Schemas, and the receipt's claimed
event digest against the event stream actually on disk) and the cleanup
observation.

It records observations. It cannot write a Gate verdict, LoopX state, the
frozen `LIVE_MATRIX.md` or a Human Admit.
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any

LIVE = Path(__file__).resolve().parent
MODULE = LIVE.parent
REPO = MODULE.parents[1]
sys.path.insert(0, str(MODULE / "scripts"))

from gateway_common import (  # noqa: E402
    BAD,
    OK,
    USAGE,
    ContractError,
    digest,
    file_digest,
    load_json,
    write_json_atomic,
)
from gateway_contract import (  # noqa: E402
    validate_adapter,
    validate_event,
    validate_receipt,
    validate_request,
)

try:
    from jsonschema import Draft202012Validator
except ModuleNotFoundError:  # pragma: no cover - reported as FATAL in main()
    Draft202012Validator = None

REPOSITORY = "ed3c/bettor-arena"
TASK_ID = "issue-91-claude-code-live-canary"
LANE_SCHEMA = "issue-91/live-lane/v1"
SKILL_NAME = "claude-code-live-canary"
PROMPT_REL = "loop_wiki/loopx-worker-gateway/live/payload/live-turn-prompt.txt"
SKILL_REL = "loop_wiki/loopx-worker-gateway/live/payload/SKILL.md"
CONTEXT_ENTRIES = ["AGENTS.md", "CLAUDE.md"]
TIMEOUT_MS = 330_000
RECEIPTS = LIVE / "receipts"
LIVE_OUTPUT = RECEIPTS / "live" / "turn-1"
NON_CLAIMS = [
    "a green run is an observation, not a Gate PASS",
    "this lane cannot change LIVE_MATRIX.md for any host",
    "no physical network or filesystem isolation is attested",
    "host-internal reasoning and tool use remain UNKNOWN at PROCESS_ONLY",
]


class LaneError(RuntimeError):
    pass


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git_out(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if result.returncode != 0:
        raise LaneError(f"git {' '.join(args)} failed: {result.stderr[-300:]}")
    return result.stdout.strip()


def with_digest(value: dict[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(value)
    result.pop("content_digest", None)
    raw = copy.deepcopy(result)
    result["content_digest"] = digest(raw)
    return result


def frozen_schema(name: str) -> dict[str, Any]:
    """Load a frozen contract schema after checking it against its manifest pin."""
    manifest = load_json(MODULE / "contracts" / "manifest.json")
    for entry in manifest["schemas"]:
        if entry["path"] != name:
            continue
        path = MODULE / "contracts" / name
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise LaneError(f"frozen schema drifted from its manifest pin: {name}")
        return load_json(path)
    raise LaneError(f"frozen manifest does not pin a schema named {name}")


def schema_errors(value: Any, name: str) -> list[Any]:
    return sorted(
        Draft202012Validator(frozen_schema(name)).iter_errors(value),
        key=lambda item: list(item.path),
    )


def schema_check(value: Any, name: str, label: str) -> None:
    errors = schema_errors(value, name)
    if errors:
        first = errors[0]
        raise LaneError(
            f"{label} violates {name}: {'/'.join(str(p) for p in first.path)}: "
            f"{first.message}"
        )


def check_contract(value: Any, name: str, label: str, host_id: str) -> str:
    """Bind a request/descriptor to its published contract.

    The published request and adapter contracts enumerate the six real hosts
    only, so a stub subject is out-of-contract by construction. Asserting that
    rejection is what makes a dry-run subject unusable as a live one; silently
    skipping the check would throw that property away.
    """
    errors = schema_errors(value, name)
    if host_id != "fixture-host":
        schema_check(value, name, label)
        return f"{label}=SCHEMA_VALID"
    if not any(str(next(iter(error.path), "")) == "host_id" for error in errors):
        raise LaneError(f"{label}: stub subject was accepted by the live {name}")
    return f"{label}=OUT_OF_CONTRACT_STUB"


def build_request(request_id: str, host_id: str, commit: str, tree: str) -> dict:
    prompt = REPO / PROMPT_REL
    skill = REPO / SKILL_REL
    return with_digest(
        {
            "schema_version": "loopx/worker-request/v1",
            "request_id": request_id,
            "subject": {
                "repository": REPOSITORY,
                "commit": commit,
                "tree": tree,
                "task_id": TASK_ID,
            },
            "adapter_id": host_id,
            "host_id": host_id,
            "skill": {
                "name": SKILL_NAME,
                "digest": file_digest(skill),
                "source_ref": SKILL_REL,
            },
            "context": {
                # The carrier injects no capsule; the host may auto-load these
                # entry files from the leased worktree. The digest therefore
                # covers exactly those bytes and claims nothing about loading.
                "digest": digest(
                    [file_digest(REPO / name) for name in CONTEXT_ENTRIES]
                ),
                "entry_files": list(CONTEXT_ENTRIES),
            },
            "workspace": {
                "lease_id": "issue-91-live-lease",
                "writable_paths": [],
                "read_only_paths": list(CONTEXT_ENTRIES),
                "cleanup": "REQUIRED",
            },
            "policy": {
                "timeout_ms": TIMEOUT_MS,
                "max_output_bytes": 1_048_576,
                "max_processes": 8,
                "network": "HOST_POLICY",
                "env_allowlist": ["HOME", "LOGNAME", "TMPDIR", "USER"],
                "require_process_group": True,
            },
            "task": {
                "prompt_ref": {
                    "artifact_id": "issue-91-live-prompt",
                    "kind": "FILE",
                    "path": PROMPT_REL,
                    "digest": file_digest(prompt),
                    "bytes": prompt.stat().st_size,
                    "media_type": "text/plain",
                    "producer": "issue-91-live-lane",
                },
                "mode": "READ_ONLY",
                "expected_artifacts": ["STDOUT", "STDERR", "GIT_DIFF", "WORKER_EVENT"],
            },
            "credential_refs": [],
        }
    )


def gateway_env() -> dict[str, str]:
    keep = {
        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONUNBUFFERED": "1",
    }
    for name in ("HOME", "LOGNAME", "TMPDIR", "USER"):
        value = os.environ.get(name)
        if value:
            keep[name] = value
    return keep


def run_gateway(
    request: dict[str, Any],
    descriptor: dict[str, Any],
    scratch: Path,
    output: Path,
    receipt_id: str,
) -> subprocess.CompletedProcess[str]:
    request_path = scratch / f"{request['request_id']}.request.json"
    descriptor_path = scratch / f"{request['request_id']}.adapter.json"
    write_json_atomic(request_path, request)
    write_json_atomic(descriptor_path, descriptor)
    argv = [
        sys.executable,
        str(MODULE / "scripts" / "gateway.py"),
        "run",
        "--request",
        str(request_path),
        "--adapter",
        str(descriptor_path),
        "--repo",
        str(REPO),
        "--output",
        str(output),
        "--receipt-id",
        receipt_id,
    ]
    if descriptor["host_id"] == "fixture-host":
        argv.append("--allow-fixture-adapter")
    return subprocess.run(
        argv,
        cwd=str(MODULE),
        env=gateway_env(),
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_MS / 1000 + 120,
        check=False,
    )


def verify_run(
    output: Path,
    request: dict[str, Any],
    descriptor: dict[str, Any],
    receipt_override: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Verify one executed run's bytes; raise LaneError on the first defect."""
    host_id = descriptor["host_id"]
    markers = [
        check_contract(request, "worker-request.schema.json", "request", host_id),
        check_contract(
            descriptor, "adapter-descriptor.schema.json", "descriptor", host_id
        ),
    ]
    if load_json(output / "adapter.json") != descriptor:
        raise LaneError("gateway recorded a different adapter descriptor")
    receipt = receipt_override or load_json(output / "receipt.json")
    schema_check(receipt, "worker-receipt.schema.json", "receipt")
    validate_receipt(receipt, request, descriptor)

    events_path = output / "events.jsonl"
    if not events_path.is_file():
        raise LaneError("run produced no event stream")
    lines = [
        line for line in events_path.read_text("utf-8").splitlines() if line.strip()
    ]
    events = []
    for index, line in enumerate(lines):
        value = json.loads(line)
        schema_check(value, "worker-event.schema.json", f"event[{index}]")
        events.append(validate_event(value, request, descriptor, index))
    if not events or events[-1]["kind"] != "PROCESS_EXIT":
        raise LaneError("event stream lacks a terminal PROCESS_EXIT")

    # The frozen receipt validator never re-reads the event stream, so a
    # fabricated trace digest survives it. This is where that dies.
    if receipt["trace"]["event_count"] != len(events):
        raise LaneError("receipt event_count disagrees with the event stream")
    if receipt["trace"]["events_digest"] != file_digest(events_path):
        raise LaneError("receipt events_digest does not match the recorded events")
    if receipt["process"]["exit_code"] != events[-1]["payload"]["exit_code"]:
        raise LaneError("receipt exit code disagrees with the terminal event")
    if receipt["executed"] is not True:
        raise LaneError("receipt reports no execution")
    if receipt["cleanup"]["state"] != "PASS" or receipt["cleanup"]["residue_paths"]:
        raise LaneError(f"cleanup was not clean: {receipt['cleanup']}")
    return receipt, markers


def observe_cleanup() -> str:
    """Prune worktree metadata and assert no gateway lease survived the run."""
    git_out(REPO, "worktree", "prune")
    paths = [
        line.split(" ", 1)[1]
        for line in git_out(REPO, "worktree", "list", "--porcelain").splitlines()
        if line.startswith("worktree ")
    ]
    # The gateway leases into a temp root named `loopx-worker-<host>.<random>`.
    residue = [
        path
        for path in paths
        if any(
            part.startswith("loopx-worker-") and "." in part
            for part in Path(path).parts
        )
    ]
    if residue:
        raise LaneError(f"gateway worktree lease survived cleanup: {residue}")
    return f"pruned; {len(paths)} worktrees registered, none leased by the gateway"


def subject() -> tuple[str, str]:
    return git_out(REPO, "rev-parse", "HEAD"), git_out(REPO, "rev-parse", "HEAD^{tree}")


def preflight(request: dict[str, Any], descriptor: dict[str, Any]) -> list[str]:
    """Check everything a run needs before the run is allowed to cost anything."""
    host_id = descriptor["host_id"]
    markers = [
        check_contract(request, "worker-request.schema.json", "request", host_id),
        check_contract(
            descriptor, "adapter-descriptor.schema.json", "descriptor", host_id
        ),
    ]
    entry = MODULE / descriptor["adapter_entry"]
    if not entry.is_file():
        raise LaneError(f"adapter entry is absent: {descriptor['adapter_entry']}")
    if descriptor["implementation_state"] != "IMPLEMENTED":
        raise LaneError(
            f"adapter is {descriptor['implementation_state']}; the gateway will not execute it"
        )
    return markers


def load_descriptor(name: str) -> dict[str, Any]:
    descriptor = load_json(LIVE / "adapters" / f"{name}.json")
    return validate_adapter(descriptor, allow_fixture=name == "fixture-host")


def execute_lane(
    host_id: str,
    request_id: str,
    receipt_id: str,
    output: Path,
    scratch: Path,
) -> dict[str, Any]:
    commit, tree = subject()
    descriptor = load_descriptor(host_id)
    request = build_request(request_id, host_id, commit, tree)
    validate_request(request, {descriptor["adapter_id"]: descriptor})
    # Bind the contracts before spending the run, not after: a schema defect
    # found in the receipt has already cost the turn it was meant to protect.
    preflight(request, descriptor)
    result = run_gateway(request, descriptor, scratch, output, receipt_id)
    if result.returncode != OK:
        raise LaneError(
            f"gateway exit={result.returncode}; "
            f"stdout={result.stdout[-400:]!r}; stderr={result.stderr[-400:]!r}"
        )
    receipt, markers = verify_run(output, request, descriptor)
    if receipt["status"] != "PASS":
        raise LaneError(f"receipt status is {receipt['status']}")
    cleanup = observe_cleanup()
    lane = {
        "schema": LANE_SCHEMA,
        "mode": "DRY_RUN_STUB_CARRIER"
        if host_id == "fixture-host"
        else "LIVE_CLAUDE_CODE",
        "carrier_launched_host_binary": descriptor["binary"],
        "host_id": host_id,
        "adapter_descriptor_digest": descriptor["content_digest"],
        "subject": {"repository": REPOSITORY, "commit": commit, "tree": tree},
        "gateway_exit_code": result.returncode,
        "contract_markers": markers,
        "receipt_binary_identity": receipt["adapter"]["binary_identity"],
        "receipt_path": str((output / "receipt.json").relative_to(REPO)),
        "cleanup_observation": cleanup,
        "observed_at": now_utc(),
        "non_claims": list(NON_CLAIMS),
    }
    write_json_atomic(output / "lane.json", lane)
    return lane


def expect_red(action, label: str) -> str:
    try:
        action()
    except (LaneError, ContractError) as exc:
        return f"{label}: RED ({str(exc)[:110]})"
    raise LaneError(f"planted control did not go RED: {label}")


def planted_descriptor(base: dict[str, Any]) -> dict[str, Any]:
    plant = copy.deepcopy(base)
    plant["adapter_entry"] = "live/selftest_plants.py"
    return with_digest(plant)


def selftest() -> int:
    commit, tree = subject()
    stub = load_descriptor("fixture-host")
    lines: list[str] = []
    with tempfile.TemporaryDirectory(prefix="loopx-91-selftest.") as temporary:
        scratch = Path(temporary)
        baseline_output = scratch / "baseline"
        baseline_request = build_request(
            "issue-91-selftest-baseline", "fixture-host", commit, tree
        )
        validate_request(baseline_request, {stub["adapter_id"]: stub})
        result = run_gateway(
            baseline_request,
            stub,
            scratch,
            baseline_output,
            "issue-91-selftest-baseline",
        )
        if result.returncode != OK:
            raise LaneError(
                f"selftest baseline is not green: exit={result.returncode}; "
                f"stderr={result.stderr[-400:]!r}"
            )
        baseline, markers = verify_run(baseline_output, baseline_request, stub)
        observe_cleanup()
        lines.append(f"baseline: stub carrier PASS ({', '.join(markers)})")

        wrong = build_request("issue-91-control-subject", "fixture-host", commit, tree)
        wrong["subject"]["commit"] = git_out(REPO, "rev-parse", "HEAD~1")
        wrong = with_digest(wrong)
        lines.append(
            expect_red(
                lambda: run_or_raise(
                    wrong,
                    stub,
                    scratch,
                    scratch / "control-subject",
                    "issue-91-control-subject",
                ),
                "wrong-subject",
            )
        )
        observe_cleanup()

        plant = planted_descriptor(stub)
        dirty = build_request("issue-91-control-dirty", "fixture-host", commit, tree)
        lines.append(
            expect_red(
                lambda: run_or_raise(
                    dirty,
                    plant,
                    scratch,
                    scratch / "control-dirty",
                    "issue-91-control-dirty",
                ),
                "dirty-worktree",
            )
        )
        observe_cleanup()

        missing = copy.deepcopy(baseline)
        missing.pop("cleanup")
        lines.append(
            expect_red(
                lambda: verify_run(baseline_output, baseline_request, stub, missing),
                "missing-receipt-field",
            )
        )

        fabricated = copy.deepcopy(baseline)
        fabricated["trace"]["events_digest"] = "sha256:" + "0" * 64
        fabricated = with_digest(fabricated)
        lines.append(
            expect_red(
                lambda: verify_run(baseline_output, baseline_request, stub, fabricated),
                "fabricated-event-digest",
            )
        )

    # Dry-run of the live subject itself: everything the admitted turn needs
    # except the launch, so a shape defect cannot cost that single turn.
    host = load_descriptor("claude-code")
    request = build_request("issue-91-live-turn", "claude-code", commit, tree)
    validate_request(request, {host["adapter_id"]: host})
    binary = shutil.which(host["binary"], path=gateway_env()["PATH"])
    lines.append(
        f"live subject: {', '.join(preflight(request, host))}, "
        f"{host['binary']}={binary or 'ABSENT_ON_PATH'} (not launched)"
    )
    for line in lines:
        print(f"  {line}")
    print(
        "issue-91 live lane selftest PASS: 1 stub baseline, 4 planted controls RED, "
        "1 live subject preflight"
    )
    return OK


def run_or_raise(
    request: dict[str, Any],
    descriptor: dict[str, Any],
    scratch: Path,
    output: Path,
    receipt_id: str,
) -> None:
    result = run_gateway(request, descriptor, scratch, output, receipt_id)
    if result.returncode != OK:
        raise LaneError(
            f"gateway exit={result.returncode}: {(result.stdout + result.stderr).strip()[-160:]}"
        )
    verify_run(output, request, descriptor)


def dry_run() -> int:
    output = (
        RECEIPTS
        / "dry-run"
        / dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    with tempfile.TemporaryDirectory(prefix="loopx-91-dry-run.") as temporary:
        lane = execute_lane(
            "fixture-host",
            "issue-91-dry-run",
            "issue-91-dry-run-receipt",
            output,
            Path(temporary),
        )
    print(json.dumps(lane, ensure_ascii=False, indent=2, sort_keys=True))
    print(f"issue-91 live lane dry-run PASS: stub carrier receipt at {output}")
    return OK


def live() -> int:
    if LIVE_OUTPUT.exists():
        raise LaneError(
            f"{LIVE_OUTPUT} already exists; the admitted turn is single-shot and its "
            "receipt is frozen evidence"
        )
    if shutil.which("claude", path=gateway_env()["PATH"]) is None:
        raise LaneError("host binary 'claude' is not on the gateway PATH")
    with tempfile.TemporaryDirectory(prefix="loopx-91-live.") as temporary:
        lane = execute_lane(
            "claude-code",
            "issue-91-live-turn",
            "issue-91-live-turn-receipt",
            LIVE_OUTPUT,
            Path(temporary),
        )
    print(json.dumps(lane, ensure_ascii=False, indent=2, sort_keys=True))
    print(f"issue-91 live lane LIVE observation recorded at {LIVE_OUTPUT}")
    return OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--selftest", action="store_true")
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    if Draft202012Validator is None:
        print(
            "FATAL: python module 'jsonschema' is required to validate receipts "
            "against the frozen contracts",
            file=sys.stderr,
        )
        return USAGE
    try:
        if args.selftest:
            return selftest()
        if args.dry_run:
            return dry_run()
        return live()
    except (LaneError, ContractError) as exc:
        print(f"issue-91 live lane RED: {exc}", file=sys.stderr)
        return BAD
    except (OSError, json.JSONDecodeError, subprocess.TimeoutExpired) as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return USAGE


if __name__ == "__main__":
    raise SystemExit(main())
