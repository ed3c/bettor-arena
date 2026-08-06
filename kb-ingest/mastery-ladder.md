# Repo mastery ladder — layered escalation SSOT (shared by repo-wiki-converge + repo-agent-native)

> Single source of truth for "wiki 收斂 ≠ repo 掌握". repo-wiki-converge is the ENTRY layer; complete mastery is a
> LAYERED set, each layer its own artifact + its own convergence gate. **Funnel is never inverted: SOURCE code =
> SSOT for every layer.**
>
> **2026-08-04 起 L1 換引擎**：L1 從「Gemini 作者 × Opus 判官 ≥90 protocol」改為 langchain-ai/openwiki 官方
> code-mode 程序的 host-native 移植（官方提示詞逐字 + 官方三閘 + 官方確定性後處理，NO API KEY）。升層決策
> 不再由判官 protocol 觸發，改為 **demand-pull**：L1 收斂後由人／goal 決定升不升層（見不變量 4）。
> 逐機制映射與退役帳本 → `.agents/skills/repo-wiki-converge/modules/official-port-map.md`。

## The ladder (each `kind` stays non-overlapping in the KG)

| L | Need it answers | Skill / entry | Artifact (`kind`) | Convergence gate |
|---|---|---|---|---|
| **L1 理解** | 「這 repo 是什麼、怎麼運作」(廣度理解 wiki) | `repo-wiki-converge` | `<TARGET>/openwiki/`(OKF v0.1)，快照 `<OUT>/repo_wiki/<slug>/` 進 KB | 官方三閘：`skeleton_critic` 無 UNRESOLVED ∧ `wiki_answer_verifier` 全 PASS ∧ `finalize` 零壞鏈(人 admit) |
| **L2 不變量** | 「精確契約／隱含依賴／確認的缺席，各釘哪行」(源碼級 typed 事實) | `repo-agent-native` | `<OUT>/invariants/<slug>/` (`kind=invariants`) | Evidence `a_ratio ≥ 0.80` ∧ `unverified=0` ∧ 新事實趨零(SURFACE，人裁) |
| **L3 掌握＋規格** | 「完整掌握 + 正式規格(隱含設計合約)」 | `/specs-as-code` → repo-agent-native | `<TARGET>/.knowledge_base/{architecture_map,data_flow_and_api,security_and_bottlenecks}.md` | evaluator-first answer-key 計分 + **RIP 封頂**(behavioral claim 真跑定案) |
| (旁) 結構圖 | 「架構/組件關係互動 KG」 | `understand-anything:understand` | 互動知識圖 | plugin 自帶 |
| (旁) runtime 黑盒 | 「runtime-only 反覆失敗、源碼 A 級解不了」 | `repo-fullstack-debugger` | L0-L4 診斷 → 畢業 playbook | 畢業 playbook |

全部 sink 進 `.cache/kg/graph.json`，靠 `kind` frontmatter 保持不重疊；全部經 `python3 -m indexing.ingest_repodoc_cli` 進 KB。

## Handoff（誰種子誰；不倒置 funnel）
- **L1 → L2**：L1 收斂 wiki 的**子系統圖 + `covers` 概念清單**種子 L2 的 **S0 SCOPE**（決定「抽哪些子系統/契約」）。但 **facts 仍來自源碼 A 級 + `source_ref`**——wiki 散文**不當事實源**（它無 source_ref，funnel 不可倒置）。
- **L2 → L3**：L2 的 source-anchored 不變量 + L1 wiki 一起餵 L3 規格生成（8-probe 把 wiki/brief 的假設當**待證命題**回源碼證偽）。
- **L2 ↔ repo-fullstack-debugger**：L2 的 S2.5 破盒推論若是 runtime-only 無法 A 級解析 → 交棒 debugger。
- **旁 understand-anything**：任何層要「結構關係互動圖」時併用，補視圖。

## 路由決策（goal → 該停在哪層）
```
goal = 廣度理解「是什麼/怎麼運作」        → L1 收斂即止，ingest。
goal = 精確契約/隱含依賴/確認的缺席        → L1 種子 → L2。
goal = 完整掌握 + 正式規格(設計合約)       → L1 → L2 → L3(/specs-as-code)。
goal = 架構組件關係互動圖                  → understand-anything（可並任一層）。
goal = runtime-only 黑盒反覆失敗           → repo-fullstack-debugger。
```

## 不變量（跨層共用，違反即停）
1. **SOURCE=SSOT 漏斗不可倒置**：源碼是每層主幹；wiki/DR 只**種子 scope／補外部缺口**，不當事實源。
2. **每層各有各的閘**：L1 官方三閘(critic + QA 迴圈 + finalize)；L2 Evidence a_ratio；L3 evaluator-first + RIP。**不共用、不代理**——L1 收斂不代表 L2/L3 綠。
3. **`kind` 保持不重疊**：RepoDoc(prose) / invariants / specs 各自 kind，KG 不打架。
4. **升層是 demand-pull，非自動**：L1 收斂後由人/goal 決定升不升層,不自動 chain。

> SSOT 交叉引用：L1 = `.agents/skills/repo-wiki-converge/`(`.claude/` 為 symlink) + `kb-ingest/openwiki/`(官方提示詞資產) + `kb-ingest/{openwiki_post.py,openwiki_subagent.sh}`；L2/L3 = `.claude/skills/repo-agent-native/` + `modules/{extraction-methodology,codebase-mastery-methodology,specs-as-code-prompt}.md` + `/specs-as-code`。
