# Module: First-Principles 引用-鑽入 Probe 協議（depth-drilling 追問構造）

> 屬 [`gemini-conversation-research`](../SKILL.md) §S1.5 + [mode-b-contextqa.md §S0-ALT R2-4](mode-b-contextqa.md)。回答一件事：**Mode B 逐輪 Q&A / S1.5 追問時，怎麼構造一個「鑽到底、抗放水」的追問**，而非泛泛「再要數據/案例/比較」。
> **層級**: how-to（Path A 提問紀律），**非**確定性閘。有效性靠 S6 `qa_effectiveness` / `density_yield` 事後觀測（別為它造假 eval = husk）。
> **錨**: 這是 [`path-b-reduction`](../../path-b-reduction/SKILL.md)「約分到鐵錨」的**提問側**應用（該 skill 是寫作/解構側）。

## 協議 — 四個動作（構造每一輪追問時套用）

**1. 引用-鑽入（quote-and-drill）** — 每輪追問**引用上一答最 load-bearing 的那一句/那一個詞**，把「它」當下一問的標靶，不另起新問。顆粒度逐輪收窄：句 → 詞 → 單一常數 → 單一代數步。（示範鏈：「修改 Tokenizer 詞表大小」→「每個 Token 的平均難度」→「val_bpb 裡常數的作用」→「Tokens 如何約分消掉」。）

**2. 漸進聚焦升級鏈（escalation chain）** — 一輪 Q&A 的骨架：架構級主張（拋自己的設計/intent）→ 帶外部 artifact 對質（貼 repo/論文逼它落到實證）→ 機制鑽入（問「底層移動了什麼資料/改了什麼約束」）→ **反向自陳**（動作 3）→ 要求精確推導（禁定性散文，要式子/步驟）→ 結晶（請它把方法寫成可複用提示詞/協議）。

**3. 反向自陳求校正（state-then-refute，抗放水核心）** — **把自己的理解寫成一個 claim 丟回去**（「我的理解是 X，對嗎」），而非開放式問（「這是什麼」）。開放問招致同意/補完（放水）；**已陳述的 claim 招致校正/證偽**。這逼模型扮演證偽者而非附和者。
> ⚠ 與 echo-back 區分（[conversation-pipeline.md §S1 橫向挑戰](conversation-pipeline.md)）：**echo-back = 被動重複 Gemini 末尾引導問題**（潛在缺失橫向維度，S1 旗標）。本動作是它的**解毒對立面**：不複述模型的話，是把**自己的** claim 丟給模型證偽。兩者都涉「引用」，方向相反——別混。

**4. First-principles 約分到鐵錨（reduce to anchor）** — 驅動問題永遠不是「對不對」，而是「**底層守恆量是什麼 / 哪個是可被操弄的槓桿 / 約分後剩什麼**」。當回應冒出平滑抽象名詞（效率/品質/優化 = 放水信號），用動作 1+4 鑽到 exit-code / 數字 / 代數步那層。這正是 [`path-b-reduction`](../../path-b-reduction/SKILL.md) 四步（鐵錨 → 槓桿 → 微觀總代價 → 約分消去）的提問側用法。

## 何時用（activation）

| 情境 | 動作 |
|------|------|
| Mode B S0-ALT R2-4 動態追問構造 | 引用 R(n-1) 最關鍵句 → 套四動作，取代泛泛「要數據/案例/比較」 |
| S1.5 PROBE 構造追問 prompt | 對每個 partial 維度套動作 1+3，逼 Gemini 展開到鐵錨層再判 sufficient |
| 回應出現平滑抽象名詞 / 平均值幻覺 | 動作 4：問守恆量/槓桿/約分，不接受名詞搪塞 |

## 限制（誠實，別過度宣稱）

- 這是**提問構造紀律**，不保證 Gemini 不放水——它降低放水機率（動作 3 逼證偽），但模型仍可能附和一個錯 claim。最終真假仍須 S3 DR 外部數據 / [external-verify](../../external-verify/SKILL.md) 事後查證；**提問協議不替代 external-verify**。
- 顆粒度收窄（動作 1）有上限：鑽到「單一代數步」後再鑽即離題；收斂仍走 S0-ALT 4 輪 / S1.5 2 輪上限。

---
> retarget 註：northstar 版錨 `path-b-semantic-reduction-engine.md` + `problem-graph/PG-001`（Same-Weights 自驗陷阱）。antigravity 對應物 = [`path-b-reduction`](../../path-b-reduction/SKILL.md) skill；PG-001「同權重自驗」紀律折成散文（動作 3 逼模型當證偽者而非附和者）。源：Gemini 對話 `7af1756ac3cb27e8`（Path B engine 的提問鏈本身就是活體示範）。
