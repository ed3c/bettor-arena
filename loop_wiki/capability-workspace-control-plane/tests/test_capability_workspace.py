from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE_ROOT = HERE.parent
SCRIPT = MODULE_ROOT / "scripts/capability_workspace.py"
BINDING_PATH = MODULE_ROOT / "contracts/upstream-binding.json"
FIXTURE_PATH = HERE / "fixtures/admitted-envelope.json"

spec = importlib.util.spec_from_file_location("capability_workspace", SCRIPT)
assert spec and spec.loader
consumer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consumer)

BINDING = json.loads(BINDING_PATH.read_text(encoding="utf-8"))
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


class CapabilityWorkspaceConsumerTest(unittest.TestCase):
    def route(self, envelope=None, binding=None, ledger=None):
        return consumer.route_envelope(
            deepcopy(FIXTURE if envelope is None else envelope),
            deepcopy(BINDING if binding is None else binding),
            {} if ledger is None else ledger,
        )

    def assert_rejected(self, mutate, *, binding=False):
        envelope = deepcopy(FIXTURE)
        current_binding = deepcopy(BINDING)
        target = current_binding if binding else envelope
        mutate(target)
        with self.assertRaises(consumer.ContractError):
            consumer.route_envelope(envelope, current_binding, {})

    def test_baseline_acknowledges_route_only(self):
        result = self.route()
        self.assertEqual("ACKNOWLEDGED", result["state"])
        self.assertEqual("ROUTE_PROPOSAL_ADMISSION_ONLY", result["maximumClaim"])
        self.assertEqual("NOT_EXERCISED", result["execution"]["state"])
        self.assertFalse(result["authority"]["consumerGrantedExecutionAuthority"])
        self.assertIsNone(result["execution"]["workerReceiptReference"])
        self.assertEqual("NOT_EXERCISED", result["evidenceBoundary"]["liveBettorHandoff"])

    def test_idempotent_replay_is_explicit(self):
        ledger = {}
        first = self.route(ledger=ledger)
        second = self.route(ledger=ledger)
        self.assertFalse(first["idempotentReplay"])
        self.assertTrue(second["idempotentReplay"])
        self.assertEqual(first["semanticFingerprint"], second["semanticFingerprint"])

    def test_same_request_id_with_new_semantics_is_denied(self):
        ledger = {}
        self.route(ledger=ledger)
        changed = deepcopy(FIXTURE)
        changed["proposal"]["intent"] = "Different semantics"
        result = self.route(changed, ledger=ledger)
        self.assertEqual("DENIED", result["state"])
        self.assertEqual("REQUEST_ID_SEMANTIC_CONFLICT", result["reasonCode"])
        self.assertIsNone(result["kawReceipt"])

    def test_capability_id_mismatch_is_rejected(self):
        self.assert_rejected(lambda value: value.__setitem__("capabilityId", "verify.claim"))

    def test_route_class_mismatch_is_rejected(self):
        self.assert_rejected(lambda value: value["proposal"].__setitem__("routeClass", "VERIFY_CLAIM"))

    def test_destination_owner_mismatch_is_rejected(self):
        self.assert_rejected(lambda value: value["proposal"]["destinationOwner"].__setitem__("ownerId", "other"))

    def test_evidence_ceiling_cannot_widen(self):
        self.assert_rejected(lambda value: value["proposal"].__setitem__("evidenceCeiling", "LIVE_WORKFLOW"))

    def test_private_subject_is_rejected(self):
        self.assert_rejected(lambda value: value["subjectAdmission"][0].__setitem__("visibility", "PRIVATE"))

    def test_confidential_subject_is_rejected(self):
        self.assert_rejected(lambda value: value["subjectAdmission"][0].__setitem__("dataClass", "CONFIDENTIAL"))

    def test_subject_version_mismatch_is_rejected(self):
        self.assert_rejected(lambda value: value["subjectAdmission"][0].__setitem__("version", "v2"))

    def test_subject_digest_mismatch_is_rejected(self):
        self.assert_rejected(lambda value: value["subjectAdmission"][0]["digest"].__setitem__("value", "b" * 64))

    def test_subject_admission_denominator_cannot_shrink(self):
        self.assert_rejected(lambda value: value.__setitem__("subjectAdmission", []))

    def test_duplicate_subject_identity_is_rejected(self):
        def mutate(value):
            value["proposal"]["exactSubjects"].append(deepcopy(value["proposal"]["exactSubjects"][0]))
            value["subjectAdmission"].append(deepcopy(value["subjectAdmission"][0]))
        self.assert_rejected(mutate)

    def test_subject_must_have_version_or_digest(self):
        def mutate(value):
            value["proposal"]["exactSubjects"][0]["expectedVersion"] = None
            value["proposal"]["exactSubjects"][0]["expectedDigest"] = None
        self.assert_rejected(mutate)

    def test_unknown_top_level_field_is_rejected(self):
        self.assert_rejected(lambda value: value.__setitem__("executionAuthority", True))

    def test_credential_like_material_is_rejected(self):
        self.assert_rejected(lambda value: value["proposal"].__setitem__("intent", "Bearer ghp_example"))

    def test_newline_owner_is_rejected(self):
        self.assert_rejected(lambda value: value["proposal"]["caller"].__setitem__("ownerId", "bad\nowner"))

    def test_upstream_commit_cannot_slide(self):
        self.assert_rejected(lambda value: value["upstream"].__setitem__("commit", "1" * 40), binding=True)

    def test_upstream_tree_cannot_slide(self):
        self.assert_rejected(lambda value: value["upstream"].__setitem__("tree", "1" * 40), binding=True)

    def test_router_blob_cannot_slide(self):
        self.assert_rejected(lambda value: value["upstream"].__setitem__("routerBlob", "1" * 40), binding=True)

    def test_worker_manifest_blob_cannot_slide(self):
        self.assert_rejected(lambda value: value["bettor"].__setitem__("workerManifestBlob", "1" * 40), binding=True)

    def test_live_handoff_cannot_be_promoted(self):
        self.assert_rejected(lambda value: value["state"].__setitem__("liveHandoff", "PASS"), binding=True)

    def test_worker_runtime_cannot_be_promoted(self):
        self.assert_rejected(lambda value: value["state"].__setitem__("workerRuntime", "PASS"), binding=True)

    def test_hard_law_denominator_cannot_shrink(self):
        self.assert_rejected(lambda value: value["hardLaws"].pop(), binding=True)

    def test_fixture_reference_mode_still_does_not_execute(self):
        envelope = deepcopy(FIXTURE)
        envelope["mode"] = "FIXTURE_REFERENCE"
        result = self.route(envelope)
        self.assertEqual("ACKNOWLEDGED", result["state"])
        self.assertEqual("NOT_EXERCISED", result["execution"]["state"])
        self.assertEqual("NOT_EXERCISED", result["evidenceBoundary"]["workerRuntime"])

    def test_fingerprint_is_order_stable(self):
        left = deepcopy(FIXTURE)
        second_expectation = deepcopy(left["proposal"]["exactSubjects"][0])
        second_expectation["key"] = {"logicalId": "WORK:KAW:L4:002", "kind": "WORK_ITEM"}
        second_expectation["expectedVersion"] = "v2"
        second_expectation["expectedDigest"]["value"] = "b" * 64
        second_admission = deepcopy(left["subjectAdmission"][0])
        second_admission["key"] = deepcopy(second_expectation["key"])
        second_admission["version"] = "v2"
        second_admission["digest"]["value"] = "b" * 64
        left["proposal"]["exactSubjects"].append(second_expectation)
        left["subjectAdmission"].append(second_admission)
        right = deepcopy(left)
        right["proposal"]["exactSubjects"].reverse()
        right["subjectAdmission"].reverse()
        left_result = self.route(left)
        right_result = self.route(right)
        self.assertEqual(left_result["semanticFingerprint"], right_result["semanticFingerprint"])

    def test_ledger_round_trip(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ledger.json"
            claims = {"REQ:KAW:L4:001": "sha256:" + "1" * 64}
            consumer.save_ledger(path, claims)
            self.assertEqual(claims, consumer.load_ledger(path))

    def test_result_echoes_only_route_receipt_fields(self):
        result = self.route()
        self.assertEqual(
            {"requestId", "routeClass", "destinationOwner", "evidenceCeiling"},
            set(result["kawReceipt"]),
        )
        self.assertNotIn("workerSuccess", result["kawReceipt"])
        self.assertNotIn("gateVerdict", result["kawReceipt"])


if __name__ == "__main__":
    unittest.main()
