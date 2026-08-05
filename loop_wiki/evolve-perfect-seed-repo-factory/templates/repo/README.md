# Generated perfect-seed candidate

This repository is a bounded local reasoning seed. It preserves source identity,
evidence, claims, unknowns, decisions, a 20-call dependency graph, results, and
artifact lineage on disk.

Run:

```sh
bun install --frozen-lockfile
bun run quality:fast
bun run scripts/plan.ts --task "Describe the next bounded implementation action"
bun test
```

The result is a candidate. A green local run is not human seed admission and is
not equivalent to twenty independent LLM or external-tool calls.
