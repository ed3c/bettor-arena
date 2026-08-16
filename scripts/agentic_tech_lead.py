#!/usr/bin/env python3
"""Fail-closed adapter from bettor-arena to projected shared Tech Lead contracts."""
from __future__ import annotations
import argparse, hashlib, json, os, re, subprocess, sys
from pathlib import Path
from typing import Any

OK, FAIL, INVALID, MECHANISM = 0, 2, 64, 70
SCHEMA = "bettor-arena/agentic-tech-lead-binding/v1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")

class Bad(ValueError): pass
class Broken(RuntimeError): pass

def canon(value: Any) -> str: return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
def sha(path: Path) -> str: return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
def load(path: Path) -> Any:
    try: return json.loads(path.read_text())
    except FileNotFoundError as exc: raise Bad(f"ABSENT: {path}") from exc
    except json.JSONDecodeError as exc: raise Bad(f"UNREADABLE_JSON: {path}: {exc}") from exc
    except OSError as exc: raise Broken(str(exc)) from exc

def validate(config: Any) -> list[dict[str,str]]:
    if not isinstance(config, dict): raise Bad("config must be an object")
    if config.get("schema") != SCHEMA: raise Bad(f"schema must be {SCHEMA}")
    failures: list[dict[str,str]]=[]
    def fail(code:str, detail:str)->None: failures.append({"code":code,"detail":detail})
    subject=config.get("subject",{})
    for key in ("base_commit","base_tree"):
        if not isinstance(subject.get(key),str) or not SHA40.fullmatch(subject[key]): fail("MUTABLE_SUBJECT",key)
    shared=config.get("shared_contracts",{})
    if shared.get("root_environment") != "SKILLS_SHARED_ROOT": fail("SHARED_ROOT_ENV_INVALID","root_environment")
    expected={"tech_lead_compiler":"skills/git-town-stacked-pr-worker/scripts/plan_tech_lead_stack.py","blindspot_checker":"skills/repo-agent-native/scripts/blindspot_contract.py"}
    for key,path in expected.items():
        if shared.get(key)!=path: fail("SHARED_CONTRACT_PATH_INVALID",key)
    orch=config.get("orchestration",{})
    if orch.get("mode")!="PLAN_AND_VERIFY_ONLY": fail("EXECUTION_MODE_TOO_BROAD","mode")
    if not isinstance(orch.get("max_parallel_workers"),int) or isinstance(orch.get("max_parallel_workers"),bool) or orch["max_parallel_workers"]<1: fail("MAX_PARALLEL_INVALID","max_parallel_workers")
    for key in ("require_path_disjoint_siblings","require_explicit_child_contract","require_convergence_after_dependencies","require_negative_control_per_task","require_source_readback_per_blindspot_query"):
        if orch.get(key) is not True: fail("ORCHESTRATION_GATE_DISABLED",key)
    branch=config.get("branch_policy",{})
    if branch.get("tool")!="git-town": fail("BRANCH_TOOL_INVALID","tool")
    if branch.get("publication")!="DRAFT_PR_ONLY": fail("PUBLICATION_BOUNDARY_INVALID","publication")
    if branch.get("merge")!="HUMAN_OWNED" or branch.get("semantic_conflict_resolution")!="HUMAN_OWNED": fail("HUMAN_BOUNDARY_INVALID","branch_policy")
    forgejo=config.get("forgejo",{})
    if forgejo.get("runtime_state") not in {"NOT_CONFIGURED","NOT_EXERCISED"}: fail("FORGEJO_RUNTIME_OVERCLAIM","runtime_state")
    effects=config.get("effects",{})
    if not isinstance(effects,dict) or any(value is not False for value in effects.values()): fail("EFFECT_OVERCLAIM","effects")
    return sorted(failures,key=canon)

def resolve_root(config: dict[str,Any], override: Path|None) -> Path:
    if override is not None: return override.resolve()
    env=config["shared_contracts"]["root_environment"]
    value=os.environ.get(env)
    if not value: raise Bad(f"SHARED_ROOT_ABSENT: set {env} or pass --shared-root")
    return Path(value).resolve()

def contract_path(root:Path, config:dict[str,Any], key:str)->Path:
    candidate=(root/config["shared_contracts"][key]).resolve()
    try: candidate.relative_to(root)
    except ValueError as exc: raise Bad(f"SHARED_CONTRACT_ESCAPES_ROOT: {key}") from exc
    if not candidate.is_file(): raise Bad(f"SHARED_CONTRACT_ABSENT: {candidate}")
    return candidate

def invoke(args: argparse.Namespace, config:dict[str,Any])->int:
    root=resolve_root(config,args.shared_root)
    key="blindspot_checker" if args.action=="verify-blindspot" else "tech_lead_compiler"
    tool=contract_path(root,config,key)
    if args.action=="verify-plan": command=[sys.executable,str(tool),"verify","--plan",str(args.plan)]
    elif args.action=="compile-plan": command=[sys.executable,str(tool),"compile","--plan",str(args.plan),"--output",str(args.output)]
    else: command=[sys.executable,str(tool),"verify","--db",str(args.db)]
    completed=subprocess.run(command,check=False)
    receipt={"schema":"bettor-arena/agentic-tech-lead-adapter-receipt/v1","action":args.action,"shared_tool":str(tool.relative_to(root)),"shared_tool_sha256":sha(tool),"return_code":completed.returncode,"effects":{"agents_spawned":False,"branches_created":False,"worktrees_created":False,"providers_invoked":False,"forgejo_contacted":False,"merge_or_publish":False}}
    if args.receipt:
        args.receipt.parent.mkdir(parents=True,exist_ok=True); args.receipt.write_text(json.dumps(receipt,indent=2)+"\n")
    print(canon(receipt),file=sys.stderr if completed.returncode else sys.stdout)
    return completed.returncode

def parser()->argparse.ArgumentParser:
    p=argparse.ArgumentParser(); p.add_argument("--config",type=Path,required=True); p.add_argument("--shared-root",type=Path); p.add_argument("--receipt",type=Path)
    sub=p.add_subparsers(dest="action",required=True)
    sub.add_parser("verify-config")
    v=sub.add_parser("verify-plan"); v.add_argument("--plan",type=Path,required=True)
    c=sub.add_parser("compile-plan"); c.add_argument("--plan",type=Path,required=True); c.add_argument("--output",type=Path,required=True)
    b=sub.add_parser("verify-blindspot"); b.add_argument("--db",type=Path,required=True)
    return p

def main()->int:
    args=parser().parse_args()
    try:
        config=load(args.config); failures=validate(config)
        if failures:
            print(canon({"state":"FAIL","failures":failures}),file=sys.stderr); return FAIL
        if args.action=="verify-config":
            print(canon({"state":"PASS","runtime_state":"NOT_EXERCISED","effects":config["effects"]})); return OK
        return invoke(args,config)
    except Bad as exc: print(f"INVALID: {exc}",file=sys.stderr); return INVALID
    except (Broken,OSError) as exc: print(f"MECHANISM_ERROR: {exc}",file=sys.stderr); return MECHANISM
if __name__=="__main__": raise SystemExit(main())
