"""Complete paired evaluation report with no automatic admission."""
from __future__ import annotations
from pathlib import Path
from knowledge_provider_eval_cases import load_cases
from knowledge_provider_eval_common import digest, load, require
from knowledge_provider_eval_contracts import load_contract
from knowledge_provider_eval_metrics import score
from knowledge_provider_eval_packet import validate_packet
from knowledge_provider_eval_registry import load_participants, provider_digests

def evaluate(root:Path,path:Path)->dict:
    config,subject,schemas=load_contract(root); people=load_participants(root,provider_digests(root)); suite=load_cases(root,people,subject=subject,fixture_only=config["fixture_only"])
    values=load(path); require(isinstance(values,list) and values,"observations array")
    ids=set(); pairs=set(); checked=[]; flags=set()
    for v in values:
        require(isinstance(v,dict),"observation must be an object"); oid=v.get("observation_id"); pair=(v.get("case_id"),v.get("participant_id"))
        require(oid not in ids,f"duplicate observation: {oid}"); require(pair not in pairs,f"duplicate pair: {pair}"); ids.add(oid); pairs.add(pair)
        checked.append(score(v,validate_packet(v,suite,people))); flags.add(v["fixture"])
    expected={(cid,pid) for cid,c in suite.items() for pid in c["participants"]}; missing=sorted(expected-pairs); extra=sorted(pairs-expected)
    if config["require_complete_pair_coverage"]: require(not missing and not extra,f"observation coverage mismatch: missing={missing}, unexpected={extra}")
    if not config["allow_mixed_fixture_scope"]: require(len(flags)==1,"fixture scope drift")
    fixture=flags=={True}; require(not config["fixture_only"] or fixture,"non-fixture observation forbidden by config")
    status="PASS" if all(x["hard_gates_passed"] for x in checked) and not missing and not extra else "FAIL"
    pairs_obj=lambda xs:[{"case_id":c,"participant_id":p} for c,p in xs]
    return {"schema_version":"knowledge-provider-eval-report/v1","contract":{"config_digest":digest(config),"subject":subject,"schema_digests":schemas},"suite":{"case_count":len(suite),"participant_count":len(people),"observation_count":len(checked),"families":["graph","memory","semantic","symbol"]},"pair_coverage":{"expected":len(expected),"observed":len(pairs),"missing":pairs_obj(missing),"unexpected":pairs_obj(extra),"complete":not missing and not extra},"evidence_scope":"FIXTURE_ONLY" if fixture else "SUBJECT_BOUND_OBSERVATIONS","status":status,"observations":sorted(checked,key=lambda x:(x["family"],x["case_id"],x["participant_id"])),"admission":{"automatic_admission":False,"human_admit_required":True,"winner":None,"reason":"Fixture observations test the evaluator only." if fixture else "Recommendations are candidates; no provider is admitted automatically."}}
