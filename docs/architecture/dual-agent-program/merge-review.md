# Merge and close review

This review separates deterministic work now admitted to public `main`, work still requiring current-main restack, and work that must remain open because the real runtime, provider, user, Human, or release boundary is absent.

## Already admitted in this review stage

### `ed3c/truth-verify-loop`

Minimal merge path:

```text
PR #29 baseline convergence
→ PR #39 DA-TV-C
→ PR #44 DA-TV-E
→ PR #45 DA-TV-D
```

Completed Issues closed:

```text
#25 #27
#31 #32 #33 #34 #35 #36 #37
```

Superseded/absorbed PRs closed without a second merge:

```text
#24 #26 #28 #38
#40 #41 #42 #43
```

Parent `#22` remains open for real physical/live/semantic evidence.

### `ed3c/runtime-env`

Admitted path:

```text
PR #69 DA-RC-C
├─ PR #76 DA-TR-C
│  ├─ PR #77 DA-TR-L
│  └─ PR #78 DA-TR-N
└─ PR #79 DA-ID-C
   ├─ PR #85 DA-ID-L
   ├─ PR #86 DA-ID-CLOUD
   └─ PR #87 DA-ID-P
        ↓
PR #104 README / AGENTS / Stack / LH-TR-001 / LH-ID-001
```

Exact public subject:

```text
implementation merge 92feed7c4e671dc63238155da9d4f394aac80d90
trace merge          baa4ce25d32a9fb4383ea8bc3530f9fd80be9ae7
tree                 117901dbd77cc93993ddc388682b7ab26a00d544
```

Completed deterministic Issues:

```text
#57 #61 #70 #71 #72 #74 #75 #80 #81 #82 #84
```

Keep open:

```text
#58 transport parent → #73 physical reconnect
#59 identity parent  → #83 live identity/revocation/rotation
```

PR #60 is an obsolete documentation snapshot and must not be merged separately.

### `ed3c/bettor-arena` Workflow + Effect

Admitted Workflow path:

```text
PR #201 DA-WF-C
└─ PR #202 DA-WF-K + integrated Effect Plane
   ├─ PR #209 DA-WF-R       exact bytes absorbed
   ├─ PR #210 DA-WF-H       exact bytes absorbed
   ├─ PR #211 DA-WF-COMP    exact bytes absorbed
   ├─ PR #232 DA-WF-E v2
   └─ PR #233 DA-WF-D
```

Admitted Effect path:

```text
PR #216 DA-EF-C
→ PR #224 DA-EF-K
→ PR #225 DA-EF-P
   ├─ PR #226 DA-EF-A       exact bytes absorbed
   └─ PR #227 DA-EF-COMP    exact bytes absorbed
→ PR #228 DA-EF-E
→ PR #229 DA-EF-D
→ PR #202
→ PR #201
```

Exact public subject:

```text
main merge 74d1e75c61589dcd163c7412e1345f726781ffb4
tree       0de94032a3227ad04dde52f138041294ef9cb810
```

Completed workflow Issues:

```text
#199 #200 #203 #204 #205 #206 #207
```

Completed effect Issues:

```text
#208 #217 #218 #219 #220 #221 #222
```

Closed absorbed/superseded PRs include:

```text
#209 #210 #211 #215 #226 #227
```

Keep open:

```text
#184 live durable-workflow parent
#185 live effect parent
#223 real reversible effect/readback
#186 physical local→cloud→local canary
#68 Human release/rollback
```

Deterministic admission does not satisfy live restart, provider I/O, external effect, user outcome, Human, release, or production HA criteria.

## Current candidate stacks requiring current-main restack and CI

### `ed3c/agent-shield-monorepo` route

Current main:

```text
30e12cc917503b56b002aa7351428811f20fea8e
tree 6f465f936515d81ed51c5b80595de530593f25fc
```

Recommended minimal path:

```text
#162 DA-INT-C
→ #166 DA-INT-E
→ #167 DA-INT-D
```

After current-main restack and exact byte-identity readback, #163/#164/#165 may close as absorbed leaves. Live route #161 remains open.

### `ed3c/agent-shield-monorepo` gVisor

Recommended minimal path:

```text
#174 DA-GV-C
→ #177 DA-GV-E
→ #178 DA-GV-D
```

After current-main restack and exact byte-identity readback, #175/#176 may close as absorbed leaves. Live runsc/gVisor #173 remains open.

### Shared Agent Shield candidate

PR #180 is non-promoting and may enter merge review only after route/gVisor/local-sandbox inputs are admitted or restacked to current main. Its only valid result is `HUMAN_REVIEW_PENDING`; it cannot write shared release/status state.

## Must remain open

```text
runtime-env#58          transport parent
runtime-env#59          identity parent
runtime-env#73          physical NATS disconnect/reconnect
runtime-env#83          live cross-runtime identity/revocation
agent-shield#95         live network enforcement
agent-shield#161        live API/browser execution
agent-shield#173        live runsc/gVisor isolation
bettor-arena#184        live durable-workflow engine
bettor-arena#185        live effect parent
bettor-arena#223        real reversible effect/readback
bettor-arena#186        physical offline local→cloud→local canary
truth-verify-loop#22    independent verification of the real bundle
bettor-arena#68         Human release/rollback convergence
```

These are not blocked by missing prose. They require trusted runtime, provider, credentials, target, egress, cleanup, and Human authority.

## Superseded documentation routes

Bettor PRs #176 and #188 were prepared against obsolete parent/main subjects and are closed. PR #231 replaced them and was then superseded as a state snapshot by issue #234 after Runtime and Workflow/Effect admission.

Runtime PR #60 is a stale pre-admission snapshot. Current runtime documentation is PR #104 on `main`.

## Review checklist

```text
[ ] current base/head/tree reread
[ ] Draft state intentionally changed
[ ] exact-head CI rerun after base movement
[ ] SKIPPED not counted as PASS
[ ] unresolved review threads dispositioned
[ ] path/writer lease conflict absent
[ ] convergence absorbed leaves by exact blob identity
[ ] evidence ceiling retained
[ ] live/Human/release states retained as open
[ ] rollback subject recorded
[ ] parent and Local Handoff Issues updated
```
