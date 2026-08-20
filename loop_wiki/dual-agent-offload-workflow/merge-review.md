# Dual-Agent workflow merge and close review

## Admitted path

```text
PR #201  DA-WF-C      MERGED
→ PR #202 DA-WF-K     MERGED
   ├─ PR #209 DA-WF-R     ABSORBED_BY_#215
   ├─ PR #210 DA-WF-H     ABSORBED_BY_#215
   └─ PR #211 DA-WF-COMP  ABSORBED_BY_#215
          ↓
       PR #215 DA-WF-E    MERGED
```

PR #215 contains and re-verifies the exact operational sibling implementation/test bytes, so #209/#210/#211 were closed without a second merge.

## Issues closed as completed

```text
#199 #200 #203 #204 #205 #206
```

## Must remain open

```text
#184 parent durable workflow
#185 external-effect plane
#186 physical local→cloud→local canary
#223 real reversible effect
#68  Human release/rollback
```

Parent #184 remains open because the merged deterministic code has not exercised a real durable-engine server/namespace, worker crash/failover, physical transport, live identity, provider execution, external effect, user-visible result or production recovery.

## Admission laws

A workflow change may merge only when:

1. exact current base/head/tree and imported runtime-contract subject are known;
2. the contract, reducer, operational leaves and complete matrix are green on the candidate;
3. no decision code directly reads wall clock, randomness, network, process or provider state;
4. LoopX remains the single task writer and workflow output remains proposal-only;
5. effect execution stays in the effect plane;
6. Human refusal, cancellation, stale result, compensation failure and cleanup failure stay distinct;
7. live/Human/release absence is not represented as PASS;
8. review threads and shared-path writers are explicitly dispositioned.

## Current verdict

```text
workflow deterministic subtree     MERGED
operational leaves                  ABSORBED_AND_VERIFIED
workflow docs convergence           CANDIDATE
real durable engine                 NOT_EXERCISED
live Human/provider/effect          NOT_EXERCISED
physical #186                       OPEN
Human admission/release             NOT_PERFORMED
```
