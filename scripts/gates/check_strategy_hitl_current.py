#!/usr/bin/env python3
"""Validate the current-main LoopX Strategy/HITL mechanism on one exact subject.

This Stage-2 gate re-executes the admitted module's deterministic contracts,
positive pipeline, controls, and mutation matrix. It also proves the authority
ceiling: the planner proposes, checkpoints are projections, Human decisions are
subject-bound, and only the LoopX reducer may commit canonical task state.

It does not call LangGraph, a model, a provider, a signer service, a UI, or a
network endpoint. Such live surfaces remain NOT_IMPLEMENTED or NOT_EXERCISED.

Exit codes:
  0  checked subject PASS
  2  checked invariant or command FAIL
 64  invalid invocation or unreadable repository state
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

OK, BAD, USAGE = 0, 2, 64

MODULE_ID = "loopx-strategy-hitl"
MODULE_PATH = Path(".arena/modules/loopx-strategy-hitl/module.json")
ROOT_PATH = Path("loop_wiki/loopx-strategy-hitl")
CONTRACT_MANIFEST = ROOT_PATH / "contracts/manifest.json"
STAGE1_RECEIPT = Path("data/stage0-validation/stage1-receipt.json")
COMPOSITION = Path(".arena/compositions/bettor-arena.requirements.json")
LOOPCTL = Path("loopctl/contract.json")
MCP_POLICY = Path(".arena/mcp-policy.json")

STAGE1_PR = 109
STAGE1_MERGE = "b46705df5d85253efc94ca152366e4d2337488b4"
IMPLEMENTATION_ISSUE = 65
IMPLEMENTATION_PR = 106
IMPLEMENTATION_HEAD = "b89c5d8dfe3b9eb26da0bcf2372bc5e54045eb0b"
IMPLEMENTATION_MERGE = "155eda7bf50a7a1788e1bc0edb64511a155ba4dd"

EXPECTED_PROVIDES = ["loopx.strategy-proposal/v1", "loopx.hitl/v1"]
EXPECTED_REQUIRES = ["arena.proof-kernel/v1", "loopx.contracts/v1", "loopx.ledger/v1"]
EXPECTED_FORBIDDEN = ["bypass", "force_skip", "override", "skip", "waive_all"]
EXPECTED_NON_WAIVABLE = [
    "CLEANUP",
    "DESTRUCTIVE",
    "RELEASE_SIGNING",
    "SECRET",
    "SECURITY",
    "SUBJECT_INTEGRITY",
]
EXPECTED_SCHEMAS = {
    "graph-checkpoint.schema.json",
    "hitl-interrupt.schema.json",
    "human-decision.schema.json",
    "resume-envelope.schema.json",
    "strategy-proposal.schema.json",
}
SHELL_META = re.compile(r"[;&|`$<>\n\r]")


class ValidationError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def read_json(root: Path, path: Path) -> Any:
    try:
        return json.loads((root / path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"ABSENT: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"UNREADABLE_JSON: {path}: {exc}") from exc


def read_text(root: Path, path: Path) -> str:
    try:
        return (root / path).read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ValidationError(f"ABSENT: {path}") from exc
    except OSError as exc:
        raise ValidationError(f"UNREADABLE_TEXT: {path}: {exc}") from exc


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise ValidationError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result


def is_ancestor(root: Path, ancestor: str, descendant: str = "HEAD") -> bool:
    return (
        git(
            root, "merge-base", "--is-ancestor", ancestor, descendant, check=False
        ).returncode
        == 0
    )


def tree_at(root: Path, rev: str, path: Path) -> str | None:
    result = git(root, "rev-parse", f"{rev}:{path.as_posix()}", check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def validate_stage1(receipt: Any) -> dict[str, Any]:
    require(isinstance(receipt, dict), "Stage-1 receipt must be an object")
    require(
        receipt.get("schema_version") == "bettor-arena/loopx-stage1-receipt/v1",
        "Stage-1 receipt schema drift",
    )
    require(receipt.get("result") == "PASS", "Stage-1 receipt is not PASS")
    subject = receipt.get("subject")
    require(isinstance(subject, dict), "Stage-1 subject missing")
    commit = subject.get("commit")
    tree = subject.get("tree")
    require(
        isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit),
        "Stage-1 commit invalid",
    )
    require(
        isinstance(tree, str) and re.fullmatch(r"[0-9a-f]{40}", tree),
        "Stage-1 tree invalid",
    )
    require(
        subject.get("worktree_clean") is True,
        "Stage-1 receipt was not emitted from a clean worktree",
    )
    deliveries = receipt.get("deliveries")
    require(
        isinstance(deliveries, list) and len(deliveries) == 5,
        "Stage-1 delivery set drift",
    )
    require(
        all(
            item.get("suite", {}).get("state") == "PASS"
            for item in deliveries
            if isinstance(item, dict)
        ),
        "Stage-1 suite evidence is incomplete",
    )
    require(
        all(
            item.get("closure", {}).get("state") == "COMPLETE"
            for item in deliveries
            if isinstance(item, dict)
        ),
        "Stage-1 closure evidence is incomplete",
    )
    return {"commit": commit, "tree": tree, "digest": canonical_sha256(receipt)}


def validate_module(module: Any) -> dict[str, Any]:
    require(isinstance(module, dict), "module manifest must be an object")
    require(module.get("schema") == "bettor-arena/module/v1", "module schema drift")
    require(module.get("id") == MODULE_ID, "module id drift")
    require(module.get("interface_version") == "1.0.0", "module interface drift")
    require(module.get("roots") == [ROOT_PATH.as_posix()], "module root drift")
    require(module.get("provides") == EXPECTED_PROVIDES, "module provides drift")
    require(module.get("requires") == EXPECTED_REQUIRES, "module requires drift")

    policy = module.get("external_policy")
    require(isinstance(policy, dict), "external_policy missing")
    require(
        policy
        == {"exposed": False, "mutation": "none", "network": "none", "secrets": "none"},
        "module external policy widened",
    )

    loops = module.get("loops")
    require(isinstance(loops, list) and len(loops) == 1, "module loop surface drift")
    require(
        loops[0].get("external_policy") == "control-only", "module loop policy drift"
    )
    require(
        loops[0].get("public_port")
        == "python3 loop_wiki/loopx-strategy-hitl/scripts/hitl.py",
        "module public port drift",
    )

    components = module.get("components")
    require(isinstance(components, dict), "module components missing")
    for name in ("contracts", "proof", "runtime"):
        component = components.get(name)
        require(
            isinstance(component, dict) and component.get("required") is True,
            f"module component missing: {name}",
        )
        paths = component.get("paths")
        require(
            isinstance(paths, list) and paths, f"module component paths missing: {name}"
        )

    proof = module.get("proof")
    require(isinstance(proof, dict), "module proof missing")
    required_proof = {
        "verify": ["sh", "loop_wiki/loopx-strategy-hitl/tests/run-all.sh"],
        "control": [
            "python3",
            "loop_wiki/loopx-strategy-hitl/scripts/control_strategy.py",
        ],
        "selftest": [
            "python3",
            "loop_wiki/loopx-strategy-hitl/scripts/hitl.py",
            "selftest",
        ],
        "mutation": [
            "python3",
            "loop_wiki/loopx-strategy-hitl/scripts/hitl.py",
            "selftest",
        ],
    }
    require(proof == required_proof, "module proof command drift")
    for name, argv in proof.items():
        require(
            isinstance(argv, list) and all(isinstance(arg, str) for arg in argv),
            f"{name}: argv list required",
        )
        require(
            all(not SHELL_META.search(arg) for arg in argv),
            f"{name}: shell metacharacter forbidden",
        )

    return {"digest": canonical_sha256(module), "proof": proof}


def validate_contract_manifest(root: Path, manifest: Any) -> dict[str, Any]:
    require(isinstance(manifest, dict), "contract manifest must be an object")
    require(
        manifest.get("schema_version") == "loopx/strategy-hitl-contract-manifest/v1",
        "contract manifest schema drift",
    )
    require(manifest.get("interface_version") == "1.0.0", "contract interface drift")
    require(
        manifest.get("canonical_authority") == "LOOPX_LEDGER_REDUCER",
        "canonical authority drift",
    )
    require(
        manifest.get("planner_authority") == "PROPOSE_ONLY", "planner authority drift"
    )
    require(
        manifest.get("runtime_state_checked_in") is False,
        "checked-in runtime state forbidden",
    )
    require(manifest.get("runtime_state_path") == ".loopx/", "runtime state path drift")
    require(
        manifest.get("requires_capabilities")
        == ["loopx.contracts/v1", "loopx.ledger/v1"],
        "required capabilities drift",
    )
    require(
        manifest.get("forbidden_decision_fields") == EXPECTED_FORBIDDEN,
        "forbidden decision fields drift",
    )
    require(
        manifest.get("non_waivable_gate_classes") == EXPECTED_NON_WAIVABLE,
        "non-waivable gate classes drift",
    )

    schemas = manifest.get("schemas")
    require(
        isinstance(schemas, list) and len(schemas) == 5,
        "exactly five Strategy/HITL schemas required",
    )
    observed: set[str] = set()
    schema_receipts: list[dict[str, str]] = []
    for entry in schemas:
        require(isinstance(entry, dict), "schema manifest entry must be object")
        rel = entry.get("path")
        expected = entry.get("sha256")
        require(
            isinstance(rel, str) and rel in EXPECTED_SCHEMAS,
            f"unexpected schema path: {rel!r}",
        )
        require(rel not in observed, f"duplicate schema path: {rel}")
        observed.add(rel)
        require(
            isinstance(expected, str) and re.fullmatch(r"[0-9a-f]{64}", expected),
            f"invalid schema digest: {rel}",
        )
        path = root / ROOT_PATH / "contracts" / rel
        require(path.is_file(), f"schema absent: {path.relative_to(root)}")
        actual = sha256_file(path)
        require(actual == expected, f"schema digest mismatch: {rel}")
        schema_receipts.append({"path": rel, "sha256": actual})
    require(observed == EXPECTED_SCHEMAS, f"schema set drift: {sorted(observed)}")
    require(
        not (root / ".loopx").exists(),
        "repository runtime .loopx state must not be checked in",
    )
    return {"digest": canonical_sha256(manifest), "schemas": schema_receipts}


def collect_module_ids(value: Any) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        if isinstance(value.get("id"), str):
            result.add(value["id"])
        for child in value.values():
            result |= collect_module_ids(child)
    elif isinstance(value, list):
        for child in value:
            result |= collect_module_ids(child)
    return result


def validate_non_admission(
    composition: Any, loopctl_text: str, mcp_text: str
) -> dict[str, Any]:
    selected = collect_module_ids(composition)
    require(
        MODULE_ID not in selected,
        "Strategy/HITL module selected before final convergence",
    )
    for label, text in (("loopctl", loopctl_text), ("MCP policy", mcp_text)):
        lowered = text.lower()
        require(
            "loopx-strategy-hitl" not in lowered, f"{label}: module exposed prematurely"
        )
        require(
            "strategy-hitl" not in lowered,
            f"{label}: Strategy/HITL public surface exposed prematurely",
        )
    return {
        "composition_selected": False,
        "loopctl_exposed": False,
        "mcp_exposed": False,
    }


def run_command(root: Path, name: str, argv: list[str]) -> dict[str, Any]:
    result = subprocess.run(argv, cwd=root, capture_output=True, text=True, check=False)
    stdout_lines = [line for line in result.stdout.splitlines() if line.strip()]
    stderr_lines = [line for line in result.stderr.splitlines() if line.strip()]
    return {
        "name": name,
        "argv": argv,
        "exit_code": result.returncode,
        "state": "PASS" if result.returncode == 0 else "FAIL",
        "stdout_tail": stdout_lines[-12:],
        "stderr_tail": stderr_lines[-12:],
    }


def validate_commands(results: list[dict[str, Any]]) -> None:
    for result in results:
        require(
            result.get("exit_code") == 0,
            f"command failed: {result.get('name')} exit={result.get('exit_code')}",
        )


def validate_repository(
    root: Path, output: Path | None, observed_at: str
) -> dict[str, Any]:
    commit = git(root, "rev-parse", "HEAD").stdout.strip()
    tree = git(root, "rev-parse", "HEAD^{tree}").stdout.strip()
    dirty = git(root, "status", "--porcelain").stdout.strip()
    require(
        is_ancestor(root, STAGE1_MERGE),
        "Stage-1 merge commit is not an ancestor of the checked subject",
    )
    require(
        is_ancestor(root, IMPLEMENTATION_MERGE),
        "Strategy/HITL merge commit is not an ancestor of the checked subject",
    )

    stage1_value = read_json(root, STAGE1_RECEIPT)
    stage1 = validate_stage1(stage1_value)
    module_value = read_json(root, MODULE_PATH)
    module = validate_module(module_value)
    contract_value = read_json(root, CONTRACT_MANIFEST)
    contracts = validate_contract_manifest(root, contract_value)
    non_admission = validate_non_admission(
        read_json(root, COMPOSITION),
        read_text(root, LOOPCTL),
        read_text(root, MCP_POLICY),
    )

    pr_head_tree = tree_at(root, IMPLEMENTATION_HEAD, ROOT_PATH)
    current_tree = tree_at(root, "HEAD", ROOT_PATH)
    require(pr_head_tree is not None, "Strategy/HITL tree absent at PR #106 head")
    require(current_tree is not None, "Strategy/HITL tree absent on checked subject")
    content_state = (
        "IDENTICAL"
        if pr_head_tree == current_tree
        else "PRESENT_WITH_CURRENT_MAIN_CHANGES"
    )
    changed_paths = []
    if content_state != "IDENTICAL":
        changed_paths = [
            line
            for line in git(
                root,
                "diff",
                "--name-only",
                IMPLEMENTATION_HEAD,
                "HEAD",
                "--",
                ROOT_PATH.as_posix(),
            ).stdout.splitlines()
            if line
        ]

    commands = [
        run_command(
            root, "verify", ["sh", "loop_wiki/loopx-strategy-hitl/tests/run-all.sh"]
        ),
        run_command(
            root,
            "control",
            ["python3", "loop_wiki/loopx-strategy-hitl/scripts/control_strategy.py"],
        ),
        run_command(
            root,
            "selftest",
            ["python3", "loop_wiki/loopx-strategy-hitl/scripts/hitl.py", "selftest"],
        ),
        run_command(
            root,
            "probe-controls",
            ["python3", "loop_wiki/loopx-strategy-hitl/scripts/probe_controls.py"],
        ),
    ]
    validate_commands(commands)

    receipt: dict[str, Any] = {
        "schema_version": "bettor-arena/loopx-stage2-strategy-hitl-receipt/v1",
        "observed_at": observed_at,
        "subject": {
            "repository": "ed3c/bettor-arena",
            "commit": commit,
            "tree": tree,
            "worktree_clean_before_receipt": dirty == "",
        },
        "predecessor": {
            "issue": 90,
            "pr": STAGE1_PR,
            "merge_commit": STAGE1_MERGE,
            "receipt_path": STAGE1_RECEIPT.as_posix(),
            **stage1,
        },
        "implementation": {
            "issue": IMPLEMENTATION_ISSUE,
            "pr": IMPLEMENTATION_PR,
            "head": IMPLEMENTATION_HEAD,
            "merge_commit": IMPLEMENTATION_MERGE,
            "module_path": ROOT_PATH.as_posix(),
            "pr_head_tree": pr_head_tree,
            "current_tree": current_tree,
            "content_state": content_state,
            "changed_paths": changed_paths,
        },
        "module": module,
        "contracts": contracts,
        "authority": {
            "canonical_writer": "LOOPX_LEDGER_REDUCER",
            "planner": "PROPOSE_ONLY",
            "checkpoint": "PROJECTION_ONLY",
            "human_decision": "SUBJECT_BOUND_SIGNED_INPUT",
            "generic_force_skip": "FORBIDDEN",
            "private_reasoning": "FORBIDDEN",
        },
        "commands": commands,
        "non_admission": non_admission,
        "live_states": {
            "langgraph_checkpoint_backend": "NOT_EXERCISED",
            "human_signer_service": "NOT_IMPLEMENTED",
            "production_interrupt_resume": "NOT_EXERCISED",
            "web_console": "NOT_IMPLEMENTED",
            "composition_selection": "NOT_PERFORMED",
            "loopctl_mcp_exposure": "NOT_PERFORMED",
            "release_promotion": "NOT_PERFORMED",
        },
        "result": "PASS",
    }

    text = json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"WROTE {output}")
    print(
        f"PASS Stage 2 Strategy/HITL validation: {commit[:8]}, 5 schemas, {len(commands)} commands"
    )
    return receipt


def expect_failure(name: str, action: Callable[[], None], expected: str) -> str:
    try:
        action()
    except ValidationError as exc:
        require(expected in str(exc), f"{name}: wrong failure: {exc}")
        return name
    raise ValidationError(f"{name}: mutation unexpectedly passed")


def run_selftest(root: Path) -> dict[str, Any]:
    module = read_json(root, MODULE_PATH)
    manifest = read_json(root, CONTRACT_MANIFEST)
    stage1 = read_json(root, STAGE1_RECEIPT)
    composition = read_json(root, COMPOSITION)
    loopctl_text = read_text(root, LOOPCTL)
    mcp_text = read_text(root, MCP_POLICY)
    outcomes: list[str] = []

    def mutate_manifest(
        name: str, mutator: Callable[[dict[str, Any]], None], expected: str
    ) -> None:
        value = copy.deepcopy(manifest)
        mutator(value)
        outcomes.append(
            expect_failure(
                name, lambda: validate_contract_manifest(root, value), expected
            )
        )

    mutate_manifest(
        "planner-authority",
        lambda value: value.update(planner_authority="STATE_WRITER"),
        "planner authority drift",
    )
    mutate_manifest(
        "canonical-authority",
        lambda value: value.update(canonical_authority="LANGGRAPH"),
        "canonical authority drift",
    )
    mutate_manifest(
        "runtime-state",
        lambda value: value.update(runtime_state_checked_in=True),
        "checked-in runtime state forbidden",
    )
    mutate_manifest(
        "force-skip-loss",
        lambda value: value["forbidden_decision_fields"].remove("force_skip"),
        "forbidden decision fields drift",
    )
    mutate_manifest(
        "security-waiver",
        lambda value: value["non_waivable_gate_classes"].remove("SECURITY"),
        "non-waivable gate classes drift",
    )
    mutate_manifest(
        "schema-digest",
        lambda value: value["schemas"][0].update(sha256="0" * 64),
        "schema digest mismatch",
    )

    bad_module = copy.deepcopy(module)
    bad_module["external_policy"]["exposed"] = True
    outcomes.append(
        expect_failure(
            "public-exposure",
            lambda: validate_module(bad_module),
            "external policy widened",
        )
    )

    bad_module = copy.deepcopy(module)
    bad_module["provides"] = ["loopx.strategy-writer/v1"]
    outcomes.append(
        expect_failure(
            "capability-drift", lambda: validate_module(bad_module), "provides drift"
        )
    )

    bad_module = copy.deepcopy(module)
    bad_module["proof"]["verify"] = "sh -c 'true'"
    outcomes.append(
        expect_failure(
            "raw-shell-proof",
            lambda: validate_module(bad_module),
            "proof command drift",
        )
    )

    bad_stage1 = copy.deepcopy(stage1)
    bad_stage1["result"] = "FAIL"
    outcomes.append(
        expect_failure("stage1-fail", lambda: validate_stage1(bad_stage1), "not PASS")
    )

    bad_composition = copy.deepcopy(composition)
    if isinstance(bad_composition.get("modules"), list):
        bad_composition["modules"].append({"id": MODULE_ID})
    else:
        bad_composition["modules"] = [{"id": MODULE_ID}]
    outcomes.append(
        expect_failure(
            "premature-selection",
            lambda: validate_non_admission(bad_composition, loopctl_text, mcp_text),
            "selected before final convergence",
        )
    )

    outcomes.append(
        expect_failure(
            "loopctl-exposure",
            lambda: validate_non_admission(
                composition, loopctl_text + "\nloopx-strategy-hitl", mcp_text
            ),
            "loopctl: module exposed",
        )
    )
    outcomes.append(
        expect_failure(
            "mcp-exposure",
            lambda: validate_non_admission(
                composition, loopctl_text, mcp_text + "\nstrategy-hitl"
            ),
            "MCP policy: Strategy/HITL public surface",
        )
    )

    require(len(outcomes) == 13, "selftest mutation count drift")
    return {"status": "PASS", "mutations": outcomes}


def find_root(explicit: str | None) -> Path:
    root = Path(explicit).resolve() if explicit else Path(__file__).resolve().parents[2]
    require((root / "AGENTS.md").is_file(), f"repository root not found: {root}")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--observed-at", default="CI_OR_LOCAL_INVOCATION")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        root = find_root(args.root)
        if args.selftest:
            result = run_selftest(root)
        else:
            result = validate_repository(root, args.output, args.observed_at)
    except ValidationError as exc:
        payload = {"status": "FAIL", "error": str(exc)}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(f"strategy-hitl-current FAIL: {exc}", file=sys.stderr)
        return BAD
    except (OSError, RuntimeError) as exc:
        payload = {"status": "FATAL", "error": str(exc)}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        else:
            print(f"strategy-hitl-current FATAL: {exc}", file=sys.stderr)
        return USAGE

    if args.selftest:
        if args.json:
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            print(
                f"strategy-hitl-current selftest PASS: {len(result['mutations'])} mutations"
            )
    return OK


if __name__ == "__main__":
    raise SystemExit(main())
