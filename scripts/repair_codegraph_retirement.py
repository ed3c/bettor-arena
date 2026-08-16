#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path: str, value) -> None:
    Path(path).write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


# Machine queue: #41 is historical only; #140 owns order-13 retirement.
seq_path = "docs/git/pdf-terminal-sequence.json"
seq = load(seq_path)
stage13 = next(item for item in seq["items"] if item["order"] == 13)
old_id = stage13["id"]
stage13.update(
    {
        "id": "stage-13-code-graph-retirement",
        "issues": [140],
        "expected_branch": "feat/92-context-funnel-retirement",
        "owner_paths": [
            "docs/knowledge-providers",
            ".skill-bindings/repo-agent-native",
            "loop_wiki/code-truth-graph-v2",
        ],
        "acceptance": [
            "Active provider, runtime, evaluator and queue routes contain no Code-Graph-RAG participant",
            "Historical Code-Graph-RAG evidence remains discoverable only as REJECTED/ABSENT",
            "Blindspots/source/SCIP/Tree-sitter contracts preserve UNKNOWN when coverage or readback is incomplete",
        ],
        "evidence_boundary": "Retirement does not prove GrepAI, SCIP/LSP, Tree-sitter, Serena, Git Town or Forgejo live health.",
        "automation_boundary": "Provider activation, semantic-conflict admission, merge, release, promotion and rollback remain separately admitted operations.",
        "title": "Retire Code-Graph-RAG and converge the Blindspots replacement route",
    }
)
for item in seq["items"]:
    item["prerequisite_items"] = [
        "stage-13-code-graph-retirement" if dep == old_id else dep
        for dep in item["prerequisite_items"]
    ]
seq["observed_at"] = "2026-08-17T00:00:00Z"
save(seq_path, seq)

# Human-readable queue surfaces.
p = Path("docs/git/PDF_TERMINAL_SEQUENCE.md")
text = p.read_text(encoding="utf-8")
old = "| 13 | #41 | `feat/code-graph-rag-readonly-admission-v1` | read-only Code-Graph-RAG runtime admission | `BLOCKED_BY_PREDECESSOR` |"
new = "| 13 | #140 | `feat/92-context-funnel-retirement` | retire Code-Graph-RAG; converge Blindspots/source/SCIP/Tree-sitter replacement route | `BLOCKED_BY_PREDECESSOR` |"
if old not in text:
    raise SystemExit("order-13 markdown anchor missing")
text = text.replace(old, new).replace(
    "#91 six-host matrix + #92/#41/#93 providers",
    "#91 six-host matrix + #92/#140/#93 code-intelligence/provider evidence",
)
p.write_text(text, encoding="utf-8")

p = Path("README.md")
text = p.read_text(encoding="utf-8")
text = text.replace(
    "Code-Graph-RAG read-only live admission                   NOT_EXERCISED",
    "Code-Graph-RAG active route / order-13 #140 retirement    RETIRED / BLOCKED_BY_PREDECESSOR",
)
if "#140" not in text:
    text += "\n\nOrder 13 retirement authority: #140; Code-Graph-RAG historical evidence remains REJECTED/ABSENT.\n"
p.write_text(text, encoding="utf-8")

# Active evaluator set excludes retired provider while historical manifest remains.
p = Path("scripts/knowledge_provider_eval_registry.py")
text = p.read_text(encoding="utf-8")
anchor = 'PROVIDERS = {"serena", "grepai", "code-graph-rag", "mem0"}\nPARTICIPANTS = PROVIDERS | {"exact-search-control", "repository-authority-control"}'
replacement = 'PROVIDERS = {"serena", "grepai", "mem0"}\nHISTORICAL_PROVIDERS = {"code-graph-rag"}\nPARTICIPANTS = PROVIDERS | {"exact-search-control", "repository-authority-control"}'
if anchor not in text:
    raise SystemExit("provider registry anchor missing")
text = text.replace(anchor, replacement)
anchor = '    require(set(out) == PROVIDERS, "provider set")\n    common_safety(reg)\n    return out'
replacement = '''    require(set(out) == PROVIDERS | HISTORICAL_PROVIDERS, "provider registry set")
    for pid in HISTORICAL_PROVIDERS:
        manifest = load(root / BASE / next(e["path"] for e in reg["providers"] if e["id"] == pid))
        admission = manifest.get("admission", {})
        adapter = manifest.get("adapter", {})
        require(admission.get("state") == "REJECTED", f"{pid}: historical provider must be REJECTED")
        require(admission.get("runtime_state") == "ABSENT", f"{pid}: historical runtime must be ABSENT")
        require(admission.get("live_claim") is False, f"{pid}: historical live claim forbidden")
        require(adapter.get("transport") == "none", f"{pid}: historical transport must be none")
    common_safety(reg)
    return {pid: value for pid, value in out.items() if pid in PROVIDERS}'''
if anchor not in text:
    raise SystemExit("provider set anchor missing")
p.write_text(text.replace(anchor, replacement), encoding="utf-8")

# Graph evaluation becomes deterministic baseline-only. Compressed retired
# observations remain immutable historical fixture bytes and are filtered only
# while fixture_only=true.
participant = Path("docs/knowledge-providers/evals/participants/code-graph-rag.json")
if participant.exists():
    participant.unlink()
graph_path = "docs/knowledge-providers/evals/cases/graph.json"
graph = load(graph_path)
graph["participants"] = ["exact-search-control"]
graph["eligible_recommendations"] = ["REJECTED"]
save(graph_path, graph)

schema_path = "docs/knowledge-providers/evals/contracts/eval-case.schema.json"
schema = load(schema_path)
schema["properties"]["participants"]["minItems"] = 1
save(schema_path, schema)

p = Path("scripts/knowledge_provider_eval_cases.py")
text = p.read_text(encoding="utf-8")
old = '''    require(
        isinstance(pids, list) and len(pids) == 2 and len(set(pids)) == 2,
        f"{cid}: participants",
    )
    kinds = [people.get(x, {}).get("kind") for x in pids]
    require(sorted(kinds) == ["control", "provider"], f"{cid}: provider/control pair")'''
new = '''    require(
        isinstance(pids, list) and pids and len(pids) <= 2 and len(set(pids)) == len(pids),
        f"{cid}: participants",
    )
    kinds = [people.get(x, {}).get("kind") for x in pids]
    if fam == "graph":
        require(pids == ["exact-search-control"] and kinds == ["control"], f"{cid}: retired graph baseline")
    else:
        require(len(pids) == 2 and sorted(kinds) == ["control", "provider"], f"{cid}: provider/control pair")'''
if old not in text:
    raise SystemExit("case validator anchor missing")
p.write_text(text.replace(old, new), encoding="utf-8")

p = Path("scripts/knowledge_provider_eval_engine.py")
text = p.read_text(encoding="utf-8")
text = text.replace(
    "from knowledge_provider_eval_registry import load_participants, provider_digests",
    "from knowledge_provider_eval_registry import HISTORICAL_PROVIDERS, load_participants, provider_digests",
)
old = '    values = load(path)\n    require(isinstance(values, list) and values, "observations array")'
new = '''    values = load(path)
    require(isinstance(values, list) and values, "observations array")
    retired = [v for v in values if isinstance(v, dict) and v.get("participant_id") in HISTORICAL_PROVIDERS]
    if retired:
        require(config["fixture_only"], "retired provider observations forbidden outside historical fixtures")
        values = [v for v in values if not (isinstance(v, dict) and v.get("participant_id") in HISTORICAL_PROVIDERS)]
    require(values, "active observations array")'''
if old not in text:
    raise SystemExit("engine observation anchor missing")
p.write_text(text.replace(old, new), encoding="utf-8")

p = Path("tests/knowledge-provider-evals/run-all.sh")
text = p.read_text(encoding="utf-8")
text = text.replace('"expected": 8,', '"expected": 7,').replace(
    '"observed": 8,', '"observed": 7,'
)
p.write_text(text, encoding="utf-8")

p = Path("docs/knowledge-providers/evals/README.md")
text = p.read_text(encoding="utf-8")
text = text.replace(
    "Code-Graph-RAG, Mem0, an LLM, or an MCP server.",
    "Mem0, an LLM, or an MCP server. Code-Graph-RAG is historical REJECTED/ABSENT evidence and is not an active evaluator participant.",
)
text = text.replace("│   ├── code-graph-rag.json\n", "")
text = text.replace(
    "| graph | Code-Graph-RAG | manifest/import/source traversal | Cross-module impact without converting coverage gaps into absence |",
    "| graph | none — retired | exact repository search | deterministic baseline only; Blindspots replacement is validated outside provider admission |",
)
text = text.replace(
    "Every case has exactly one provider and one control. The default contract\nrequires all eight case/participant pairs.",
    "Provider-admission cases retain provider/control pairs. The graph family is a deterministic baseline-only case after Code-Graph-RAG retirement. The active matrix requires seven case/participant pairs; historical retired observations remain fixture history only.",
)
text = text.replace(
    "Code-Graph-RAG adapter/index     NOT_CONFIGURED",
    "Code-Graph-RAG active evaluator   RETIRED (historical manifest REJECTED/ABSENT)",
)
p.write_text(text, encoding="utf-8")

p = Path("docs/knowledge-providers/evals/STATUS.md")
text = p.read_text(encoding="utf-8")
text = text.replace(
    "Four cases and eight paired observations",
    "Four cases and seven active observations; retired Code-Graph-RAG fixture remains historical",
)
text = text.replace(
    "| Code-Graph-RAG | NOT_CONFIGURED | Read-only adapter and graph coverage receipt absent |",
    "| Code-Graph-RAG | RETIRED | Historical manifest REJECTED/ABSENT; no active evaluator/runtime route |",
)
p.write_text(text, encoding="utf-8")

# Persistent deterministic retirement checker with planted mutations.
checker = Path("scripts/gates/check_code_graph_rag_retirement.py")
checker.write_text(
    r'''#!/usr/bin/env python3
from __future__ import annotations
import argparse, copy, json, sys
from pathlib import Path
class E(ValueError): pass
def req(v,m):
    if not v: raise E(m)
def load(p): return json.loads(p.read_text(encoding="utf-8"))
def snapshot(root=Path(".")):
    seq=load(root/"docs/git/pdf-terminal-sequence.json")
    manifest=load(root/"docs/knowledge-providers/providers/code-graph-rag.json")
    registry=(root/"scripts/knowledge_provider_eval_registry.py").read_text(encoding="utf-8")
    return seq,manifest,(root/"docs/knowledge-providers/evals/participants/code-graph-rag.json").exists(),registry,(root/"docs/git/PDF_TERMINAL_SEQUENCE.md").read_text(encoding="utf-8"),(root/"README.md").read_text(encoding="utf-8")
def validate_values(seq,manifest,participant,registry,doc,readme):
    stage=next(x for x in seq["items"] if x["order"]==13)
    req(stage["id"]=="stage-13-code-graph-retirement","legacy stage id active")
    req(stage["issues"]==[140],"legacy issue #41 active")
    req(all(41 not in x["issues"] for x in seq["items"]),"#41 remains queue issue")
    req(all("stage-13-code-graph-rag" not in x["prerequisite_items"] for x in seq["items"]),"legacy prerequisite active")
    adm=manifest.get("admission",{}); adapter=manifest.get("adapter",{})
    req(adm.get("state")=="REJECTED" and adm.get("runtime_state")=="ABSENT" and adm.get("live_claim") is False,"historical manifest active")
    req(adapter.get("transport")=="none","historical transport active")
    req(not participant,"retired evaluator participant present")
    providers=next(x for x in registry.splitlines() if x.startswith("PROVIDERS ="))
    req("code-graph-rag" not in providers,"retired provider active in evaluator")
    req("HISTORICAL_PROVIDERS" in registry,"historical classification missing")
    req("| 13 | #140 |" in doc,"human queue stale")
    req("#140" in readme and "RETIRED" in readme,"README retirement missing")
    return {"status":"PASS","stage":stage["id"],"issue":140}
def validate(root=Path(".")): return validate_values(*snapshot(root))
def selftest(root=Path(".")):
    vals=list(snapshot(root)); validate_values(*vals); names=[]; tests=[]
    a=copy.deepcopy(vals); next(x for x in a[0]["items"] if x["order"]==13)["issues"]=[41]; tests.append(("queue-41",a))
    a=copy.deepcopy(vals); a[1]["admission"]["state"]="CANDIDATE"; tests.append(("manifest-active",a))
    a=copy.deepcopy(vals); a[2]=True; tests.append(("participant-active",a))
    a=copy.deepcopy(vals); a[3]=a[3].replace('PROVIDERS = {"serena", "grepai", "mem0"}','PROVIDERS = {"serena", "grepai", "code-graph-rag", "mem0"}'); tests.append(("provider-set",a))
    for name,a in tests:
        try: validate_values(*a)
        except E: names.append(name); continue
        raise E(name+": planted mutation passed")
    return {"status":"PASS","controls":names}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--selftest",action="store_true"); ns=ap.parse_args()
    try: out=selftest() if ns.selftest else validate()
    except (E,OSError,json.JSONDecodeError) as exc: print("FAIL:",exc,file=sys.stderr); return 2
    print(json.dumps(out,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
''',
    encoding="utf-8",
)

module_path = ".arena/modules/knowledge-providers/module.json"
module = load(module_path)
target = "scripts/gates/check_code_graph_rag_retirement.py"
for paths in (module["roots"], module["components"]["proof"]["paths"]):
    if target not in paths:
        paths.append(target)
save(module_path, module)
