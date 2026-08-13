# Domain-context policy for coding Agents

This policy adapts the useful document conventions from `setup-matt-pocock-skills` to Bettor's governed multi-hop route. It does not replace the root glossary, architecture SSOT, nearest READMEs, or machine contracts.

## Read order

Read only the documents relevant to the task, in this order:

```text
CONTEXT.md
→ CONTEXT-MAP.md when it genuinely exists
→ relevant docs/adr/ and nested ADR directories
→ nearest directory README.md
→ module manifest/public interface/tests/receipts
```

The repository entry route in `AGENTS.md` or `CLAUDE.md` remains mandatory before this policy.

## Context documents

### `CONTEXT.md`

`CONTEXT.md` is the bounded, passive glossary for stable Bettor terms. Use its vocabulary exactly. It is not a current-state ledger and contains no implementation detail, provider credential, session state, or mutable branch assumption.

### `CONTEXT-MAP.md`

Use a context map only when the repository actually contains multiple bounded contexts with different vocabularies or owners. A map points to context files; it does not flatten them into one giant prompt. Bettor currently has a single root glossary, so a missing `CONTEXT-MAP.md` is optional rather than an error unless a future task packet explicitly requires it.

### Nearest README

After global context and applicable ADRs, read the nearest README for every path the task may change. A nearest README narrows ownership, public/private boundaries, inputs, outputs, evidence, and local change rules.

## ADR policy

- Search `docs/adr/` and nested ADR directories only for decisions related to the task.
- Record the ADR ID/path and status; do not treat a superseded or proposed ADR as current law.
- When an ADR conflicts with current source, manifest, or another current ADR, preserve the conflict and identify the owning authority instead of choosing silently.
- A historical ADR can explain why a design existed; it does not prove the current implementation or runtime state.
- Create an ADR only for a durable architectural decision, not for per-task notes or transient provider observations.

## Missing-document policy

Domain documents may be created lazily when a real domain or decision needs a durable home. Do not create empty `CONTEXT-MAP.md`, ADR directories, or duplicate READMEs merely to satisfy a template.

A document is no longer optional when:

- `AGENTS.md`, a task packet, a module manifest, or a Skill binding names it as required;
- a new owner/context/public boundary cannot be expressed by an inherited document;
- an unresolved architecture decision must survive the current session.

Missing required documents are `ABSENT`; chat history or Agent memory is not a substitute.

## Vocabulary and memory

Repository context and current ADRs outrank retrieved memories. Memory may nominate an incident, preference, or prior decision to verify. When memory conflicts with current context, ADRs, source, tests, or receipts, current repository authority wins and the conflict remains visible in the evidence artifact.

## Evidence boundary

Context files and ADRs provide vocabulary, intent, ownership, and decisions. Source establishes mechanism; tests and receipts establish only the executed subject. No document converts `NOT_EXERCISED`, provider absence, or an old SHA into `PASS`.

## Change contract

A domain-policy change requires affected contexts/ADRs/directories, read-order and context-budget impact, positive and stale/conflicting/missing-document controls, memory-conflict behavior, privacy boundary, rollback subject, exact issue/PR, and Human Admit.
