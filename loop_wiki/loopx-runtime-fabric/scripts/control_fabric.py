#!/usr/bin/env python3
"""Physical control group. Real workspaces, real processes, real observations.

#66 asks for "at least one isolation control that physically turns red". A
fixture asserting that a rule exists does not answer that. So this file builds
actual temporary source trees, runs actual subprocesses, and checks what really
happened on disk afterwards.

The three physical controls:

1. a process that writes outside its declared writable paths is caught by the
   residue scan, and the receipt classifies POLICY_REFUSAL rather than PASS --
   even though the process itself exits 0;
2. a process that exceeds its timeout is killed with its children and does not
   leave the workspace behind;
3. a clean run leaves no residue and removes its workspace, so control 1's red
   is attributable to the write rather than to the harness being red always.

Control 3 is not decoration. Without it, a residue scanner that returned a
constant non-empty list would pass control 1 and prove nothing.

Exit: 0 all controls behaved, 2 one did not, 64 unusable environment.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fabric_common import BAD, OK, USAGE, ProviderUnavailable  # noqa: E402
from fabric_local import emit_receipt, execute  # noqa: E402
from fabric_lease import admit_lease  # noqa: E402

SUBJECT = {
    "repository": "ed3c/bettor-arena",
    "commit": "0" * 39 + "1",
    "tree": "0" * 39 + "2",
    "task_id": "fabric-physical-control",
}


def lease(lease_id: str, workspace_root: str) -> dict[str, Any]:
    return {
        "schema_version": "loopx/runtime-lease/v1",
        "lease_id": lease_id,
        "owner": "control-fabric",
        "subject": SUBJECT,
        "granted_at": "2026-08-15T10:00:00Z",
        "expires_at": "2026-08-15T11:00:00Z",
        "expected_state_revision": 0,
        "workspace_root": workspace_root,
        "provider_id": "local-process",
    }


def request(argv: list[str], request_id: str, expected: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "loopx/runtime-request/v1",
        "request_id": request_id,
        "subject": SUBJECT,
        "closure_digest": "sha256:" + "ab" * 32,
        "provider": {
            "provider_id": "local-process",
            "adapter_id": "local-disposable-workspace",
            "image_ref": None,
            "runtime_identity": "python3-local",
        },
        "workspace": {
            "lease_id": request_id,
            "read_only_paths": ["src"],
            "writable_paths": ["artifacts"],
            "cleanup": "REQUIRED",
        },
        "process": {
            "argv": argv,
            "timeout_ms": 5000,
            "process_group": True,
            "max_output_bytes": 65536,
            "max_memory_bytes": 268435456,
            "max_disk_bytes": 104857600,
        },
        # deny would be a claim this adapter cannot enforce, so it is not made.
        "network": {"requested": "inherit", "attested": "UNENFORCED", "allowlist": []},
        "environment": {"allowlist": ["PATH"], "secret_refs": []},
        "dependencies": {
            "cache_policy": "none",
            "cache_key": None,
            "contamination_check": True,
        },
        "artifacts": {"expected_paths": expected, "capture_root": "artifacts"},
    }


def build_source(root: Path, script: str) -> Path:
    source = root / "source"
    (source / "src").mkdir(parents=True, exist_ok=True)
    (source / "artifacts").mkdir(parents=True, exist_ok=True)
    (source / "src" / "input.txt").write_text("input\n", encoding="utf-8")
    (source / "src" / "run.py").write_text(script, encoding="utf-8")
    return source


CLEAN = """
import pathlib
pathlib.Path("artifacts/result.json").write_text('{"ok": true}\\n')
print("done")
"""

ESCAPES = """
import pathlib
pathlib.Path("artifacts/result.json").write_text('{"ok": true}\\n')
# Writes outside every declared writable path, then exits 0. The exit code
# cannot see this; the residue scan can.
pathlib.Path("src/sneaked.txt").write_text("this should not be here\\n")
print("done")
"""

SLEEPS = """
import time
time.sleep(30)
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.parse_args()

    failures: list[str] = []

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)

        # --- control 3 first: a clean run must be clean ---------------------
        source = build_source(base / "clean", CLEAN)
        req = request(
            [sys.executable, "src/run.py"], "clean-run", ["artifacts/result.json"]
        )
        try:
            observation = execute(source, req)
        except ProviderUnavailable as exc:
            print(f"fabric control FATAL: {exc}", file=sys.stderr)
            return USAGE
        receipt = emit_receipt(req, lease("clean-run", str(source)), observation)
        if receipt["outcome"] != "PASS":
            failures.append(
                f"clean run did not pass: outcome={receipt['outcome']}, "
                f"residue={observation['residue_paths']}, exit={observation['exit_code']}"
            )
        if observation["residue_paths"]:
            failures.append(
                "clean run reported residue; the scanner is red regardless of input, "
                "which would make the escape control meaningless"
            )
        if not observation["workspace_removed"]:
            failures.append("clean run left its workspace behind")

        # --- control 1: the escape, physically ------------------------------
        source = build_source(base / "escape", ESCAPES)
        req = request(
            [sys.executable, "src/run.py"], "escape-run", ["artifacts/result.json"]
        )
        observation = execute(source, req)
        receipt = emit_receipt(req, lease("escape-run", str(source)), observation)

        if observation["exit_code"] != 0:
            failures.append(
                "the escaping process was expected to exit 0; the point of this "
                "control is that the exit code cannot see the violation"
            )
        if "src/sneaked.txt" not in observation["residue_paths"]:
            failures.append(
                "residue scan did not find the file written outside the declared "
                f"writable paths; found {observation['residue_paths']}"
            )
        if receipt["outcome"] != "POLICY_REFUSAL":
            failures.append(
                f"a run that wrote outside its workspace was classified "
                f"{receipt['outcome']!r}; residue must outrank a zero exit code"
            )
        if not observation["workspace_removed"]:
            failures.append("escape run left its workspace behind")

        # --- control 2: timeout takes the process group with it -------------
        source = build_source(base / "timeout", SLEEPS)
        req = request([sys.executable, "src/run.py"], "timeout-run", [])
        req["process"]["timeout_ms"] = 400
        observation = execute(source, req)
        receipt = emit_receipt(req, lease("timeout-run", str(source)), observation)

        if not observation["timed_out"]:
            failures.append("the sleeping process was expected to time out")
        if receipt["outcome"] != "TASK_FAILURE":
            failures.append(
                f"a timeout was classified {receipt['outcome']!r}; a workload that ran "
                "out of time failed the task, it did not violate policy"
            )
        if not observation["workspace_removed"]:
            failures.append(
                "timeout left the workspace mounted; a killed Worker must not leave "
                "a directory nobody will release"
            )

    # --- lease admission, exercised through its real boundary --------------
    granted = lease("l-1", "/tmp/whatever")
    try:
        admit_lease(granted, "2026-08-15T10:30:00Z", 0)
    except Exception as exc:  # noqa: BLE001 - any refusal here is a failure
        failures.append(f"a valid lease was refused: {exc}")
    for label, now, revision, held in (
        ("expired lease", "2026-08-15T11:00:01Z", 0, None),
        ("stale revision", "2026-08-15T10:30:00Z", 3, None),
        ("double-held lease", "2026-08-15T10:30:00Z", 0, {"l-1"}),
    ):
        try:
            admit_lease(granted, now, revision, held)
        except Exception:
            continue
        failures.append(f"{label} was admitted")

    if failures:
        for line in failures:
            print(f"fabric control RED: {line}", file=sys.stderr)
        return BAD

    print(
        "loopx-runtime-fabric control PASS: clean=PASS escape=POLICY_REFUSAL "
        "(exit 0, residue found) timeout=TASK_FAILURE workspaces removed, "
        "3 lease refusals"
    )
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
