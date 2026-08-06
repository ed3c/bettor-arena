# Module: harness-wiki — antigravity → skill-bettor retarget 映射 + 誠實帳本

> 屬 [`harness-wiki`](../SKILL.md)。本檔＝移植的命門與誠實帳本。

---

## 1. 為何不能逐字複製——antigravity 原版 95% 是它自己 10 條迴圈的組件卡

antigravity `antigravity-harness-wiki` 的組件卡列了 10 條它自己的迴圈:`repo-wiki-converge`／
`repo-agent-native`／`dr-research-loop`／`gemini-conversation-research`／`ds-workflow-loop`／
`truth-verify-loop`／`design_governance`……**這些迴圈 skill-bettor 完全沒有**,逐字複製這張表毫無意義
——搬過來的會是一張列著不存在系統的空表。

真正可搬的是**這份文件的存在理由本身**:「迴圈一多,就需要一張指針式全景圖防止改任一階段時互相
漂移」。skill-bettor 現在只有 1 條已落地迴圈(演化 op)+ 1 條規劃中迴圈(DR proposal),組件卡因此
天生就薄——這是**誠實反映現況**,不是刻意精簡。組件卡會隨新迴圈落地 additive 增列。

## 2. 逐機制 retarget 映射表

| antigravity 機制 | skill-bettor 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| 10 條迴圈組件卡(repo-wiki-converge/dr-research-loop/ds-workflow-loop/……) | **換成 skill-bettor 自己的組件卡,隨落地 additive 增列** | antigravity 的迴圈在 skill-bettor 不存在,硬搬＝死指針。初始只列 skill-bettor 當時存在/規劃中的迴圈;後續 clc、N-variant、dx-adversarial-fix、plan-truth production seed 依真落地證據追加。 |
| N×M host×driver 全景圖(`loop-architecture-ssot.md` §⓪) | **拿掉** | 同 `loop-harness-standard/modules/retarget-map.md` 已記錄的理由:skill-bettor 恆單 host,不存在 host 翻面的問題。 |
| 8 防退化鐵律技術等價表(仿 ix-agy 三欄) | **併入 loop-harness-standard 的防退化鐵律,不在本檔重複** | 那張表本來就是「建新迴圈的工程規範」範疇,職責上屬 loop-harness-standard,本檔(記錄現有)不重複列。 |
| 「husk retarget 帳」(質數 demo/agy CWD 假設/Gemini cache 門檻/skills.json 不搬) | **不搬這份具體清單,改成本檔§1 自己的移植帳本** | 那份清單記的是 antigravity 從 ix-agy 移植時拿掉什麼,是它自己的歷史,不是 skill-bettor 的移植決策。 |
| §⑦「為何不/鏡像對立防誤改記錄」(northstar flywheel/emergence-trace-recorder 等) | **不搬** | 這些是 antigravity 對比 northstar 架構的具體歷史決策,skill-bettor 沒有對應的候選架構要拒絕。 |
| §⑧「邊界與落地程度記錄」+「缺口/漂移 SURFACE」 | **不搬** | 記的是 antigravity 各 skill 當時的邊界爭議與已知指針漂移,skill-bettor 沒有這些具體 skill。 |
| 「不可簡化的不變量」清單(SOURCE=SSOT funnel/各閘不共用/prompt SSOT 單一真源等) | **精簡後原樣映**(5 條,見 SKILL.md) | 這是全篇少數真正跨專案通用的部分——「知識單向流」「各閘不共用」「收斂=人 admit」對任何多迴圈系統都成立,只是把措辭換成 skill-bettor 的知識單向流(proposals→驗證→merge)。 |
| 組合/遞迴圖(內容收穫源→repo 掌握階梯→應用閉環) | **換成 skill-bettor 自己的每日管線圖**(SKILL.md「組合圖」) | 圖形式(疊加關係視覺化)可轉移,內容全換成 ARCHITECTURE.md §9 已定義的管線。 |

## 3. 拿掉的東西不是「簡化」,而是「對應迴圈本來就不存在」

- **能映的映**:全景圖的存在理由(指針不複製防雙圖漂移)、少數幾條真正跨系統的不變量(知識單向流、
  各閘不共用、收斂=人 admit)、組合圖的圖示形式。
- **對應迴圈不存在、真拿掉**:10 條 antigravity 專屬迴圈組件卡、N×M host×driver 全景。
- **antigravity 自己的歷史決策記錄、不搬**:husk retarget 帳、northstar 對比記錄、邊界爭議記錄。

## 4. 判別「retarget 成立」的鐵錨
- SKILL.md 組件卡每一列都必須可查證:有 owner SSOT、資料流、收斂閘、證成狀態。
- 新增迴圈前,先確認它接上「收斂原語+自己的閘」(loop-harness-standard §1 recipe),再回本圖
  additive 增列——不預先虛構欄位撐場面。

---

## Sources / Lineage
- antigravity 源:`/Users/neon/antigravity/.agents/skills/antigravity-harness-wiki/`(SKILL.md +
  `modules/{loop-architecture-ssot,token-efficiency-anchors,composition-and-prompts}.md`)。
  `token-efficiency-anchors.md`(Superpowers 6 降本實測錨)整份**不搬**——那是外部研究筆記,與「多迴圈
  組合地圖」職能無關,誤植進本檔屬 antigravity 自己的模組邊界問題,不隨本次移植複製。
- skill-bettor 既有同構:`ARCHITECTURE.md` §1(三層飛輪→大小迴圈映射表)、§9(每日管線)——本檔的
  組件卡/組合圖是這兩節的「地圖化」呈現,不重複其內容,只加「指針不複製」的紀律外殼。
