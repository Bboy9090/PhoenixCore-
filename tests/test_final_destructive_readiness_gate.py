import unittest
import os
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from writer_safety_contract import (
    build_contract_preview_payload,
    build_writer_contract_ledger_record,
    build_final_destructive_readiness_gate,
    validate_final_destructive_readiness_gate,
    build_readiness_gate_summary,
)


class TestFinalDestructiveReadinessGate(unittest.TestCase):
    def setUp(self):
        # Base contract payload
        self.contract = build_contract_preview_payload(
            target_drive="E:\\",
            image="C:\\test\\ubuntu.iso",
            audit_passed=True,
            simulation_passed=True,
            typed_confirmation="I UNDERSTAND THIS WILL OVERWRITE THE SELECTED USB DRIVE",
            destructive_acknowledgement="I CONFIRM THIS IS A REMOVABLE TEST USB DRIVE",
        )
        if self.contract.get("device_identity"):
            self.contract["device_identity"]["removable"] = True
        self.contract["lab_mode"] = True
        self.ledger = build_writer_contract_ledger_record(
            self.contract, "cli_preview_action"
        )

    def test_01_schema_is_correct(self):
        """1. Schema is bootforge.final_destructive_readiness_gate.v1."""
        gate = build_final_destructive_readiness_gate(self.contract, self.ledger)
        self.assertEqual(
            gate["schema"], "bootforge.final_destructive_readiness_gate.v1"
        )

    def test_02_normal_preview_keeps_readiness_false(self):
        """2. Normal preview (non-lab mode) keeps readiness false."""
        contract_normal = self.contract.copy()
        contract_normal["lab_mode"] = False
        gate = build_final_destructive_readiness_gate(contract_normal, self.ledger)
        self.assertFalse(gate["readiness_passed"])
        self.assertFalse(gate["lab_write_allowed"])

    def test_03_missing_env_unlock_blocks(self):
        """3. Lab mode missing env unlock blocks."""
        if "BOOTFORGE_ENABLE_LAB_WRITE" in os.environ:
            del os.environ["BOOTFORGE_ENABLE_LAB_WRITE"]
        gate = build_final_destructive_readiness_gate(self.contract, self.ledger)
        self.assertFalse(gate["readiness_passed"])
        self.assertIn(
            "Missing or invalid BOOTFORGE_ENABLE_LAB_WRITE environment variable.",
            gate["block_reasons"],
        )

    def test_04_wrong_typed_confirmation_blocks(self):
        """4. Wrong typed confirmation phrase blocks."""
        os.environ["BOOTFORGE_ENABLE_LAB_WRITE"] = "I_ACCEPT_REAL_USB_WRITE_RISK"
        contract_bad = self.contract.copy()
        contract_bad["typed_confirmation"] = "wrong phrase"
        gate = build_final_destructive_readiness_gate(contract_bad, self.ledger)
        self.assertFalse(gate["readiness_passed"])
        self.assertIn("Typed confirmation phrase mismatch.", gate["block_reasons"])

    def test_05_wrong_acknowledgement_blocks(self):
        """5. Wrong destructive acknowledgement blocks."""
        os.environ["BOOTFORGE_ENABLE_LAB_WRITE"] = "I_ACCEPT_REAL_USB_WRITE_RISK"
        contract_bad = self.contract.copy()
        contract_bad["destructive_acknowledgement"] = "wrong phrase"
        gate = build_final_destructive_readiness_gate(contract_bad, self.ledger)
        self.assertFalse(gate["readiness_passed"])
        self.assertIn(
            "Destructive acknowledgement phrase mismatch.", gate["block_reasons"]
        )

    def test_06_missing_ledger_blocks(self):
        """6. Missing ledger record blocks."""
        os.environ["BOOTFORGE_ENABLE_LAB_WRITE"] = "I_ACCEPT_REAL_USB_WRITE_RISK"
        gate = build_final_destructive_readiness_gate(self.contract, None)
        self.assertFalse(gate["readiness_passed"])
        self.assertIn("Ledger record is missing.", gate["block_reasons"])

    def test_07_missing_audit_blocks(self):
        """7. Missing audit trail blocks."""
        os.environ["BOOTFORGE_ENABLE_LAB_WRITE"] = "I_ACCEPT_REAL_USB_WRITE_RISK"
        contract_bad = build_contract_preview_payload(
            target_drive="E:\\",
            image="C:\\test\\ubuntu.iso",
            audit_passed=False,
            simulation_passed=True,
        )
        contract_bad["lab_mode"] = True
        gate = build_final_destructive_readiness_gate(contract_bad, self.ledger)
        self.assertFalse(gate["readiness_passed"])
        self.assertIn("Safety audit gate not passed.", gate["block_reasons"])

    def test_08_missing_simulation_blocks(self):
        """8. Missing simulation blocks."""
        os.environ["BOOTFORGE_ENABLE_LAB_WRITE"] = "I_ACCEPT_REAL_USB_WRITE_RISK"
        contract_bad = build_contract_preview_payload(
            target_drive="E:\\",
            image="C:\\test\\ubuntu.iso",
            audit_passed=True,
            simulation_passed=False,
        )
        contract_bad["lab_mode"] = True
        gate = build_final_destructive_readiness_gate(contract_bad, self.ledger)
        self.assertFalse(gate["readiness_passed"])
        self.assertIn(
            "Mock write simulation gate pending or failed.", gate["block_reasons"]
        )

    def test_09_full_mock_lab_prerequisites_can_pass(self):
        """9. Full mock lab prerequisites can pass readiness when everything matches."""
        os.environ["BOOTFORGE_ENABLE_LAB_WRITE"] = "I_ACCEPT_REAL_USB_WRITE_RISK"
        self.contract["export_skipped"] = True
        gate = build_final_destructive_readiness_gate(self.contract, self.ledger)
        self.assertTrue(gate["readiness_passed"])
        self.assertTrue(validate_final_destructive_readiness_gate(gate))

    def test_10_payload_json_serializable(self):
        """10. Readiness gate payload is JSON serializable."""
        gate = build_final_destructive_readiness_gate(self.contract, self.ledger)
        try:
            res = json.dumps(gate)
            self.assertIsNotNone(res)
        except Exception as e:
            self.fail(f"Readiness gate payload not JSON serializable: {e}")


if __name__ == "__main__":
    unittest.main()
