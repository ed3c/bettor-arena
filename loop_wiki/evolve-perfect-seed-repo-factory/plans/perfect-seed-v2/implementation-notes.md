# Implementation notes

## Policy

Append execution observations here only after a Work-Item is explicitly
admitted. Do not edit `plan-registry.json` to report progress. Each entry must
name the Work-Item, base HEAD, candidate commit when present, commands, receipts,
attestation refs, Forgejo readback, failures, and next legal edge.

## Current state

- Plan package created: yes.
- Implementation Work-Item admitted: no.
- Milestone progress projection: not generated; the projector does not exist.
- V2 product claim: not implemented.
- Existing v1.1 factory tests observed during planning: 13 tests, 189 assertions,
  passing on the dirty worktree.
- Existing factory fast preflight observed during planning: passing; its claim
  boundary remains `preflight-only-not-code-quality-axis`.
- Central candidate primitives observed during planning: 73 targeted Forgejo,
  lineage, and verification tests, 207 assertions, passing. They are not wired
  into the factory.

The current factory worktree contains earlier uncommitted CQ-preflight changes.
They are preserved as user work and are not evidence that Milestone 05 is done.
