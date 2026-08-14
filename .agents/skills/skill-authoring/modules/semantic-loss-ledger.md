# Semantic-loss ledger — skill-authoring official profile refactor

Baseline 是 bettor-arena commit `266c0af7d6389e15b6f92cd2af7f8859c4c40b9a` 的 `.agents/skills/skill-authoring/SKILL.md`。本帳只說每項舊語意現在住哪，不把「刪短了」當成功。

| 舊語意單元 | 分類 | Current durable home | Check |
|---|---|---|---|
| 建 Skill 前先找既有 owner | `ACTIVE_IN_SKILL` | `SKILL.md` Current procedure 1 | 人工讀取 Match 段 |
| slim core + know-why modules | `ACTIVE_IN_SKILL` | `SKILL.md` Current procedure 3–4；`legacy-skill-2026-08-14.md` 保存移出的歷史內容 | package-specific entrypoint budget + body≤500 ceiling |
| semantic-loss ledger 與 domain terms | `ACTIVE_IN_SKILL` | `SKILL.md` Current procedure 2 | 本帳存在且主檔有 pointer |
| scripts 承載確定性邏輯 | `ACTIVE_IN_SKILL` | `SKILL.md` Current procedure 5–7 | conformance selftest + mutations |
| Codex/Claude discovery 與 invocation | `PRESERVED_IN_MODULE` | `official-agent-skills-profile.md` | primary URLs + host summary |
| typed execution、hard/advisory assertion | `PRESERVED_IN_MODULE` | `execution-and-assertions.md` | local harness schema pointers |
| 行為遵循消融與程序泛化 | `ACTIVE_IN_SKILL` | `SKILL.md` Current procedure 9；`execution-and-assertions.md` 行為量測與比較 | 四臂同 subject/evaluator、alias advisory、mutation/cross-harness receipt requirements |
| `families/` 商品工場、舊 GCR/eval gates | `LEGACY_ARCHIVED` | `legacy-skill-2026-08-14.md`、`authoring-clauses.md`、`panorama.md` | archive banner，不再進 model-visible core 或宣稱 current |
| 舊 `check_all_skills.py`、`check_ssot_index.py` inventory | `LEGACY_ARCHIVED` | `defense-form-ssot.md` | legacy banner + 主檔降級說明 |
| Claude-only `!` expansion、`context: fork` | `CANONICAL_OWNER_WITH_LEGACY_COPY` | Claude official docs；舊文留 `authoring-clauses.md` | portable core 明示不得依賴 |
| ASCII colon 禁令 | `LEGACY_ARCHIVED` | `legacy-skill-2026-08-14.md` 可追；active rule 已反駁 | positive control 含 block colon |

Physical Codex/Claude A/B 由各被重構 Skill 的 delivery slice 產 receipt；本次 `skill-authoring` 只建立共同 protocol，不代替 runtime run。
