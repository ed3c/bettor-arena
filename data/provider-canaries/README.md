# Provider canary receipts

This directory contains bounded live-execution receipts for exact immutable
implementation commits. Serena receipts live under `serena/`; GrepAI receipts
live under `grepai/`.

A receipt is evidence only for its recorded commit, tree, executable, workload,
coverage, controls, and cleanup result. It is never provider activation, a Gate
waiver, or release promotion. The live wrapper must create each receipt from a
clean committed worktree; later commits may admit the receipt without changing
its recorded subject.
