# Merge and close review

This review separates work that can be admitted after current-subject CI from work that must stay open because the real runtime, provider, user, Human, or release boundary is absent.

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

Superseded PRs closed without a second merge:

```text
#24 #26 #28 #38
#40 #41 #42 #43
```

Parent `#22` remains open for real physical/live/semantic evidence.

## Candidate stacks that require current-main restack and CI

### `ed3c/runtime-env`

Recommended minimal merge order:

```text
#69 DA-RC-C
  ↓
#76 DA-TR-C
  ├─ #77 DA-TR-L
  └─ #78 DA-TR-N

#79 DA-ID-C
  ├─ #85 DA-ID-L
  ├─ #86 DA-ID-CLOUD
  └─ #87 DA-ID-P

then #74 / #84 documentation convergence
```

Do not close parent `#58` or `#59` after deterministic merge. Physical reconnect `#73` and live identity `#83` remain open.

### `ed3c/bettor-arena` workflow

Recommended minimal convergence path:

```text
#201 DA-WF-C
→ #202 DA-WF-K
→ #215 DA-WF-E
→ #207 DA-WF-D or a clean current-main successor
```

After #215 lands and exact byte identity is reread, leaf PRs #209/#210/#211 may close as superseded rather than being merged again.

Parent `#184` may close only after the deterministic workflow acceptance is present on main and documentation is current. It does not close physical runtime #186.

### `ed3c/bettor-arena` effect

Recommended path:

```text
#216 DA-EF-C
→ #224 DA-EF-K
→ #225 DA-EF-P
→ #228 DA-EF-E
→ #229 DA-EF-D
```

After #228 lands and exact blob identity is reread, #226/#227 may close as superseded. Parent #185 can close for deterministic scope only after the docs convergence lands. Live effect #223 remains open.

### `ed3c/agent-shield-monorepo` route

Recommended path:

```text
#162 DA-INT-C
→ #166 DA-INT-E
→ #167 DA-INT-D
```

After #166 lands, #163/#164/#165 may close as exact-byte absorbed leaves. Live route #161 remains open.

### `ed3c/agent-shield-monorepo` gVisor

Recommended path:

```text
#174 DA-GV-C
→ #177 DA-GV-E
→ #178 DA-GV-D
```

After #177 lands, #175/#176 may close as exact-byte absorbed leaves. Live runsc/gVisor #173 remains open.

### Shared Agent Shield candidate

PR #180 is non-promoting and may enter merge review only after route/gVisor/local-sandbox inputs are admitted or restacked to current main. Its only valid result is `HUMAN_REVIEW_PENDING`; it cannot write shared release/status state.

## Must remain open

```text
runtime-env#73          physical NATS disconnect/reconnect
runtime-env#83          live cross-runtime identity/revocation
agent-shield#95         live network enforcement
agent-shield#161        live API/browser execution
agent-shield#173        live runsc/gVisor isolation
bettor-arena#223        real reversible effect/readback
bettor-arena#186        physical offline local→cloud→local canary
truth-verify-loop#22    independent verification of the real bundle
bettor-arena#68         Human release/rollback convergence
```

These are not blocked by missing prose. They require trusted runtime, provider, credentials, target, egress, cleanup, and Human authority.

## Old documentation PRs

Bettor PRs #176 and #188 were prepared against obsolete parent/main subjects and previously carried restack blockers. After this current-main successor is green and admitted, they should close as superseded with their failure/restack history preserved. They should not be force-merged or used as current authority.

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
