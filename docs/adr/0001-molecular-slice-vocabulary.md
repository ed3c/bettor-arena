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

## Consequences

- commit 意圖錨免費接上追溯鏈頭端(issue→commit→receipt→lineage)。
- 歷史 corpus parity receipt(data/receipts/molecular-corpus-parity.json)按舊詞彙量測,
  是凍結證據;replay 工具在新詞彙下對同語料會給出不同判決分佈,屬預期演化非缺陷。
- tracker 遷移(如 repo 換家)時 n 的解析域要隨 ADR 更新。
