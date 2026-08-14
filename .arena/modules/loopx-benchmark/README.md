# `loopx-benchmark` module

`loopx-benchmark` owns the measurement and claim contract under [`../../../loop_wiki/loopx-benchmark/`](../../../loop_wiki/loopx-benchmark/), with receipts in [`../../../data/benchmarks/`](../../../data/benchmarks/).

## Capabilities

```text
loopx.benchmark/v1
loopx.claim-verdict/v1
```

Required capabilities:

```text
loopx.contracts/v1
arena.proof-kernel/v1
```

Answers issue #100. Intentionally not selected in the shared `bettor-arena` composition by this leaf.

## Public control port

```sh
python3 loop_wiki/loopx-benchmark/scripts/loopxbench.py \
  <check|selftest|synthetic|measure|verdict>
```

Exit `0` ok, `2` a checked invariant disagreed, `64` unusable input.

There is no `promote` subcommand. Claim promotion is Human Admit.

## Boundaries

- **Every trial is retained**, including `FAILED`, `TIMEOUT` and `OOM`. A mean over the runs that finished is a different statistic wearing the same name, and a timeout is the most interesting trial in the set. The report carries `success_rate` because that is the number a dropped trial actually moves — timeouts have no duration, so removing them leaves every percentile exactly where it was.
- **Below five successful trials, no timing statistic is derived at all**, and the report says why. That is the point at which a percentile is a single observation with a percentile's name on it.
- **A warm run and a cold run are never summarised together.** Mixed cache states withhold the summary; averaging them produces a speedup that belongs to neither.
- **The claim ladder is `CLAIM_UNVERIFIED → PROFILE_OBSERVED → CORROBORATED` and nothing climbs it on its own.** `CORROBORATED` needs *independent* profiles: running the same box twice raises confidence in the mean without widening what the mean is about.
- **A source-proposal or vendor number is never evidence.** `SOURCE_PROPOSAL` and `VENDOR_BENCHMARK` are refused by name, not scored low. A number in a document was measured somewhere, on hardware nobody here has, with software nobody here pinned.
- **A report pinned to `latest`, `main` or `nightly` cannot corroborate.** The thing measured can be replaced without the version string moving.
- **Profiles that disagree stay in the evidence list.** Reporting only the ones that agreed would be the same measurement with a different conclusion.
- **CI runs the synthetic lane, never the real one.** A duration from a shared runner whose neighbours nobody can see is a fact about that runner at that moment. The test runner asserts the report's locale is `SYNTHETIC`, so an edit that starts timing things in CI turns red rather than quietly producing a benchmark.
- `live_hardware_matrix_state` is `NOT_EXERCISED`: the six-host and local/cloud families need machines this repository does not have.

## A defect the first real receipt found

The first `measure` run reported a peak RSS of 0.14 MB for a process that plainly used more. `getrusage(RUSAGE_CHILDREN).ru_maxrss` is a **monotonic high-water mark** across every child ever reaped, so an after-minus-before delta reads ~0 for any trial smaller than a previous one — and a benchmark whose memory numbers collapse toward zero as it runs looks like a benchmark of something very efficient.

The measurement now reads that child's own rusage via `os.wait4`. The physical control runs a small process immediately after a 64 MB one and requires the small number to be non-trivial and strictly smaller; a probe that restores the delta turns it red.

## Evidence

```sh
sh loop_wiki/loopx-benchmark/tests/run-all.sh
```

Two schemas under a digest manifest, nineteen manifest mutations, nineteen positive properties, twenty planted controls, and nine physical controls on real subprocesses — a real timeout, a real non-zero exit, a real missing binary, a real 64 MB allocation measured against a tight two-sided bound, and the same real run summarised twice so the difference the retained failures make is a number on the page (0.75 honest, 1.00 cherry-picked, identical medians).
