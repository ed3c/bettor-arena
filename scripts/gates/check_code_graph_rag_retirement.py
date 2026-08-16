#!/usr/bin/env python3
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
