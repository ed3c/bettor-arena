#!/usr/bin/env python3
"""Execute a workload and keep every trial, including the ones that went wrong.

The measurement loop is small and the discipline is all in what it refuses to
throw away. A trial that timed out is a trial: it goes into the list with
`outcome: TIMEOUT` and a null wall time, it counts toward the declared
repetitions, and it is exactly the observation a mean would have removed.

Warmup runs are executed and **discarded by name**: they are not in the trial
list and the count of them is on the record. A warmup silently folded into the
sample is a cold run averaged with warm ones; a warmup silently skipped is a cold
run reported as warm. Both are invisible in the summary.

Peak RSS comes from `os.wait4`, which reports the rusage of *that* child. The
obvious alternative -- `getrusage(RUSAGE_CHILDREN)` before and after -- is wrong
in a way that reads as a great result: that counter is a monotonic high-water
mark across every child the process has ever reaped, so the difference is zero
for any trial smaller than a previous one. A benchmark whose memory numbers
collapse toward zero as it runs looks like a benchmark of something very
efficient.

`synthetic` exists so CI can prove this pipeline works without publishing a
timing number from a shared runner. It emits fixed values and a locale of
SYNTHETIC, which `bm_claim` excludes from corroboration by name.
"""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time
from typing import Any

from bm_common import SYNTHETIC_LOCALE, ContractError, non_empty_str

# ru_maxrss is bytes on macOS and kilobytes on Linux. Above this, the value can
# only be bytes: a process whose peak RSS was genuinely 10 GB is not one of the
# subprocesses this benchmark runs, and reading bytes as kilobytes would divide
# every memory number by 1024 -- which puts any threshold claim comfortably under
# its threshold with nothing about the number looking wrong.
BYTES_THRESHOLD = 10_000_000

# How often the wait loop wakes. Small enough that a timeout is a timeout rather
# than a rounding, large enough not to be a spin.
POLL_S = 0.005


def rss_mb_from_rusage(raw: float) -> float:
    """Convert a ru_maxrss value to MB, choosing the unit by magnitude.

    Pure, and separate from the measurement, so both branches can be exercised on
    a machine that only ever produces one of them. The branch this platform does
    not take is the one a bound check on a real process can never reach.
    """
    if raw < 0:
        raise ContractError("ru_maxrss cannot be negative")
    return raw / (1024 * 1024) if raw > BYTES_THRESHOLD else raw / 1024


def run_trial(
    command: list[str], index: int, timeout_s: float, cache_state: str
) -> dict[str, Any]:
    """One trial. Every way it can end is a recorded outcome.

    Output goes to temporary files rather than pipes. A pipe that fills while
    nobody is reading it blocks the child, and the harness would record that as
    the workload being slow.
    """

    def outcome(
        state: str, detail: str, wall: float | None = None, rss: float | None = None
    ):
        return {
            "index": index,
            "outcome": state,
            "wall_ms": wall,
            "peak_rss_mb": rss,
            "cache_state": cache_state,
            "detail": detail,
        }

    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        started = time.monotonic()
        try:
            proc = subprocess.Popen(command, stdout=out, stderr=err)
        except OSError as exc:
            return outcome("FAILED", f"could not execute: {exc}")

        deadline = started + timeout_s
        timed_out = False
        while True:
            try:
                pid, status, usage = os.wait4(proc.pid, os.WNOHANG)
            except ChildProcessError:
                # Already reaped by something else. Nothing measured, and saying
                # so beats reporting a duration with no rusage behind it.
                return outcome(
                    "FAILED", "the child was reaped before its rusage was read"
                )
            if pid != 0:
                break
            if time.monotonic() >= deadline:
                timed_out = True
                proc.kill()
                os.wait4(proc.pid, 0)
                break
            time.sleep(POLL_S)

        elapsed_ms = (time.monotonic() - started) * 1000.0
        # Popen must not try to reap a process os.wait4 already collected.
        proc.returncode = 0
        if timed_out:
            return outcome("TIMEOUT", f"exceeded {timeout_s}s")

        err.seek(0)
        stderr_text = err.read().decode("utf-8", "replace").strip()[:120]

    peak = rss_mb_from_rusage(usage.ru_maxrss)
    exited_ok = os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0
    if exited_ok:
        return outcome("OK", "", elapsed_ms, peak)

    killed = os.WIFSIGNALED(status) and os.WTERMSIG(status) in (signal.SIGKILL,)
    code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -os.WTERMSIG(status)
    # A non-zero exit is a FAILED trial that still took time. The duration is
    # kept in `detail` rather than in wall_ms: a failure's runtime is real, and
    # averaging it with the successes would be measuring how long it takes to
    # not work.
    return outcome(
        "OOM" if killed else "FAILED",
        f"exit {code} after {elapsed_ms:.1f}ms: {stderr_text}",
    )


def execute(
    workload: dict[str, Any], timeout_s: float = 30.0, cache_state: str = "COLD"
) -> dict[str, Any]:
    """Run warmup then the declared repetitions. Nothing is dropped silently."""
    command = workload["command"]
    if not isinstance(command, list) or not command:
        raise ContractError("workload.command must be the exact argv")
    non_empty_str(workload["name"], "workload.name")

    warmup = workload["warmup"]
    for index in range(warmup):
        run_trial(command, index, timeout_s, cache_state)

    trials = [
        run_trial(command, index, timeout_s, cache_state)
        for index in range(workload["repetitions"])
    ]
    return {
        "trials": trials,
        # On the record, both of them. A warmup folded into the sample is a cold
        # run averaged with warm ones; a warmup skipped is a cold run reported as
        # warm, and neither is visible in a summary.
        "warmup_runs_discarded": warmup,
        "cache_state": cache_state,
    }


SYNTHETIC_ENVIRONMENT = {
    "os": "synthetic",
    "arch": "synthetic",
    "cpu": "synthetic",
    "ram_gb": 1,
    "runtime": "synthetic",
    "image": "synthetic@v1",
    "locale": SYNTHETIC_LOCALE,
}


def synthetic(workload: dict[str, Any]) -> dict[str, Any]:
    """Deterministic trials with no timing meaning at all.

    CI needs to prove that the pipeline runs -- that trials are validated, that
    failures are retained, that a summary is derived and gated. It must not
    publish a duration measured on a shared runner whose neighbours nobody can
    see. So these numbers are fixed, they are the same on every machine, and the
    locale says so loudly enough that bm_claim drops them by name.
    """
    pattern = [100.0, 105.0, 110.0, 115.0, 120.0, 125.0]
    trials = []
    for index in range(workload["repetitions"]):
        # One deliberate failure, always. A synthetic run whose trials all pass
        # would exercise the pipeline without ever exercising the part that keeps
        # failures in the count.
        if index == 2:
            trials.append(
                {
                    "index": index,
                    "outcome": "TIMEOUT",
                    "wall_ms": None,
                    "peak_rss_mb": None,
                    "cache_state": "COLD",
                    "detail": "synthetic timeout, retained on purpose",
                }
            )
            continue
        trials.append(
            {
                "index": index,
                "outcome": "OK",
                "wall_ms": pattern[index % len(pattern)],
                "peak_rss_mb": 12.0 + (index % 3),
                "cache_state": "COLD",
                "detail": "",
            }
        )
    return {
        "trials": trials,
        "warmup_runs_discarded": workload["warmup"],
        "cache_state": "COLD",
    }
