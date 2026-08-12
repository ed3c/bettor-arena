# Context Capsule evidence

This directory stores deterministic evidence derived from `.arena/contexts/*.json` and `.arena/contexts.lock.json`.

[`driver-parity.json`](driver-parity.json) records whether the Claude Code and Codex CLI carriers resolve the same native context bytes and declared working directory. It does not claim that either live host CLI was present or authenticated.

Regenerate/check with:

```sh
python3 scripts/arena_context.py lock
python3 scripts/arena_context.py parity
python3 scripts/arena_context.py check
```
