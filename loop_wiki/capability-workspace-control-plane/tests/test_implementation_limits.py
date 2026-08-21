from __future__ import annotations

import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE_ROOT = HERE.parent
CHECKER = MODULE_ROOT / "scripts/check_capability_workspace.py"
LIMITS_PATH = MODULE_ROOT / "receipts/implementation-limits.json"

spec = importlib.util.spec_from_file_location("check_capability_workspace", CHECKER)
assert spec and spec.loader
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

LIMITS = json.loads(LIMITS_PATH.read_text(encoding="utf-8"))


class ImplementationLimitsTest(unittest.TestCase):
    def assert_rejected(self, mutate):
        value = deepcopy(LIMITS)
        mutate(value)
        with self.assertRaises(checker.CheckError):
            checker.verify_limits(value)

    def test_baseline(self):
        checker.verify_limits(deepcopy(LIMITS))

    def test_maximum_claim_cannot_widen(self):
        self.assert_rejected(lambda value: value.__setitem__("maximumClaim", "LIVE_BETTOR_HANDOFF_PASS"))

    def test_worker_runtime_cannot_be_promoted(self):
        self.assert_rejected(lambda value: value["states"].__setitem__("workerRuntime", "PASS"))

    def test_gate_runtime_cannot_be_promoted(self):
        self.assert_rejected(lambda value: value["states"].__setitem__("gateRuntime", "PASS"))

    def test_loopx_reducer_cannot_be_promoted(self):
        self.assert_rejected(lambda value: value["states"].__setitem__("loopxReducer", "PASS"))

    def test_live_handoff_cannot_be_promoted(self):
        self.assert_rejected(lambda value: value["states"].__setitem__("liveBettorHandoff", "PASS"))

    def test_user_outcome_cannot_be_promoted(self):
        self.assert_rejected(lambda value: value["states"].__setitem__("userOutcome", "PASS"))

    def test_external_authority_denominator_cannot_shrink(self):
        self.assert_rejected(lambda value: value["externalAuthority"].pop())

    def test_forbidden_claim_denominator_cannot_shrink(self):
        self.assert_rejected(lambda value: value["forbiddenClaims"].pop())

    def test_fixture_cannot_be_promoted_to_live(self):
        self.assert_rejected(lambda value: value["forbiddenClaims"].remove("FIXTURE_IS_LIVE"))

    def test_kaw_cannot_write_loopx_state_law_is_required(self):
        self.assert_rejected(lambda value: value["forbiddenClaims"].remove("KAW_WROTE_LOOPX_STATE"))

    def test_unknown_field_is_rejected(self):
        self.assert_rejected(lambda value: value.__setitem__("providerSuccess", True))


if __name__ == "__main__":
    unittest.main()
