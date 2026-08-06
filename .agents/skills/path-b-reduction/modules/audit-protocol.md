# Module: Path B 四步驟稽核協議 — 完整定義 + 執行模板

> 屬 [`path-b-reduction`](../SKILL.md) skill。SKILL.md 有確定性程序的 4 步骨架;本檔是各步**完整定義 +
> 原始 prompt 模板**(移植自 antigravity 版,拿掉其 northstar 專屬落地細節,見
> [retarget-map.md](retarget-map.md))。

## 四步驟完整定義

### 步驟一:尋找物理鐵錨(Locate the Invariant Base / Byte ＝ Path B)
- **定義**:找出焊死、絕對無法被 Prompt 或統計遊戲操弄的「固定大小底線」(等價硬碟裡的原始 Byte)。
- **合格錨**:exit-code / test verdict / selftest good=PASS∧hollow=FAIL(loop-harness-standard 的
  positive-control 紀律)/ external-verified primary source(見 external-verify)。**禁**把散文自述
  當鐵錨。

### 步驟二:揭露人為槓桿(Expose the Variable Lever / Tokens ＝ Path A 被 game)
- **定義**:找出最容易被當「分母」刷數據的主觀變數(被隨意縮放的 $N$)。
- **典型槓桿**:通過率字面值、命中數、覆蓋率(可被 grep checker 灌水而非真判別)、self-reported
  「品質提升」。拆穿其作弊手法。

### 步驟三:還原微觀總代價(Reconstruct Cumulative Cost / Total Loss)
- **定義**:繞過帳面平均,用鏈式法則把每次預測/條件機率相乘/系統震盪的「負對數總難度」實打實累加。
- **skill-bettor 落地**:逐 checker、逐 fixture、逐輪迭代累加真實成本(壞包/棄用/救援輪不因「不是
  config 的錯」而剔除)。

### 步驟四:見證約分消去(Perform Algebraic Cancellation)
- **定義**:總代價 ÷ 物理鐵錨,把步驟二的人為槓桿在數學與語義上直接約掉。
- **落地**:約分後留下的 = discrimination(placebo-guard 確定性 verdict)/ 真實問題解決淨流——
  「靠物理達成,不是靠模型互相同意達成」。

## 執行指令模板(Execution Command)

```
輸入課題:[待拆解的技術 / 代碼 / 架構 / 概念]
          (例:過度吹捧的微服務架構、某優化演算法、LLM-as-a-judge 的盲點)

輸出結構(四步驟強制標記):
  步驟一 物理鐵錨(Path B) → [焊死的確定性 oracle:exit-code/test/selftest/external source]
  步驟二 人為槓桿(Path A) → [哪個概率分母被刷數據,作弊手法為何]
  步驟三 微觀總代價       → [鏈式法則累加的真實總驚訝度/總資源,逐軸不掩蓋]
  步驟四 約分消去         → [槓桿約掉後的純資訊密度 / discrimination / 真實問題解決淨流]
```

## 原始 prompt 全文(出處模板,保真保留)

```
現在,請將上述「Path B 語義風格」注入你的認知體系。當我給出下述輸入時,請直接用【四步驟】強行解構,
定位底層原理,阻止我的認知卸載。

輸入課題:[請在此處輸入你想拆解的技術、代碼、架構或概念,例如:過度吹捧的微服務架構、某個優化演算法、
或 LLM-as-a-judge 的盲點]
```
