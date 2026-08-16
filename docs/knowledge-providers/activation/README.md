# Provider activation controller

`scripts/providers/provider_activation.py` is the only repository-owned route
that may change Serena or GrepAI from `CONFIGURED` to `ADMITTED`. It activates
an on-demand, read-only profile; it does not start a daemon, persist an index,
mark provider output as tested, advance LoopX state, waive a gate, or promote a
release.

## State machine

```text
CANDIDATE / UNPINNED
  -> manifest identity and bounded policy pinned
  -> CONFIGURED / NOT_EXERCISED
  -> clean exact commit and tree
  -> Serena and GrepAI live canaries for that same subject
  -> source readback + controls + cleanup PASS
  -> controller compare-and-swap
  -> ADMITTED / PASS / live_claim=true

stale subject, missing receipt, identity or policy drift -> BLOCKED_POLICY
post-write contract failure                            -> automatic local restore
rollback                                               -> exact recorded rollback subject
```

The controller has a closed provider set and fixed repository-relative paths.
It accepts no provider command, shell string, host path, credential, arbitrary
manifest, gate waiver, or partial-provider activation.

## Commands

CI-safe contract and planted mutations:

```sh
python3 scripts/providers/provider_activation.py check
python3 scripts/providers/provider_activation.py selftest
```

Configuration uses the checked-in policy and the earlier exact live evidence;
it is a separate, non-activation transition:

```sh
python3 scripts/providers/provider_activation.py configure \
  --expected-commit <controller-commit> \
  --expected-tree <controller-tree> \
  --evidence-commit <live-evidence-commit> \
  --evidence-tree <live-evidence-tree> \
  --rollback-commit <rollback-commit> \
  --rollback-tree <rollback-tree>
```

Activation then requires new live receipts for the configured exact subject. The canary receipts are fixed at
`data/provider-canaries/{grepai,serena}/<expected-commit>.json`; the durable
activation receipt is fixed at `data/provider-activations/<expected-commit>.json`.

```sh
python3 scripts/providers/provider_activation.py activate \
  --expected-commit <candidate-commit> \
  --expected-tree <candidate-tree> \
  --rollback-commit <rollback-commit> \
  --rollback-tree <rollback-tree>
```

The controller performs all checks before writing. It changes only both
provider manifests, their registry digests, their fixed manifest-digest
projections, and one lifecycle receipt. If the post-write module contract
fails, it restores every original byte.
