# Serena live canary

This terminal executes Serena against a disposable, exact-subject coverage
snapshot. It proves a bounded read-only MCP interaction for one committed
repository subject; it does not prove full-repository coverage, provider
activation, or release fitness.

## State machine

```text
DECLARED
  -> SUBJECT_BOUND
  -> IDENTITY_CHECKED
  -> DISPOSABLE_INDEX_BUILT
  -> MCP_OBSERVED
  -> SOURCE_READ_BACK
  -> CONTROLS_PASS
  -> CLEANED
  -> CANDIDATE_ONLY

any missing executable/source/receipt              -> ABSENT
identity, subject, tool, result, bound, or cleanup -> FAIL
manifest/source/adapter identity drift             -> BLOCKED_POLICY
```

Only `scripts/providers/serena_canary.py` owns these transitions. Serena may
return candidate symbol observations but cannot write canonical task state,
mark a Gate green, activate itself, or promote a release.

## Data flow

```text
committed coverage files + workload identity
  -> digest-bound temporary project
  -> isolated SERENA_HOME + read-only project.yml
  -> fixed-argv indexer and stdio MCP server
  -> allowlisted symbol queries
  -> direct current-source readback
  -> stale/wrong-subject/unsupported-path controls
  -> bounded receipt + process-group cleanup
```

The coverage manifest is intentionally `complete: false`. A miss is therefore
`UNKNOWN`, never proof that a symbol or reference is absent from the repository.
The wrapper denies editing, shell, memory, dashboard, GUI, secrets, external
network, and external spend. It never reads the user's existing `.serena`
project or global Serena configuration.

## Commands and evidence ceiling

CI-safe contract and mutation checks:

```sh
python3 scripts/providers/serena_canary.py check
python3 scripts/providers/serena_canary.py --selftest
```

Local live execution on a clean committed subject:

```sh
python3 scripts/providers/serena_canary.py live \
  --output data/provider-canaries/serena/<commit>.json
```

The pinned workload is `.runtime-env/workloads/provider-serena.json`. A live
PASS remains `CANDIDATE_ONLY`. Until the repository provider manifest binds the
same source commit and executable digest as `PINNED`, admission is recorded as
`BLOCKED_POLICY` rather than silently inferred.

## Primary sources

- Serena source subject: <https://github.com/oraios/serena/commit/414f591d58967e2fd29c5c6a5f8e58cb03b77eee>
- Serena MIT license: <https://github.com/oraios/serena/blob/main/LICENSE>

Local package metadata, executable bytes, MCP responses, and receipts are
runtime evidence for their exact measured subject, not universal upstream
truth.
