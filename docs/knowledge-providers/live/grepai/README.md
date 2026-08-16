# GrepAI live canary

This terminal executes GrepAI against a disposable exact-subject snapshot and
a loopback-only Ollama embedder. It proves one bounded semantic candidate query;
it does not prove complete code coverage, exact symbol identity, provider
activation, or release fitness.

## State machine

```text
DECLARED
  -> SUBJECT_BOUND
  -> EXECUTABLE_AND_SBOM_CHECKED
  -> LOOPBACK_MODEL_CHECKED
  -> DISPOSABLE_INDEX_BUILT
  -> MCP_OBSERVED
  -> SOURCE_READ_BACK
  -> CONTROLS_PASS
  -> CLEANED
  -> CANDIDATE_ONLY

missing executable/model/source/receipt             -> ABSENT
identity, subject, result, bound, or cleanup failure -> FAIL
manifest/source/adapter identity drift               -> BLOCKED_POLICY
```

Only `scripts/providers/grepai_canary.py` owns these transitions. GrepAI may
suggest candidate anchors but cannot establish call edges, prove code absence,
write canonical task state, waive a Gate, activate itself, or promote a release.

## Data flow

```text
committed coverage files + workload identity
  -> digest-bound temporary project
  -> fixed local Ollama model + disposable GOB index
  -> foreground watcher + stdio MCP server
  -> bounded semantic candidate query
  -> direct current-source readback
  -> stale/wrong-subject controls
  -> bounded receipt + process-group cleanup
```

The wrapper supplies an isolated `HOME`, XDG configuration/state roots, and
project `.grepai/config.yaml`. It never reads or mutates the user's existing
`.grepai` index. Network scope is limited to `localhost:11434`; external network,
secrets, and external spend are denied. Coverage is deliberately incomplete, so
a miss remains `UNKNOWN`.

## Commands and evidence ceiling

CI-safe contract and mutation checks:

```sh
python3 scripts/providers/grepai_canary.py check
python3 scripts/providers/grepai_canary.py --selftest
```

Local live execution on a clean committed subject with the pinned Ollama model:

```sh
python3 scripts/providers/grepai_canary.py live \
  --output data/provider-canaries/grepai/<commit>.json
```

The pinned workload is `.runtime-env/workloads/provider-grepai.json`. A live
PASS remains `CANDIDATE_ONLY`. Until the repository provider manifest binds the
same source commit and executable digest as `PINNED`, admission is recorded as
`BLOCKED_POLICY`.

## Primary sources

- GrepAI v0.30.0 release: <https://github.com/yoanbernabeu/grepai/releases/tag/v0.30.0>
- GrepAI source subject: <https://github.com/yoanbernabeu/grepai/commit/176ff9dbd091345b6e8b2afd4d79664b4aa17194>
- GrepAI MIT license: <https://github.com/yoanbernabeu/grepai/blob/main/LICENSE>

The installed Homebrew SPDX document, executable bytes, local model inventory,
MCP results, and receipts are runtime evidence for the exact measured subject,
not universal upstream truth.
