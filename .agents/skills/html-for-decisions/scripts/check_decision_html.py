#!/usr/bin/env python3
"""check_decision_html — html-for-decisions 不變量的 T0 機械驗證（零 LLM）。

WHY: skill 的不變量（自包含/投影宣告/快照日期/quiz 閘/title）若只是散文紀律，
就是「規則存在但無 activation loop」的半橋。本腳本把可機械判的子集收斂成 exit code。
生成 HTML 仍由 agent 親寫（無轉換器）——本腳本只驗不產。

CHECKS（全部唯讀）:
  declare  — 頁面帶「本頁為投影非 SSOT」宣告（不變量 2 前半）
  snapshot — 帶快照日期（快照…YYYY-MM-DD；不變量 2 後半）
  selfhost — 自包含：無外部資源載入（src=/href=/​@import/url( 指向 http(s)；不變量 3）
  quiz     — quiz 閘存在（radio 題組 + 判卷函式 + 「全對」判準字樣；不變量 4）
  title    — <title> 存在（決策面可被分頁辨識）

EXIT:
  0 PASS 全過 · 2 FAIL 任一不過（逐項印 PASS/FAIL＋證據）· 1 用法/檔案錯
  --selftest: 正控鑑別（合成 good fixture 應全 PASS；剝除宣告與 quiz 後的 hollow 版應 FAIL）
             ——placebo checker 防護（分不出 good/hollow 的 checker 不算活）。

retarget 記事（skill-bettor 版 vs antigravity 原版）:
  原版 selftest 讀 skill 自帶的 reference/loop-panorama-decisions.html 當 good fixture。
  skill-bettor 決定不把該檔內容當本地案例(見 modules/retarget-map.md)，故本檔的 selftest 改為
  完全合成的最小 fixture(手法同 context_trace.py 的 --selftest)——不依賴 reference/ 目錄下任何
  檔案是否存在，checker 的可攜性因此與「要不要保留 antigravity 的示範 HTML」這個決策解耦。
"""
import re
import sys
from pathlib import Path

EXTERNAL_RES = re.compile(
    r'(src|href)\s*=\s*["\']https?://|@import\s+["\']?https?://|url\(\s*["\']?https?://',
    re.IGNORECASE,
)

# 合成正控 fixture——只求踩中五個 CHECKS 的判定條件，不追求 schema 完整（schema 完整度由
# prompts/decision-report.prompt.md 的契約 + 人眼 open 目檢負責，不是本腳本的職責）。
GOOD_FIXTURE = (
    "<title>決策面 selftest 樣本</title>\n"
    "<div class=\"mast\">\n"
    "  <p>本頁為投影非 SSOT。快照 2026-01-01。</p>\n"
    "</div>\n"
    "<section>\n"
    "  <form id=\"quiz\">\n"
    "    <label><input type=\"radio\" name=\"q1\" value=\"a\"> A</label>\n"
    "    <label><input type=\"radio\" name=\"q1\" value=\"b\"> B</label>\n"
    "    <button onclick=\"grade()\">交卷</button>\n"
    "    <p>全對才算通過。</p>\n"
    "  </form>\n"
    "</section>\n"
    "<script>function grade(){return true}</script>\n"
)


def run_checks(text: str):
    results = []

    def add(name, ok, evidence):
        results.append((name, ok, evidence))

    m = re.search(r"本頁為投影非 SSOT|投影非 SSOT", text)
    add("declare", bool(m), m.group(0) if m else "缺「本頁為投影非 SSOT」宣告")

    m = re.search(r"快照[^\n<]{0,40}?(20\d{2}-\d{2}-\d{2})", text)
    add("snapshot", bool(m), f"快照日期 {m.group(1)}" if m else "缺快照日期（快照…YYYY-MM-DD）")

    ext = EXTERNAL_RES.findall(text)
    add("selfhost", not ext, "無外部資源載入" if not ext else f"外部資源載入 {len(ext)} 處（CDN/遠端 src|href|@import|url）")

    has_radio = 'type="radio"' in text
    has_grade = re.search(r"function\s+grade|grade\s*=\s*\(", text) is not None
    has_pass_criterion = "全對" in text
    ok = has_radio and has_grade and has_pass_criterion
    add("quiz", ok, "radio 題組＋判卷函式＋全對判準齊" if ok
        else f"quiz 缺件（radio={has_radio}, 判卷={has_grade}, 全對判準={has_pass_criterion}）")

    m = re.search(r"<title>([^<]{1,80})</title>", text)
    add("title", bool(m), m.group(1) if m else "缺 <title>")

    return results


def report(results, label):
    all_ok = True
    print(f"check_decision_html — {label}")
    for name, ok, evidence in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:8s} {evidence}")
        all_ok = all_ok and ok
    return all_ok


def selftest():
    if not report(run_checks(GOOD_FIXTURE), "good（合成正控 fixture，非讀外部檔）"):
        print("SELFTEST FAIL: 合成正控應全 PASS", file=sys.stderr)
        return 2
    hollow = GOOD_FIXTURE.replace("本頁為投影非 SSOT", "").replace('type="radio"', 'type="_x"')
    hollow_results = run_checks(hollow)
    hollow_failed = [n for n, ok, _ in hollow_results if not ok]
    if "declare" in hollow_failed and "quiz" in hollow_failed:
        print(f"  [PASS] hollow   剝除宣告/quiz 後如預期 FAIL（{','.join(hollow_failed)}）——checker 有判別力")
        print("SELFTEST PASS")
        return 0
    print("SELFTEST FAIL: hollow 版未被抓出 → placebo checker", file=sys.stderr)
    return 2


def main(argv):
    if len(argv) == 2 and argv[1] == "--selftest":
        return selftest()
    if len(argv) != 2:
        print("用法: check_decision_html.py <decision.html> | --selftest", file=sys.stderr)
        return 1
    target = Path(argv[1])
    if not target.is_file():
        print(f"ERROR: 檔案不存在 {target}", file=sys.stderr)
        return 1
    ok = report(run_checks(target.read_text(encoding="utf-8")), str(target))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
