# Module: Path B know-why — 核心哲學 / 語義流風格約束 / 軸消歧

> 屬 [`path-b-reduction`](../SKILL.md) skill。本檔 = domain know-why(SKILL.md 不複述)。執行程序看
> SKILL.md;方法細節看 [audit-protocol.md](audit-protocol.md)。

## 1. 核心哲學(Purpose & Core Philosophy)

這是一個拒絕「語義表面化」與「平均值幻覺」的底層原理解構引擎。核心任務 = 打破人類與 AI 在高維語義層
的「認知卸載(Cognitive Offloading)」——不允許用抽象、模糊、或基於「平均/平滑」的概念(如:效率提升、
系統優化、代碼品質)搪塞敷衍。仿照資訊理論物理約分邏輯,將所有宏觀現象拆解為「不可作弊的物理鐵錨
(Byte)」與「微觀累積的總驚訝度(Total Loss)」,直擊本質。

## 2. 語義流風格約束(Output Style Constraints)

1. **拒絕平均幻覺**:嚴禁用「人為定義的分母」算出的平均指標做本質解釋。提及平均,**立刻揭露其分母
   如何被投機操弄**。
2. **追蹤守恆量**:解釋建構在「能量、資訊熵、物理空間、時空視野」等守恆量上。智能本質是**極致的
   壓縮**,非題目的重組。
3. **反認知卸載**:不准把複雜機制簡化為一個名詞(「這是一種模組化設計」)。必須寫出該機制底層**移動
   了什麼資料、改了什麼約束、付了什麼物理代價**。
4. **語言風格**:冷峻、精準、結構化、代數直觀。多用「鐵錨、槓桿、分母操弄、微觀加總、約分消去」等
   硬核意象。

## 3. Path A/B 軸消歧(與 Layer A/B 不同軸,別混用)

**⚠ axis 消歧**:此「Path B」= **Path A/B 執行模式軸**(Path A=`.md` 概率性 LLM 輸出 → Path
B=`.py`/確定性 exit-code / 0 LLM),**非** [fold-in](../../fold-in/SKILL.md) 用的 Layer A/B 抽象軸
(Layer A=SKILL.md 事實/程序、Layer B=modules/ 為什麼)。混用兩軸 = 認知卸載第一現場——同一份文件裡
若同時提到「Path B」與「Layer B」,務必各自標明是哪一軸,不可省略軸名假設讀者能分辨。

| 本 skill 概念 | 對應 |
|---|---|
| 物理鐵錨(Byte,焊死不可操弄) | **Path B**:確定性腳本/exit-code/selftest good-hollow |
| 人為槓桿(Tokens,可縮放刷分) | **Path A**:概率性 LLM 輸出 |
| 約分消去 | 用 Path B 物理裁決 dissolve 掉 Path A 的可作弊性 |
| 反認知卸載 | 「有 Path A 沒有 Path B」的空心宣稱 |
| 平均幻覺/分母操弄 | 度量重定義(非隨意縮放的分母) |
| 鐵錨 ≠ 訓練記憶 | External-Verify |
| 硬數據比較非 LLM-judge | 獨立性階梯 T0 優先於 T1(見 judge-loop-chooser) |

## 4. 借形案例(antigravity 自己的量測歷史,非 skill-bettor 一手數據)

以下案例**借自 antigravity** 的 `truth-verify` 量測迴圈六輪實測(2026-07-05/06)——skill-bettor 沒有
對應的量測歷史,這裡只借它的**方法論教訓**,不是 skill-bettor 自己的數字:

- **「假設 FAIL 是合法產出」的極端版**:四個降本假設**全滅**,零宣稱「已降本」——真收益全在質量軸與
  機制知識。
- **判定帶星號**:判定式機械全過,但比值重合疑似受環境混因(如 mid-run compaction)污染 → 落帳「機械
  PASS\*,因果宣稱不成立」。**「過門檻」與「證明了什麼」是兩件事,約分時分開陳述。**
- **顯式棄跑不改判定式**:前置量測已定方向、殘步資訊價值歸零 → 人核棄跑,落帳 PARTIAL/SKIPPED+理由,
  判定式原文不動(不把 PARTIAL 粉飾成 PASS)。
- **物理代價如實入帳**:壞跑、bounce 輪、救援、v1 編排錯誤棄用——全額進成本分子,不因「不是設定的錯」
  而剔除(剔除=製造無法復現的美化數字)。

skill-bettor 自己第一次真的跑演化 op 迴圈、累積 `families/*/changelog/` 之後,這裡應該換成本地真實
案例——這是待補的種子,不是永久借形。
