#!/usr/bin/env python3
"""product_board — 產品後台觀測面(零 LLM 機械投影;與決策面語義隔離,不變量 7)。

投影源:product/state.json(產品機器帳)+各家族 FAMILY.yaml(雙軌現值)。
內容:落地階段梯/訂閱與方案 vs token 成本(未上線=誠實 N/A)/數據驅動決策規則表/家族資產現值。
零判定、無 quiz、非 SSOT;訂閱數只從 state.json 讀,null 一律顯示「未上線」——禁投影假數。

用法: product_board.py <repo_root> -o <out.html> --as-of YYYY-MM-DD
      --selftest = 合成 fixture 正控
exit: 0 / 1 用法錯 / 2 selftest 失敗
"""
import argparse
import html
import json
import sys
from pathlib import Path

OK, WARN, RISK, INFO, MUTE = "#1A7A4A", "#B45309", "#B3382C", "#1D6FA8", "#7A5CB8"
CSS = f"""
body{{font-family:-apple-system,'PingFang TC','Noto Sans CJK TC',sans-serif;margin:0;
background:#F7F6F2;color:#1F2937;line-height:1.55}}
.wrap{{max-width:1080px;margin:0 auto;padding:28px 20px 60px}}
.banner{{background:#FFF7E6;border:1px solid {WARN};border-radius:8px;padding:10px 14px;font-size:13px;margin-bottom:18px}}
h1{{font-size:26px;margin:6px 0}} h2{{font-size:17px;margin:26px 0 10px;border-bottom:2px solid #E5E1D8;padding-bottom:6px}}
.eyebrow{{font-size:12px;letter-spacing:.14em;color:{INFO};font-weight:700}}
.tiles{{display:flex;flex-wrap:wrap;gap:12px}}
.tile{{flex:1 1 150px;background:#fff;border:1px solid #E5E1D8;border-radius:10px;padding:14px}}
.tile .n{{font-size:24px;font-weight:800}} .tile .l{{font-size:12px;color:#6B7280;margin-top:2px}}
table{{border-collapse:collapse;width:100%;background:#fff;font-size:13px}}
th,td{{border:1px solid #E5E1D8;padding:6px 9px;text-align:left}} th{{background:#EFEDE6}}
.chip{{display:inline-block;padding:1px 8px;border-radius:999px;color:#fff;font-size:11.5px;font-weight:700}}
.ladder{{display:flex;gap:6px;margin:10px 0}}
.step{{flex:1;border-radius:8px;padding:10px;color:#fff;font-size:13px}}
.note{{font-size:12px;color:#6B7280}}
footer{{margin-top:34px;font-size:12px;color:#6B7280;border-top:1px solid #E5E1D8;padding-top:10px}}
"""

STATUS_COLOR = {"done": OK, "pending-gate": WARN, "not-started": "#9CA3AF"}


def chip(t, c):
    return f'<span class="chip" style="background:{c}">{html.escape(str(t))}</span>'


def na(v, unit=""):
    return "未上線(N/A)" if v is None else f"{v}{unit}"


def collect(root: Path):
    import yaml
    state = json.loads((root / "product" / "state.json").read_text(encoding="utf-8"))
    families = []
    for fy in sorted(root.glob("families/*/FAMILY.yaml")):
        d = yaml.safe_load(fy.read_text(encoding="utf-8"))
        for sk in d.get("skills", []):
            families.append({"family": d["family"], "skill": sk["id"], "status": sk["status"],
                             "m": sk.get("metrics", {})})
    return state, families


def render(state, families, as_of: str) -> str:
    subs = state["subscribers"]
    plans = state["plans"]
    ca = state["cost_anchors"]
    est = "" if ca.get("measured") else "(估算,S1 實測回填)"
    ladder = "".join(
        f'<div class="step" style="background:{STATUS_COLOR.get(s["status"], MUTE)}">'
        f'{s["id"]} {html.escape(s["name"])}<br><small>{html.escape(str(s.get("evidence") or "—"))}</small></div>'
        for s in state["stages"])
    fam_rows = "".join(
        f"<tr><td>{html.escape(f['family'])}/{html.escape(f['skill'])}</td><td>{f['status']}</td>"
        f"<td>{f['m'].get('success_rate','—')}</td>"
        f"<td>{'未量測' if f['m'].get('semantic_pass_rate') is None else f['m']['semantic_pass_rate']}</td>"
        f"<td>{f['m'].get('median_context_tokens','—')}</td></tr>" for f in families)
    rule_rows = "".join(
        f"<tr><td>{html.escape(r['metric'])}</td><td>{html.escape(r['source'])}</td>"
        f"<td>{html.escape(r['trigger'])}</td><td>{html.escape(r['action'])}</td>"
        f"<td>{chip('人閘' if r['human_gate'] else '自動', WARN if r['human_gate'] else INFO)}</td></tr>"
        for r in state["decision_rules"])
    lo, hi = ca["daily_batch_usd_est"]
    plo, phi = ca["task_plan_usd_est"]
    hb = state.get("heartbeat")
    hb_tile = ""
    if hb:
        from datetime import date
        days = (date.fromisoformat(hb["next"]) - date.fromisoformat(as_of)).days
        hb_tile = (f'<div class="tile"><div class="n" style="color:{WARN}">{days} 天</div>'
                   f'<div class="l">下一心跳 {hb["next"]}(節拍 {hb["cadence_days"]} 天=留存節拍)</div></div>')
    return f"""<title>產品後台:skill-bettor</title><style>{CSS}</style><div class="wrap">
<div class="banner">⚙ 本頁為<b>產品後台觀測面</b>:零 LLM 機械投影(源=product/state.json+FAMILY.yaml)。
本頁為投影非 SSOT。快照 {as_of}。訂閱數=null 時誠實顯示未上線,禁投影假數(PRODUCT.md 紅線)。</div>
<div class="eyebrow">PRODUCT BACKSTAGE · stage {html.escape(state['stage'])}</div>
<h1>產品後台:落地進度 × 單位經濟 × 決策規則</h1>
<h2>落地階段梯(晉級=人閘;程序=PRODUCT.md 階段閘表)</h2>
<div class="ladder">{ladder}</div>
<h2>訂閱與方案 × token 成本{est}</h2>
<div class="tiles">
<div class="tile"><div class="n">{na(subs['free'])}</div><div class="l">Free 訂閱數</div></div>
<div class="tile"><div class="n">{na(subs['bettor'])}</div><div class="l">Bettor(${plans['bettor_usd_yr']}/年)</div></div>
<div class="tile"><div class="n">{na(subs['pro'])}</div><div class="l">Pro(${plans['pro_usd_mo']}/月)</div></div>
<div class="tile"><div class="n">${lo}–{hi}</div><div class="l">每日演化批次成本(集中,與人數無關)</div></div>
{hb_tile}
</div>
{f'<p class="note">心跳={html.escape(hb["beat"])};供給側:{html.escape(hb["supply_rule"])}。</p>' if hb else ''}
<table style="margin-top:12px"><tr><th>方案</th><th>售價</th><th>邊際成本</th><th>毛利邏輯</th></tr>
<tr><td>Free</td><td>$0</td><td>≈0(延遲快照)</td><td>漏斗</td></tr>
<tr><td>Bettor</td><td>${plans['bettor_usd_yr']}/年</td><td>≈0(git pull+點數帳)</td><td>訊號價值>成本;批次成本由全體攤提</td></tr>
<tr><td>Pro</td><td>${plans['pro_usd_mo']}/月</td><td>${plo}–{phi}/執行計劃×≤90/月=${plo*90:.0f}–{phi*90:.0f}</td><td>紅線:計劃非代跑;成本逼近售價→改 credits</td></tr></table>
<p class="note">context 足跡錨(口徑 v2):有 skill run 中位 {ca['sonnet_run_peak_ctx_median']:,}/上限 {ca['ctx_limit']:,}。</p>
<h2>數據驅動決策規則(指標→觸發→動作;源=state.json decision_rules,SSOT=PRODUCT.md)</h2>
<table><tr><th>指標</th><th>源</th><th>觸發</th><th>動作</th><th>閘</th></tr>{rule_rows}</table>
<h2>家族資產現值(雙軌)</h2>
<table><tr><th>家族/子技能</th><th>狀態</th><th>機械 sr</th><th>語意 spr</th><th>ctx 中位(v2)</th></tr>{fam_rows}</table>
<h2>生命週期事件 schema(S1 起蒐集;事件不回溯,schema 先行)</h2>
<p class="note">{'<br>'.join(html.escape(e) for e in state['event_schema'])}<br>
預判服務門檻:≥{state['prediction_gate']['min_active_bettors']} 活躍 bettor×{state['prediction_gate']['min_days']} 天;
之前={html.escape(state['prediction_gate']['until_then'])}。</p>
<footer>再生:python3 .claude/skills/html-for-decisions/scripts/product_board.py . -o dashboard/product-board.html
--as-of &lt;日期&gt; · 本頁為投影非 SSOT · 回填訂閱/成本實測:改 product/state.json 再重生</footer></div>"""


def selftest() -> int:
    state = {"stage": "S0", "stages": [{"id": "S0", "name": "x", "status": "done", "evidence": "e"}],
             "subscribers": {"free": None, "bettor": None, "pro": None},
             "plans": {"free_usd": 0, "bettor_usd_yr": 30, "pro_usd_mo": 20},
             "cost_anchors": {"sonnet_run_peak_ctx_median": 1, "ctx_limit": 2,
                              "daily_batch_usd_est": [1, 2], "task_plan_usd_est": [0.1, 0.2], "measured": False},
             "decision_rules": [{"metric": "m", "source": "s", "trigger": "t", "action": "a", "human_gate": True}],
             "event_schema": ["bet{...}"], "prediction_gate": {"min_active_bettors": 1, "min_days": 1, "until_then": "u"}}
    out = render(state, [], "2026-01-01")
    good = all(s in out for s in ("投影非 SSOT", "快照 2026-01-01", "未上線(N/A)", "估算"))
    hollow = ('type="radio"' in out) or ("判卷" in out)  # 觀測面不得含 quiz 機件(語義隔離)
    if good and not hollow:
        print("selftest PASS: null→未上線 ∧ 估算標示 ∧ 無 quiz 機件")
        return 0
    print(f"selftest FAIL: good={good} hollow={hollow}")
    return 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?")
    ap.add_argument("-o", "--out")
    ap.add_argument("--as-of", dest="as_of")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not (a.root and a.out and a.as_of):
        sys.exit("用法: product_board.py <repo_root> -o <out.html> --as-of YYYY-MM-DD(禁系統時間)")
    root = Path(a.root).resolve()
    out = Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    state, families = collect(root)
    out.write_text(render(state, families, a.as_of), encoding="utf-8")
    print(f"[board] {out}")


if __name__ == "__main__":
    main()
