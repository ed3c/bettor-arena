# Module: product-ops — 營運 know-why(效益帳+tier 成本結構+信任論證)

> 屬 [`product-ops`](../SKILL.md)。SKILL.md=runbook;本檔=為何這樣營運。數字皆 2026-07-11/12 實測。

## 1. 效益疊加帳(每個機制對迴圈工程值多少;fold-in 自首日全流程)
| 機制 | 實測效益 | 疊加型態 |
|---|---|---|
| D3 對抗層(fresh Opus,DR 迴圈) | 三題共 **11 條 block-admit findings** 全實查證實(4+4+3),含一條戰略級證偽(pinescript 藍海→紅海,0bbb26a)——無 D3 則全數流進產品決策 | **DR 迴圈質量的主來源**;每題 T0 綠後固定收益 |
| external-verify 段(fresh Claude 釘數字) | 10 組真值釘死;揪出內容農場數字+幻覺指紋數字各一(agy 自查=同權重,無效) | 每題數字類 needs_diamond 的固定收益 |
| check_licenses L3(GitHub API 實抓,04b5c06) | codex 題 2 例謊標「會在 iter 內被打回」(hollow fixture 鎖證)——把 D3 一類活轉成 T0,省一輪 feedback | 一次機械化,之後每題白吃 |
| engine 判活 diff(2026-07-12,exit 22) | 把「判活=target diff」從 orchestrator 手工紀律轉成 load-bearing 代碼(正負控實測);silent no-op 不再依賴人眼 | 一次機械化,每次 dispatch 白吃 |
| **Stage 1 廣度段(訂閱池瀏覽器 DR)** | **誠實負結論:drift 無改善**(無 Stage 1 的 codex=0.52;有 Stage 1 的 cross-market/pinescript=0.48/0.52),agy dispatch 次數也未降(皆 1)——效益只在額度轉嫁+源池廣度([推論]),**不在質量** | 質量投資該繼續押對抗層,非收集層 |
| token 上限校準(mock 尺度→真實 harness) | 沒有它兩 arm 全判 0,原點量測作廢 | 一次修正,之後每次評測都站在上面 |
| engine/run 分層 | 修掉 2 個 stop-loss 失效 bug(tee 吃 rc/單調進度) | **乘法級**:每條 op 沙盒免疫同類 bug,迴圈控制單點維護 |
| 三層閘+content-hash 快取 | iter1 真攔不可解案例(擋壞考題污染 holdout);real 層省 ~67% 昂貴驗證 | 每條 spawn-cases op 重複收益 |
| selftest 正控(good∧hollow) | 30 秒買到「判分器沒死」;是其他所有數字可信的前提 | 每次 harness 改動後固定收益 |
| 多 tier 語意驗證+判官矩陣 | 把「Δ 只是格式」翻案成「Sonnet tier 含語意價值」;白撿跨家族齊平=案例非單模型技巧 | 每批新案例的畢業段固定收益 |
| 量尺釘死(Sonnet 重落基線) | holdout 0.833=第一個可被超越的誠實目標;跨量尺不可比防曲線造假 | 產品信任的地基 |

## 2. tier 成本結構(實測,營運排程依據)
- 機械層:4 個 Haiku subagent(各管一 arm,15 次真跑編排)≈ 10 萬 tokens 級——便宜到可以每批跑。
- 裁決層:1 個 Opus fresh 判官(15 份報告矩陣)≈ 5.5 萬 tokens——只在畢業段跑一次,不進機械迴圈。
- 被測層:eval agent 釘 Sonnet(非 Fable)——量尺穩定且成本可控,弱於編排 tier 反而放大 skill 可測價值。
- 編排層:Fable 主 session 只做分解/指揮/admit 準備——最貴的模型不做機械事(tier 錯配=浪費或漏抓)。
- DR 批次(2026-07-11 首跑實測):agy 1 dispatch 內部自迭代補齊 14 維+13 URL(免 Claude quota,
  跨家族隔離白吃);D3=1 Opus fresh(~5.5 萬 token 級,只在 T0 綠後跑一次);feedback 輪=1 agy
  單發。每題全程 3 次 LLM 調用級——研究批次的貴不在 LLM 而在 D3 逐錨實查,故 D3 永不進機械內迴圈。

## 3. 為何雙軌成長曲線(機械+語意)
2026-07-11 實證:5 個無 skill tier 機械分完全齊平(0.5/0.667/0.667),但語意上裸 Sonnet/Haiku 在
誤報陷阱捏造機制、agy 3.1 Pro evasion 改寫——**機械分對「產品真正賣的東西」(判斷品質)全盲**。
只發布機械軌=給自己留 Goodhart 後門(塞格式分就能讓曲線上漲);雙軌同升才是可信成長,
這正是訂閱者付費的證據本體,也是 fork 不走的資料資產。

## 4. 為何人閘不可自動化(產品論證,補 ARCHITECTURE §8 的工程論證)
訂閱者買的是「每天變強」的**可信度**。自動 merge 的曲線=平台自己出題自己閱卷自己發獎——
一次過擬合事故(壞案例入 holdout、膨脹 diff 過閘)就毀掉「eval 曲線不可造假」這個唯一賣點。
人 admit 每天 5 分鐘=產品信任的保險費;walk-forward 全綠之後仍需人按實盤鍵,同一條紀律。

## 5. 營運節奏(成本紅線的執行形)
- 每日:增量評測(diff 觸及的案例+smoke set)+晨檢;集中一次批次,不按訂閱者人數跑(PRODUCT.md 紅線)。
- 每週:全量 suite+trigger evals。
- 每次 spawn:trigger evals 必跑(正交性);每次輪替:runs=3+judge-cmd+semantic_pass_rate 量測。

## 6. 為何大迴圈不沙盒化八大基座(防「補完主義」誤改;鏡像 antigravity 為何不記錄)
八大基座是給**無人值守執行體**的裝甲——被動上下文防漂移、stop-loss 防空轉、獨立 verifier 防自證,
全部在替「沒有人在場」兜底。大迴圈(主 session)有人在場,它的基座等價物早已存在且形態不同:
被動上下文=root CLAUDE.md(派生)+SSOT 文件;目標合約=PRODUCT.md/ARCHITECTURE.md;調度=engine.sh;
狀態帳本=git history+各家族 changelog;verifier=**人閘本身**。
若未來有人想「幫大迴圈也建一套沙盒+自動迭代」——擋下:那等於把人 admit 埋進自動化迴圈,
正是產品信任模型(§4)要防的事。大迴圈的「不完備」是設計,不是缺件。
