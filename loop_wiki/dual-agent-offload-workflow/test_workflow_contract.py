#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("dual_agent_workflow_contract", ROOT / "workflow_contract.py")
assert SPEC is not None and SPEC.loader is not None
contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(contract)


def expect(code: str, fn: Callable[[], Any]) -> None:
    try:
        fn()
    except contract.WorkflowContractError as exc:
        if exc.code != code:
            raise AssertionError(f"expected {code}, got {exc}") from exc
        print(f"{code}: RED/{code}")
    else:
        raise AssertionError(f"{code}: planted control survived")


def main() -> int:
    base_contract = contract.fixed_contract()
    contract.validate_contract(base_contract)
    submission = contract.fixed_submission()
    receipt = contract.workflow_receipt(submission)
    assert receipt["contract_state"] == "PASS"
    assert receipt["canonical_task_writer"] == "loopx-ledger"
    assert receipt["task_state"] == "NOT_EXERCISED"
    contract.validate_activity(contract.fixed_activity(), 3)
    contract.validate_transition("SUBMITTED", "ADMISSION_PENDING")
    contract.validate_transition("WAITING_FOR_HUMAN", "ADMITTED")
    contract.validate_transition("COMPENSATING", "COMPENSATED")
    print("P1: PASS deterministic workflow contract")

    bad = copy.deepcopy(submission); bad["workflow_subject"]["commit"] = "main"
    expect("MUTABLE_WORKFLOW_SUBJECT", lambda: contract.validate_submission(bad))

    bad_contract = copy.deepcopy(base_contract); bad_contract["runtime_contract"]["contract_set_digest"] = "0" * 64
    expect("RUNTIME_CONTRACT_MISMATCH", lambda: contract.validate_contract(bad_contract))

    bad = copy.deepcopy(submission); bad["decision_sources"] = ["CLOCK"]
    expect("NONDETERMINISTIC_DECISION_SOURCE", lambda: contract.validate_submission(bad))

    activity = contract.fixed_activity(); activity["decision_source"] = "NETWORK"
    expect("NONDETERMINISTIC_DECISION_SOURCE", lambda: contract.validate_activity(activity, 3))

    bad = copy.deepcopy(submission); bad["canonical_task_writer"] = "dual-agent-workflow"
    expect("SECOND_TASK_WRITER", lambda: contract.validate_submission(bad))

    bad = copy.deepcopy(submission); bad["loopx_write_mode"] = "DIRECT_APPEND"
    expect("DIRECT_LOOPX_WRITE", lambda: contract.validate_submission(bad))

    activity = contract.fixed_activity(); activity["authority"] = "CANONICAL_WRITER"
    expect("DIRECT_LOOPX_WRITE", lambda: contract.validate_activity(activity, 3))

    bad = copy.deepcopy(submission); bad["effect_routing"] = "DIRECT_PROVIDER_WRITE"
    expect("EFFECT_OWNER_BYPASS", lambda: contract.validate_submission(bad))

    bad = copy.deepcopy(submission); bad["evidence"]["gate_state"] = "PASS"
    expect("LANE_SUBSTITUTION", lambda: contract.validate_submission(bad))

    expect("HUMAN_WAIT_AS_SUCCESS", lambda: contract.validate_transition("WAITING_FOR_HUMAN", "COMPLETED"))
    expect("TERMINAL_COMPLETION_LAUNDERING", lambda: contract.validate_transition("POLICY_REFUSED", "COMPLETED"))

    bad = copy.deepcopy(submission); bad["job"]["retry_policy"]["max_attempts"] = 4
    expect("UNBOUNDED_WORKFLOW", lambda: contract.validate_submission(bad))

    bad = copy.deepcopy(submission); bad["history_fields"].append("private_reasoning")
    expect("SECRET_OR_REASONING_LEAK", lambda: contract.validate_submission(bad))

    bad = copy.deepcopy(submission); bad["job"]["secret_handles"] = ["plaintext-token"]
    expect("SECRET_OR_REASONING_LEAK", lambda: contract.validate_submission(bad))

    bad = copy.deepcopy(submission); bad["job"]["contract_set_ref"]["manifest_digest"] = "f" * 64
    expect("RUNTIME_CONTRACT_MISMATCH", lambda: contract.validate_submission(bad))

    print("PASS: DA-WF-C positive contract + planted disagreement controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
