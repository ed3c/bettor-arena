#!/usr/bin/env python3
"""Semantic validators for LoopX Contract v1."""
from __future__ import annotations

import copy
from typing import Any

from contract_common import *

def state(x:Any,name:str,sub:dict[str,Any],gates:dict[str,dict[str,Any]])->dict[str,Any]:
    v=obj(x,STATE,name)
    if v["schema_version"]!="loopx/task-state/v1": raise Violation(f"{name}.schema_version drifted")
    same(subject(v["subject"],name+".subject"),sub,name)
    if type(v["state_revision"]) is not int or v["state_revision"]<0: raise Violation(f"{name}.state_revision invalid")
    sha(v["ledger_head_digest"],name+".ledger_head_digest",True)
    if v["lifecycle"] not in {"DRAFT","READY","ACTIVE","HITL_PENDING","COMPLETED","COMPLETED_WITH_EXCEPTION","FAILED","CANCELLED"}: raise Violation(f"{name}.lifecycle invalid")
    ob=obj(v["objective"],{"statement","scope","non_goals","acceptance"},name+".objective"); text(ob["statement"],name+".objective.statement")
    for k,minn in (("scope",1),("non_goals",0),("acceptance",1)):
        if not isinstance(ob[k],list) or len(ob[k])<minn: raise Violation(f"{name}.objective.{k} invalid")
        for z in ob[k]:text(z,f"{name}.objective.{k}")
    if not isinstance(v["human_decision_refs"],list) or len(v["human_decision_refs"])!=len(set(v["human_decision_refs"])): raise Violation(f"{name}.human refs invalid")
    decisions={sid(z,name+".human_decision_refs") for z in v["human_decision_refs"]}
    if not isinstance(v["evidence"],list): raise Violation(f"{name}.evidence invalid")
    evidence={}
    for i,a in enumerate(v["evidence"]):
        a=artifact(a,f"{name}.evidence[{i}]")
        if a["artifact_id"] in evidence:raise Violation(f"{name}.evidence duplicate")
        evidence[a["artifact_id"]]=a
    if not isinstance(v["todos"],list) or not v["todos"]: raise Violation(f"{name}.todos invalid")
    todos={}
    for i,t in enumerate(v["todos"]):
        t=obj(t,TODO,f"{name}.todos[{i}]"); tid=sid(t["todo_id"],f"{name}.todos[{i}].todo_id"); text(t["title"],f"{name}.todos[{i}].title",256)
        if tid in todos or t["status"] not in {"PENDING","READY","DISPATCHED","RUNNING","RETRY","HITL_PENDING","COMPLETED","COMPLETED_WITH_EXCEPTION","FAILED","CANCELLED"}: raise Violation(f"{name}.todos[{i}] invalid id/status")
        for k in ("depends_on","gate_ids","evidence_refs"):
            if not isinstance(t[k],list) or len(t[k])!=len(set(t[k])): raise Violation(f"{name}.todos[{i}].{k} invalid")
            for z in t[k]:sid(z,f"{name}.todos[{i}].{k}")
        if set(t["gate_ids"])-set(gates) or any(z not in evidence for z in t["evidence_refs"]): raise Violation(f"{name}.todos[{i}] unknown gate/evidence")
        if not isinstance(t["gate_results"],list):raise Violation(f"{name}.todos[{i}].gate_results invalid")
        results={}
        for j,r in enumerate(t["gate_results"]):
            r=gate_result(r,f"{name}.todos[{i}].gate_results[{j}]",gates)
            if r["gate_id"] in results:raise Violation(f"{name}.todos[{i}] duplicate gate result")
            results[r["gate_id"]]=r
        if type(t["attempts"]) is not int or t["attempts"]<0: raise Violation(f"{name}.todos[{i}].attempts invalid")
        for k in ("last_failure_ref","exception_ref"):
            if t[k] is not None:sid(t[k],f"{name}.todos[{i}].{k}")
        if t["last_failure_ref"] is not None and t["last_failure_ref"] not in evidence:raise Violation(f"{name}.todos[{i}] missing failure evidence")
        if t["exception_ref"] is not None and t["exception_ref"] not in decisions:raise Violation(f"{name}.todos[{i}] missing Human decision")
        if t["status"]=="COMPLETED":
            if t["exception_ref"] is not None or not t["evidence_refs"]:raise Violation(f"{name}.todos[{i}] invalid ordinary completion")
            for gid in t["gate_ids"]:
                if gates[gid]["severity"]=="CRITICAL" and (gid not in results or results[gid]["verdict"]!="PASS"):raise Violation(f"{name}.todos[{i}] completed without critical gate PASS: {gid}")
        if t["status"]=="COMPLETED_WITH_EXCEPTION" and t["exception_ref"] is None:raise Violation(f"{name}.todos[{i}] exception missing")
        todos[tid]=t
    visiting=set(); done=set()
    def visit(n:str)->None:
        if n in done:return
        if n in visiting:raise Violation(f"todo dependency cycle: {n}")
        visiting.add(n)
        for d in todos[n]["depends_on"]:
            if d not in todos or d==n:raise Violation(f"todo {n} invalid dependency {d}")
            visit(d)
        visiting.remove(n);done.add(n)
    for n in todos:visit(n)
    cur=v["current_todo_id"]
    if cur is not None and (sid(cur,name+".current_todo_id") not in todos):raise Violation(f"{name}.current todo absent")
    if v["lifecycle"] in {"COMPLETED","COMPLETED_WITH_EXCEPTION","FAILED","CANCELLED"} and cur is not None:raise Violation(f"{name} terminal current todo")
    if v["lifecycle"] in {"ACTIVE","HITL_PENDING"} and (cur is None or todos[cur]["status"] not in {"READY","DISPATCHED","RUNNING","RETRY","HITL_PENDING"}):raise Violation(f"{name} active current todo invalid")
    if v["lifecycle"]=="COMPLETED" and any(t["status"]!="COMPLETED" for t in todos.values()):raise Violation(f"{name} incomplete completed task")
    q=obj(v["quota"],{"limits","used","state"},name+".quota"); lim=obj(q["limits"],{"max_attempts","max_worker_seconds","max_output_bytes","max_tokens","max_cost_microunits"},name+".quota.limits"); used=obj(q["used"],{"attempts","worker_seconds","output_bytes","tokens","cost_microunits"},name+".quota.used")
    exhausted=False
    for u,l in (("attempts","max_attempts"),("worker_seconds","max_worker_seconds"),("output_bytes","max_output_bytes"),("tokens","max_tokens"),("cost_microunits","max_cost_microunits")):
        if type(used[u]) is not int or used[u]<0 or (lim[l] is not None and (type(lim[l]) is not int or lim[l]<1)):raise Violation(f"{name}.quota {u}/{l} invalid")
        exhausted|=lim[l] is not None and used[u]>=lim[l]
    if q["state"]!=("EXHAUSTED" if exhausted else "AVAILABLE") or (exhausted and v["lifecycle"]=="ACTIVE"):raise Violation(f"{name}.quota.state inconsistent")
    forbidden(v,PRIVATE,name);return v

def command(x:Any,name:str,sub:dict[str,Any],revision:int)->dict[str,Any]:
    v=obj(x,COMMAND,name)
    if v["schema_version"]!="loopx/command/v1":raise Violation(f"{name}.schema_version drifted")
    sid(v["command_id"],name+".command_id");same(subject(v["subject"],name+".subject"),sub,name)
    if type(v["expected_state_revision"]) is not int or not 0<=v["expected_state_revision"]<=revision:raise Violation(f"{name}.expected revision invalid")
    if v["kind"] not in {"INITIALIZE_TASK","DISPATCH_TODO","REQUEST_RETRY","REQUEST_HITL","CANCEL_TASK","SUBMIT_HUMAN_DECISION"}:raise Violation(f"{name}.kind unsupported")
    a=obj(v["actor"],{"actor_id","class"},name+".actor");sid(a["actor_id"],name+".actor.id")
    if a["class"] not in {"STRATEGY","AGENT","HUMAN_OPERATOR"}:raise Violation(f"{name}.actor class invalid")
    p=obj(v["payload"],CPAY,name+".payload")
    if p["todo_id"] is not None:sid(p["todo_id"],name+".payload.todo_id")
    for k in ("request_ref","reason_ref"):
        if p[k] is not None:artifact(p[k],name+".payload."+k)
    if p["human_decision"] is not None:human(p["human_decision"],name+".payload.human_decision")
    if v["kind"]=="SUBMIT_HUMAN_DECISION":
        if a["class"]!="HUMAN_OPERATOR" or p["human_decision"] is None:raise Violation(f"{name} Human decision authority invalid")
    elif p["human_decision"] is not None:raise Violation(f"{name} unexpected Human decision")
    if v["kind"]=="DISPATCH_TODO" and (p["todo_id"] is None or p["request_ref"] is None):raise Violation(f"{name} dispatch lacks todo/request")
    forbidden(v,CMD_FORBID,name);return v

def gate_obs(x:Any,name:str,gates:dict[str,dict[str,Any]])->dict[str,Any]:
    v=obj(x,{"gate_id","verdict","observed_exit_code","evaluator_digest","artifact_refs"},name);gid=sid(v["gate_id"],name+".gate_id")
    if gid not in gates or v["verdict"] not in {"PASS","FAIL","NOT_RUN","SKIPPED_BY_POLICY"} or (v["observed_exit_code"] is not None and type(v["observed_exit_code"]) is not int):raise Violation(f"{name} invalid gate observation")
    sha(v["evaluator_digest"],name+".evaluator_digest")
    if not isinstance(v["artifact_refs"],list) or not v["artifact_refs"]:raise Violation(f"{name}.artifact_refs invalid")
    for i,a in enumerate(v["artifact_refs"]):artifact(a,f"{name}.artifact_refs[{i}]")
    if v["verdict"]=="PASS" and v["observed_exit_code"]!=0:raise Violation(f"{name} PASS without exit zero")
    if v["verdict"]=="FAIL" and v["observed_exit_code"] in {None,0}:raise Violation(f"{name} FAIL without nonzero exit")
    return v

def event(x:Any,name:str,sub:dict[str,Any],gates:dict[str,dict[str,Any]],commands:set[str],prev:str|None,seq:int)->dict[str,Any]:
    v=obj(x,EVENT,name)
    if v["schema_version"]!="loopx/event/v1":raise Violation(f"{name}.schema_version drifted")
    sid(v["event_id"],name+".event_id");same(subject(v["subject"],name+".subject"),sub,name)
    if v["sequence"]!=seq or v["previous_event_digest"]!=prev:raise Violation(f"{name} sequence/hash-chain drift")
    sha(v["event_digest"],name+".event_digest")
    raw=copy.deepcopy(v);raw.pop("event_digest")
    if v["event_digest"]!=digest(raw):raise Violation(f"{name}.event_digest mismatch")
    try:datetime.strptime(text(v["occurred_at"],name+".occurred_at",32),"%Y-%m-%dT%H:%M:%SZ")
    except ValueError as e:raise Violation(f"{name}.occurred_at invalid") from e
    typ=v["type"]
    if typ not in {"TASK_INITIALIZED","COMMAND_ACCEPTED","COMMAND_REJECTED","WORKER_OBSERVED","GATE_OBSERVED","QUOTA_DEBITED","HITL_REQUESTED","HUMAN_DECISION_RECORDED","STATE_TRANSITION_COMMITTED"}:raise Violation(f"{name}.type unsupported")
    a=obj(v["actor"],{"actor_id","class","authority"},name+".actor");sid(a["actor_id"],name+".actor.id")
    if a["class"] not in {"LOOPX","STRATEGY","AGENT","WORKER","GATE_ENGINE","HUMAN","SYSTEM"} or a["authority"] not in {"PROPOSAL","OBSERVATION","DECISION","STATE_COMMIT"}:raise Violation(f"{name}.actor invalid")
    p=obj(v["payload"],EPAY,name+".payload")
    if p["todo_id"] is not None:sid(p["todo_id"],name+".payload.todo_id")
    if p["command_id"] is not None and (sid(p["command_id"],name+".payload.command_id") not in commands):raise Violation(f"{name} unknown command")
    for k in ("request_ref","worker_result_ref"):
        if p[k] is not None:artifact(p[k],name+".payload."+k)
    if p["gate_observation"] is not None:gate_obs(p["gate_observation"],name+".payload.gate",gates)
    if p["human_decision"] is not None:human(p["human_decision"],name+".payload.human")
    if p["quota_delta"] is not None:
        q=obj(p["quota_delta"],{"attempts","worker_seconds","output_bytes","tokens","cost_microunits"},name+".payload.quota")
        if any(type(z) is not int or z<0 for z in q.values()):raise Violation(f"{name}.quota delta invalid")
    if p["transition"] is not None:
        tr=obj(p["transition"],{"from","to","reason_event_ids"},name+".payload.transition")
        if (tr["from"],tr["to"]) not in ALLOWED_TRANSITIONS or not isinstance(tr["reason_event_ids"],list) or not tr["reason_event_ids"]:raise Violation(f"{name}.transition invalid")
        for z in tr["reason_event_ids"]:sid(z,name+".transition.reason")
    expected={
        "TASK_INITIALIZED":("LOOPX","STATE_COMMIT",{"request_ref"}),
        "COMMAND_ACCEPTED":("LOOPX","STATE_COMMIT",{"command_id"}),
        "COMMAND_REJECTED":("LOOPX","STATE_COMMIT",{"command_id"}),
        "WORKER_OBSERVED":("WORKER","OBSERVATION",{"worker_result_ref"}),
        "GATE_OBSERVED":("GATE_ENGINE","OBSERVATION",{"gate_observation"}),
        "QUOTA_DEBITED":("LOOPX","STATE_COMMIT",{"quota_delta"}),
        "HITL_REQUESTED":("LOOPX","STATE_COMMIT",{"transition"}),
        "HUMAN_DECISION_RECORDED":("HUMAN","DECISION",{"human_decision"}),
        "STATE_TRANSITION_COMMITTED":("LOOPX","STATE_COMMIT",{"transition"}),
    }[typ]
    if (a["class"],a["authority"])!=expected[:2]:raise Violation(f"{name} actor lacks authority for {typ}")
    populated={k for k,z in p.items() if z is not None}
    allowed=expected[2]|({"todo_id","command_id"} if typ in {"COMMAND_ACCEPTED","COMMAND_REJECTED","WORKER_OBSERVED"} else {"todo_id"})
    if not expected[2]<=populated or populated-allowed:raise Violation(f"{name} payload authority drift: {sorted(populated)}")
    forbidden(v,PRIVATE,name);return v

def snapshot(x:Any,name:str,sub:dict[str,Any],task:dict[str,Any],events:list[dict[str,Any]])->dict[str,Any]:
    v=obj(x,SNAP,name)
    if v["schema_version"]!="loopx/snapshot/v1":raise Violation(f"{name}.schema_version drifted")
    same(subject(v["subject"],name+".subject"),sub,name);r=obj(v["reducer"],{"id","version","digest"},name+".reducer");sid(r["id"],name+".reducer.id");text(r["version"],name+".reducer.version",64);sha(r["digest"],name+".reducer.digest")
    if v["state_revision"]!=task["state_revision"] or v["canonical_authority"]!="LOOPX_LEDGER_REDUCER" or v["rebuildable"] is not True or v["state"]!=task:raise Violation(f"{name} is not reducer-owned/rebuildable")
    led=obj(v["ledger"],{"event_count","last_sequence","head_digest"},name+".ledger")
    if led["event_count"]!=len(events) or led["last_sequence"]!=(len(events)-1) or led["head_digest"]!=(events[-1]["event_digest"] if events else None):raise Violation(f"{name}.ledger mismatch")
    if v["state_digest"]!=digest(task):raise Violation(f"{name}.state_digest mismatch")
    raw=copy.deepcopy(v);raw.pop("content_digest")
    if v["content_digest"]!=digest(raw):raise Violation(f"{name}.content_digest mismatch")
    forbidden(v,PRIVATE|{"graph_checkpoint"},name);return v

def bundle(x:Any)->dict[str,Any]:
    v=obj(x,BUNDLE,"bundle")
    if v["schema_version"]!="loopx/fixture-bundle/v1" or v["fixture"] is not True or v["evidence_scope"]!="FIXTURE_ONLY":raise Violation("bundle fixture/evidence scope drifted")
    sub=subject(v["subject"],"bundle.subject")
    if not isinstance(v["gate_definitions"],list) or not v["gate_definitions"]:raise Violation("bundle.gate_definitions empty")
    gates={}
    for i,g in enumerate(v["gate_definitions"]):
        g=gate(g,f"bundle.gate_definitions[{i}]")
        if g["gate_id"] in gates:raise Violation("duplicate gate id")
        gates[g["gate_id"]]=g
    task=state(v["task_state"],"bundle.task_state",sub,gates)
    if not isinstance(v["commands"],list):raise Violation("bundle.commands invalid")
    commands=set()
    for i,c in enumerate(v["commands"]):
        c=command(c,f"bundle.commands[{i}]",sub,task["state_revision"])
        if c["command_id"] in commands:raise Violation("duplicate command id")
        commands.add(c["command_id"])
    if not isinstance(v["events"],list) or not v["events"]:raise Violation("bundle.events empty")
    prev=None; events=[]; ids=set()
    for i,e in enumerate(v["events"]):
        e=event(e,f"bundle.events[{i}]",sub,gates,commands,prev,i)
        if e["event_id"] in ids:raise Violation("duplicate event id")
        ids.add(e["event_id"]);prev=e["event_digest"];events.append(e)
    snapshot(v["snapshot"],"bundle.snapshot",sub,task,events)
    if task["ledger_head_digest"]!=events[-1]["event_digest"]:raise Violation("task ledger head mismatch")
    forbidden(v,PRIVATE,"bundle");return v
