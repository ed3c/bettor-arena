# Context Capsule manifests

Each JSON file defines the native passive context and working directory for one loop or aggregate surface. [`../contexts.lock.json`](../contexts.lock.json) freezes the exact tracked bytes.

Context materialization is not “concatenate a prompt”:

```text
resolve immutable subject
→ materialize root + loop native files
→ verify/freeze context digest
→ set the declared working directory
→ launch an allowlisted Claude/Codex adapter
→ validate the typed response
```

Commands:

```sh
python3 scripts/arena_context.py check
python3 scripts/arena_context.py lock
python3 scripts/arena_context.py parity
```

A missing carrier or unavailable host CLI is `NOT_EXERCISED`/FATAL according to the command contract, never PASS.
