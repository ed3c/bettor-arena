# Module: path-b-reduction — antigravity → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`path-b-reduction`](../SKILL.md)。本檔 = 移植的命門與誠實帳本。

---

## 1. 為何這個 port 相對輕量——核心方法論本來就平台無關

path-b-reduction 的四步驟稽核協議(尋找物理鐵錨→揭露人為槓桿→還原微觀總代價→約分消去)是一套**純推理
紀律**,不依賴任何特定 KG/registry/machine-gate 基座——這與其他幾個 port(loop-harness-standard/
repo-agent-native)不同,那些都有明確的「antigravity 專屬 sink 層」要拿掉。path-b-reduction 沒有這層,
所以本檔的映射表很短。

## 2. 逐項調整表

| antigravity 機制 | skill-bettor 對應物 | 為何這樣調整 |
|---|---|---|
| northstar SSOT 權威(`/Users/neon/northstar/.claude/modules/path-b-semantic-reduction-engine.md`,「衝突時以 northstar 為準」) | **拿掉外部 SSOT 依賴**——antigravity 版四步驟定義已完整,不需要回指一個 skill-bettor 環境不一定能存取的第三方 repo | northstar 是 antigravity 主機上的另一個獨立 repo,skill-bettor 開發環境不保證能讀到它;方法論本身已經自足(antigravity 版早已把 northstar 概念逐項映射進本檔),不需要維持對外部 repo 的依賴鏈。 |
| `dr-research-loop` 專屬模板指針(`PATH_B_TEMPLATE`/`PATH_B_REFINE_TEMPLATE`,`dr-research-loop/modules/loop-panorama-ssot.md §3.2/§3.7`) | **拿掉**——skill-bettor 無 dr-research-loop 這條 YouTube 影片管線 | 那是 antigravity DR 管線專屬的四階段量規版模板,skill-bettor 沒有對應迴圈,本檔的通用版 `audit-protocol.md` 模板已足夠。 |
| truth-verify 案例錨(六 run 實測,`truth-verify/loop-ledger.md`) | **保留,明確標為借形案例**(know-why.md §4) | truth-verify-loop 本身未移植進 skill-bettor(見 loop-harness-standard 的補充說明),但案例本身是通用的方法論教訓(判定帶星號/顯式棄跑/物理代價入帳),值得借用當說明——已明確標註「借自 antigravity,非本地數據」,不冒充本地實測。 |
| Path A/B 軸消歧 vs Layer A/B(對照 fold-in) | **保留並強化**——新增與 skill-bettor 本地 fold-in 的直接對照表 | fold-in 已於本批移植落地,兩軸容易混淆的風險是真實的(同一個 repo 裡兩個 skill 各用一種「A/B」),需要顯式互相指認。 |
| 四步驟稽核協議本體 | **原樣映** | 平台無關的推理紀律,無需改寫。 |

## 3. 判別「retarget 成立」的鐵錨

- `.claude/skills/fold-in/SKILL.md`(Layer A/B 用法對照對象)已存在——`test -e`已驗證。
- `.claude/skills/external-verify/SKILL.md`(鐵錨查證消費對象)已存在。
- `.claude/skills/judge-loop-chooser/SKILL.md`(獨立性階梯 T0/T1 對照對象)已存在。
- truth-verify 案例明確標「借形」,不宣稱本地 SSOT 存在。

---

## Sources / Lineage
- antigravity 源:`/Users/neon/antigravity/.agents/skills/path-b-reduction/`(SKILL.md + `modules/
  {audit-protocol,know-why}.md`)。
- 更上游:northstar `path-b-semantic-reduction-engine.md`(未在本次移植鏈中直接引用,見 §2)。
