# Module: skill-bettor Port Map

> Owner: [gemini-conversation-research](../SKILL.md). Purpose: keep the copied antigravity skill honest after landing in skill-bettor. This file is the local path-routing SSOT for "what is runnable here" versus "what is external evidence/engine".

## Source Evidence

- Source skill: `/Users/neon/antigravity/.agents/skills/gemini-conversation-research/`
- Local skill copy: `/Users/neon/ts-skill-bettor/.claude/skills/gemini-conversation-research/`
- Local small-loop template: `/Users/neon/ts-skill-bettor/loop_wiki/evolve-unknown-discovery-plan-truth/templates/gemini-conversation-research/`
- Local plan anchor: `/Users/neon/ts-skill-bettor/docs/plans/2026-07-22-unknown-discovery-gcr-order/01-small-loop-plan-truth-rerun.md`

## Runnable Locally

| Capability | Local artifact | Gate |
| --- | --- | --- |
| Guided conversation state graph | `modules/guided-conversation-observation.md` | Must expose match/generate/verify nodes and conditional edges. |
| Three Gemini conversation seed cases | `templates/gemini-conversation-research/golden/guided-conversation-cases.json` | Must include `047d548af8f8e34c`, `874b5c3430c13837`, `37731ad84bf5b546`. |
| Guided conversation golden traces | `templates/gemini-conversation-research/golden/guided-conversation-traces.json` | Must serialize event order, state transitions, prompt slots, semantic-loss ledger, and terminal artifacts. |
| Guided trace schema | `templates/gemini-conversation-research/schemas/guided-conversation-trace.schema.json` | Must define required fields and prevent `external_engine_required` traces from claiming live execution. |
| Behavior validator | `templates/gemini-conversation-research/evals/check_guided_conversation_cases.py` | Must validate event order, prompt slots, semantic-loss repair, and truth policy. |
| Small-loop harness entry | `scripts/test_gcr_guided_conversation_template.sh` | Must be called by `selftest.sh` and `verify.sh`. |

## External Engine Required

| Capability | External anchor | Required declaration |
| --- | --- | --- |
| Live Gemini browser extraction | extension Chrome: repo-root `scripts/extract-gemini-conversation-browser-runtime.mjs`; CDP: `/Users/neon/antigravity/scripts/extract-gemini-conversation.mjs` | Extension receipts make this local-runnable; CDP packets still mark `external_engine_required: true`. |
| Gemini DR monitor/retry/extract engine | extension Chrome: repo-root bounded adapter; CDP: antigravity `automate.js`, `ui.js`, `data.js`, and `gemini-deep-research-extract` | Claim extension S3 runnable only when the live launch receipt and completion/extraction receipts all pass; CDP still requires the external engines. |
| S9 KG ingest | antigravity `indexing.*` modules and graph cache | Use `GCR_EXTERNAL_ANTIGRAVITY_ROOT` and `ANTIGRAVITY_GRAPH_PATH`; never hide this behind implicit path claims. |

## Historical References

Historical antigravity/northstar references inside `retarget-map.md` and older evidence notes are allowed when they describe origin, test history, or anti-patterns. They are not allowed to be used as local runnable proof unless paired with a skill-bettor artifact and a passing gate.

## Forbidden Claims

- "S0/S3/S9 are production runnable in skill-bettor" without local extractor/DR/KG engine evidence.
- "`gemini-deep-research-extract` is a local sibling skill" unless `.claude/skills/gemini-deep-research-extract/SKILL.md` exists.
- "Contextual buttons are handled" without a golden trace containing `assistant_response -> suggestion_button -> auto_prompt -> auto_answer`.
- "Semantic truth is preserved" without `missing_information`, `simplified_information`, and `missing_domain_terms` fields plus `judge-loop-chooser` routing.

## Promotion Rule

A future port can move any row from External Engine Required to Runnable Locally only after:

1. A local artifact exists under `/Users/neon/ts-skill-bettor`.
2. A paired automated gate runs without network/browser side effects by default.
3. A route-result packet records fixed prompt, iteration auto prompt, emergent prompt, dataflow edge, and evidence path.
4. `verify.sh` and `selftest.sh` both call the gate.
