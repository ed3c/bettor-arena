#!/usr/bin/env python3
"""context_trace — Claude Code session JSONL → 上下文觀測面 HTML（零 LLM 全路徑）。

WHY: html-for-decisions 的決策面捕捉語義流（LLM 從 md 萃取判定）；本腳本是**觀測面**——
機械投影 session 底層（逐 turn token 經濟/cache 命中/工具軌跡/subagent 分佈）。
兩面語義隔離（northstar viz-sync 的 mf-adapter read-only 先例）：觀測面無 quiz、無判定，
禁與決策面混同一頁。零 LLM ＝ 天然零幻覺；同輸入必同輸出（可重生投影）。

直接紅利：D7 cache oracle 可視化——迭代期 commit 造成 prefix 全 miss 會在 cache_read
曲線上當場現形（cache_read_input_tokens 驟降）。

用法:
  context_trace.py <session.jsonl> [-o out.html]
  context_trace.py --selftest          # 合成 fixture 正控（防 placebo parser）

EXIT: 0 成功 · 1 用法/檔案錯 · 2 selftest FAIL

retarget 記事: 本檔零 antigravity 專屬路徑/假設（selftest 走合成 fixture，非讀外部檔），
移植到 skill-bettor 僅原樣複製，見 modules/retarget-map.md。
"""
import html as html_mod
import json
import sys
from pathlib import Path

# 與 skill 家族同源的視覺 tokens（已過 dataviz validator 的狀態色）
C_ADOPT, C_BORROW, C_PENDING, C_RECORD, C_HUSK = "#1A7A4A", "#1D6FA8", "#B45309", "#7A5CB8", "#B3382C"
ACCENT, INK, INK2, HAIR, GROUND = "#175E75", "#1B2530", "#56677A", "#D9E0E6", "#F1F3F5"


def parse_session(lines):
    """JSONL 行 → trace dict。逐 assistant 訊息以 message.id 去重（串流分片防重計）。"""
    calls = {}          # id → call dict（保留最後一次出現）
    order = []
    tool_counts = {}
    human_turns = 0
    record_types = {}
    first_ts = last_ts = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = d.get("type", "?")
        record_types[t] = record_types.get(t, 0) + 1
        ts = d.get("timestamp")
        if ts:
            first_ts = first_ts or ts
            last_ts = ts
        m = d.get("message") or {}
        content = m.get("content")
        if t == "user":
            blocks = content if isinstance(content, list) else []
            has_tool_result = any(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks)
            if not has_tool_result and (isinstance(content, str) or blocks):
                human_turns += 1
        elif t == "assistant":
            mid = m.get("id") or f"noid-{len(order)}"
            u = m.get("usage") or {}
            tools, text_chars, think_chars = [], 0, 0
            for b in (content if isinstance(content, list) else []):
                if not isinstance(b, dict):
                    continue
                bt = b.get("type")
                if bt == "tool_use":
                    tools.append(b.get("name", "?"))
                elif bt == "text":
                    text_chars += len(b.get("text", ""))
                elif bt == "thinking":
                    think_chars += len(b.get("thinking", ""))
            cc = u.get("cache_creation") or {}
            call = {
                "ts": ts,
                "in": u.get("input_tokens", 0),
                "out": u.get("output_tokens", 0),
                "cache_read": u.get("cache_read_input_tokens", 0),
                "cache_create": u.get("cache_creation_input_tokens", 0),
                "eph_5m": cc.get("ephemeral_5m_input_tokens", 0),
                "eph_1h": cc.get("ephemeral_1h_input_tokens", 0),
                "tools": tools, "text_chars": text_chars, "think_chars": think_chars,
                "has_usage": bool(u),
            }
            if mid not in calls:
                order.append(mid)
            calls[mid] = call
    seq = [calls[i] for i in order]
    for c in seq:
        for name in c["tools"]:
            tool_counts[name] = tool_counts.get(name, 0) + 1
    usage_calls = [c for c in seq if c["has_usage"]]
    for c in usage_calls:
        c["ctx"] = c["in"] + c["cache_read"] + c["cache_create"]
    # prefix-miss 事件：cache_read 相對前一 call 驟降（>50% 且前值夠大）
    misses = []
    for i in range(1, len(usage_calls)):
        prev, cur = usage_calls[i - 1]["cache_read"], usage_calls[i]["cache_read"]
        if prev > 10_000 and cur < prev * 0.5:
            misses.append({"idx": i, "prev": prev, "cur": cur})
    total_read = sum(c["cache_read"] for c in usage_calls)
    total_create = sum(c["cache_create"] for c in usage_calls)
    total_in = sum(c["in"] for c in usage_calls)
    denom = total_read + total_create + total_in
    return {
        "calls": seq, "usage_calls": usage_calls, "tool_counts": tool_counts,
        "human_turns": human_turns, "record_types": record_types,
        "first_ts": first_ts, "last_ts": last_ts,
        "totals": {
            "out": sum(c["out"] for c in usage_calls),
            "read": total_read, "create": total_create, "in": total_in,
            "eph_5m": sum(c["eph_5m"] for c in usage_calls),
            "eph_1h": sum(c["eph_1h"] for c in usage_calls),
            "tool_calls": sum(tool_counts.values()),
            "think_chars": sum(c["think_chars"] for c in seq),
        },
        "cache_hit_ratio": (total_read / denom) if denom else 0.0,
        "misses": misses,
        "oracle_turns": sum(1 for c in usage_calls if c["cache_read"] > 0),
    }


def _fmt(n):
    return f"{n:,}"


def _svg_chart(usage_calls):
    """context 規模與 cache_read 兩線 SVG（thin marks、淡格線、端點直標）。"""
    if not usage_calls:
        return "<p>（無 usage 資料）</p>"
    W, H, PL, PB, PT = 880, 240, 64, 26, 14
    n = len(usage_calls)
    ymax = max(max(c["ctx"] for c in usage_calls), 1)
    xs = lambda i: PL + (W - PL - 10) * (i / max(n - 1, 1))
    ys = lambda v: PT + (H - PT - PB) * (1 - v / ymax)
    def poly(key, color, label):
        pts = " ".join(f"{xs(i):.1f},{ys(c[key]):.1f}" for i, c in enumerate(usage_calls))
        dots = "".join(
            f'<circle cx="{xs(i):.1f}" cy="{ys(c[key]):.1f}" r="2.4" fill="{color}">'
            f"<title>call {i + 1} · {label} {_fmt(c[key])}</title></circle>"
            for i, c in enumerate(usage_calls)
        )
        end = usage_calls[-1][key]
        return (f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2"/>{dots}'
                f'<text x="{W-6}" y="{ys(end)-6:.1f}" text-anchor="end" font-size="11" fill="{INK}">{label} {_fmt(end)}</text>')
    grid = "".join(
        f'<line x1="{PL}" y1="{ys(ymax*f):.1f}" x2="{W-10}" y2="{ys(ymax*f):.1f}" stroke="{HAIR}" stroke-width="1"/>'
        f'<text x="{PL-6}" y="{ys(ymax*f)+4:.1f}" text-anchor="end" font-size="10" fill="{INK2}">{_fmt(int(ymax*f))}</text>'
        for f in (0.25, 0.5, 0.75, 1.0)
    )
    return (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="context 規模與 cache_read 曲線" '
            f'style="width:100%;height:auto">{grid}'
            f'{poly("ctx", C_ADOPT, "context")}{poly("cache_read", C_BORROW, "cache_read")}</svg>'
            f'<div class="legend"><span style="color:{C_ADOPT}">● context（in+read+create）</span>'
            f'<span style="color:{C_BORROW}">● cache_read</span></div>')


def render_html(trace, source_name):
    t = trace["totals"]
    date = (trace["last_ts"] or "")[:10] or "unknown-date"
    hit_pct = f"{trace['cache_hit_ratio']*100:.1f}%"
    noq = len(trace["usage_calls"])
    oracle_ok = trace["oracle_turns"] == noq and noq > 0
    oracle_chip = (f'<span class="chip ok">cache oracle PASS（{trace["oracle_turns"]}/{noq} calls cache_read&gt;0）</span>'
                   if oracle_ok else
                   f'<span class="chip warn">cache oracle {trace["oracle_turns"]}/{noq} calls cache_read&gt;0</span>')
    miss_html = ("".join(
        f'<tr><td class="id">call {m["idx"]+1}</td><td>{_fmt(m["prev"])} → {_fmt(m["cur"])}</td>'
        f"<td>cache_read 驟降 &gt;50%——疑 prefix miss（git 狀態變動/prefix 不穩/超 TTL）</td></tr>"
        for m in trace["misses"]) or '<tr><td colspan="3">無驟降事件</td></tr>')
    tools_sorted = sorted(trace["tool_counts"].items(), key=lambda kv: -kv[1])
    tmax = max([v for _, v in tools_sorted] or [1])
    tool_rows = "".join(
        f'<div class="trow"><span class="tname">{html_mod.escape(k)}</span>'
        f'<span class="tbar"><span style="width:{v/tmax*100:.0f}%"></span></span>'
        f'<span class="tnum">{v}</span></div>' for k, v in tools_sorted)
    rows = "".join(
        f'<tr><td class="id">{i+1}</td><td class="id">{(c["ts"] or "")[11:19]}</td>'
        f'<td>{_fmt(c["cache_read"])}</td><td>{_fmt(c["cache_create"])}</td>'
        f'<td>{_fmt(c["out"])}</td><td>{html_mod.escape(", ".join(c["tools"]) or "—")}</td></tr>'
        for i, c in enumerate(trace["usage_calls"]))
    return f"""<title>上下文觀測 · {html_mod.escape(source_name)}</title>
<style>
 body{{background:{GROUND};color:{INK};font-family:"PingFang TC","Noto Sans TC",system-ui,sans-serif;
  font-size:14.5px;line-height:1.6;margin:0;padding:0 20px 60px}}
 .wrap{{max-width:1020px;margin:0 auto}} h1{{font-family:"Songti TC","Noto Serif TC",serif;font-size:26px;margin:0}}
 h2{{font-family:"Songti TC","Noto Serif TC",serif;font-size:19px;margin:0 0 8px}}
 .eyebrow{{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:{ACCENT};font-weight:600;margin-bottom:6px}}
 .mast{{padding:34px 0 14px;border-bottom:2px solid {INK};margin-bottom:18px}}
 .meta{{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:{INK2};margin-top:8px}}
 section{{background:#fff;border:1px solid {HAIR};border-radius:6px;padding:18px 22px;margin:14px 0}}
 .tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:14px 0 2px}}
 .tile{{background:#fff;border:1px solid {HAIR};border-radius:6px;padding:10px 12px}}
 .tile .n{{font-family:ui-monospace,Menlo,monospace;font-variant-numeric:tabular-nums;font-size:22px;font-weight:700}}
 .tile .l{{font-size:11.5px;color:{INK2}}}
 .chip{{display:inline-block;font-size:11.5px;font-weight:600;padding:1px 8px;border-radius:999px}}
 .chip.ok{{background:#E7F3EC;color:{C_ADOPT}}} .chip.warn{{background:#F8EFE2;color:{C_PENDING}}}
 .legend{{display:flex;gap:16px;font-size:12px;color:{INK2};margin-top:4px}}
 table{{border-collapse:collapse;width:100%;font-size:12.5px}}
 th{{font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:{INK2};text-align:left;border-bottom:1.5px solid {INK};padding:5px 8px 5px 0}}
 td{{border-bottom:1px solid {HAIR};padding:5px 8px 5px 0;vertical-align:top;font-variant-numeric:tabular-nums}}
 td.id{{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;white-space:nowrap}}
 .scroll{{overflow-x:auto}} details{{margin-top:8px}} summary{{cursor:pointer;font-weight:600;color:{ACCENT};font-size:13px}}
 .trow{{display:flex;align-items:center;gap:10px;padding:3px 0}}
 .tname{{font-family:ui-monospace,Menlo,monospace;font-size:12px;flex:0 0 300px;overflow:hidden;text-overflow:ellipsis}}
 .tbar{{flex:1;background:{GROUND};border-radius:3px;height:14px;overflow:hidden}}
 .tbar span{{display:block;height:100%;background:{ACCENT};border-radius:3px}}
 .tnum{{font-family:ui-monospace,Menlo,monospace;font-size:12px;width:44px;text-align:right}}
 .note{{font-size:12px;color:{INK2};border-left:3px solid {HAIR};padding-left:10px;margin-top:10px}}
</style>
<div class="wrap">
<header class="mast">
 <div class="eyebrow">觀測面 · 機械投影（零 LLM）· 與決策面語義隔離</div>
 <h1>上下文觀測 — {html_mod.escape(source_name)}</h1>
 <div class="meta">本頁為投影非 SSOT（源＝session JSONL，同輸入必同輸出）· 快照 {date} ·
  {trace["human_turns"]} 人類 turns · {len(trace["usage_calls"])} API calls</div>
</header>
<div class="tiles">
 <div class="tile"><div class="n">{_fmt(t["out"])}</div><div class="l">輸出 tokens</div></div>
 <div class="tile"><div class="n">{hit_pct}</div><div class="l">cache 命中率（read/(read+create+in)）</div></div>
 <div class="tile"><div class="n">{_fmt(max((c["ctx"] for c in trace["usage_calls"]), default=0))}</div><div class="l">峰值 context（tokens）</div></div>
 <div class="tile"><div class="n">{_fmt(t["tool_calls"])}</div><div class="l">工具調用</div></div>
 <div class="tile"><div class="n">{_fmt(t["think_chars"])}</div><div class="l">thinking 字元</div></div>
</div>
<section>
 <div class="eyebrow">D7 oracle · cache_read_input_tokens</div>
 <h2>context 規模與 cache 命中曲線 {oracle_chip}</h2>
 {_svg_chart(trace["usage_calls"])}
 <div class="scroll" style="margin-top:12px"><table>
  <tr><th>事件</th><th>cache_read 變化</th><th>解讀</th></tr>{miss_html}</table></div>
 <p class="note">cache_creation 分桶：5 分鐘 {_fmt(t["eph_5m"])} · 1 小時 {_fmt(t["eph_1h"])} tokens。
 迭代期 commit／prefix 不穩會以驟降事件現形（D7 gotcha 1/3）。</p>
</section>
<section>
 <div class="eyebrow">工具軌跡</div>
 <h2>工具調用分佈</h2>
 {tool_rows or "<p>（無工具調用）</p>"}
</section>
<section>
 <div class="eyebrow">逐 call 帳</div>
 <h2>API call 時間線</h2>
 <details><summary>展開 {len(trace["usage_calls"])} 筆</summary>
 <div class="scroll"><table>
  <tr><th>#</th><th>時刻</th><th>cache_read</th><th>cache_create</th><th>out</th><th>tools</th></tr>
  {rows}</table></div></details>
</section>
<p style="font-size:11.5px;color:{INK2}">generated by context_trace.py（html-for-decisions 觀測面）· 本頁為投影非 SSOT · 無 quiz——觀測面不承載 LAND-DECISION 語義</p>
</div>"""


def selftest():
    fixture = [
        json.dumps({"type": "user", "timestamp": "2026-07-09T10:00:00Z",
                    "message": {"role": "user", "content": "hi"}}),
        json.dumps({"type": "assistant", "timestamp": "2026-07-09T10:00:05Z",
                    "message": {"id": "m1", "role": "assistant",
                                "content": [{"type": "tool_use", "name": "Bash", "input": {}},
                                            {"type": "text", "text": "ok"}],
                                "usage": {"input_tokens": 2, "output_tokens": 100,
                                          "cache_read_input_tokens": 50_000,
                                          "cache_creation_input_tokens": 1_000,
                                          "cache_creation": {"ephemeral_5m_input_tokens": 0,
                                                             "ephemeral_1h_input_tokens": 1_000}}}}),
        json.dumps({"type": "assistant", "timestamp": "2026-07-09T10:01:00Z",
                    "message": {"id": "m2", "role": "assistant", "content": [{"type": "text", "text": "x"}],
                                "usage": {"input_tokens": 2, "output_tokens": 30,
                                          "cache_read_input_tokens": 900,
                                          "cache_creation_input_tokens": 60_000,
                                          "cache_creation": {"ephemeral_5m_input_tokens": 60_000,
                                                             "ephemeral_1h_input_tokens": 0}}}}),
        json.dumps({"type": "assistant", "timestamp": "2026-07-09T10:01:00Z",
                    "message": {"id": "m2", "role": "assistant", "content": [],
                                "usage": {"input_tokens": 2, "output_tokens": 30,
                                          "cache_read_input_tokens": 900,
                                          "cache_creation_input_tokens": 60_000,
                                          "cache_creation": {}}}}),  # 同 id 重複 → 去重
    ]
    tr = parse_session(fixture)
    checks = {
        "去重後 2 calls": len(tr["usage_calls"]) == 2,
        "人類 turns=1": tr["human_turns"] == 1,
        "工具計數 Bash=1": tr["tool_counts"].get("Bash") == 1,
        "輸出 tokens=130": tr["totals"]["out"] == 130,
        "prefix-miss 抓到 1 起": len(tr["misses"]) == 1,
        "oracle 2/2": tr["oracle_turns"] == 2,
    }
    ok = True
    for name, passed in checks.items():
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
        ok = ok and passed
    h = render_html(tr, "selftest")
    for marker in ("本頁為投影非 SSOT", "<title>", "cache_read"):
        present = marker in h
        print(f"  [{'PASS' if present else 'FAIL'}] html 含 {marker!r}")
        ok = ok and present
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 2


def main(argv):
    if len(argv) == 2 and argv[1] == "--selftest":
        return selftest()
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 1
    src = Path(argv[1])
    if not src.is_file():
        print(f"ERROR: 檔案不存在 {src}", file=sys.stderr)
        return 1
    out = Path(argv[argv.index("-o") + 1]) if "-o" in argv else src.with_suffix(".trace.html")
    trace = parse_session(src.read_text(encoding="utf-8").splitlines())
    out.write_text(render_html(trace, src.stem[:12]), encoding="utf-8")
    t = trace["totals"]
    print(f"OK {out} · {len(trace['usage_calls'])} calls · out {_fmt(t['out'])} tok · "
          f"cache 命中 {trace['cache_hit_ratio']*100:.1f}% · 驟降 {len(trace['misses'])} 起")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
