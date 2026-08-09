from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def _json_for_script(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).replace("</", "<\\/")


def _derive_stage(node: dict[str, Any]) -> int:
    metadata = node.get("metadata") or {}
    if "visual_stage" in metadata:
        return int(metadata["visual_stage"])
    kind = str(node.get("kind", ""))
    if kind in {"package", "module", "class", "interface"}:
        return 0
    if kind in {"method", "function", "constructor"}:
        return 1
    if kind in {"parameter", "variable", "field", "literal", "expression"}:
        return 2
    if kind in {"payload_field", "message_field", "request_field"}:
        return 3
    if kind in {"endpoint", "route", "handler"}:
        return 4
    if kind in {"database", "vault", "external_store", "queue"}:
        return 5
    if kind in {"runtime_event", "trace", "receipt"}:
        return 6
    if kind == "business_invariant":
        return 7
    return 3


def _prepare_view(graph: dict[str, Any]) -> dict[str, Any]:
    node_by_id = {node["id"]: node for node in graph["nodes"]}
    relevant: set[str] = {node["id"] for node in graph["nodes"] if node.get("critical")}
    for edge in graph["edges"]:
        if (
            edge.get("critical")
            or edge["source"] in relevant
            or edge["target"] in relevant
        ):
            relevant.add(edge["source"])
            relevant.add(edge["target"])
    for invariant in graph.get("invariants", []):
        relevant.update(invariant.get("subject_ids", []))
    if not relevant:
        relevant = set(node_by_id)

    stages: dict[int, list[dict[str, Any]]] = {}
    for node_id in sorted(relevant):
        node = node_by_id.get(node_id)
        if not node:
            continue
        stages.setdefault(_derive_stage(node), []).append(node)

    positions: dict[str, dict[str, float]] = {}
    width = max(1180, (max(stages, default=0) + 1) * 215 + 120)
    height = max(
        620, max((len(nodes) for nodes in stages.values()), default=1) * 115 + 140
    )
    for stage, nodes in stages.items():
        for index, node in enumerate(nodes):
            positions[node["id"]] = {"x": 70 + stage * 205, "y": 70 + index * 105}
    relevant_edges = [
        edge
        for edge in graph["edges"]
        if edge["source"] in positions and edge["target"] in positions
    ]
    return {
        "positions": positions,
        "edge_ids": [edge["id"] for edge in relevant_edges],
        "width": width,
        "height": height,
    }


TEMPLATE = r"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>@@TITLE@@</title>
<style>
:root{--ink:#152033;--muted:#627086;--paper:#f4f7fb;--card:#fff;--line:#d7e0ea;--nav:#0d223c;--blue:#176da5;--green:#18794e;--amber:#ad5c00;--red:#b1362e;--purple:#6552c7;--grey:#8795a8}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans TC",sans-serif}
header{background:linear-gradient(135deg,#0c2139,#17486f);color:#fff;padding:34px max(18px,calc((100vw - 1380px)/2)) 28px}header h1{margin:.25em 0;font-size:clamp(27px,4vw,44px)}header p{max-width:980px;margin:.45em 0;color:#d7e8f7}.banner{background:#fff3d8;color:#704800;border-left:6px solid #e49a00;padding:11px 16px;font-weight:800}
.tabs{position:sticky;top:0;z-index:30;display:flex;overflow-x:auto;background:var(--nav);padding:0 max(12px,calc((100vw - 1380px)/2));box-shadow:0 4px 16px #05132640}.tab{appearance:none;border:0;border-bottom:3px solid transparent;background:transparent;color:#9fb5cd;padding:13px 16px;font-weight:750;white-space:nowrap;cursor:pointer}.tab[aria-selected="true"]{color:#fff;border-bottom-color:#5ab3e8;background:#ffffff0a}
main{max-width:1380px;margin:auto;padding:22px 18px 70px}.view[hidden]{display:none}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:17px;box-shadow:0 7px 25px #16314f0c}.metric b{display:block;font-size:25px;color:var(--blue)}.metric span{color:var(--muted)}h2{font-size:23px;border-bottom:2px solid var(--line);padding-bottom:8px}h3{line-height:1.25}code{background:#edf2f7;border-radius:5px;padding:.12em .34em}pre{background:#101a28;color:#e7eef7;border-radius:10px;padding:14px;overflow:auto}
.workspace{display:grid;grid-template-columns:250px minmax(500px,1fr) 340px;gap:12px;align-items:start}.panel{background:#fff;border:1px solid var(--line);border-radius:13px;min-height:640px;overflow:hidden}.panel-head{padding:11px 13px;background:#edf3f8;border-bottom:1px solid var(--line);font-weight:800;display:flex;justify-content:space-between;gap:8px;align-items:center}.panel-body{padding:12px;max-height:76vh;overflow:auto}#graph-wrap{overflow:auto;background:#fbfdff;min-height:640px}svg{font-family:inherit}.edge{fill:none;stroke:#7d8ca0;stroke-width:2}.edge.static{stroke-dasharray:8 6}.edge.sandbox{stroke-width:3}.edge.prod{stroke-width:5}.edge.refuted{stroke:var(--red)}.edge.survived{stroke:var(--green)}.edge.unknown{stroke:var(--amber)}.node rect{fill:#fff;stroke:#95a8ba;stroke-width:1.5;rx:10}.node.critical rect{stroke:#b45309;stroke-width:3}.node.blind rect{fill:#eef1f5;stroke:#a0a8b2}.node:hover rect,.node.selected rect{stroke:var(--blue);stroke-width:4}.node text{pointer-events:none}.edge-label{font-size:10px;fill:#526277;cursor:pointer}.node-label{font-size:12px;font-weight:750;fill:#1f2d3d}.badge{font-size:9px;font-weight:850}.tree-row,.evidence-row,.session-row,.event-row{border-bottom:1px solid #e8edf2;padding:8px 4px}.tree-row button{border:0;background:transparent;color:var(--blue);cursor:pointer;text-align:left;padding:0}.pill{display:inline-block;border-radius:999px;padding:2px 7px;font-size:10px;font-weight:850;background:#e8eef5;color:#40566f;margin-right:4px}.pill.static,.pill.ast,.pill.semantic{background:#edf1f6}.pill.sandbox{background:#e7f5ee;color:#12613a}.pill.prod{background:#e8f2fb;color:#145d87}.pill.refuted{background:#fdeceb;color:#9f2d28}.pill.demo{background:#fff1ce;color:#7e5500}.pill.agent{background:#eeebff;color:#5141a7}.controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:10px 0}input[type=search]{min-width:260px;padding:9px 11px;border:1px solid var(--line);border-radius:8px}button.action{border:1px solid #b8c7d5;background:#fff;color:#245579;border-radius:8px;padding:8px 11px;cursor:pointer;font-weight:750}button.action.active{background:#173f63;color:#fff}table{width:100%;border-collapse:collapse}th,td{border:1px solid var(--line);padding:8px;vertical-align:top;text-align:left}th{background:#eaf1f7}.timeline{padding:12px;background:#fff;border:1px solid var(--line);border-radius:12px}.timeline input{width:100%}.timeline-current{font-size:17px;font-weight:800}.status-block{border-left:5px solid var(--amber);background:#fff8e8;padding:12px 14px;margin:12px 0}.status-block.settled{border-color:var(--green);background:#eef9f3}.status-block.refuted{border-color:var(--red);background:#fff0ef}.community{border:1px solid var(--line);border-radius:11px;padding:12px;margin:9px 0;background:#fff}.small{font-size:12px;color:var(--muted)}.code-title{font-weight:800;margin-bottom:7px}
@media(max-width:1100px){.workspace{grid-template-columns:1fr}.panel{min-height:auto}.panel-body{max-height:none}.grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:650px){.grid{grid-template-columns:1fr}main{padding:12px 10px 55px}}@media print{.tabs,.controls{display:none}body{background:#fff}.card,.panel{box-shadow:none}}
</style>
</head>
<body>
<header><div class="small">Code Truth Graph · evidence-bounded slice</div><h1>@@TITLE@@</h1><p>AST / SEMANTIC / SANDBOX / PROD / Agent retrieval / Human review are separate evidence lanes. No lane may silently stand in for another.</p></header>
<div class="banner">@@BANNER@@</div>
<nav class="tabs" role="tablist">
<button class="tab" data-view="overview" aria-selected="true">Decision Overview</button><button class="tab" data-view="graph" aria-selected="false">Code Graph</button><button class="tab" data-view="history" aria-selected="false">Invariant History</button><button class="tab" data-view="agent" aria-selected="false">Agent Scope</button><button class="tab" data-view="evidence" aria-selected="false">Evidence Ledger</button><button class="tab" data-view="graphrag" aria-selected="false">GraphRAG Overview</button>
</nav>
<main>
<section class="view" id="view-overview"></section>
<section class="view" id="view-graph" hidden>
<div class="controls"><input id="global-search" type="search" placeholder="symbol / payload / invariant / file…"><button class="action active" id="agent-overlay">Agent overlay</button><button class="action" id="critical-only">Critical slice only</button><span class="small">Line style: dashed STATIC · solid SANDBOX · thick PROD</span></div>
<div class="workspace"><div class="panel"><div class="panel-head">Directory & symbol tree <span class="small">navigation only</span></div><div class="panel-body" id="tree"></div></div><div class="panel"><div class="panel-head">Reach-aware code graph <span id="graph-count"></span></div><div id="graph-wrap"><svg id="graph-svg"></svg></div></div><div class="panel"><div class="panel-head">Node / edge evidence</div><div class="panel-body" id="detail"><p class="small">Select a node or edge.</p></div></div></div>
</section>
<section class="view" id="view-history" hidden><div id="history"></div></section><section class="view" id="view-agent" hidden><div id="agent"></div></section><section class="view" id="view-evidence" hidden><div id="evidence"></div></section><section class="view" id="view-graphrag" hidden><div id="graphrag"></div></section>
</main>
<script id="graph-data" type="application/json">@@DATA@@</script>
<script>
const DATA=JSON.parse(document.getElementById('graph-data').textContent);const G=DATA.graph,V=DATA.view;
const byId=Object.fromEntries(G.nodes.map(n=>[n.id,n]));const evidenceById=Object.fromEntries(G.evidence.map(e=>[e.id,e]));
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const reachClass=e=>{const r=e.reach||[];if(r.includes('PROD'))return'prod';if(r.includes('SANDBOX'))return'sandbox';return'static'};
const reachBadges=r=>(r||[]).map(x=>`<span class="pill ${x.toLowerCase()}">${esc(x)}</span>`).join('');
const eventStatusAt=(edge,seq)=>{const events=G.invariant_events.filter(e=>(e.affected_edge_ids||[]).includes(edge.id)&&Number(e.sequence)<=seq).sort((a,b)=>Number(a.sequence)-Number(b.sequence));const last=events.at(-1);if(!last)return'unknown';if(['REFUTED','INVALIDATED'].includes(last.action))return'refuted';if(['SURVIVED','SETTLED','REASSERTED'].includes(last.action))return'survived';return'unknown'};
let timelineSeq=Math.max(0,...G.invariant_events.map(e=>Number(e.sequence)||0));let agentOverlay=true;let criticalOnly=false;let search='';
function switchView(id){document.querySelectorAll('.view').forEach(v=>v.hidden=v.id!==`view-${id}`);document.querySelectorAll('.tab').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.view===id)));if(id==='graph')renderGraph()}
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>switchView(b.dataset.view));
function relevantNodes(){let ids=new Set(V.positions?Object.keys(V.positions):G.nodes.map(n=>n.id));if(!criticalOnly)return ids;const critical=new Set(G.nodes.filter(n=>n.critical).map(n=>n.id));G.edges.filter(e=>e.critical).forEach(e=>{critical.add(e.source);critical.add(e.target)});return critical}
function agentTouched(){return new Set(G.agent_sessions.flatMap(s=>s.touched_node_ids||[]))}
function renderGraph(){const svg=document.getElementById('graph-svg');const ids=relevantNodes();const touched=agentTouched();const visible=[...ids].filter(id=>{if(!search)return true;return JSON.stringify(byId[id]).toLowerCase().includes(search)});const visibleSet=new Set(visible);const edges=G.edges.filter(e=>visibleSet.has(e.source)&&visibleSet.has(e.target));svg.setAttribute('width',V.width);svg.setAttribute('height',V.height);svg.innerHTML='<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#718196"/></marker></defs>';
for(const e of edges){const a=V.positions[e.source],b=V.positions[e.target];if(!a||!b)continue;const x1=a.x+150,y1=a.y+29,x2=b.x,y2=b.y+29,bend=(x1+x2)/2;const p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',`M${x1},${y1} C${bend},${y1} ${bend},${y2} ${x2},${y2}`);p.setAttribute('class',`edge ${reachClass(e)} ${eventStatusAt(e,timelineSeq)}`);p.setAttribute('marker-end','url(#arrow)');p.dataset.id=e.id;p.onclick=()=>showEdge(e);svg.appendChild(p);const t=document.createElementNS('http://www.w3.org/2000/svg','text');t.setAttribute('x',bend);t.setAttribute('y',(y1+y2)/2-5);t.setAttribute('class','edge-label');t.textContent=e.kind;t.onclick=()=>showEdge(e);svg.appendChild(t)}
for(const id of visible){const n=byId[id],p=V.positions[id];if(!n||!p)continue;const group=document.createElementNS('http://www.w3.org/2000/svg','g');const blind=agentOverlay&&!touched.has(id);group.setAttribute('class',`node ${n.critical?'critical':''} ${blind?'blind':''}`);group.setAttribute('transform',`translate(${p.x},${p.y})`);group.dataset.id=id;const rect=document.createElementNS('http://www.w3.org/2000/svg','rect');rect.setAttribute('width','150');rect.setAttribute('height','58');group.appendChild(rect);const label=document.createElementNS('http://www.w3.org/2000/svg','text');label.setAttribute('x','9');label.setAttribute('y','20');label.setAttribute('class','node-label');label.textContent=n.label.length>21?n.label.slice(0,20)+'…':n.label;group.appendChild(label);const kind=document.createElementNS('http://www.w3.org/2000/svg','text');kind.setAttribute('x','9');kind.setAttribute('y','39');kind.setAttribute('class','badge');kind.textContent=`${n.kind} · ${(n.reach||[]).join('/')||'UNKNOWN'}`;group.appendChild(kind);group.onclick=()=>showNode(n);svg.appendChild(group)}document.getElementById('graph-count').textContent=`${visible.length} nodes · ${edges.length} edges`}
function evidenceCard(e){return `<div class="evidence-row">${reachBadges([e.reach])}<b>${esc(e.method)}</b> · ${esc(e.status)}<div>${esc(e.summary)}</div><div class="small">${esc(e.source)} · authority=${esc(e.authority)} · environment=${esc(e.environment_class)}</div></div>`}
function showNode(n){document.querySelectorAll('.node').forEach(x=>x.classList.toggle('selected',x.dataset.id===n.id));const loc=n.location||{},ev=(n.evidence_ids||[]).map(id=>evidenceById[id]).filter(Boolean);document.getElementById('detail').innerHTML=`<h3>${esc(n.label)}</h3>${reachBadges(n.reach)}${n.critical?'<span class="pill demo">CRITICAL</span>':''}<p><b>Kind:</b> ${esc(n.kind)}<br><b>ID:</b> <code>${esc(n.id)}</code><br><b>Source:</b> <code>${esc(loc.repo||'virtual')}@${esc(loc.sha||'')}:${esc(loc.path||'')}:${loc.start_line||''}-${loc.end_line||''}</code></p><div class="code-title">Expandable exact source context</div><pre><code>${esc((n.metadata||{}).snippet||'No embedded source snippet; evidence may be virtual or external.')}</code></pre><h3>Evidence</h3>${ev.map(evidenceCard).join('')||'<p class="small">No evidence attached.</p>'}`}
function showEdge(e){const ev=(e.evidence_ids||[]).map(id=>evidenceById[id]).filter(Boolean);document.getElementById('detail').innerHTML=`<h3>${esc(e.kind)}</h3>${reachBadges(e.reach)}${e.critical?'<span class="pill demo">CRITICAL EDGE</span>':''}<p><b>From:</b> ${esc(byId[e.source]?.label||e.source)}<br><b>To:</b> ${esc(byId[e.target]?.label||e.target)}<br><b>ID:</b> <code>${esc(e.id)}</code></p><h3>Evidence by reach</h3>${ev.map(evidenceCard).join('')||'<p class="small">No evidence attached.</p>'}`}
function renderTree(){const groups={};for(const n of G.nodes){const path=n.location?.path||'[virtual]';(groups[path]??=[]).push(n)}document.getElementById('tree').innerHTML=Object.entries(groups).sort().map(([path,nodes])=>`<details><summary><b>${esc(path)}</b> <span class="small">${nodes.length}</span></summary>${nodes.sort((a,b)=>(a.location?.start_line||0)-(b.location?.start_line||0)).map(n=>`<div class="tree-row"><button data-id="${esc(n.id)}">${esc(n.label)}:${n.location?.start_line||''}</button> ${n.critical?'<span class="pill demo">critical</span>':''}</div>`).join('')}</details>`).join('');document.querySelectorAll('#tree button').forEach(b=>b.onclick=()=>showNode(byId[b.dataset.id]))}
function renderOverview(){const criticalEdges=G.edges.filter(e=>e.critical),staticOnly=criticalEdges.filter(e=>!(e.reach||[]).some(r=>['SANDBOX','PROD'].includes(r))),inv=G.invariants[0];document.getElementById('view-overview').innerHTML=`<div class="grid"><div class="card metric"><b>${G.nodes.length}</b><span>nodes</span></div><div class="card metric"><b>${G.edges.length}</b><span>typed edges</span></div><div class="card metric"><b>${criticalEdges.length}</b><span>critical edges</span></div><div class="card metric"><b>${staticOnly.length}</b><span>STATIC-only critical edges</span></div></div><div class="status-block ${(inv?.current_status||'').toLowerCase()}"><h2>${esc(inv?.id||'Invariant')} · ${esc(inv?.current_status||'UNKNOWN')}</h2><p>${esc(inv?.statement||'No invariant loaded')}</p><p><b>Product truth:</b> synthetic fixtures never satisfy real-authority settlement. Current build validates the pipeline and exposes missing receipts.</p></div><div class="card"><h2>What this slice proves</h2><table><tr><th>Lane</th><th>Current meaning</th></tr><tr><td>AST</td><td>Compiler-derived symbols and possible typed relations from the declared source scope.</td></tr><tr><td>SEMANTIC</td><td>Typed definition/reference observations; a missing observation never means zero references.</td></tr><tr><td>SANDBOX</td><td>Coverage lights nodes only. A specific edge requires an explicit runtime receipt.</td></tr><tr><td>PROD</td><td>Structured log/trace/state receipt. Unobserved remains unknown unless sampling and instrumentation justify more.</td></tr><tr><td>Agent</td><td>Which file ranges an agent retrieved. This predicts blind spots but is not correctness evidence.</td></tr></table></div><div class="card"><h2>Evidence closure vector</h2><pre>${esc(JSON.stringify(G.closure,null,2))}</pre></div>`}
function renderHistory(){const max=Math.max(0,...G.invariant_events.map(e=>Number(e.sequence)||0));document.getElementById('history').innerHTML=G.invariants.map(inv=>{const events=G.invariant_events.filter(e=>e.invariant_id===inv.id).sort((a,b)=>a.sequence-b.sequence);return `<div class="card"><h2>${esc(inv.id)} · ${esc(inv.current_status)}</h2><p>${esc(inv.statement)}</p><div class="timeline"><input type="range" min="0" max="${max}" value="${timelineSeq}" id="timeline-slider"><div class="timeline-current" id="timeline-current"></div></div><div>${events.map(e=>`<div class="event-row" data-seq="${e.sequence}"><span class="pill ${['REFUTED','INVALIDATED'].includes(e.action)?'refuted':(e.reach||'').toLowerCase()}">T${e.sequence} ${esc(e.action)}</span><b>${esc(e.reach||'')}</b><div>${esc(e.note||'')}</div><div class="small">independence=${esc(e.independence_group||'')} · evidence=${(e.evidence_ids||[]).map(esc).join(', ')}</div></div>`).join('')}</div><h3>Settlement evaluation</h3><pre>${esc(JSON.stringify(inv.settlement,null,2))}</pre></div>`}).join('');const slider=document.getElementById('timeline-slider');if(slider){slider.oninput=()=>{timelineSeq=Number(slider.value);updateTimeline();renderGraph()};updateTimeline()}}
function updateTimeline(){const current=G.invariant_events.filter(e=>Number(e.sequence)<=timelineSeq).sort((a,b)=>a.sequence-b.sequence).at(-1),el=document.getElementById('timeline-current');if(el)el.textContent=current?`T${current.sequence} · ${current.action} · ${current.note}`:'T0 · before evidence';document.querySelectorAll('.event-row').forEach(row=>row.style.opacity=Number(row.dataset.seq)<=timelineSeq?'1':'.25')}
function renderAgent(){const closure=G.closure.agent_retrieval||{};document.getElementById('agent').innerHTML=`<div class="card"><h2>Agent retrieval coverage</h2><p>Stages: DISCOVERABLE → ENUMERATED → RETRIEVED → DELIVERED_TO_CONTEXT → CITED → EDITED → TESTED. Reading is not validation.</p><pre>${esc(JSON.stringify(closure,null,2))}</pre></div>${G.agent_sessions.map(s=>`<div class="card"><h2>${esc(s.agent)} · ${esc(s.session_id||s.thread_id||s.id)}</h2><p class="small">${esc(s.source)} · events=${s.event_count} · touched nodes=${(s.touched_node_ids||[]).length}</p>${(s.accesses||[]).map(a=>`<div class="session-row"><span class="pill agent">${esc(a.stage)}</span><code>${esc(a.file)}:${a.line_start}-${a.line_end}</code> · ${esc(a.tool)}</div>`).join('')||'<p class="small">No recognized file ranges: scope UNKNOWN, not zero.</p>'}</div>`).join('')}`}
function renderEvidence(){document.getElementById('evidence').innerHTML=`<div class="card"><h2>Terminal evidence ledger</h2><table><thead><tr><th>Reach</th><th>Method / status</th><th>Summary</th><th>Source & authority</th></tr></thead><tbody>${G.evidence.map(e=>`<tr><td>${reachBadges([e.reach])}</td><td><b>${esc(e.method)}</b><br>${esc(e.status)}</td><td>${esc(e.summary)}</td><td><code>${esc(e.source)}</code><br><span class="small">${esc(e.authority)} / ${esc(e.environment_class)}</span></td></tr>`).join('')}</tbody></table></div><div class="card"><h2>Diagnostics</h2>${G.diagnostics.map(d=>`<div class="evidence-row"><span class="pill ${d.severity==='warning'?'demo':''}">${esc(d.code)}</span>${esc(d.summary)}<pre>${esc(JSON.stringify(d.details,null,2))}</pre></div>`).join('')||'<p>No diagnostics.</p>'}</div>`}
function renderGraphRag(){document.getElementById('graphrag').innerHTML=`<div class="card"><h2>GraphRAG BYOG overview</h2><p>Authoritative nodes and edges are produced deterministically. GraphRAG may summarize or retrieve this graph, but generated community prose is never terminal evidence.</p><p>Exports: <code>build/graphrag/entities.csv</code>, <code>relationships.csv</code>, <code>text_units.csv</code>; optional Parquet conversion requires <code>pyarrow</code>.</p></div>${G.communities.map(c=>`<div class="community"><h3>${esc(c.title)} <span class="pill">${c.node_ids.length} nodes</span></h3><p>${esc(c.summary)}</p><div class="small">${esc(c.summary_kind)} · ${esc(c.warning)}</div></div>`).join('')}`}
document.getElementById('global-search').oninput=e=>{search=e.target.value.trim().toLowerCase();renderGraph()};document.getElementById('agent-overlay').onclick=e=>{agentOverlay=!agentOverlay;e.currentTarget.classList.toggle('active',agentOverlay);renderGraph()};document.getElementById('critical-only').onclick=e=>{criticalOnly=!criticalOnly;e.currentTarget.classList.toggle('active',criticalOnly);renderGraph()};
renderOverview();renderTree();renderHistory();renderAgent();renderEvidence();renderGraphRag();renderGraph();
</script>
</body></html>"""


def render_html(graph: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    view = _prepare_view(graph)
    title = html.escape(graph.get("title", "Code Truth Graph"))
    scope_mode = graph.get("scope", {}).get("mode", "unknown")
    synthetic = scope_mode in {"demo", "synthetic"} or graph.get("scope", {}).get(
        "synthetic", False
    )
    banner = (
        "DEMO / SYNTHETIC — 此頁驗證抽取、追溯與介面，不構成產品或 production 真相。"
        if synthetic
        else "LIVE SCOPE — Production claims still require artifact mapping and receipts."
    )
    payload = _json_for_script({"graph": graph, "view": view})
    document = (
        TEMPLATE.replace("@@TITLE@@", title)
        .replace("@@BANNER@@", html.escape(banner))
        .replace("@@DATA@@", payload)
    )
    output.write_text(document, encoding="utf-8")
