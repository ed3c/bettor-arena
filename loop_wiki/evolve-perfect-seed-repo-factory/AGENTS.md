# AGENTS.md — perfect-seed repo factory

## Read order

1. `PROMPT.md` for the bounded target contract.
2. `ROUTES.md` for state, actor, validator, and failure edges.
3. `modules/architecture.md` for the reduced IR and generated-repo boundary.
4. `modules/exchange-formats.md` before changing packet or result fields.
5. `modules/production-readiness.md` before claiming reusable-seed status.
6. `modules/semantic-truth-context.md` before generating task context.

## Eight bases

| base                             | owner                                                                                               |
| -------------------------------- | --------------------------------------------------------------------------------------------------- |
| 1 passive context                | `AGENTS.md` and `CLAUDE.md`                                                                         |
| 2 settings and authorization     | local-only Bun commands; no network or shell-bearing packet fields                                  |
| 3 lifecycle evidence             | `_engine-run/` generated context plus `PLAN.md` durable summary                                     |
| 4+5 routes and specialized skill | `ROUTES.md`, `.agents/agents/seed-factory-router.md`, `.agents/skills/perfect-seed-domain/SKILL.md` |
| 6 independent verifier           | fast quality receipt, `verify.sh`, `selftest.sh`, and generated-repo validator                      |
| 7 target contract                | `PROMPT.md`                                                                                         |
| 8 state ledger                   | `PLAN.md`                                                                                           |

`run.sh` is a one-shot dispatch. It contains no iteration logic. The factory is
deterministic; a failed packet/build surfaces to the caller for packet or code
repair. It does not ask an LLM to self-repair or self-admit.

## Ownership boundary

- Macro loop owns orchestration, cross-loop comparison, and human admission.
- This loop owns one packet's validation, reduced IR, repo materialization,
  twenty-call local execution, route result, baseline/trend, and failure surface.
- The generated repo owns its local operator skill and local data. It does not
  own this factory's governance or sibling-loop routing.
- “Perfect” is an optimization target. Legal machine states are candidate,
  validated, failed, and human-required.

## Execution

```sh
sh verify.sh
 bun run quality:fast
sh trigger.sh packets/inbox/dr-example.json /absolute/output/path
```

Never edit tests, baselines, or packet state merely to make a target pass.
Baseline changes require a reviewed/admitted baseline-update packet.
