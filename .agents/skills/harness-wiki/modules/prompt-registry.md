# Module: prompt-registry — raw prompt and judgment-logic ownership index

> Owner: [`harness-wiki`](../SKILL.md). This module is the panorama-level
> pointer index for prompt ownership, dataflow ownership, and loop judgment
> logic. It exists to prevent prompt/loop simplification while avoiding copied
> prompt bodies that would drift.

## Registry Rule

Every loop must name the physical owner for:

- raw human constraints;
- fixed passive context;
- task prompt / target contract;
- generated iteration context;
- emergent context;
- judge prompt or judge material;
- route/result packet format;
- verifier / exit-code logic.

Do not paste long prompt bodies into this module. If a prompt body must be
preserved verbatim, preserve it in its loop's own fixed-context module,
dispatch file, packet, or generated context artifact, then point here to that
physical owner.

## Cross-loop Prompt And Logic Registry

| loop | raw human / task prompt owner | generated prompt/context owner | judgment logic owner | dataflow owner |
|---|---|---|---|---|
| 演化 op | sandbox `CLAUDE.md` + `PROMPT.md` under `loop_wiki/evolve-<family>-<op>/` | `loop_wiki/engine.sh` writes `_engine-run/` trajectory and dispatch prompt context | sandbox `verify.sh` + family `scripts/runner.py --family <f> --compare`; engine exit contract in `loop_wiki/engine.sh` | sandbox `PLAN.md`; global component card in `harness-wiki/SKILL.md` |
| DR proposal | `loop_wiki/_template_dr/PROMPT.md` and proposal-specific sandbox `PROMPT.md` | proposal feedback dispatch files under the plan/proposal folder | `_template_dr/scripts/check_*.py` + `judge-loop-chooser` D3 findings + human TTL/admit | `dr-research-loop` owner skill + `harness-wiki/SKILL.md` component row |
| mvp-radar | `loop_wiki/mvp-radar/PROMPT.md` | `dispatches/round-NN.md` convention for driver/judge prompts | `loop_wiki/mvp-radar/verify.sh` + `DESIGN-SCORE.md` dual-score AND + human LAND-DECISION | `dr-to-mvp` owner skill + `harness-wiki/SKILL.md` component row |
| N-variant execution feedback | assertion table in the plan slice using `harness-spec.md §4.5` B-1 schema | `loop_wiki/engine_nv.sh` materializes `variant-*/APPROACH.md`, `judge-materials.md`, and rerun prompt | `loop_wiki/engine_nv.sh` exit contract + `loop-harness-standard/scripts/execution-feedback/` checkers | `loop-harness-standard/modules/execution-feedback.md` |
| clc literal-claim challenge | `loop_wiki/clc/evals/claims.jsonl` | `loop_wiki/clc/` verifier outputs and `EQUIVALENCE-VERDICT.md` | `loop_wiki/clc/verify.sh` artifact-alive and true-equivalence rates | `skill-authoring` METHODOLOGY + clc component row |
| dx-adversarial-fix cockpit | `loop_wiki/dx-adversarial-fix/decision-data.json` plus source-read automation map | `decision-shell.html`, POST payload, and monitor `DECISION:` events | `scripts/check_narration.py`, `decision_server.py`, `decision_router.py`, human admit | `loop_wiki/dx-adversarial-fix/` component row |
| plan-truth production seed | `loop_wiki/evolve-unknown-discovery-plan-truth/modules/semantic-truth-context.md` preserves the human low-compression semantic-truth constraint; `PROMPT.md` owns the target contract | `trigger.sh` writes `_engine-run/exchange-context.<packet_id>.md`; packets carry `fixed_prompt_context`, `iteration_auto_context`, and `emergent_prompt_context` | `verify.sh` T0 anchors, `scripts/validate_exchange.py`, `scripts/test_production_readiness.sh`, `scripts/compute_dataflow_stats.py`, and human admit | `modules/plan-truth-dataflow.md`, `modules/exchange-formats.md`, `modules/production-readiness.md`, `baselines/dataflow-stats.json` |
| bounded perfect-seed repo factory | `loop_wiki/evolve-perfect-seed-repo-factory/PROMPT.md` owns the task contract; `modules/semantic-truth-context.md` owns the anti-compression constraint | `trigger.sh` writes `_engine-run/exchange-context.<packet_id>.md`; the generated repo operator writes `data/call-plan.json` and `data/call-results.jsonl`; `run_fast_quality.ts` writes ignored preflight receipts | factory `verify.sh`/`selftest.sh`, `src/contracts.ts`, minimum-lineage/fast-quality runners, `src/verify_generated_repo.ts`, generated repo tests, and human admit; fast receipt is not an async CQ/PU axis receipt | `ROUTES.md`, `modules/architecture.md`, `modules/exchange-formats.md`, `modules/production-readiness.md`, `baselines/seed-stats.json` |

## Raw Human Constraint Anchor

The plan-truth production seed loop preserves this load-bearing human
constraint in `modules/semantic-truth-context.md`:

> 內容壓縮程度太高，需要按照 /judge-loop-chooser 追求語意真相(Opus or Codex or agy)，用LLM可以理解的方式敘述，不能在缺乏上下文情況讓LLM 模糊決策。

The operational meaning is owned by that module, not repeated here. Any loop
that depends on this constraint must include that module or an equivalent local
fixed-context module in its packet's `fixed_prompt_context`.

## Generated Prompt Ownership

Generated prompts and contexts are runtime artifacts. They may be ignored by
git, but the generator and packet format must be committed:

| generated artifact | generator SSOT | committed evidence |
|---|---|---|
| `_engine-run/exchange-context.<packet_id>.md` | plan-truth `trigger.sh` | packet files, trigger tests, and `PLAN.md` trajectory |
| engine dispatch prompt | sandbox `run.sh` + `PROMPT.md` | `run.sh`, `PROMPT.md`, `verify.sh`, and engine trajectory |
| N-variant judge materials | `loop_wiki/engine_nv.sh` | `engine_nv.sh`, checker fixtures, and verdict file |
| decision cockpit prompt surface | `decision-shell.html` + `decision-data.json` | narration checker, router, and human decision record |

If a generated context reveals a new load-bearing prompt, fold it into the
owning loop's fixed-context module or dispatch file first, then update this
registry with a pointer.

## Drift Guard

- A panorama row without a physical prompt owner is invalid.
- A prompt owner without a verifier/exit-code owner is incomplete.
- A copied prompt body outside its owner file is a duplicate SSOT unless it is
  explicitly labeled as a short anchor quote.
- A raw human constraint that affects routing must be part of fixed context,
  not only a transcript memory.
