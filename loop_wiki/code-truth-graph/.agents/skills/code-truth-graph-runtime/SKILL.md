---
name: code-truth-graph-runtime
description: Run or verify the generic bettor-owned CTG runtime against an admitted packet bundle.
---

# Code Truth Graph runtime

Use `loopctl ctg run --packet <absolute> --output <fresh-absolute>` for execution.
Use `loopctl ctg build-local --manifest <absolute> --output <fresh-absolute>` only on a trusted co-located
subject checkout; it can read raw evidence, is not exposed over MCP, and its output stays subject-owned.
Use `loopctl ctg prove` for traversal evidence and `loopctl ctg test` for the independent behavioral control.
Read `PROMPT.md`, `ROUTES.md`, and `modules/exchange-formats.md` before changing packet/result semantics.
