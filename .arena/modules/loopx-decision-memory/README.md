# `loopx-decision-memory` module

Machine authority: [`module.json`](module.json)

This module provides `loopx.decision-memory/v1` and remains unselected until final convergence.

## State Machine

```text
observable evidence
→ bounded memory proposal
→ evidence/privacy/retention/conflict checks
→ Human admission receipt
→ candidate capsule
→ future trusted-reducer memory event
→ optional rebuildable projection
→ expire / supersede / delete
```

## Public control port

```sh
python3 loop_wiki/loopx-decision-memory/scripts/memory.py check
python3 loop_wiki/loopx-decision-memory/scripts/memory.py selftest
```

## Authority ceiling

The compiler cannot persist durable memory, write Mem0, change repository source/docs, decide a Gate, advance LoopX state, sign Human authority, merge or promote. Candidate capsules explicitly carry `persisted=false` and name `LOOPX_MEMORY_LEDGER` plus `TRUSTED_REDUCER` as the future canonical authority.

## Evidence

```sh
sh loop_wiki/loopx-decision-memory/tests/run-all.sh
```

Live provider projection, durable append-only memory events, current-repository conflict reconciliation and deletion residue proof remain separately evidenced.
