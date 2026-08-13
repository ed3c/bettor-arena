"""Exact paired provider evaluation cases."""
from __future__ import annotations
from pathlib import Path
from typing import Any
from knowledge_provider_eval_common import EVALS, FAMILIES, IDENT, common_safety, digest, load, require, strict_keys, validate_subject

def validate_case(v:Any, people:dict[str,dict], *, subject:dict, fixture_only:bool)->None:
    strict_keys(v,required={"schema_version","id","family","capability","subject","query","query_digest","participants","oracle","hard_gates","budgets","eligible_recommendations","fixture_subject"},optional={"memory_policy"},label="eval case")
    cid,fam=v["id"],v["family"]; require(v["schema_version"]=="knowledge-provider-eval-case/v1","case schema")
    require(isinstance(cid,str) and IDENT.fullmatch(cid) and fam in FAMILIES,f"{cid}: identity")
    validate_subject(v["subject"],f"{cid}.subject"); require(v["subject"]==subject,f"{cid}: subject drift")
    require(isinstance(v["query"],dict) and digest(v["query"])==v["query_digest"],f"{cid}: query digest")
    pids=v["participants"]; require(isinstance(pids,list) and len(pids)==2 and len(set(pids))==2,f"{cid}: participants")
    kinds=[people.get(x,{}).get("kind") for x in pids]; require(sorted(kinds)==["control","provider"],f"{cid}: provider/control pair")
    require(all(x in people and fam in people[x]["families"] for x in pids),f"{cid}: participant family")
    oracle=v["oracle"]; strict_keys(oracle,required={"relevant_ids","must_remain_unknown"},label=f"{cid}.oracle")
    rel,unk=oracle["relevant_ids"],oracle["must_remain_unknown"]; require(rel and len(rel)==len(set(rel)) and len(unk)==len(set(unk)) and not(set(rel)&set(unk)),f"{cid}: oracle")
    gates=v["hard_gates"]; require(all(gates.get(k) is True for k in ["source_readback_required","fresh_index_required","candidate_only","no_authority_escalation","cleanup_required"]),f"{cid}: hard gates")
    require(all(isinstance(gates.get(k),(int,float)) and 0<=gates[k]<=1 for k in ["min_verified_precision","min_verified_recall"]),f"{cid}: thresholds")
    require(all(isinstance(v["budgets"].get(k),int) and v["budgets"][k]>0 for k in ["max_results","max_context_bytes","max_latency_ms","max_tool_calls"]),f"{cid}: budgets")
    require(v["fixture_subject"] is fixture_only,f"{cid}: fixture scope")
    if fam=="memory": require(all(v.get("memory_policy",{}).get(k) is True for k in ["preserve_conflict","current_authority_wins","durable_write_requires_human_admit"]),f"{cid}: memory policy")
    else: require("memory_policy" not in v,f"{cid}: unexpected memory policy")
    common_safety(v)

def load_cases(root:Path, people:dict[str,dict], *, subject:dict, fixture_only:bool)->dict[str,dict]:
    out={}
    for p in sorted((root/EVALS/"cases").glob("*.json")):
        v=load(p); validate_case(v,people,subject=subject,fixture_only=fixture_only); require(v["id"] not in out,f"duplicate case: {v['id']}"); out[v["id"]]=v
    require({v["family"] for v in out.values()}==FAMILIES and len(out)==4,"case family coverage"); return out
