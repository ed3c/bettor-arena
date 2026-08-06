#!/usr/bin/env python3
"""family_metrics_board — 家族全指標觀測面(零 LLM 機械投影;與決策面語義隔離,不變量 7)。

WHY: 決策面由 LLM 從 md 萃取「判定」;本板只投影「機器帳」——FAMILY.yaml 雙軌現值、
baselines 基線帳(分量尺/口徑段,絕不跨段連線)、context 足跡 vs 上限、results 使用統計、
輪替 registry、目錄結構(家族內部契約 vs 檔案系統實況)。零判定、無 quiz、非 SSOT——
確定性渲染:同輸入同輸出。

用法: family_metrics_board.py <family_root> -o <out.html> --as-of YYYY-MM-DD
      --selftest = 合成 fixture 正控(不讀真家族)
exit: 0 成功 / 1 用法錯 / 2 selftest 鑑別失敗
色 tokens 沿用 decision-report.prompt schema v1 已過 CVD 驗證組(ok/warn/risk/借形)。
"""
import argparse
import html
import json
import sys
from pathlib import Path

OK, WARN, RISK, INFO, MUTE = "#1A7A4A", "#B45309", "#B3382C", "#1D6FA8", "#7A5CB8"

SUBSKILL_LINE_LIMIT = 500  # 家族內部契約:子技能 SKILL.md <500 行(契約源=ARCHITECTURE.md §2)

CSS = f"""
body{{font-family:-apple-system,'PingFang TC','Noto Sans CJK TC',sans-serif;margin:0;
background:#F7F6F2;color:#1F2937;line-height:1.55}}
.wrap{{max-width:1080px;margin:0 auto;padding:28px 20px 60px}}
.banner{{background:#FFF7E6;border:1px solid {WARN};border-radius:8px;padding:10px 14px;
font-size:13px;margin-bottom:18px}}
h1{{font-size:26px;margin:6px 0}} h2{{font-size:17px;margin:26px 0 10px;border-bottom:2px solid #E5E1D8;padding-bottom:6px}}
.eyebrow{{font-size:12px;letter-spacing:.14em;color:{INFO};font-weight:700}}
.tiles{{display:flex;flex-wrap:wrap;gap:12px}}
.tile{{flex:1 1 150px;background:#fff;border:1px solid #E5E1D8;border-radius:10px;padding:14px}}
.tile .n{{font-size:24px;font-weight:800}} .tile .l{{font-size:12px;color:#6B7280;margin-top:2px}}
table{{border-collapse:collapse;width:100%;background:#fff;font-size:13px}}
th,td{{border:1px solid #E5E1D8;padding:6px 9px;text-align:left}} th{{background:#EFEDE6}}
.chip{{display:inline-block;padding:1px 8px;border-radius:999px;color:#fff;font-size:11.5px;font-weight:700}}
.bar{{height:20px;border-radius:4px;background:{INFO};color:#fff;font-size:11.5px;
padding:1px 6px;box-sizing:border-box;min-width:2%}}
.track{{background:#E5E1D8;border-radius:4px;margin:4px 0 10px;position:relative}}
.limitline{{position:absolute;top:-4px;bottom:-4px;width:2px;background:{RISK}}}
.note{{font-size:12px;color:#6B7280}}
footer{{margin-top:34px;font-size:12px;color:#6B7280;border-top:1px solid #E5E1D8;padding-top:10px}}
"""


def chip(text, color):
    return f'<span class="chip" style="background:{color}">{html.escape(str(text))}</span>'


def collect_structure(family: Path):
    """家族內部契約(ARCHITECTURE.md §2)各槽位的檔案系統實況——只量測不判定。"""
    def nlines(p: Path):
        return len(p.read_text(encoding="utf-8").splitlines()) if p.is_file() else None

    def nfiles(p: Path):
        return sum(1 for f in p.rglob("*") if f.is_file() and f.name != ".gitkeep") if p.is_dir() else 0

    def ncases(p: Path):
        return sum(1 for d in p.iterdir() if d.is_dir()) if p.is_dir() else 0

    subs = []
    skills_dir = family / "skills"
    if skills_dir.is_dir():
        for d in sorted(skills_dir.iterdir()):
            if not d.is_dir():
                continue
            subs.append({"name": d.name, "lines": nlines(d / "SKILL.md"),
                         "refs": (d / "references").is_dir(), "scripts": (d / "scripts").is_dir(),
                         "cases": ncases(family / "evals" / "cases" / d.name),
                         "holdout": ncases(family / "evals" / "holdout" / d.name),
                         "candidates": ncases(family / "evals" / "candidates" / d.name)})
    return {"router_lines": nlines(family / "SKILL.md"),
            "family_yaml": (family / "FAMILY.yaml").is_file(),
            "shared_files": nfiles(family / "shared"),
            "changelog_files": nfiles(family / "changelog"),
            "proposals_files": nfiles(family / "proposals"),
            "subskills": subs}


def collect(family: Path):
    import yaml
    fam_yaml = yaml.safe_load((family / "FAMILY.yaml").read_text(encoding="utf-8"))
    baselines = []
    for f in sorted(family.glob("evals/baselines/2*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        sk = next(iter(d["skills"].values()))
        baselines.append({"file": f.name, "set": d.get("set", "?"), "agent": d.get("agent_cmd", "?"),
                          "sr": sk["success_rate"], "tok": sk["median_context_tokens"]})
    runs = []
    for f in sorted(family.glob("evals/results/*/summary.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        sk = next(iter(d["skills"].values()))
        runs.append({"date": d["date"], "set": d.get("set", "?"), "agent": d.get("agent_cmd", "?"),
                     "sr": sk["success_rate"], "tok": sk["median_context_tokens"]})
    reg_path = family / "evals" / "candidates" / "registry.json"
    registry = json.loads(reg_path.read_text(encoding="utf-8")) if reg_path.exists() else {}
    limits = set()
    for ey in family.glob("evals/*/*/*/expect.yaml"):
        for line in ey.read_text(encoding="utf-8").splitlines():
            if "max_context_tokens:" in line:
                limits.add(int(line.split(":")[1].strip()))
    return fam_yaml, baselines, runs, registry, limits, collect_structure(family)


def agent_label(cmd: str) -> str:
    if "mock_agent" in cmd: return "mock"
    if cmd.startswith("echo"): return "echo(hollow)"
    if "no_skill" in cmd: return "no-skill 對照"
    if "sonnet" in cmd: return "sonnet(釘死量尺)"
    return "fable-default(退役量尺)"


def yardstick_label(b) -> str:
    v2 = "-v2" in b["file"]
    if "no-skill" in b["file"]: return "對照(非曲線)"
    if "sonnet" in b["agent"]: return "Sonnet/口徑v2 ✅現行" if v2 else "Sonnet/口徑v1(退役)"
    if "mock" in b["agent"]: return "mock(自測)"
    return "Fable/口徑v1(退役)"


def structure_section(st) -> str:
    """契約槽位 vs 實況。唯一機械判定=SKILL.md 行數對契約閾值、必備槽位存在性;其餘中性計數。"""
    def presence(exists, absent_label="缺"):
        return chip("✓", OK) if exists else chip(absent_label, RISK)

    router = f"{st['router_lines']} 行" if st["router_lines"] is not None else chip("缺", RISK)
    fam_rows = (
        f"<tr><td>SKILL.md(路由器)</td><td>只放地圖不放知識</td><td>{router}</td></tr>"
        f"<tr><td>FAMILY.yaml</td><td>機器可讀 metrics/status/interface</td><td>{presence(st['family_yaml'])}</td></tr>"
        f"<tr><td>shared/</td><td>共享原語,引用不複製</td><td>{st['shared_files']} 檔</td></tr>"
        f"<tr><td>changelog/</td><td>每日加/刪/分數變化</td><td>{st['changelog_files']} 篇</td></tr>"
        f"<tr><td>proposals/</td><td>DR 隔離區,家族內容禁引用</td><td>{st['proposals_files']} 件</td></tr>")

    sub_rows = ""
    for s in st["subskills"]:
        if s["lines"] is None:
            line_cell = chip("缺 SKILL.md", RISK)
        else:
            over = s["lines"] >= SUBSKILL_LINE_LIMIT
            line_cell = f"{s['lines']} 行 " + chip("超約" if over else "契約內", RISK if over else OK)
        sub_rows += (
            f"<tr><td>{html.escape(s['name'])}</td><td>{line_cell}</td>"
            f"<td>{'✓' if s['refs'] else '—'}</td><td>{'✓' if s['scripts'] else '—'}</td>"
            f"<td>{s['cases']}</td><td>{s['holdout']}</td><td>{s['candidates']}</td></tr>")
    sub_rows = sub_rows or "<tr><td colspan=7>N/A(無子技能目錄)</td></tr>"

    return f"""<h2>結構(家族內部契約 vs 檔案系統實況;契約源=ARCHITECTURE.md §2,本表只投影不改契約)</h2>
<table><tr><th>家族層槽位</th><th>契約</th><th>實況</th></tr>{fam_rows}</table>
<p class="note">子技能契約:SKILL.md &lt;{SUBSKILL_LINE_LIMIT} 行 + references/ + scripts/;
案例計數=evals 各 set 下該子技能的案例目錄數(candidates/_validation 不掛子技能名,天然不計)。</p>
<table><tr><th>子技能</th><th>SKILL.md(契約&lt;{SUBSKILL_LINE_LIMIT}行)</th><th>references/</th>
<th>scripts/</th><th>cases(public)</th><th>holdout</th><th>candidates</th></tr>{sub_rows}</table>"""


def render(fam_yaml, baselines, runs, registry, limits, structure, as_of: str) -> str:
    sk = fam_yaml["skills"][0]
    m = sk["metrics"]
    limit = max(limits) if limits else 0
    p = [b for b in baselines if "sonnet-public-v2" in b["file"]]
    h = [b for b in baselines if "sonnet-holdout-v2" in b["file"]]
    pub_tok = p[0]["tok"] if p else None
    hold_tok = h[0]["tok"] if h else None

    def tile(n, l, c):
        return f'<div class="tile"><div class="n" style="color:{c}">{n}</div><div class="l">{l}</div></div>'

    def bar_row(label, val):
        if not (val and limit):
            return f"<div>{label}: N/A</div>"
        pct = min(100 * val / limit, 100)
        return (f'<div class="note">{label}: {val:,.0f} / 上限 {limit:,}</div>'
                f'<div class="track"><div class="bar" style="width:{pct:.1f}%">{pct:.0f}%</div>'
                f'<div class="limitline" style="left:100%"></div></div>')

    serving = [(s, c, v) for s, cases in registry.items() for c, v in cases.items()]
    reg_rows = "".join(
        f"<tr><td>{html.escape(c)}</td><td>{html.escape(v['admitted'])}</td>"
        f"<td>{chip(v['status'], OK if v['status']=='serving' else MUTE)}</td></tr>"
        for s, c, v in serving) or "<tr><td colspan=3>N/A</td></tr>"

    base_rows = "".join(
        f"<tr><td>{html.escape(b['file'])}</td><td>{b['set']}</td><td>{html.escape(yardstick_label(b))}</td>"
        f"<td>{b['sr']}</td><td>{b['tok'] if b['tok'] else '—'}</td></tr>" for b in baselines)
    run_rows = "".join(
        f"<tr><td>{r['date']}</td><td>{r['set']}</td><td>{html.escape(agent_label(r['agent']))}</td>"
        f"<td>{r['sr']}</td><td>{r['tok'] if r['tok'] else '—'}</td></tr>" for r in runs)

    sem = m.get("semantic_pass_rate")
    return f"""<title>觀測面:{fam_yaml['family']}</title><style>{CSS}</style><div class="wrap">
<div class="banner">⚙ 本頁為<b>觀測面</b>:腳本機械投影(零 LLM、無判定、無 quiz)。本頁為投影非 SSOT。
快照 {as_of}。決策/裁決請看決策面與 md SSOT;兩面語義隔離(html-for-decisions 不變量 7)。</div>
<div class="eyebrow">FAMILY OBSERVABILITY · {html.escape(fam_yaml['family'])}</div>
<h1>全指標觀測板</h1>
<h2>雙軌現值(源:FAMILY.yaml metrics)</h2>
<div class="tiles">
{tile(m['success_rate'], '機械 success_rate(Sonnet/口徑v2)', OK)}
{tile('未量測' if sem is None else sem, '語意 semantic_pass_rate(首量=輪替畢業段)', WARN if sem is None else OK)}
{tile(f"{m['median_context_tokens']:,}", 'median context(口徑v2 峰值)', INFO)}
{tile(f"{limit:,}" if limit else 'N/A', 'max_context_tokens 上限', INFO)}
{tile(len(serving), 'candidates 服役中(到期 2026-07-25)', MUTE)}
</div>
{structure_section(structure)}
<h2>context 足跡(口徑 v2=峰值 context;上限紅線={limit:,})</h2>
{bar_row('public 中位數(有 skill,Sonnet)', pub_tok)}
{bar_row('holdout 中位數(有 skill,Sonnet)', hold_tok)}
{bar_row('觀測最大值(校準樣本 n=9)', 51684)}
{bar_row('mock 自測', next((r['tok'] for r in reversed(runs) if 'mock' in r['agent'] and r['tok']), None))}
<p class="note">退役口徑 v1 同批量測值:public 354,095/holdout 320,418(膨脹 6.7–7.1×;跨口徑不可比,
不繪同一標尺——詳 changelog 2026-07-11 追記 4)。</p>
<h2>基線帳(跨量尺/跨口徑不可比,分段閱讀)</h2>
<table><tr><th>檔</th><th>set</th><th>量尺/口徑</th><th>success_rate</th><th>median tokens</th></tr>{base_rows}</table>
<h2>使用統計(evals/results 現存 {len(runs)} 批;含自測/對照/量測)</h2>
<table><tr><th>時間戳</th><th>set</th><th>agent</th><th>success_rate</th><th>median tokens</th></tr>{run_rows}</table>
<h2>輪替 registry</h2>
<table><tr><th>案例</th><th>admitted</th><th>狀態</th></tr>{reg_rows}</table>
<footer>再生:python3 .claude/skills/html-for-decisions/scripts/family_metrics_board.py
families/pinescript-audit -o &lt;out&gt; --as-of &lt;日期&gt; · 源=FAMILY.yaml/baselines/results/registry/
目錄實況(契約=ARCHITECTURE.md §2) · 本頁為投影非 SSOT</footer></div>"""


def selftest() -> int:
    fam = {"family": "synthetic", "skills": [{"metrics": {
        "success_rate": 0.9, "median_context_tokens": 100, "semantic_pass_rate": None}}]}
    st = {"router_lines": 16, "family_yaml": True, "shared_files": 2, "changelog_files": 1,
          "proposals_files": 0, "subskills": [
              {"name": "syn-lean", "lines": 120, "refs": True, "scripts": True,
               "cases": 2, "holdout": 1, "candidates": 3},
              {"name": "syn-fat", "lines": 512, "refs": False, "scripts": False,
               "cases": 0, "holdout": 0, "candidates": 0}]}
    out = render(fam, [], [], {}, {200}, st, "2026-01-01")
    good = all(s in out for s in ("觀測面", "投影非 SSOT", "快照 2026-01-01", "0.9", "未量測",
                                  "syn-lean", "契約內", "syn-fat", "超約"))
    # 觀測面不得含 quiz 機件(語義隔離)——查真實元件(radio/判卷),不查字面(banner 提及「無 quiz」合法)
    hollow = ('type="radio"' in out) or ("判卷" in out)
    if good and not hollow:
        print("selftest PASS: 投影欄位齊 ∧ 無 quiz(觀測/決策隔離)")
        return 0
    print(f"selftest FAIL: good={good} hollow(quiz 混入)={hollow}")
    return 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("family", nargs="?")
    ap.add_argument("-o", "--out")
    ap.add_argument("--as-of", dest="as_of")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if not (a.family and a.out and a.as_of):
        sys.exit("用法: family_metrics_board.py <family_root> -o <out.html> --as-of YYYY-MM-DD(禁系統時間)")
    fam = Path(a.family).resolve()
    out = Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(*collect(fam), a.as_of), encoding="utf-8")
    print(f"[board] {out}")


if __name__ == "__main__":
    main()
