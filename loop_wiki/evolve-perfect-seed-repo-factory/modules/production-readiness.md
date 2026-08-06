# Production readiness

| property                                     | physical owner                                                     |
| -------------------------------------------- | ------------------------------------------------------------------ |
| Match/Generate/Validate/Record/Observe/Admit | `ROUTES.md`                                                        |
| typed exchange                               | `src/contracts.ts`                                                 |
| physical trigger                             | `trigger.sh`                                                       |
| route result                                 | `trigger.sh` outbox JSON                                           |
| baseline governance                          | `src/stats.ts`, `src/update_baseline.ts`, baseline-update packet   |
| schema replay                                | `src/migrate_packet.ts`, legacy packet fixture                     |
| template lifecycle                           | `templates/template-metadata.json`, lifecycle checker              |
| behavior eval                                | `packets/outbox/behavior-eval.json`, Bun tests                     |
| seed scaffold/materializer                   | `src/materialize.ts`, `templates/repo/`                            |
| trend observation                            | `src/record_trend.ts`                                              |
| fail-fast minimum lineage                    | generated repo checker + factory materialization control           |
| low-cost static quality                      | locked Prettier, typed ESLint, strict TypeScript, fast receipt     |
| security/fallback                            | typed source kind/path, no shell fields, no overwrite, hollow test |

Passing these gates yields a validated candidate. Promotion to lifecycle `seed`
requires a human decision and must update template metadata and evidence in the
same reviewed patch.

## Deliberate asynchronous downgrade

Code Quality and Production Use asynchronous small-loop gates are **not yet
integrated**. The factory currently has no axis request schema, background
worker carrier, hash-bound terminal axis receipt, stale projection, retry
budget, or promotion checker. The fast receipt may be listed as an observed
check later, but it must never change either full axis from `pending` to
`passed`. Adding those physical owners is a separate production slice.
