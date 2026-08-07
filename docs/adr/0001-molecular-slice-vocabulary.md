# 0001 — Molecular Intent-Slice 詞彙錨定 Forgejo issue(ISSUE-<n>)

日期:2026-08-06 · 狀態:accepted(人裁)

## Context

molecular commit-msg 閘要求 protected surface(.githooks/、scripts/gates/)的 commit 帶
Intent-Slice 意圖錨。重建自來源 repo 的閘原硬編其詞彙表(GCR-SLICE-/TS-SLICE-/
GOLDEN-FLOW-SLICE-/HARNESS-CROSS-CUTTING-),啟用後會拒掉本 repo 自己的閘面維護 commit。

## Decision

Intent-Slice 唯一合法形態=`ISSUE-<n>`,n 錨 ts-skill-bettor Forgejo tracker 的 issue 編號
(PRD #2、切片 #3–#13、殘債 #14–#20 及其後)。

## Alternatives rejected

- **沿用來源 repo 三前綴**:把 ts-skill-bettor 的拓撲二次寫進本 repo 合約——正是重建時
  剝除清單剛清掉的東西。
- **自創新前綴系統**:issue tracker 已是本計劃意圖鏈的事實 SSOT,第二套編號=雙圖漂移源。

## Amendment 2026-08-07(人裁):Intent-Slice 僅限小迴圈,閘按角色過濾

原 Decision 只定了**詞彙**,判準仍是「碰到 protected surface 就要 Intent-Slice」。那條把
「改了哪個檔」當成「誰觸發的」——但控制面本來就由兩種角色維護:小迴圈按切片改它,大迴圈
做基礎設施維護也改它,而**大迴圈沒有切片可指**。

觸發這次修正的實例:共用 skills 遷移要改 `scripts/gates/check_skill_pointers.py`(它的解析語意
與共用 checkout 相衝)。那不是任何一張 issue 的切片,舊判準卻要求一個 `ISSUE-<n>`——唯一能過閘
的方法是捏一個號碼,而**捏號碼比不可追溯更糟**:它把追溯鏈頭端指到錯的意圖上,而且看起來是對的。

新判準:`requiresMolecular(paths) = 碰 protected surface **且** 碰 `loop_wiki/`。
小迴圈改閘要指切片;大迴圈改閘走一般 commit 紀律(subject 形狀仍驗,只是不強制 molecular block)。
若訊息裡**主動**帶了 molecular block,欄位完整性與順序照驗——不因為不強制就不檢查。

四條正負對照落在 `validate_molecular_message.ts` 的 selftest:小迴圈碰閘要 slice、大迴圈碰閘
不要、小迴圈沒碰閘不算閘變更、一般編輯不要。

## Consequences

- commit 意圖錨免費接上追溯鏈頭端(issue→commit→receipt→lineage)。
- 歷史 corpus parity receipt(data/receipts/molecular-corpus-parity.json)按舊詞彙量測,
  是凍結證據;replay 工具在新詞彙下對同語料會給出不同判決分佈,屬預期演化非缺陷。
- tracker 遷移(如 repo 換家)時 n 的解析域要隨 ADR 更新。
