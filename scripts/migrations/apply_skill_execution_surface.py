#!/usr/bin/env python3
"""One-shot migration for the portable Skill execution public surface.

This script is intentionally idempotent. It is run once by the feature-branch
contract synchronizer, then removed with the temporary workflow hook. The
resulting contract, wiring, proof and documentation remain normal tracked files.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"migration marker missing in {path}: {old[:80]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


RUN_COMMAND: dict[str, Any] = {
    "loop": "skill-execution",
    "mode": "run",
    "target": ".agents/skills/harness-wiki/scripts/run_portable_skill.py",
    "mcp_exposed": False,
    "required": ["--assertions", "--output", "--repo", "--request"],
    "optional": ["--json"],
    "io": {
        "input": {
            "--request": "path to one skill-execution-request/v1 document bound to an exact repository commit/tree and Skill digest",
            "--assertions": "path to the independent skill-assertion-set/v1 document whose canonical digest is pinned by the request",
            "--repo": "trusted host path to the source Git repository; never accepted through MCP",
            "--output": "fresh host-owned directory for the immutable request, assertion set, content-addressed artifacts and receipt"
        },
        "output": [
            "<output>/request.json and assertions.json — canonical execution inputs",
            "<output>/artifacts/<sha256> — stdout, stderr, change artifact and runner diagnostics",
            "<output>/receipt.json — skill-execution-receipt/v1 with exact subject, independent assertion verdicts and cleanup state"
        ],
        "exit": "0 executed and every hard assertion passed · 2 checked failure or fail-closed policy skip · 64 usage, absent executable, malformed input or receipt collision",
        "note": "The local-process adapter attests a detached worktree, process group, timeout, explicit environment and post-run path boundary. It cannot attest network denial or OS filesystem isolation, so deny/allowlisted requests fail closed until a physical sandbox adapter is bound."
    },
    "writes": ["<output>/ only; never LoopX state, promotion state or Human Admit"]
}
PROVE_COMMAND: dict[str, Any] = {
    "loop": "skill-execution",
    "mode": "prove",
    "target": "proof_workflow/prove_skill_execution.sh",
    "mcp_exposed": False,
    "required": [],
    "optional": ["--force-receipt", "--json"],
    "io": {
        "input": "tracked runner, schemas, context route and executable selftest at the current checkout",
        "output": ["data/proof-workflow/skill-execution-<commit12>[-dirty].json"],
        "exit": "0 traversal and executable selftest passed · 2 a proof step went red · 64 missing context/tool or receipt collision"
    },
    "writes": ["data/proof-workflow/skill-execution-<commit12>[-dirty].json"]
}
TEST_COMMAND: dict[str, Any] = {
    "loop": "skill-execution",
    "mode": "test",
    "target": "proof_workflow/control_skill_execution_entry.sh",
    "mcp_exposed": False,
    "required": [],
    "optional": ["--json"],
    "io": {
        "input": "synthetic Git repository plus one positive and ten independent planted negatives",
        "output": ["proof_workflow/data/<run_id>/skill-execution-control.json and captured streams"],
        "exit": "0 positive passed and every planted defect turned red · 2 the public port missed a defect · 64 fixture/tool failure"
    },
    "writes": ["proof_workflow/data/<run_id>/"]
}


def migrate_contract() -> None:
    path = ROOT / "loopctl/contract.json"
    contract = json.loads(path.read_text(encoding="utf-8"))
    contract["surface_version"] = "3.0.0"
    existing = {
        (entry["loop"], entry["mode"]): entry
        for entry in contract["commands"]
    }
    wanted = [RUN_COMMAND, PROVE_COMMAND, TEST_COMMAND]
    if not any(key[0] == "skill-execution" for key in existing):
        indices = [
            index
            for index, entry in enumerate(contract["commands"])
            if entry["loop"] == "agent-runtime"
        ]
        if not indices:
            raise RuntimeError("agent-runtime insertion anchor is absent")
        at = max(indices) + 1
        contract["commands"][at:at] = wanted
    else:
        for item in wanted:
            key = (item["loop"], item["mode"])
            if existing.get(key) != item:
                raise RuntimeError(f"existing contract entry drifted: {key}")
    path.write_text(
        json.dumps(contract, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def migrate_loopctl() -> None:
    replace_once(
        "loopctl/loopctl.sh",
        "#   loopctl.sh <macro|micro|openwiki|notebooklm|agent-runtime|ctg> <mode> [flags]",
        "#   loopctl.sh <macro|micro|openwiki|notebooklm|agent-runtime|skill-execution|ctg> <mode> [flags]",
    )
    replace_once(
        "loopctl/loopctl.sh",
        "usage: loopctl.sh <macro|micro|openwiki|notebooklm|agent-runtime|equivalence|ctg> <mode> [flags]",
        "usage: loopctl.sh <macro|micro|openwiki|notebooklm|agent-runtime|skill-execution|equivalence|ctg> <mode> [flags]",
    )
    marker = '  agent-runtime/test) sh "$ROOT/$TARGET" ;;\n'
    insertion = marker + '''  skill-execution/run)\n    _skill_request=$(value_of --request "$@")\n    _skill_assertions=$(value_of --assertions "$@")\n    _skill_repo=$(value_of --repo "$@")\n    _skill_output=$(value_of --output "$@")\n    python3 "$ROOT/$TARGET" run \\\n      --request "$_skill_request" \\\n      --assertions "$_skill_assertions" \\\n      --repo "$_skill_repo" \\\n      --output "$_skill_output" ;;\n  skill-execution/prove) if has_flag --force-receipt "$@"; then PROVE_FORCE_RECEIPT=1 sh "$ROOT/$TARGET"; else sh "$ROOT/$TARGET"; fi ;;\n  skill-execution/test) sh "$ROOT/$TARGET" ;;\n'''
    replace_once("loopctl/loopctl.sh", marker, insertion)
    replace_once(
        "loopctl/selftest.sh",
        "(macro|micro|openwiki|notebooklm|agent-runtime|equivalence|ctg)/(run|prove|test|build-local)",
        "(macro|micro|openwiki|notebooklm|agent-runtime|skill-execution|equivalence|ctg)/(run|prove|test|build-local)",
    )


def migrate_module() -> None:
    path = ROOT / ".arena/modules/agent-runtime-integration/module.json"
    module = json.loads(path.read_text(encoding="utf-8"))
    module["interface_version"] = "1.2.0"
    module["components"]["portable_skill_execution"] = {
        "paths": [
            ".agents/skills/harness-wiki/contracts",
            ".agents/skills/harness-wiki/scripts/run_portable_skill.py",
            ".agents/skills/harness-wiki/tests/run-execution-selftest.py",
            "scripts/check_agent_runtime_module.py"
        ],
        "required": True
    }
    loops = [entry for entry in module["loops"] if entry["id"] != "skill-execution"]
    loops.append({
        "class": "execution-port",
        "external_policy": "host-only",
        "id": "skill-execution",
        "interface_version": "1.0.0",
        "public_port": "sh loopctl/loopctl.sh skill-execution"
    })
    module["loops"] = loops
    module["proof"] = {
        "control": ["sh", "proof_workflow/control_agent_runtime_module.sh", "--json"],
        "mutation": ["sh", "proof_workflow/control_agent_runtime_module.sh", "--json"],
        "selftest": ["python3", "scripts/check_agent_runtime_module.py"],
        "verify": ["python3", "scripts/check_agent_runtime_module.py"]
    }
    if "skill-execution.runner/v1" not in module["provides"]:
        module["provides"].append("skill-execution.runner/v1")
    if "scripts/check_agent_runtime_module.py" not in module["roots"]:
        module["roots"].append("scripts/check_agent_runtime_module.py")
    for tool in ("git", "sh"):
        if tool not in module["runtime"]["tools"]:
            module["runtime"]["tools"].append(tool)
    module["runtime"]["tools"] = sorted(module["runtime"]["tools"])
    if "harness-wiki" not in module["skills"]["repo_owned"]:
        module["skills"]["repo_owned"].append("harness-wiki")
    module["summary"] = (
        "Resolved skills-shared/runtime-env closure, generated host projections, "
        "Claude Code/Codex CLI adapter verdicts, and a host-owned portable Skill "
        "execution/assertion port that cannot advance state on Worker prose."
    )
    path.write_text(json.dumps(module, indent=2) + "\n", encoding="utf-8")


def write_new_files() -> None:
    write(
        "scripts/check_agent_runtime_module.py",
        '''#!/usr/bin/env python3\n"""Aggregate offline verification for the Agent runtime integration module."""\nfrom __future__ import annotations\n\nimport subprocess\nimport sys\nfrom pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nCOMMANDS = [\n    [sys.executable, "scripts/agent_runtime.py", "check", "--offline"],\n    [sys.executable, ".agents/skills/harness-wiki/scripts/run_portable_skill.py", "selftest"],\n]\n\n\ndef main() -> int:\n    red = False\n    for command in COMMANDS:\n        result = subprocess.run(command, cwd=ROOT, check=False)\n        red = red or result.returncode != 0\n    print("agent-runtime module: " + ("FAIL" if red else "PASS"))\n    return 2 if red else 0\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n''',
    )
    write(
        "proof_workflow/prove_skill_execution.sh",
        '''#!/bin/sh\n# Traversal proof for the host-owned portable Skill runner.\nset -u\n\nPROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)\n. "$PROVE_HOME/lib/prove.sh"\n\nprove_init skill-execution "typed request + independent assertions -> disposable worktree -> subject-bound receipt"\nprove_context repo-context CONTEXT.md "repository route -> bounded authority and multi-hop documentation"\nprove_context skill-context .agents/skills/harness-wiki/CONTEXT.md "harness-wiki route -> portable execution vocabulary and authority"\nprove_context runner-design .agents/skills/harness-wiki/modules/portable-runner.md "public port -> isolation claims, named gaps and state boundary"\nprove_harness request-schema .agents/skills/harness-wiki/contracts/skill-execution-request.schema.json "proposal -> closed executable/argv/sandbox subject"\nprove_harness assertion-schema .agents/skills/harness-wiki/contracts/skill-assertion-set.schema.json "expected property -> independent hard/advisory assertion"\nprove_harness receipt-schema .agents/skills/harness-wiki/contracts/skill-execution-receipt.schema.json "observed execution -> exact receipt shape"\nprove_harness runner .agents/skills/harness-wiki/scripts/run_portable_skill.py \\\n  "exact Git subject -> local-process execution and independent assertion verdict" \\\n  -- python3 .agents/skills/harness-wiki/scripts/run_portable_skill.py selftest\nprove_note physical-sandbox .arena/modules/agent-runtime-integration/README.md \\\n  "network deny and OS filesystem isolation remain NOT_EXERCISED in the local-process adapter; a physical sandbox adapter is required before either can be TESTED"\nprove_note live-hosts .agents/skills/harness-wiki/modules/host-skill-compatibility.md \\\n  "Codex CLI, Claude Code, Grok Build, OpenCode, Pi and Ante live canaries remain separate; portable runner PASS is not a host/provider PASS"\nprove_note independent-control proof_workflow/control_skill_execution_entry.sh \\\n  "drives the public loopctl path with one positive and ten planted defects"\nprove_emit\n''',
    )
    write(
        "proof_workflow/control_skill_execution_entry.sh",
        '''#!/bin/sh\n# Independent behavior control for the public portable Skill execution port.\nset -u\n\nROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel) || exit 64\nRUN_ID=$(date -u +%Y%m%dT%H%M%SZ)-skill-execution-$$\nOUT="$ROOT/proof_workflow/data/$RUN_ID"\nmkdir -p "$OUT" || exit 64\n\npython3 "$ROOT/.agents/skills/harness-wiki/tests/run-execution-selftest.py" \\\n  --loopctl "$ROOT/loopctl/loopctl.sh" >"$OUT/stdout.txt" 2>"$OUT/stderr.txt"\nRC=$?\nSTATUS=FAIL\n[ "$RC" -eq 0 ] && STATUS=PASS\npython3 - "$OUT/skill-execution-control.json" "$STATUS" "$RC" <<'PY'\nimport datetime as dt\nimport json\nimport sys\nfrom pathlib import Path\n\nPath(sys.argv[1]).write_text(json.dumps({\n    "schema": "bettor-arena/skill-execution-control/v1",\n    "status": sys.argv[2],\n    "exit_code": int(sys.argv[3]),\n    "observed_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),\n    "axes": [\n        "positive", "network-fail-closed", "assertion-digest", "skill-digest",\n        "tree-subject", "exit-code", "timeout", "diff-boundary",\n        "unsupported-assertion", "raw-shell", "append-only-receipt"\n    ]\n}, indent=2) + "\\n", encoding="utf-8")\nPY\ncat "$OUT/stdout.txt"\ncat "$OUT/stderr.txt" >&2\n[ "$RC" -eq 0 ] && exit 0\nexit 2\n''',
    )
    write(
        "proof_workflow/control_agent_runtime_module.sh",
        '''#!/bin/sh\n# Aggregate independent controls for both loops owned by agent-runtime-integration.\nset -u\nROOT=$(git -C "$(dirname "$0")" rev-parse --show-toplevel) || exit 64\nRED=0\nsh "$ROOT/proof_workflow/control_agent_runtime_entry.sh" || RED=1\nsh "$ROOT/proof_workflow/control_skill_execution_entry.sh" || RED=1\n[ "$RED" -eq 0 ] && { echo "agent-runtime module control: PASS"; exit 0; }\necho "agent-runtime module control: FAIL" >&2\nexit 2\n''',
    )
    write(
        ".agents/skills/harness-wiki/modules/portable-runner.md",
        '''# Host-owned portable Skill runner\n\n## Decision\n\n`SKILL.md` supplies reusable procedure and context. It does not execute a command, evaluate its own assertions, mark a Todo complete, promote a release, or issue Human Admit. Those powers remain in deterministic host code.\n\nThe public host-only port is:\n\n```bash\nsh loopctl/loopctl.sh skill-execution run \\\n  --request /trusted/request.json \\\n  --assertions /trusted/assertions.json \\\n  --repo /trusted/repository \\\n  --output /fresh/receipt-directory\n```\n\n## Execution chain\n\n```text\nexact request + assertion-set digest\n→ exact Git repository / commit / tree\n→ exact canonical Skill directory digest\n→ detached disposable worktree\n→ executable + argv (shell=false)\n→ bounded process group / timeout / environment / output\n→ OS and artifact observations\n→ independent assertion evaluator\n→ content-addressed artifacts\n→ subject-bound receipt\n→ mandatory worktree cleanup\n```\n\nThe Worker may propose source changes and emit stdout/stderr. It cannot write an assertion verdict, modify LoopX state, waive a hard gate, promote a release, or sign Human Admit.\n\n## Local-process adapter: what it proves\n\nThe current adapter can directly observe and attest:\n\n- exact repository remote, commit and tree;\n- exact Skill package digest;\n- exact assertion-set digest;\n- one executable plus an argv vector with `shell=False`;\n- explicit environment names with secret-like names refused;\n- a new process group, timeout and forced termination;\n- stdout, stderr, changed paths and selected artifacts by SHA-256;\n- post-run writable/read-only path boundaries;\n- independent hard/advisory assertion outcomes;\n- append-only output directory and worktree cleanup.\n\nIt does **not** claim physical network denial or OS-enforced filesystem isolation. Requests declaring `network=deny` or `network=allowlisted` return `SKIPPED_BY_POLICY` until a physical sandbox adapter can produce that evidence. Post-run diff checks detect a repository boundary violation; they do not prevent a malicious process from touching the host.\n\n## Assertion support\n\nImplemented assertion kinds:\n\n- `subject_match`\n- `exit_code`\n- `stderr_pattern`\n- `stdout_json_schema`\n- `file_exists`\n- `file_hash`\n- `file_content`\n- `git_diff_allowlist`\n- `lsp_diagnostics` from a declared JSON artifact\n- `test_report` from a declared JUnit XML artifact\n- `artifact_digest`\n\nAn unknown assertion kind fails closed. A model-based reviewer belongs in an `advisory` assertion or a separately calibrated verifier; it cannot silently become a hard gate.\n\n## Named exits\n\n- `0`: execution occurred, cleanup passed and every hard assertion passed.\n- `2`: checked execution/assertion failure or fail-closed policy skip.\n- `64`: malformed usage/input, absent executable, unresolvable exact subject or output collision.\n\nPortable execution PASS is not a live Codex CLI, Claude Code, Grok Build, OpenCode, Pi or Ante canary. Host/provider/model/sandbox evidence remains separately named.\n''',
    )
    write(
        ".agents/skills/harness-wiki/modules/portable-execution-index.md",
        '''# Portable execution index\n\nRead these modules in this order only when the task crosses host, execution, assertion, or provider boundaries:\n\n1. [`host-skill-compatibility.md`](host-skill-compatibility.md)\n2. [`executable-skill-contract.md`](executable-skill-contract.md)\n3. [`portable-runner.md`](portable-runner.md)\n4. [`knowledge-provider-topology.md`](knowledge-provider-topology.md)\n\nMachine contracts:\n\n- [`../contracts/skill-execution-request.schema.json`](../contracts/skill-execution-request.schema.json)\n- [`../contracts/skill-assertion-set.schema.json`](../contracts/skill-assertion-set.schema.json)\n- [`../contracts/skill-execution-receipt.schema.json`](../contracts/skill-execution-receipt.schema.json)\n\nDeterministic contract and executable gates:\n\n```bash\nsh .agents/skills/harness-wiki/tests/run-all.sh\nsh loopctl/loopctl.sh skill-execution test\nsh loopctl/loopctl.sh skill-execution prove\n```\n\nThe local-process runner proves its explicitly declared execution boundary. Live host, provider, model, physical sandbox and cloud execution remain separate receipts.\n''',
    )
    write(
        ".arena/modules/agent-runtime-integration/README.md",
        '''# `agent-runtime-integration` module\n\nMachine authority: [`module.json`](module.json)\nInterface version: `1.2.0`\n\n## Role\n\nResolves the selected `skills-shared` and `runtime-env` closure, binds it to bettor-arena, reports host-adapter readiness without storing secret values, and owns the host-only portable Skill execution/assertion port.\n\n## Public ports\n\n| Loop | Class | Interface | External policy | Entry |\n|---|---|---|---|---|\n| `agent-runtime` | aggregate | `1.0.0` | control-only | `sh loopctl/loopctl.sh agent-runtime` |\n| `skill-execution` | execution-port | `1.0.0` | host-only | `sh loopctl/loopctl.sh skill-execution` |\n\n## Capability boundary\n\n**Provides**\n\n- `agent-runtime.aggregate/v1`\n- `skill-execution.runner/v1`\n\n**Requires**\n\n- `arena.module-catalog/v1`\n- `arena.loopctl/v1`\n- `arena.proof-kernel/v1`\n\n## Owned implementation roots\n\n- `.agents/`\n- `.runtime-env/`\n- `scripts/agent_runtime.py`\n- `scripts/check_agent_runtime_module.py`\n- `scripts/runtime-env/`\n- `docs/agent-runtime-integration.md`\n- `docs/runtime-env-integration.md`\n\n`proof_workflow/` remains owned by `proof-kernel`; its traversal/control scripts bind evidence to this module without transferring ownership.\n\n## Runtime and Skills\n\n- Runtime: `claude`, `codex`, `git`, `python3`, `sh`; profile `bettor-arena-runtime-local`\n- Skills: required upstream `shared-skills-infra`; repo-owned `harness-wiki`\n\n## Evidence\n\n- Verify/selftest: `python3 scripts/check_agent_runtime_module.py`\n- Independent aggregate control/mutation: `sh proof_workflow/control_agent_runtime_module.sh --json`\n- Portable execution proof: `sh loopctl/loopctl.sh skill-execution prove`\n- Portable public-port control: `sh loopctl/loopctl.sh skill-execution test`\n\n## External boundary\n\nNot MCP-exposed. A local process receipt cannot proxy a physical sandbox, live host, live provider or Human Admit. `network=deny` and `network=allowlisted` fail closed until an admitted sandbox adapter can enforce and attest them.\n\n## Change discipline\n\n`module.json` is the source of truth for ownership, components, capabilities, effects and proof commands. This README is navigation only. Public input/output, named exits, required flags, effects or artifact contracts require an interface bump.\n''',
    )
    write(
        "proof_workflow/prove_agent_runtime.sh",
        '''#!/bin/sh\n# Portable traversal proof for the aggregate Agent module set. Live carrier\n# canaries are deliberately separate: hashed-not-run is not a live PASS.\nset -u\n\nPROVE_HOME=$(cd "$(dirname "$0")" && pwd -P)\n. "$PROVE_HOME/lib/prove.sh"\n\nprove_init agent-runtime "consumer requirements -> resolved bindings -> host adapters + portable execution gate"\nprove_context architecture ARCHITECTURE.md "repo entry -> engineering placement and invariants"\nprove_context integration-doc docs/agent-runtime-integration.md "Agent -> concrete update and verdict contract"\nprove_context skill-context .agents/skills/harness-wiki/CONTEXT.md "multi-hop Skill routing -> execution/assertion authority"\nprove_harness module-set .agents/module-set.json "two upstream closures + host carriers -> aggregate interface"\nprove_harness shared-requirements .agents/shared-skills.requirements.json "desired shared names -> resolver input"\nprove_harness shared-binding .agents/bindings/bettor-arena.json "shared resolver -> pinned skill closure"\nprove_harness runtime-requirements .runtime-env/requirements.json "desired runtime modules -> resolver input"\nprove_harness runtime-binding .runtime-env/bindings/bettor-arena-local.json "runtime resolver -> pinned module closure"\nprove_harness aggregate-gate scripts/check_agent_runtime_module.py \\\n  "module set + portable execution contract -> offline aggregate verdict" \\\n  -- python3 scripts/check_agent_runtime_module.py\nprove_harness portable-runner .agents/skills/harness-wiki/scripts/run_portable_skill.py \\\n  "typed request/assertions -> detached worktree -> independent receipt"\nprove_harness runtime-projection-gate scripts/gates/check_runtime_env_binding.py \\\n  "runtime binding/workload/policies/example -> consumer-local integrity verdict" \\\n  -- python3 scripts/gates/check_runtime_env_binding.py\nprove_note live-carriers data/agent-runtime/live.json \\\n  "not fired by proof because it spends real model turns; strict agent-runtime run requires a same-HEAD receipt and treats absence as NOT_EXERCISED"\nprove_note control-owned-by-harness proof_workflow/control_agent_runtime_module.sh \\\n  "independent controls plant shared/runtime/Claude/Codex plus portable execution defects; proof-kernel owns control bytes"\nprove_emit\n''',
    )


def migrate_context() -> None:
    replace_once(
        ".agents/skills/harness-wiki/CONTEXT.md",
        "- Executable Skill and assertion boundary: [`modules/executable-skill-contract.md`](modules/executable-skill-contract.md)\n- Serena / GrepAI / graph / memory ownership:",
        "- Executable Skill and assertion boundary: [`modules/executable-skill-contract.md`](modules/executable-skill-contract.md)\n- Host-owned portable runner and named isolation limits: [`modules/portable-runner.md`](modules/portable-runner.md)\n- Serena / GrepAI / graph / memory ownership:",
    )


def migrate_workflow() -> None:
    write(
        ".github/workflows/harness-wiki-portable-execution.yml",
        '''name: harness-wiki Portable Execution Contract\n\non:\n  pull_request:\n    types:\n      - opened\n      - ready_for_review\n      - reopened\n      - synchronize\n    paths:\n      - '.agents/skills/harness-wiki/**'\n      - '.arena/modules/agent-runtime-integration/**'\n      - 'scripts/check_agent_runtime_module.py'\n      - 'loopctl/contract.json'\n      - 'loopctl/loopctl.sh'\n      - 'loopctl/selftest.sh'\n      - 'loopctl/surface.lock'\n      - 'proof_workflow/prove_skill_execution.sh'\n      - 'proof_workflow/control_skill_execution_entry.sh'\n      - 'proof_workflow/control_agent_runtime_module.sh'\n      - '.github/workflows/harness-wiki-portable-execution.yml'\n  push:\n    branches:\n      - main\n      - 'refactor/**'\n      - 'integration/**'\n    paths:\n      - '.agents/skills/harness-wiki/**'\n      - '.arena/modules/agent-runtime-integration/**'\n      - 'scripts/check_agent_runtime_module.py'\n      - 'loopctl/contract.json'\n      - 'loopctl/loopctl.sh'\n      - 'loopctl/selftest.sh'\n      - 'loopctl/surface.lock'\n      - 'proof_workflow/prove_skill_execution.sh'\n      - 'proof_workflow/control_skill_execution_entry.sh'\n      - 'proof_workflow/control_agent_runtime_module.sh'\n      - '.github/workflows/harness-wiki-portable-execution.yml'\n      - '.arena/locks/bettor-arena.lock.json'\n      - 'data/module-proof/release-receipt.json'\n      - 'data/module-proof/subjects.lock.json'\n      - 'data/origins/status.json'\n  workflow_dispatch:\n\npermissions:\n  contents: read\n\nconcurrency:\n  group: harness-wiki-portable-execution-${{ github.event.pull_request.number || github.ref }}\n  cancel-in-progress: true\n\njobs:\n  contract:\n    if: github.event_name != 'pull_request' || github.event.pull_request.draft == false\n    runs-on: ubuntu-latest\n    timeout-minutes: 8\n    steps:\n      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09\n        with:\n          persist-credentials: false\n          fetch-depth: 0\n      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1\n        with:\n          python-version: '3.12'\n      - name: Validate contracts, executable runner, hollow and mutation controls\n        run: sh .agents/skills/harness-wiki/tests/run-all.sh\n      - name: Validate loopctl surface and public execution port\n        run: |\n          sh loopctl/loopctl.sh --selftest\n          sh loopctl/loopctl.sh skill-execution test\n          sh loopctl/loopctl.sh skill-execution prove\n      - name: Validate aggregate module gate\n        run: python3 scripts/check_agent_runtime_module.py\n''',
    )


def main() -> int:
    migrate_contract()
    migrate_loopctl()
    migrate_module()
    write_new_files()
    migrate_context()
    migrate_workflow()
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "loopctl/surface_digest.py"),
            "relock",
            str(ROOT / "loopctl/contract.json"),
            str(ROOT / "loopctl/surface.lock"),
        ],
        cwd=ROOT,
        check=True,
    )
    print("portable Skill execution surface migration: READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
