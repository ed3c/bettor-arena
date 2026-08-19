# Inception A1 P4 — SQLite crash fault matrix

Status: **PUBLIC PROCESS-FAULT CANDIDATE**

This atom is a true child of `bettor-arena#194` at `77c0da129a933a11de067dac051db14c3e002eec`. It does not modify the admitted P3 checkpoint contract. It exercises that exact parent through abrupt child-process termination and file-backed SQLite reopen/readback.

## State Machine

```text
CHECKPOINT_PARENT_BOUND
→ FAULT_MATRIX_DECLARED
→ ABRUPT_EXIT_INJECTED
→ DATABASE_REOPENED
→ INTEGRITY_CHECKED
→ STATE_TRANSITION_READ_BACK
→ SHADOW_REVIEW_REQUIRED
```

## Fault matrix

```text
CRASH_BEFORE_PREPARE
CRASH_AFTER_PREPARE_COMMIT
CRASH_BEFORE_RECOVERY_PROBE
CRASH_AFTER_RECOVERY_PROBE_COMMIT
CRASH_BEFORE_ACTIVATION
CRASH_AFTER_ACTIVATION_COMMIT
UNCOMMITTED_METADATA_MUTATION_CRASH
```

The worker uses `os._exit()` without closing the SQLite connection. The test runner then creates a new process/connection and checks the persisted state. This is stronger than exception-only fault injection but remains a GitHub-hosted process-crash fixture, not physical power-loss evidence.

## Required invariants

- crash before prepare creates no checkpoint;
- committed prepare survives abrupt termination but does not advance active revision;
- crash before recovery cannot unlock activation;
- committed recovery PASS survives abrupt termination but does not activate;
- crash before activation preserves the previous active revision;
- committed activation survives abrupt termination and retains the exact checkpoint row;
- an uncommitted metadata mutation is rolled back after abrupt termination;
- every recovered database returns `PRAGMA integrity_check = ok`.

## Data flow

```text
P3 checkpoint contract @ exact parent
        ↓
child subprocess + file-backed SQLite
        ↓
public transition call / raw uncommitted mutation
        ↓
os._exit()
        ↓
fresh SQLite connection
        ↓
revision / checkpoint / candidate readback
        ↓
PRAGMA integrity_check
        ↓
Shadow review
```

## Evidence ceiling

```text
process crash before/after transitions  TARGETED_PUBLIC_CANARY
SQLite reopen/readback                  TARGETED_PUBLIC_CANARY
uncommitted rollback                    TARGETED_PUBLIC_CANARY
physical power loss                     NOT_EXERCISED
live context reconstruction             NOT_EXERCISED
provider tokenizer/context accounting   NOT_EXERCISED
production recovery                     NOT_EXERCISED
Human admission / release               NOT_PERFORMED
```

Next transition: `RUN_LIVE_CONTEXT_RECONSTRUCTION_AND_PROVIDER_BUDGET_CANARY`.

Machine authority: [`preflight.json`](preflight.json).
