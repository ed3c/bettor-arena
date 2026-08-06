---
type: Contract
title: Molecular commit-message contract
description: The rebuilt validate_molecular_message.ts gate — its legislated charter, required trailer fields, protected-surface trigger, ISSUE-n Intent-Slice vocabulary, and the corpus-parity measurement of what the rebuild deliberately dropped.
tags: [commit-msg, molecular, protected-surface]
node_kind: RepoDoc
repo: neon/bettor-arena
commit: 2c36ddf
covers: [molecular-message, intent-slice, protected-surface, corpus-parity]
generated_by: claude-code+claude-fable-5
generated_at: null
---

# Molecular commit-message contract

`.githooks/lib/validate_molecular_message.ts` is the commit-msg gate's brain, run under bun by the [commit-msg hook](git-hooks.md). It was REBUILT (S8, commit 99fa15d) from the source repo's UDPT validator rather than copied — the iron-law-7 discipline of judging equivalence by rebuild, not by name (src: ARCHITECTURE.md:55).

## Legislated charter

The header legislates what the gate MAY do and nothing else (src: .githooks/lib/validate_molecular_message.ts:5-11):

- READS ONLY: the commit-message file named in argv, and this repo's `git diff --cached --name-only` (or an explicit `--changed-paths-file`).
- FORBIDDEN: imports from outside the file except `node:` builtins; repo-specific data paths inside the contract; reading sibling checkouts; any network access.

This charter is *tested*, not just stated: `tests/test_molecular_gate.sh` checks "single file, node: builtins only, no sibling-checkout reads" (src: tests/test_molecular_gate.sh:20). The same fixture then traces real commit behavior with the staged hooks ACTIVATED: an ordinary message on an ordinary file commits successfully and `rev-list --count` confirms the commit exists (src: tests/test_molecular_gate.sh:40-45); the post-commit stage-request receipt must exist, name the resulting sha, and carry `"stage-request"` — record-only, never blocking (src: tests/test_molecular_gate.sh:47-52); and a hollow molecular message (`Intent-Slice` present but the trailer block incomplete) is REJECTED with no commit created (src: tests/test_molecular_gate.sh:57-59).

## What was deliberately stripped, and why

Six UDPT-specific rule groups were removed because each violated the charter (src: .githooks/lib/validate_molecular_message.ts:14-33): S1 the commit-verification-envelope trailer set (required importing runtime/verification from outside the gate dir), S2 canonical absolute-path equality (repo-specific data paths), S3 "at least five absolute dataflow paths under repo root" (home-directory coupling), S4 mandatory GCR source-conversation reference (absolute path into a sibling checkout), S5 mandatory literal references to source-repo files, S6 the UDPT protected path list — retargeted to THIS repo's control surface.

## The contract itself

- **Trigger**: a message is molecular iff it matches `Intent-Slice:\s+ISSUE-\d+` (src: .githooks/lib/validate_molecular_message.ts:60-62). Vocabulary is ADR 0001: `ISSUE-<n>` anchors the ts-skill-bettor Forgejo tracker; the source repo's prefixes (`GCR-SLICE-` etc.) are deliberately unsupported and rejected on protected surface (src: .githooks/lib/validate_molecular_message.ts:56-59, 154-156).
- **Protected surface**: `.githooks/` and `scripts/gates/` (src: .githooks/lib/validate_molecular_message.ts:53-54). If any staged path starts with those prefixes, the message MUST be molecular; ordinary messages are rejected with "protected gate surface requires a molecular commit message" (src: .githooks/lib/validate_molecular_message.ts:64-69, 93-95). Ordinary commits elsewhere pass with no molecular fields at all.
- **Required fields** when molecular (src: .githooks/lib/validate_molecular_message.ts:39-51): `Intent-Slice:`, `Route:`, `Plan-Package:`, `Small-Loop:`, `Final-Repo:`, `Exchange-Format:`, `Exchange-Packet:`, `Fixed-Prompt-Context:`, `Iteration-Auto-Context:`, `Emergent-Prompt-Context:`, `Dataflow:`.
- **Shape rules**: non-empty subject; blank line between subject and the molecular block; `Fixed-Prompt-Context` must appear before `Iteration-Auto-Context` (src: .githooks/lib/validate_molecular_message.ts:72-85).
- **Exit codes**: 0 pass · 2 fail · 64 usage (src: .githooks/lib/validate_molecular_message.ts:34).

## Dry-run seam

`--changed-paths-file <f>` substitutes the staged-path read, letting a caller validate a message against a hypothetical change set without staging anything (src: .githooks/lib/validate_molecular_message.ts:163-178). `--selftest` runs both directions: an ordinary message passes unprotected but is rejected on protected surface; a good molecular message passes both; a hollow molecular message (fields missing) fails; swapped context ordering fails; a missing subject separator fails; source-repo vocabulary fails protected surface (src: .githooks/lib/validate_molecular_message.ts:115-159).

## Corpus parity — measuring what the rebuild changed

`tests/tools/replay_corpus_parity.py` replays the last N commit messages of a `--source-repo` through BOTH the original UDPT validator (read-only, inside the source repo) and this rebuilt validator, in message-only mode, and reports exit-code parity. Mismatches are expected by design — the rebuild stripped S1–S5, so commits the original rejects under those rules pass here. "This script measures the gap; it does not judge it" (src: tests/tools/replay_corpus_parity.py:2-15). Every missing precondition (bun, repo, validator) dies FATAL 64 with a diagnostic, never a bare traceback (src: tests/test_replay_corpus_parity.sh:2-5; hardened by commit 35a0ca2). The frozen measurement lives at `data/receipts/molecular-corpus-parity.json`; ADR 0001 records that it was measured under the OLD vocabulary and stays frozen (src: docs/adr/0001-molecular-slice-vocabulary.md:25-26). Rerun protection: reruns write elsewhere instead of overwriting tracked evidence (commit 579771c).

## Composing a molecular message in practice

For a commit touching the protected surface, dry-run first:

```sh
bun run .githooks/lib/validate_molecular_message.ts --changed-paths-file <paths.txt> <msg.txt>
```

then commit with the exact validated message. The smoke and TDD-red receipts of the gate's own construction are frozen at `data/receipts/molecular-gate-smoke.json` and `data/receipts/molecular-gate-tdd-red.json` — see [data ledgers](../data-ledgers.md).
