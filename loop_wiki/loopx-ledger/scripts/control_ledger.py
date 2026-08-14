#!/usr/bin/env python3
"""Independent subprocess control for the public LoopX Ledger v1 CLI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Sequence

OK, BAD, USAGE = 0, 2, 64


class ControlFailure(RuntimeError):
    pass


def invoke(argv: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env={"PATH": str(Path(sys.executable).parent) + ":/usr/local/bin:/usr/bin:/bin"},
    )


def expect(
    result: subprocess.CompletedProcess[str],
    *,
    code: int,
    label: str,
    stdout_marker: str | None = None,
    stderr_marker: str | None = None,
) -> None:
    if result.returncode != code:
        raise ControlFailure(
            f"{label}: expected exit {code}, observed {result.returncode}; "
            f"stdout={result.stdout[-500:]!r}; stderr={result.stderr[-500:]!r}"
        )
    if stdout_marker is not None and stdout_marker not in result.stdout:
        raise ControlFailure(f"{label}: missing stdout marker {stdout_marker!r}")
    if stderr_marker is not None and stderr_marker not in result.stderr:
        raise ControlFailure(f"{label}: missing stderr marker {stderr_marker!r}")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ControlFailure(f"JSON root is not an object: {path}")
    return value


def write(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def receipt_status(path: Path, expected: str, label: str) -> None:
    receipt = load(path)
    if receipt.get("status") != expected or receipt.get("cleanup") != "PASS":
        raise ControlFailure(f"{label}: unexpected receipt status/cleanup")
    content = dict(receipt)
    observed = content.pop("content_digest", None)
    import hashlib

    canonical = json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected_digest = "sha256:" + hashlib.sha256(canonical).hexdigest()
    if observed != expected_digest:
        raise ControlFailure(f"{label}: receipt content digest mismatch")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="LoopX ledger module root",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    ledger = root / "scripts" / "ledger.py"
    checker = root / "scripts" / "check_contracts.py"
    fixtures = root / "tests" / "fixtures" / "good"
    if not ledger.is_file() or not checker.is_file() or not fixtures.is_dir():
        print("FATAL: ledger public port or fixtures are absent", file=sys.stderr)
        return USAGE

    try:
        with tempfile.TemporaryDirectory(prefix="loopx-ledger-control.") as temporary:
            temp = Path(temporary)
            contract_check = invoke([sys.executable, str(checker), "--root", str(root)], root)
            expect(
                contract_check,
                code=OK,
                label="contract check",
                stdout_marker="loopx-ledger-contracts PASS:",
            )
            selftest = invoke([sys.executable, str(ledger), "selftest", "--root", str(root)], root)
            expect(
                selftest,
                code=OK,
                label="ledger selftest",
                stdout_marker="loopx-ledger selftest PASS:",
            )

            store = temp / "store"
            init_receipt = temp / "init-receipt.json"
            result = invoke(
                [
                    sys.executable,
                    str(ledger),
                    "init",
                    "--contract",
                    str(fixtures / "contract.json"),
                    "--store",
                    str(store),
                    "--created-at",
                    "2026-08-14T00:00:00Z",
                    "--receipt",
                    str(init_receipt),
                    "--operation-id",
                    "control-init",
                ],
                root,
            )
            expect(result, code=OK, label="init")
            receipt_status(init_receipt, "PASS", "init")

            event_paths = sorted((fixtures / "events").glob("*.json"))
            if not event_paths:
                raise ControlFailure("positive event fixtures are absent")
            last_request: Path | None = None
            for revision, event_path in enumerate(event_paths):
                request = temp / f"request-{revision}.json"
                write(
                    request,
                    {
                        "schema_version": "loopx/append-request/v1",
                        "request_id": f"control-request-{revision}",
                        "expected_state_revision": revision,
                        "event": load(event_path),
                    },
                )
                receipt = temp / f"append-{revision}.json"
                result = invoke(
                    [
                        sys.executable,
                        str(ledger),
                        "append",
                        "--store",
                        str(store),
                        "--request",
                        str(request),
                        "--receipt",
                        str(receipt),
                        "--operation-id",
                        f"control-append-{revision}",
                    ],
                    root,
                )
                expect(result, code=OK, label=f"append {revision}")
                receipt_status(receipt, "PASS", f"append {revision}")
                last_request = request

            verify_receipt = temp / "verify.json"
            result = invoke(
                [
                    sys.executable,
                    str(ledger),
                    "verify",
                    "--store",
                    str(store),
                    "--receipt",
                    str(verify_receipt),
                    "--operation-id",
                    "control-verify",
                ],
                root,
            )
            expect(result, code=OK, label="verify")
            receipt_status(verify_receipt, "PASS", "verify")

            replay_output = temp / "replay.json"
            replay_receipt = temp / "replay-receipt.json"
            result = invoke(
                [
                    sys.executable,
                    str(ledger),
                    "replay",
                    "--store",
                    str(store),
                    "--snapshot-out",
                    str(replay_output),
                    "--receipt",
                    str(replay_receipt),
                    "--operation-id",
                    "control-replay",
                ],
                root,
            )
            expect(result, code=OK, label="replay")
            receipt_status(replay_receipt, "PASS", "replay")
            if replay_output.read_bytes() != (fixtures / "expected-snapshot.json").read_bytes():
                raise ControlFailure("replay does not match checked positive snapshot bytes")

            assert last_request is not None
            duplicate_receipt = temp / "duplicate.json"
            result = invoke(
                [
                    sys.executable,
                    str(ledger),
                    "append",
                    "--store",
                    str(store),
                    "--request",
                    str(last_request),
                    "--receipt",
                    str(duplicate_receipt),
                    "--operation-id",
                    "control-duplicate",
                ],
                root,
            )
            expect(result, code=OK, label="duplicate append")
            receipt_status(duplicate_receipt, "NOOP", "duplicate append")

            tampered = temp / "tampered"
            shutil.copytree(store, tampered)
            lines = (tampered / "events.jsonl").read_text(encoding="utf-8").splitlines()
            event = json.loads(lines[3])
            event["event_digest"] = "sha256:" + "0" * 64
            lines[3] = json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            (tampered / "events.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
            result = invoke(
                [
                    sys.executable,
                    str(ledger),
                    "verify",
                    "--store",
                    str(tampered),
                    "--receipt",
                    str(temp / "tampered-receipt.json"),
                    "--operation-id",
                    "control-tampered",
                ],
                root,
            )
            expect(
                result,
                code=BAD,
                label="tampered ledger",
                stderr_marker="loopx-ledger RED:",
            )

            result = invoke(
                [
                    sys.executable,
                    str(ledger),
                    "append",
                    "--store",
                    str(store),
                    "--request",
                    str(temp / "ABSENT.json"),
                    "--receipt",
                    str(temp / "missing-receipt.json"),
                    "--operation-id",
                    "control-missing",
                ],
                root,
            )
            expect(result, code=USAGE, label="missing input", stderr_marker="FATAL:")

            result = invoke([sys.executable, str(ledger), "append", "--store", str(store)], root)
            expect(result, code=USAGE, label="invalid invocation", stderr_marker="FATAL:")

            print(
                "loopx-ledger control PASS: "
                "init/append/verify/replay=0 duplicate=NOOP tamper=2 missing=64 invocation=64"
            )
            return OK
    except subprocess.TimeoutExpired as exc:
        print(f"FATAL: control timed out: {exc}", file=sys.stderr)
        return USAGE
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FATAL: control runtime/input error: {exc}", file=sys.stderr)
        return USAGE
    except ControlFailure as exc:
        print(f"loopx-ledger control RED: {exc}", file=sys.stderr)
        return BAD


if __name__ == "__main__":
    raise SystemExit(main())
