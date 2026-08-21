#!/usr/bin/env python3
"""Fail-closed Bettor admission for exact KAW route proposals."""
from __future__ import annotations

import argparse, hashlib, json, re, sys
from pathlib import Path
from typing import Any, MutableMapping

LOGICAL = re.compile(r"^[A-Za-z][A-Za-z0-9._:-]{2,127}$")
OWNER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
REASON = re.compile(r"^[A-Z0-9_]{1,96}$")
AUTH = {"SOURCE_PROVIDER","GITHUB","DOMAIN_REPOSITORY","METHOD_REPOSITORY","QUALIFIER","EXPERIMENT_OWNER","RUNTIME_OWNER","ORCHESTRATOR","USER","EXTERNAL"}
KINDS = {"SOURCE","CLAIM","REQUIREMENT","CAPABILITY","TECHNOLOGY_DECISION","SKILL_CANDIDATE","SKILL","WORK_ITEM","IMPLEMENTATION","EVIDENCE","EXPERIMENT","OUTCOME","PROMPT","DOCUMENT","OTHER"}
SECRETS = ("github_pat_","ghp_","gho_","ghu_","ghs_","ghr_","bearer ","authorization:","set-cookie:","cookie:","access_token","refresh_token","client_secret")
LAWS = {"ROUTE_ACK != WORKER_EXECUTION","WORKER_EXECUTION != GATE_SUCCESS","GATE_RECEIPT != DOMAIN_TRUTH","REQUEST_ID != SEMANTIC_IDENTITY","FIXTURE != LIVE","KAW_CANNOT_WRITE_LOOPX_STATE"}

class ContractError(ValueError): pass

def req(ok: bool, msg: str) -> None:
    if not ok: raise ContractError(msg)

def as_obj(v: Any, label: str) -> dict[str, Any]:
    req(isinstance(v, dict), f"{label} must be object"); return v

def as_arr(v: Any, label: str) -> list[Any]:
    req(isinstance(v, list), f"{label} must be array"); return v

def exact(v: dict[str, Any], keys: set[str], label: str) -> None:
    req(set(v) == keys, f"{label} keys mismatch")

def text(v: Any, label: str, n: int=1024) -> str:
    req(isinstance(v, str) and v and len(v) <= n and "\n" not in v and "\r" not in v, f"{label} invalid"); return v

def strings(v: Any):
    if isinstance(v, str): yield v
    elif isinstance(v, dict):
        for x in v.values(): yield from strings(x)
    elif isinstance(v, list):
        for x in v: yield from strings(x)

def scan(v: Any) -> None:
    for raw in strings(v):
        low = raw.lower()
        req(not any(x in low for x in SECRETS), "credential-like material")
        req("private.github" not in low, "private locator")

def authority(v: Any, label: str) -> dict[str,str]:
    o=as_obj(v,label); exact(o,{"kind","ownerId"},label)
    k=text(o["kind"],label+".kind",64); owner=text(o["ownerId"],label+".ownerId",256)
    req(k in AUTH and OWNER.fullmatch(owner) is not None, f"{label} invalid")
    return {"kind":k,"ownerId":owner}

def digest(v: Any, label: str) -> dict[str,str]:
    o=as_obj(v,label); exact(o,{"algorithm","value"},label)
    raw=text(o["value"],label+".value",64)
    req(o["algorithm"]=="sha256" and SHA64.fullmatch(raw) is not None, f"{label} invalid")
    return {"algorithm":"sha256","value":raw}

def key(v: Any, label: str) -> dict[str,str]:
    o=as_obj(v,label); exact(o,{"logicalId","kind"},label)
    lid=text(o["logicalId"],label+".logicalId",128); kind=text(o["kind"],label+".kind",64)
    req(LOGICAL.fullmatch(lid) is not None and kind in KINDS, f"{label} invalid")
    return {"logicalId":lid,"kind":kind}

def kt(k: dict[str,str]) -> tuple[str,str]: return k["kind"],k["logicalId"]

def _validate_binding(b: dict[str,Any]) -> None:
    exact(b,{"schema","upstream","bettor","state","hardLaws"},"binding")
    req(b["schema"]=="bettor.capability-workspace-binding/v1","binding schema")
    u=as_obj(b["upstream"],"upstream")
    exact(u,{"repository","commit","tree","routerPath","routerBlob","contractsPath","contractsBlob","capabilityId","routeClass","destinationOwner"},"upstream")
    expected_u={
      "repository":"ed3c/kotlin-auto-webview","commit":"56eb824866e7e74d63a4297748c647cff738db51","tree":"0a32759d10c4a08a1815026f9504145d2fbc7cad",
      "routerBlob":"d25f92d140fa1b7012345a921d52efa7af1d10e7","contractsBlob":"47ea8f32ea12bc80239dcb48070174de43a77944",
      "capabilityId":"orchestrate.work","routeClass":"ORCHESTRATE_WORK","destinationOwner":{"kind":"ORCHESTRATOR","ownerId":"bettor-arena"}}
    for k0,v0 in expected_u.items(): req(u[k0]==v0,f"upstream {k0} drift")
    bt=as_obj(b["bettor"],"bettor")
    exact(bt,{"repository","commit","tree","workerManifestPath","workerManifestBlob","workerReceiptSchemaPath","workerReceiptSchemaBlob"},"bettor")
    expected_b={"repository":"ed3c/bettor-arena","commit":"65b7188ba57b0769419850db462bd92b5c834e00","tree":"41f0ecdef0232114d9f339fbfd984e37e56f3dc5","workerManifestBlob":"ed851c870b519184bf6b2ea258f291515d783271","workerReceiptSchemaBlob":"c9aded898d0108e550e8614b716251f3afef2cd5"}
    for k0,v0 in expected_b.items(): req(bt[k0]==v0,f"bettor {k0} drift")
    st=as_obj(b["state"],"state"); exact(st,{"consumer","workerGateway","workerRuntime","gateRuntime","liveHandoff"},"state")
    req(st=={"consumer":"IMPLEMENTED","workerGateway":"CONTRACT_PRESENT_FIXTURE_ONLY","workerRuntime":"NOT_EXERCISED","gateRuntime":"NOT_EXERCISED","liveHandoff":"NOT_EXERCISED"},"state widened")
    req(set(as_arr(b["hardLaws"],"hardLaws"))==LAWS,"hard-law denominator")
    scan(b)

def expectation(v: Any,i:int) -> dict[str,Any]:
    o=as_obj(v,f"expectation[{i}]"); req(set(o).issubset({"key","expectedVersion","expectedDigest"}) and "key" in o,"expectation keys")
    ver=o.get("expectedVersion"); dig=o.get("expectedDigest")
    ver=text(ver,"expectedVersion",256) if ver is not None else None
    dig=digest(dig,"expectedDigest") if dig is not None else None
    req(ver is not None or dig is not None,"expectation not exact")
    return {"key":key(o["key"],"expectation.key"),"expectedVersion":ver,"expectedDigest":dig}

def admission(v: Any,i:int) -> dict[str,Any]:
    o=as_obj(v,f"admission[{i}]"); exact(o,{"key","version","digest","visibility","dataClass","canonicalAuthority"},"admission")
    ver=text(o["version"],"version",256) if o["version"] is not None else None
    dig=digest(o["digest"],"digest") if o["digest"] is not None else None
    req(ver is not None or dig is not None,"admission not exact")
    req(o["visibility"]=="PUBLIC" and o["dataClass"]=="PUBLIC","subject not public")
    return {"key":key(o["key"],"admission.key"),"version":ver,"digest":dig,"visibility":"PUBLIC","dataClass":"PUBLIC","canonicalAuthority":authority(o["canonicalAuthority"],"canonicalAuthority")}

def _validate_envelope(e: dict[str,Any], b: dict[str,Any]) -> dict[str,Any]:
    exact(e,{"schema","capabilityId","proposal","subjectAdmission","mode"},"envelope")
    req(e["schema"]=="bettor.capability-workspace-envelope/v1" and e["capabilityId"]==b["upstream"]["capabilityId"],"envelope binding")
    req(e["mode"] in {"CONTRACT_ONLY","FIXTURE_REFERENCE"},"mode")
    p=as_obj(e["proposal"],"proposal"); exact(p,{"requestId","caller","intent","routeClass","destinationOwner","evidenceCeiling","exactSubjects"},"proposal")
    rid=text(p["requestId"],"requestId",128); req(LOGICAL.fullmatch(rid) is not None,"requestId")
    caller=authority(p["caller"],"caller"); intent=text(p["intent"],"intent")
    req(p["routeClass"]==b["upstream"]["routeClass"],"routeClass")
    dest=authority(p["destinationOwner"],"destinationOwner"); req(dest==b["upstream"]["destinationOwner"],"destinationOwner")
    ev=text(p["evidenceCeiling"],"evidence",32); req(ev in {"SOURCE_ONLY","TECHNICAL"},"evidence ceiling")
    ex=[expectation(x,i) for i,x in enumerate(as_arr(p["exactSubjects"],"exactSubjects"))]; req(1<=len(ex)<=32,"subject count")
    exkeys=[kt(x["key"]) for x in ex]; req(len(exkeys)==len(set(exkeys)),"duplicate subject")
    ads=[admission(x,i) for i,x in enumerate(as_arr(e["subjectAdmission"],"subjectAdmission"))]; req(len(ads)==len(ex),"admission count")
    by={kt(x["key"]):x for x in ads}; req(len(by)==len(ads) and set(by)==set(exkeys),"admission identity")
    for x in ex:
        a=by[kt(x["key"])]
        if x["expectedVersion"] is not None: req(a["version"]==x["expectedVersion"],"version mismatch")
        if x["expectedDigest"] is not None: req(a["digest"]==x["expectedDigest"],"digest mismatch")
    out={"schema":e["schema"],"capabilityId":e["capabilityId"],"proposal":{"requestId":rid,"caller":caller,"intent":intent,"routeClass":p["routeClass"],"destinationOwner":dest,"evidenceCeiling":ev,"exactSubjects":sorted(ex,key=lambda x:kt(x["key"]))},"subjectAdmission":sorted(ads,key=lambda x:kt(x["key"])),"mode":e["mode"]}
    scan(out); return out

def semantic_fingerprint(n: dict[str,Any]) -> str:
    payload={"capabilityId":n["capabilityId"],**{k:n["proposal"][k] for k in ("caller","intent","routeClass","destinationOwner","evidenceCeiling","exactSubjects")},"subjectAdmission":n["subjectAdmission"],"mode":n["mode"]}
    raw=json.dumps(payload,sort_keys=True,separators=(",",":")).encode(); return "sha256:"+hashlib.sha256(raw).hexdigest()

def route_envelope(e: dict[str,Any], b: dict[str,Any], ledger: MutableMapping[str,str]) -> dict[str,Any]:
    _validate_binding(b); n=_validate_envelope(e,b); rid=n["proposal"]["requestId"]; fp=semantic_fingerprint(n); old=ledger.get(rid)
    if old is not None and old!=fp: return make_result(n,b,"DENIED","REQUEST_ID_SEMANTIC_CONFLICT",fp,False)
    replay=old==fp; ledger[rid]=fp; return make_result(n,b,"ACKNOWLEDGED","ROUTE_PROPOSAL_ACKNOWLEDGED",fp,replay)

def make_result(n,b,state,reason,fp,replay):
    req(REASON.fullmatch(reason) is not None,"reason"); p=n["proposal"]; ack=state=="ACKNOWLEDGED"
    r={"schema":"bettor.capability-workspace-result/v1","requestId":p["requestId"],"state":state,"reasonCode":reason,"maximumClaim":"ROUTE_PROPOSAL_ADMISSION_ONLY","semanticFingerprint":fp,"idempotentReplay":replay,
      "kawReceipt":{"requestId":p["requestId"],"routeClass":p["routeClass"],"destinationOwner":p["destinationOwner"],"evidenceCeiling":p["evidenceCeiling"]} if ack else None,
      "binding":{"kawRepository":b["upstream"]["repository"],"kawCommit":b["upstream"]["commit"],"kawTree":b["upstream"]["tree"],"kawRouterBlob":b["upstream"]["routerBlob"],"bettorRepository":b["bettor"]["repository"],"bettorBaselineCommit":b["bettor"]["commit"],"workerManifestBlob":b["bettor"]["workerManifestBlob"],"workerReceiptSchemaBlob":b["bettor"]["workerReceiptSchemaBlob"]},
      "execution":{"state":"NOT_EXERCISED","workerReceiptReference":None,"gateReceiptReference":None,"loopxStateWritten":False},
      "authority":{"kawWroteLoopxState":False,"consumerSubmittedGateVerdict":False,"consumerGrantedExecutionAuthority":False,"consumerPerformedHumanAdmit":False,"consumerPromotedRelease":False,"consumerClaimedDomainTruth":False},
      "cleanup":{"state":"PASS","residue":[]},"evidenceBoundary":{"consumerContract":"PASS","routeAcknowledgement":"PASS" if ack else "FAIL","workerRuntime":"NOT_EXERCISED","gateRuntime":"NOT_EXERCISED","liveBettorHandoff":"NOT_EXERCISED","domainTruth":"NOT_CLAIMED","userOutcome":"ABSENT","mergeRelease":"NOT_AUTHORIZED"}}
    scan(r); return r

def load_json(path:Path)->dict[str,Any]:
    try: return as_obj(json.loads(path.read_text()),str(path))
    except (OSError,json.JSONDecodeError) as x: raise ContractError(f"cannot load {path}") from x

def load_ledger(path:Path)->dict[str,str]:
    if not path.exists(): return {}
    root=load_json(path); exact(root,{"schema","claims"},"ledger"); req(root["schema"]=="bettor.capability-workspace-ledger/v1","ledger schema")
    claims=as_obj(root["claims"],"claims")
    for rid,fp in claims.items(): req(LOGICAL.fullmatch(rid) is not None and isinstance(fp,str) and re.fullmatch(r"sha256:[0-9a-f]{64}",fp),"ledger entry")
    return dict(claims)

def save_ledger(path:Path,claims:dict[str,str])->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps({"schema":"bettor.capability-workspace-ledger/v1","claims":dict(sorted(claims.items()))},indent=2,sort_keys=True)+"\n")

def main(argv=None)->int:
    p=argparse.ArgumentParser(); p.add_argument("route",nargs="?"); p.add_argument("--input",required=True,type=Path); p.add_argument("--binding",required=True,type=Path); p.add_argument("--ledger",required=True,type=Path); p.add_argument("--output",required=True,type=Path); a=p.parse_args(argv)
    try:
        ledger=load_ledger(a.ledger); result=route_envelope(load_json(a.input),load_json(a.binding),ledger); save_ledger(a.ledger,ledger); a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    except ContractError as x: print(f"capability workspace consumer: FAIL: {x}",file=sys.stderr); return 2
    print(f"capability workspace consumer: {result['state']} {result['reasonCode']}"); return 0 if result["state"]=="ACKNOWLEDGED" else 2

if __name__=="__main__": raise SystemExit(main())
