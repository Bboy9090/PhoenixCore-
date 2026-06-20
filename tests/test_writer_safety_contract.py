"""
tests/test_writer_safety_contract.py
PhoenixCore / BootForge USB Creator
Phase 4C-1: Writer Safety Contract Tests

Tests prove that:
  1.  Schema is bootforge.writer_safety_contract.v1
  2.  real_writer_implemented is always False
  3.  destructive_operations_enabled is always False
  4.  Missing target drive blocks
  5.  Missing image blocks
  6.  System drive blocks
  7.  Fixed/internal drive blocks
  8.  Missing device identity hash blocks
  9.  Missing image identity hash blocks
  10. Audit not passed blocks
  11. Simulation not passed blocks
  12. Missing typed confirmation blocks
  13. Missing destructive acknowledgement blocks
  14. Even a fully valid mock contract still does not enable real writing
  15. Payload is JSON serializable
  16. Validation is deterministic for the same inputs

No test in this file writes, formats, partitions, mounts, unmounts,
or accesses any real drive or device.
"""

import json
import unittest

from writer_safety_contract import (
    SCHEMA,
    REQUIRED_GATES,
    build_device_identity,
    build_image_identity,
    build_writer_safety_contract,
    validate_writer_safety_contract,
)


# ---------------------------------------------------------------------------
# Helpers to build fully-populated mock inputs
# ---------------------------------------------------------------------------

def _mock_device_identity(**overrides):
    """Return a device identity dict representing a safe removable USB."""
    base = dict(
        root_path="E:\\",
        label="MY_USB",
        filesystem="FAT32",
        capacity_bytes=32 * 1024 ** 3,
        removable=True,
        external=True,
        system_drive=False,
        fixed=False,
        hardware_id="USB\\VID_0781&PID_5581",
        serial_number="4C530001231009104264",
        stable_os_id="disk#4",
        scan_timestamp="2026-06-20T12:00:00Z",
    )
    base.update(overrides)
    return build_device_identity(**base)


def _mock_image_identity(**overrides):
    """Return an image identity dict representing a valid OS image."""
    base = dict(
        image_path="C:\\Users\\Bobby\\Downloads\\ubuntu.iso",
        filename="ubuntu.iso",
        extension=".iso",
        size_bytes=1_234_567_890,
        sha256="a" * 64,
        modified_timestamp="2026-06-20T10:00:00Z",
        audit_timestamp="2026-06-20T11:00:00Z",
    )
    base.update(overrides)
    return build_image_identity(**base)


def _all_gates_true():
    """Return gate_results dict with every gate set to True."""
    return {gate: True for gate in REQUIRED_GATES}


def _all_non_future_gates_true():
    """Return gate_results dict with prerequisite gates True, future gates False."""
    future = {
        "fresh_device_rescan_required",
        "typed_confirmation_required",
        "destructive_acknowledgement_required",
        "final_confirmation_token_required",
    }
    return {gate: (gate not in future) for gate in REQUIRED_GATES}


def _build_minimal_valid_contract():
    """
    Build the closest thing to a 'fully valid' contract possible in Phase 4C-1.
    All structural gates pass; all future gates are True as well.
    The contract will still be blocked because real_writer_implemented is False.
    """
    return build_writer_safety_contract(
        target_drive="E:\\",
        image="C:\\Users\\Bobby\\Downloads\\ubuntu.iso",
        device_identity=_mock_device_identity(),
        image_identity=_mock_image_identity(),
        gate_results=_all_gates_true(),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestWriterSafetyContractSchema(unittest.TestCase):
    """Test 1 & 2 & 3 — schema, real_writer_implemented, destructive flag."""

    def test_01_schema_is_correct(self):
        """Test 1: Contract schema must be bootforge.writer_safety_contract.v1."""
        contract = _build_minimal_valid_contract()
        self.assertEqual(contract["schema"], "bootforge.writer_safety_contract.v1")
        self.assertEqual(contract["schema"], SCHEMA)

    def test_02_real_writer_implemented_is_false(self):
        """Test 2: real_writer_implemented must always be False in Phase 4C-1."""
        contract = _build_minimal_valid_contract()
        self.assertIs(contract["real_writer_implemented"], False)

    def test_03_destructive_operations_enabled_is_false(self):
        """Test 3: destructive_operations_enabled must always be False in Phase 4C-1."""
        contract = _build_minimal_valid_contract()
        self.assertIs(contract["destructive_operations_enabled"], False)


class TestWriterSafetyContractBlocking(unittest.TestCase):
    """Tests 4–13 — verify every blocking condition fires correctly."""

    def test_04_missing_target_drive_blocks(self):
        """Test 4: Missing target drive must block the contract."""
        contract = build_writer_safety_contract(
            target_drive=None,
            image="ubuntu.iso",
            device_identity=_mock_device_identity(),
            image_identity=_mock_image_identity(),
            gate_results=_all_gates_true(),
        )
        self.assertTrue(contract["blocked"])
        reasons = " ".join(contract["block_reasons"])
        self.assertIn("target_drive", reasons)

    def test_04b_empty_target_drive_blocks(self):
        """Test 4b: Empty-string target drive must also block."""
        contract = build_writer_safety_contract(
            target_drive="   ",
            image="ubuntu.iso",
            device_identity=_mock_device_identity(),
            image_identity=_mock_image_identity(),
            gate_results=_all_gates_true(),
        )
        self.assertTrue(contract["blocked"])

    def test_05_missing_image_blocks(self):
        """Test 5: Missing image must block the contract."""
        contract = build_writer_safety_contract(
            target_drive="E:\\",
            image=None,
            device_identity=_mock_device_identity(),
            image_identity=_mock_image_identity(),
            gate_results=_all_gates_true(),
        )
        self.assertTrue(contract["blocked"])
        reasons = " ".join(contract["block_reasons"])
        self.assertIn("image", reasons)

    def test_06_system_drive_blocks(self):
        """Test 6: System drive must be permanently blocked."""
        contract = build_writer_safety_contract(
            target_drive="C:\\",
            image="ubuntu.iso",
            device_identity=_mock_device_identity(
                root_path="C:\\",
                system_drive=True,
                removable=False,
                external=False,
                fixed=True,
            ),
            image_identity=_mock_image_identity(),
            gate_results=_all_gates_true(),
        )
        self.assertTrue(contract["blocked"])
        reasons = " ".join(contract["block_reasons"])
        self.assertIn("system drive", reasons)

    def test_07_fixed_internal_drive_blocks(self):
        """Test 7: Fixed/internal drive must be blocked."""
        contract = build_writer_safety_contract(
            target_drive="D:\\",
            image="ubuntu.iso",
            device_identity=_mock_device_identity(
                root_path="D:\\",
                fixed=True,
                removable=False,
                external=False,
                system_drive=False,
            ),
            image_identity=_mock_image_identity(),
            gate_results=_all_gates_true(),
        )
        self.assertTrue(contract["blocked"])
        reasons = " ".join(contract["block_reasons"])
        self.assertIn("fixed", reasons)

    def test_08_missing_device_identity_hash_blocks(self):
        """Test 8: Device identity with no identity_hash must block."""
        dev_id = _mock_device_identity()
        dev_id["identity_hash"] = None   # forcibly remove the hash
        contract = build_writer_safety_contract(
            target_drive="E:\\",
            image="ubuntu.iso",
            device_identity=dev_id,
            image_identity=_mock_image_identity(),
            gate_results=_all_gates_true(),
        )
        self.assertTrue(contract["blocked"])
        reasons = " ".join(contract["block_reasons"])
        self.assertIn("identity_hash", reasons)

    def test_08b_missing_device_identity_entirely_blocks(self):
        """Test 8b: Entirely absent device_identity must block."""
        contract = build_writer_safety_contract(
            target_drive="E:\\",
            image="ubuntu.iso",
            device_identity=None,
            image_identity=_mock_image_identity(),
            gate_results=_all_gates_true(),
        )
        self.assertTrue(contract["blocked"])

    def test_09_missing_image_identity_hash_blocks(self):
        """Test 9: Image identity with no identity_hash must block."""
        img_id = _mock_image_identity()
        img_id["identity_hash"] = None   # forcibly remove the hash
        contract = build_writer_safety_contract(
            target_drive="E:\\",
            image="ubuntu.iso",
            device_identity=_mock_device_identity(),
            image_identity=img_id,
            gate_results=_all_gates_true(),
        )
        self.assertTrue(contract["blocked"])
        reasons = " ".join(contract["block_reasons"])
        self.assertIn("identity_hash", reasons)

    def test_09b_missing_image_identity_entirely_blocks(self):
        """Test 9b: Entirely absent image_identity must block."""
        contract = build_writer_safety_contract(
            target_drive="E:\\",
            image="ubuntu.iso",
            device_identity=_mock_device_identity(),
            image_identity=None,
            gate_results=_all_gates_true(),
        )
        self.assertTrue(contract["blocked"])

    def test_10_audit_not_passed_blocks(self):
        """Test 10: audit_passed=False must block the contract."""
        gates = _all_gates_true()
        gates["audit_passed"] = False
        contract = build_writer_safety_contract(
            target_drive="E:\\",
            image="ubuntu.iso",
            device_identity=_mock_device_identity(),
            image_identity=_mock_image_identity(),
            gate_results=gates,
        )
        self.assertTrue(contract["blocked"])
        reasons = " ".join(contract["block_reasons"])
        self.assertIn("audit_passed", reasons)

    def test_11_simulation_not_passed_blocks(self):
        """Test 11: simulation_passed=False must block the contract."""
        gates = _all_gates_true()
        gates["simulation_passed"] = False
        contract = build_writer_safety_contract(
            target_drive="E:\\",
            image="ubuntu.iso",
            device_identity=_mock_device_identity(),
            image_identity=_mock_image_identity(),
            gate_results=gates,
        )
        self.assertTrue(contract["blocked"])
        reasons = " ".join(contract["block_reasons"])
        self.assertIn("simulation_passed", reasons)

    def test_12_missing_typed_confirmation_blocks(self):
        """Test 12: typed_confirmation_required=False must appear in gate_results as unmet."""
        gates = _all_gates_true()
        gates["typed_confirmation_required"] = False
        contract = build_writer_safety_contract(
            target_drive="E:\\",
            image="ubuntu.iso",
            device_identity=_mock_device_identity(),
            image_identity=_mock_image_identity(),
            gate_results=gates,
        )
        self.assertTrue(contract["blocked"])
        self.assertFalse(contract["gate_results"]["typed_confirmation_required"])
        # Must appear in warnings (future gate) even when False
        warnings_str = " ".join(contract["warnings"])
        self.assertIn("typed_confirmation_required", warnings_str)

    def test_13_missing_destructive_acknowledgement_blocks(self):
        """Test 13: destructive_acknowledgement_required=False must appear as unmet."""
        gates = _all_gates_true()
        gates["destructive_acknowledgement_required"] = False
        contract = build_writer_safety_contract(
            target_drive="E:\\",
            image="ubuntu.iso",
            device_identity=_mock_device_identity(),
            image_identity=_mock_image_identity(),
            gate_results=gates,
        )
        self.assertTrue(contract["blocked"])
        self.assertFalse(
            contract["gate_results"]["destructive_acknowledgement_required"]
        )
        warnings_str = " ".join(contract["warnings"])
        self.assertIn("destructive_acknowledgement_required", warnings_str)


class TestWriterSafetyContractFullyValidStillBlocked(unittest.TestCase):
    """Test 14 — even a fully-satisfied mock contract does not enable writing."""

    def test_14_fully_valid_mock_still_does_not_enable_writing(self):
        """
        Test 14: Even when every gate is True and all identity data is present,
        the contract must still be blocked because real_writer_implemented=False.
        No write is ever enabled in Phase 4C-1.
        """
        contract = _build_minimal_valid_contract()

        # The contract is blocked — the writer is not implemented.
        self.assertTrue(contract["blocked"])

        # Safety fields are immutably False.
        self.assertIs(contract["real_writer_implemented"], False)
        self.assertIs(contract["destructive_operations_enabled"], False)

        # The block_reasons must include the Phase 4C-1 lock message.
        reasons_combined = " ".join(contract["block_reasons"])
        self.assertIn("real_writer_implemented is false", reasons_combined)

        # Validate via the validator — valid must be False.
        result = validate_writer_safety_contract(contract)
        self.assertFalse(result["valid"])
        self.assertTrue(result["real_writer_implemented_ok"])  # correctly False
        self.assertTrue(result["destructive_disabled_ok"])     # correctly False
        self.assertTrue(result["blocked"])


class TestWriterSafetyContractSerialization(unittest.TestCase):
    """Test 15 — payload is JSON serializable."""

    def test_15_payload_is_json_serializable(self):
        """Test 15: Contract payload must serialize to JSON without error."""
        contract = _build_minimal_valid_contract()
        try:
            serialized = json.dumps(contract)
        except (TypeError, ValueError) as exc:
            self.fail(f"Contract is not JSON serializable: {exc}")
        # Round-trip check
        reloaded = json.loads(serialized)
        self.assertEqual(reloaded["schema"], SCHEMA)
        self.assertIs(reloaded["real_writer_implemented"], False)
        self.assertIs(reloaded["destructive_operations_enabled"], False)

    def test_15b_empty_contract_is_json_serializable(self):
        """Test 15b: Minimal (all-None) contract must also be JSON serializable."""
        contract = build_writer_safety_contract()
        serialized = json.dumps(contract)
        reloaded = json.loads(serialized)
        self.assertTrue(reloaded["blocked"])


class TestWriterSafetyContractDeterminism(unittest.TestCase):
    """Test 16 — validation is deterministic for the same inputs."""

    def test_16_deterministic_for_same_inputs(self):
        """
        Test 16: Building the same contract twice with identical inputs must
        produce identical block_reasons, gate_results, schema, safety flags,
        and blocked state. (contract_id and created_at are allowed to differ.)
        """
        kwargs = dict(
            target_drive="E:\\",
            image="ubuntu.iso",
            device_identity=_mock_device_identity(),
            image_identity=_mock_image_identity(),
            gate_results=_all_gates_true(),
        )
        c1 = build_writer_safety_contract(**kwargs)
        c2 = build_writer_safety_contract(**kwargs)

        self.assertEqual(c1["schema"], c2["schema"])
        self.assertEqual(c1["real_writer_implemented"], c2["real_writer_implemented"])
        self.assertEqual(
            c1["destructive_operations_enabled"],
            c2["destructive_operations_enabled"],
        )
        self.assertEqual(c1["blocked"], c2["blocked"])
        self.assertEqual(sorted(c1["block_reasons"]), sorted(c2["block_reasons"]))
        self.assertEqual(c1["gate_results"], c2["gate_results"])
        self.assertEqual(c1["required_gates"], c2["required_gates"])
        self.assertEqual(c1["next_required_action"], c2["next_required_action"])

    def test_16b_device_identity_hash_is_deterministic(self):
        """Test 16b: Device identity hash must be identical for identical inputs."""
        dev1 = _mock_device_identity()
        dev2 = _mock_device_identity()
        self.assertEqual(dev1["identity_hash"], dev2["identity_hash"])

    def test_16c_image_identity_hash_is_deterministic(self):
        """Test 16c: Image identity hash must be identical for identical inputs."""
        img1 = _mock_image_identity()
        img2 = _mock_image_identity()
        self.assertEqual(img1["identity_hash"], img2["identity_hash"])

    def test_16d_different_drives_produce_different_hashes(self):
        """Test 16d: Different drive paths must produce different identity hashes."""
        dev_e = _mock_device_identity(root_path="E:\\")
        dev_f = _mock_device_identity(root_path="F:\\")
        self.assertNotEqual(dev_e["identity_hash"], dev_f["identity_hash"])


class TestRequiredGatesPresent(unittest.TestCase):
    """Structural tests — all required gates are present in every contract."""

    def test_all_required_gates_in_contract(self):
        """Every required gate name must appear in gate_results."""
        contract = _build_minimal_valid_contract()
        for gate in REQUIRED_GATES:
            self.assertIn(
                gate,
                contract["gate_results"],
                msg=f"Required gate '{gate}' missing from gate_results",
            )

    def test_required_gates_list_unchanged(self):
        """The required_gates list in the contract must match the module constant."""
        contract = _build_minimal_valid_contract()
        self.assertEqual(contract["required_gates"], REQUIRED_GATES)


if __name__ == "__main__":
    unittest.main()
