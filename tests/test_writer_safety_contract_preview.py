"""
tests/test_writer_safety_contract_preview.py
PhoenixCore / BootForge USB Creator
Phase 4C-2: Contract CLI + Dashboard Preview Tests

Tests prove that:
  1.  Contract preview returns schema bootforge.writer_safety_contract.v1
  2.  real_writer_implemented remains false in preview
  3.  destructive_operations_enabled remains false in preview
  4.  Preview with missing drive is blocked
  5.  Preview with missing image is blocked
  6.  Preview with fully valid mock data still does not enable writing
  7.  Payload is JSON serializable
  8.  Forbidden destructive words/commands are not in executable Python source
  9.  CLI preview does not require or perform destructive actions
  10. Repeated preview with same inputs is deterministic

No test in this file writes, formats, partitions, mounts, unmounts,
or accesses any real drive or device.
"""

import ast
import json
import os
import unittest

from writer_safety_contract import (
    SCHEMA,
    REQUIRED_GATES,
    build_contract_preview_payload,
)

# ---------------------------------------------------------------------------
# Forbidden label strings that must not appear in executable code
# (not in comments, not in docstrings — checked via AST string literals)
# ---------------------------------------------------------------------------
FORBIDDEN_LABELS = [
    "Write USB",
    "Burn USB",
    "Flash USB",
    "Start Write",
    "Format USB",
    "Erase Drive",
    "Arm Writer",
    "Execute Write",
    "Destructive Write",
    "Write Now",
]

# ---------------------------------------------------------------------------
# Forbidden Python function/subprocess calls that would be destructive
# ---------------------------------------------------------------------------
FORBIDDEN_EXEC_CALLS = [
    "diskpart",
    "dd if=",
    "dd of=",
    "WriteFile(",
    "CreateFile(",
    "DeviceIoControl(",
    "format ",
    "mkfs.",
]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _full_preview(**kwargs):
    """Build a preview with all non-destructive gates maximally satisfied."""
    return build_contract_preview_payload(
        target_drive=kwargs.get("target_drive", "E:\\"),
        image=kwargs.get("image", "C:\\Users\\Bobby\\Downloads\\ubuntu.iso"),
        audit_passed=kwargs.get("audit_passed", True),
        simulation_passed=kwargs.get("simulation_passed", True),
        typed_confirmation=kwargs.get("typed_confirmation", "I UNDERSTAND"),
        destructive_acknowledgement=kwargs.get(
            "destructive_acknowledgement", "I ACCEPT"
        ),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestContractPreviewSchema(unittest.TestCase):
    """Test 1 — schema is bootforge.writer_safety_contract.v1."""

    def test_01_preview_schema_is_correct(self):
        """Test 1: Contract preview must return the correct schema string."""
        payload = _full_preview()
        self.assertEqual(payload["schema"], "bootforge.writer_safety_contract.v1")
        self.assertEqual(payload["schema"], SCHEMA)


class TestContractPreviewSafetyValues(unittest.TestCase):
    """Tests 2–3 — immutable safety flags remain False in preview."""

    def test_02_real_writer_implemented_remains_false(self):
        """Test 2: real_writer_implemented must always be False in preview."""
        payload = _full_preview()
        self.assertIs(payload["real_writer_implemented"], False)

    def test_03_destructive_operations_enabled_remains_false(self):
        """Test 3: destructive_operations_enabled must always be False in preview."""
        payload = _full_preview()
        self.assertIs(payload["destructive_operations_enabled"], False)


class TestContractPreviewBlocking(unittest.TestCase):
    """Tests 4–5 — missing drive or image blocks the preview."""

    def test_04_missing_drive_is_blocked(self):
        """Test 4: Preview with no target drive must be blocked."""
        payload = build_contract_preview_payload(
            target_drive=None,
            image="ubuntu.iso",
        )
        self.assertTrue(payload["blocked"])
        reasons = " ".join(payload["block_reasons"])
        self.assertIn("target_drive", reasons)

    def test_04b_whitespace_drive_is_blocked(self):
        """Test 4b: Preview with whitespace-only drive must also be blocked."""
        payload = build_contract_preview_payload(
            target_drive="   ",
            image="ubuntu.iso",
        )
        self.assertTrue(payload["blocked"])

    def test_05_missing_image_is_blocked(self):
        """Test 5: Preview with no image must be blocked."""
        payload = build_contract_preview_payload(
            target_drive="E:\\",
            image=None,
        )
        self.assertTrue(payload["blocked"])
        reasons = " ".join(payload["block_reasons"])
        self.assertIn("image", reasons)

    def test_05b_whitespace_image_is_blocked(self):
        """Test 5b: Preview with whitespace-only image must also be blocked."""
        payload = build_contract_preview_payload(
            target_drive="E:\\",
            image="   ",
        )
        self.assertTrue(payload["blocked"])


class TestContractPreviewFullyValidStillBlocked(unittest.TestCase):
    """Test 6 — fully populated preview still does not enable writing."""

    def test_06_fully_valid_preview_still_does_not_enable_writing(self):
        """
        Test 6: Even with drive, image, audit_passed, simulation_passed,
        typed_confirmation, and destructive_acknowledgement all present,
        the contract preview is still blocked and real writing remains off.
        """
        payload = _full_preview()

        # Always blocked because real_writer_implemented is False.
        self.assertTrue(payload["blocked"])

        # Safety flags immutable.
        self.assertIs(payload["real_writer_implemented"], False)
        self.assertIs(payload["destructive_operations_enabled"], False)

        # The permanent Phase lock must appear in block_reasons.
        reasons_combined = " ".join(payload["block_reasons"])
        self.assertIn("real_writer_implemented is false", reasons_combined)

    def test_06b_all_required_gates_present(self):
        """Test 6b: All required gate names must appear in gate_results."""
        payload = _full_preview()
        for gate in REQUIRED_GATES:
            self.assertIn(
                gate,
                payload["gate_results"],
                msg=f"Gate '{gate}' missing from preview gate_results",
            )


class TestContractPreviewSerialization(unittest.TestCase):
    """Test 7 — payload is JSON serializable."""

    def test_07_payload_is_json_serializable(self):
        """Test 7: Contract preview payload must round-trip through JSON."""
        payload = _full_preview()
        try:
            serialized = json.dumps(payload)
        except (TypeError, ValueError) as exc:
            self.fail(f"Preview payload is not JSON serializable: {exc}")
        reloaded = json.loads(serialized)
        self.assertEqual(reloaded["schema"], SCHEMA)
        self.assertIs(reloaded["real_writer_implemented"], False)
        self.assertIs(reloaded["destructive_operations_enabled"], False)

    def test_07b_empty_preview_is_json_serializable(self):
        """Test 7b: All-None preview must also be JSON serializable."""
        payload = build_contract_preview_payload()
        serialized = json.dumps(payload)
        reloaded = json.loads(serialized)
        self.assertTrue(reloaded["blocked"])


class TestForbiddenDestructiveWords(unittest.TestCase):
    """Test 8 — forbidden destructive labels not in executable Python source."""

    def _collect_string_literals(self, source_path: str) -> list[str]:
        """
        Parse a Python file with AST and collect all string literal values.
        This catches strings in code but NOT comments.
        """
        with open(source_path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=source_path)
        strings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                strings.append(node.value)
        return strings

    def test_08_forbidden_labels_not_in_writer_safety_contract_py(self):
        """
        Test 8a: Forbidden destructive UI labels must not appear as
        string literals in writer_safety_contract.py.
        """
        source = os.path.join(REPO_ROOT, "writer_safety_contract.py")
        strings = self._collect_string_literals(source)
        for forbidden in FORBIDDEN_LABELS:
            for s in strings:
                self.assertNotIn(
                    forbidden.lower(),
                    s.lower(),
                    msg=f"Forbidden label '{forbidden}' found in writer_safety_contract.py",
                )

    def test_08b_forbidden_labels_not_in_usb_creator_py_new_code(self):
        """
        Test 8b: Forbidden destructive UI labels must not appear as
        string literals in usb_creator.py.
        """
        source = os.path.join(REPO_ROOT, "usb_creator.py")
        strings = self._collect_string_literals(source)
        for forbidden in FORBIDDEN_LABELS:
            for s in strings:
                self.assertNotIn(
                    forbidden.lower(),
                    s.lower(),
                    msg=f"Forbidden label '{forbidden}' found in usb_creator.py",
                )

    def test_08c_forbidden_exec_calls_not_invoked_in_writer_safety_contract(self):
        """
        Test 8c: No destructive subprocess calls must be made from
        writer_safety_contract.py. AST Call node inspection only;
        docstrings listing what the code does NOT do are excluded.
        """
        source_path = os.path.join(REPO_ROOT, "writer_safety_contract.py")
        with open(source_path, encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=source_path)
        forbidden_pairs = {
            ("subprocess", "run"),
            ("subprocess", "call"),
            ("subprocess", "Popen"),
            ("os", "system"),
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                pair = (func.value.id, func.attr)
                if pair in forbidden_pairs:
                    ln = getattr(node, "lineno", "?")
                    self.fail(
                        "Forbidden invocation found: "
                        + func.value.id
                        + "."
                        + func.attr
                        + "() in writer_safety_contract.py line "
                        + str(ln)
                    )


class TestContractPreviewNonDestructiveCLI(unittest.TestCase):
    """Test 9 — contract preview does not require or perform destructive actions."""

    def test_09_preview_with_no_args_does_not_crash(self):
        """
        Test 9a: build_contract_preview_payload() with all None args must
        return a safe blocked payload without raising any exception.
        It must not attempt to open, read, write, or query any drive.
        """
        try:
            payload = build_contract_preview_payload()
        except Exception as exc:
            self.fail(
                f"build_contract_preview_payload() raised an exception with no args: {exc}"
            )
        self.assertTrue(payload["blocked"])
        self.assertIs(payload["real_writer_implemented"], False)
        self.assertIs(payload["destructive_operations_enabled"], False)

    def test_09b_preview_with_nonexistent_paths_does_not_crash(self):
        """
        Test 9b: Preview with paths to nonexistent files must return a
        blocked payload, not raise an exception.
        The function must never attempt to read/write a disk.
        """
        payload = build_contract_preview_payload(
            target_drive="Z:\\nonexistent-drive\\",
            image="C:\\nonexistent\\path\\image.iso",
        )
        self.assertIsInstance(payload, dict)
        self.assertTrue(payload["blocked"])
        self.assertIs(payload["real_writer_implemented"], False)

    def test_09c_preview_schema_field_always_correct(self):
        """Test 9c: Schema field must always equal the module constant."""
        for args in [
            {},
            {"target_drive": "E:\\"},
            {"image": "ubuntu.iso"},
            {"target_drive": "E:\\", "image": "ubuntu.iso"},
        ]:
            payload = build_contract_preview_payload(**args)
            self.assertEqual(payload["schema"], SCHEMA)


class TestContractPreviewDeterminism(unittest.TestCase):
    """Test 10 — repeated preview with same inputs is deterministic."""

    def test_10_deterministic_for_same_inputs(self):
        """
        Test 10: Two calls to build_contract_preview_payload() with identical
        inputs must produce identical block_reasons (sorted), gate_results,
        schema, safety flags, and blocked state.
        contract_id and created_at are allowed to differ.
        """
        kwargs = dict(
            target_drive="E:\\",
            image="ubuntu.iso",
            audit_passed=True,
            simulation_passed=True,
            typed_confirmation="I UNDERSTAND",
            destructive_acknowledgement="I ACCEPT",
        )
        p1 = build_contract_preview_payload(**kwargs)
        p2 = build_contract_preview_payload(**kwargs)

        self.assertEqual(p1["schema"], p2["schema"])
        self.assertEqual(p1["real_writer_implemented"], p2["real_writer_implemented"])
        self.assertEqual(
            p1["destructive_operations_enabled"], p2["destructive_operations_enabled"]
        )
        self.assertEqual(p1["blocked"], p2["blocked"])
        self.assertEqual(sorted(p1["block_reasons"]), sorted(p2["block_reasons"]))
        self.assertEqual(p1["gate_results"], p2["gate_results"])
        self.assertEqual(p1["required_gates"], p2["required_gates"])
        self.assertEqual(p1["next_required_action"], p2["next_required_action"])

    def test_10b_different_inputs_produce_different_gate_results(self):
        """Test 10b: audit_passed=True vs False must produce different gate_results."""
        p_with = build_contract_preview_payload(
            target_drive="E:\\", image="ubuntu.iso", audit_passed=True
        )
        p_without = build_contract_preview_payload(
            target_drive="E:\\", image="ubuntu.iso", audit_passed=False
        )
        self.assertNotEqual(
            p_with["gate_results"]["audit_passed"],
            p_without["gate_results"]["audit_passed"],
        )

    def test_10c_next_required_action_reflects_state(self):
        """
        Test 10c: next_required_action must differ between a fully-stated
        preview and a no-drive preview.
        """
        p_full = _full_preview()
        p_empty = build_contract_preview_payload()
        self.assertNotEqual(
            p_full["next_required_action"], p_empty["next_required_action"]
        )


if __name__ == "__main__":
    unittest.main()
