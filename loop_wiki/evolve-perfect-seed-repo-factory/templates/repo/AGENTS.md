# Generated repo agent contract

- Read `.agents/skills/seed-repo-operator/SKILL.md` before planning work.
- Treat `data/source.json`, `evidence.jsonl`, `claims.jsonl`, `unknowns.json`,
  `decisions.jsonl`, and `lineage.json` as separate evidence-bearing records.
- Run `bun run scripts/plan.ts --task "<task>"` to produce exactly twenty local
  function calls.
- Run `bun run quality:fast` before behavior work; it checks minimum lineage,
  formatting, lint, and strict types with local locked dependencies.
- Do not present the result as twenty external model/tool calls.
- Do not edit evidence or lineage to make a task pass.
- Human admission remains required.
