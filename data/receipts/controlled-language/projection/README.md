# Controlled-language projection receipts

This directory reserves the projection evidence route. CTL 07B commits no
receipt file: the materializer emits its path-redacted receipt on stdout, so a
stored verdict can never outlive the run that produced it.

```text
sealed materializer mechanism     IMPLEMENTED
synthetic Git parity controls     IMPLEMENTED
exact-head hosted contract        NOT_EXERCISED until its workflow runs
real upstream private checkout    NOT_EXERCISED
Codex physical carrier            NOT_EXERCISED
Claude physical carrier           NOT_EXERCISED
model or manual processing        NOT_EXERCISED
production termbase               ABSENT
official compliance               NOT_CLAIMED
```

A receipt from the synthetic lane carries `source_class:
SYNTHETIC_FIXTURE`; it is mechanism evidence and must never be presented as a
projection of the real upstream bundle. Only a run with
`--source`/`--target` against the selected immutable checkout produces
`source_class: SELECTED_UPSTREAM_CHECKOUT`, and even that stays a static
materializer result: both physical carrier lanes remain `NOT_EXERCISED` in the
same receipt.

A later physical receipt must bind the consumer commit/tree, the admitted
binding blob, the immutable upstream commit/tree/Skill tree, the projected
content digest, the carrier and harness version, model/environment,
condition/repetition, deterministic verifier, privacy lane, termbase identity,
and any required Human approval. Do not store credentials, browser or device
sessions, document contents, private reasoning, machine-local absolute paths, or
mutable branch names as authority.
