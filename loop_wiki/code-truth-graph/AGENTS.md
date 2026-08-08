# AGENTS.md — Code Truth Graph runtime

## Read order

1. `PROMPT.md` — bounded target and stop-loss.
2. `ROUTES.md` — state, validator, pass/failure edges.
3. `modules/exchange-formats.md` — packet/result ownership.
4. `modules/eight-base-laws.md` — reach and proof/control meaning.
5. `PLAN.md` — append-only implementation trajectory.

## Local rules

- One trigger processes one immutable packet into one fresh output directory.
- Packet, snapshot, profile, evidence, graph and result identities stay separate.
- Never infer a missing SANDBOX/PROD lane from STATIC evidence.
- `0` means the requested measurement completed; it does not Human-admit an invariant.
- Do not add shell-bearing tool fields. Tool selection is by pinned profile id only.
- Do not persist absolute checkout/worktree paths in artifacts.
- `run.sh` and `trigger.sh` are one-shot dispatchers; iteration belongs to the caller.

## Execution

```sh
sh verify.sh
sh trigger.sh /absolute/ctg-input.json /absolute/fresh-output
```
