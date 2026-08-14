#!/usr/bin/env python3
"""Physical control group: a real workload, really run, really failing sometimes.

Every number in the selftest is one this file wrote. That proves the arithmetic
and nothing about the measurement, and the measurement is where the interesting
failures live -- a trial that timed out has to actually be a timeout, a peak RSS
has to come from a process, and a workload that cannot be executed at all has to
land as FAILED rather than as a shorter list.

So this group runs real subprocesses:

  * a command that succeeds, timed, with peak RSS read from the OS;
  * a command that sleeps past its timeout, which must land as TIMEOUT with a
    null wall time rather than as a very slow success;
  * a command that exits non-zero, which must land as FAILED;
  * a command that does not exist, which must land as FAILED and not raise;
  * a real allocation of a known size, checked against the RSS this module
    reports -- because the units of ru_maxrss differ by platform, and a silent
    factor-of-1024 would land a memory claim comfortably under any threshold;
  * the same run summarised twice, once with the failures and once without, so
    the difference the retained failures make is a number on this page.

Exits 0 or 2.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bm_common import BAD, OK, ContractError  # noqa: E402
from bm_report import summarize  # noqa: E402
from bm_run import execute, rss_mb_from_rusage, run_trial  # noqa: E402
from bm_selftest import IDENTITIES, SUBJECT  # noqa: E402
from loopxbench import local_environment  # noqa: E402

WORKLOAD = {
    "family": "gate_startup_and_execution",
    "name": "physical-control-probe",
    "seed": 1,
    "repetitions": 6,
    "warmup": 1,
    "stopping_rule": "fixed repetitions; no early stop on a favourable trial",
    "command": [sys.executable, "-c", "pass"],
}

# ~64 MB, allocated and touched so the pages are real rather than reserved.
ALLOCATE = "b = bytearray(64 * 1024 * 1024)\nb[::4096] = b'x' * (len(b) // 4096)\n"


def main() -> int:
    checks = 0

    # 1. A command that really runs.
    trial = run_trial([sys.executable, "-c", "pass"], 0, 30.0, "COLD")
    if trial["outcome"] != "OK" or trial["wall_ms"] is None or trial["wall_ms"] <= 0:
        raise ContractError(f"a working command produced {trial}")
    checks += 1

    # 2. A command that really exceeds its timeout. TIMEOUT, with no wall time --
    #    a duration here would be the timeout value wearing a measurement's name.
    slow = run_trial(
        [sys.executable, "-c", "import time; time.sleep(5)"], 1, 0.4, "COLD"
    )
    if slow["outcome"] != "TIMEOUT" or slow["wall_ms"] is not None:
        raise ContractError(f"a command that ran past its timeout produced {slow}")
    if "0.4" not in slow["detail"]:
        raise ContractError("the timeout trial did not record the limit it exceeded")
    checks += 1

    # 3. A command that really fails.
    broken = run_trial([sys.executable, "-c", "raise SystemExit(3)"], 2, 30.0, "COLD")
    if broken["outcome"] != "FAILED" or broken["wall_ms"] is not None:
        raise ContractError(f"a failing command produced {broken}")
    checks += 1

    # 4. A command that cannot be executed at all. FAILED, not an exception --
    #    an exception here would abort the run and lose every trial before it,
    #    so the raise is caught and reported rather than allowed to propagate.
    try:
        missing = run_trial(["/nonexistent/binary/probe"], 3, 30.0, "COLD")
    except OSError as exc:
        raise ContractError(
            f"an absent binary raised {exc!r} instead of landing as a FAILED trial; "
            "the raise would abort the run and lose every trial before it"
        ) from exc
    if missing["outcome"] != "FAILED" or "could not execute" not in missing["detail"]:
        raise ContractError(f"an absent binary produced {missing}")
    checks += 1

    # 4b. Both ru_maxrss units, on a machine that only ever produces one of them.
    #     The branch this platform does not take is the one the bound check below
    #     can never reach, and it is the one that divides every memory number by
    #     1024.
    if abs(rss_mb_from_rusage(64 * 1024) - 64.0) > 0.01:
        raise ContractError("a kilobyte ru_maxrss did not convert to MB")
    if abs(rss_mb_from_rusage(64 * 1024 * 1024) - 64.0) > 0.01:
        raise ContractError("a byte ru_maxrss did not convert to MB")
    if rss_mb_from_rusage(64 * 1024) != rss_mb_from_rusage(64 * 1024 * 1024):
        raise ContractError(
            "the two ru_maxrss units disagree about the same 64 MB; one of the branches "
            "is off by a factor of 1024, and that factor puts any memory claim under "
            "any threshold"
        )
    checks += 1

    # 5. A real allocation of a known size, measured. The bound is tight on both
    #    sides: too low catches the wrong unit, too high catches a number that is
    #    not this child's.
    fat = run_trial([sys.executable, "-c", ALLOCATE], 4, 60.0, "COLD")
    if fat["outcome"] != "OK":
        raise ContractError(f"the allocation probe did not run: {fat['detail']}")
    if not 48 <= fat["peak_rss_mb"] <= 512:
        raise ContractError(
            f"a process that touched 64 MB reported {fat['peak_rss_mb']:.1f} MB peak RSS. "
            "ru_maxrss is bytes on some platforms and kilobytes on others, and the wrong "
            "unit puts every memory claim under its threshold"
        )
    checks += 1

    # 5b. A small process run immediately after the large one. This is the check
    #     the obvious implementation fails: getrusage(RUSAGE_CHILDREN) is a
    #     monotonic high-water mark across every child ever reaped, so an
    #     after-minus-before delta reports ~0 here -- and a benchmark whose memory
    #     numbers collapse toward zero as it runs looks like a benchmark of
    #     something very efficient.
    thin = run_trial([sys.executable, "-c", "pass"], 5, 30.0, "COLD")
    if thin["outcome"] != "OK":
        raise ContractError(f"the small probe did not run: {thin['detail']}")
    if thin["peak_rss_mb"] < 1.0:
        raise ContractError(
            f"a Python interpreter that started at all reported {thin['peak_rss_mb']:.3f} MB "
            "after a 64 MB child. The measurement is a high-water-mark delta, not this "
            "child's rusage, and it reports near zero for every trial smaller than a "
            "previous one"
        )
    if thin["peak_rss_mb"] >= fat["peak_rss_mb"]:
        raise ContractError(
            f"an empty interpreter ({thin['peak_rss_mb']:.1f} MB) measured at least as much "
            f"as one that touched 64 MB ({fat['peak_rss_mb']:.1f} MB); the number is not "
            "per-child"
        )
    checks += 1

    # 6. A real run of the whole loop, with a real warmup discarded.
    result = execute(WORKLOAD, timeout_s=30.0, cache_state="COLD")
    if len(result["trials"]) != WORKLOAD["repetitions"]:
        raise ContractError(f"execute returned {len(result['trials'])} trials")
    if result["warmup_runs_discarded"] != WORKLOAD["warmup"]:
        raise ContractError("the discarded warmup count was not recorded")
    report = summarize(
        SUBJECT, local_environment(), IDENTITIES, WORKLOAD, result["trials"]
    )
    if report["ok_count"] != WORKLOAD["repetitions"]:
        raise ContractError(
            f"a trivially working command failed {report['failure_count']} times"
        )
    if report["timing_ms"] is None:
        raise ContractError(
            f"a full clean run withheld its summary: {report['summary_withheld']}"
        )
    checks += 1

    # 7. Plant two real failures in a real run, and measure what dropping them
    #    buys. The whole module rests on this difference being visible.
    mixed_workload = {**WORKLOAD, "repetitions": 8}
    trials = execute(mixed_workload, timeout_s=30.0, cache_state="COLD")["trials"]
    for index in (2, 5):
        trials[index] = run_trial(
            [sys.executable, "-c", "import time; time.sleep(5)"], index, 0.3, "COLD"
        )
    honest = summarize(SUBJECT, local_environment(), IDENTITIES, mixed_workload, trials)
    if honest["failure_count"] != 2 or honest["success_rate"] != 0.75:
        raise ContractError(
            f"two real timeouts produced failure_count={honest['failure_count']} "
            f"success_rate={honest['success_rate']}"
        )

    survivors = [t for t in trials if t["outcome"] == "OK"]
    cherry = summarize(
        SUBJECT,
        local_environment(),
        IDENTITIES,
        {**WORKLOAD, "repetitions": len(survivors)},
        [{**t, "index": i} for i, t in enumerate(survivors)],
    )
    if cherry["success_rate"] != 1.0 or cherry["failure_count"] != 0:
        raise ContractError("dropping the timeouts did not produce a perfect run")
    if honest["timing_ms"]["median"] != cherry["timing_ms"]["median"]:
        raise ContractError(
            "the medians differ, so this comparison is not isolating the thing it means "
            "to isolate"
        )
    checks += 1

    print(
        f"loopx-benchmark physical control PASS: {checks} controls on real subprocesses "
        f"(honest run {honest['success_rate']:.2f} success, cherry-picked "
        f"{cherry['success_rate']:.2f}, identical medians)"
    )
    return OK


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractError as exc:
        print(f"loopx-benchmark physical control RED: {exc}", file=sys.stderr)
        raise SystemExit(BAD) from exc
