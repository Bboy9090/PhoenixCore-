import unittest
import os
import json
import io
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).parent.parent))

from real_writer_interface import (
    PHYSICAL_USB_WRITE_ENV_VAR,
    PHYSICAL_USB_WRITE_ENV_VALUE,
    PHYSICAL_TYPED_CONFIRMATION,
    PHYSICAL_DESTRUCTIVE_ACKNOWLEDGEMENT,
    PHYSICAL_FINAL_IRREVERSIBLE,
    build_physical_usb_write_lab_request,
    build_physical_usb_write_lab_result,
    build_physical_usb_write_lab_verification,
    validate_physical_usb_write_lab_gates,
    PhysicalUSBWriteLabAdapter,
    build_physical_usb_write_lab_status,
    validate_physical_usb_write_lab_export_path,
    export_physical_usb_write_lab_json,
    export_physical_usb_write_lab_markdown,
    generate_physical_usb_write_lab_markdown,
    _write_image_to_seekable_target,
    RawWriteError,
)


class TestPhysicalUSBWriteLabSchemas(unittest.TestCase):
    def test_request_schema_v1(self):
        req = build_physical_usb_write_lab_request(
            target_drive="E:\\", platform="win32"
        )
        self.assertEqual(req["schema"], "bootforge.physical_usb_write_lab_request.v1")
        self.assertTrue(req["request_id"].startswith("phyreq_"))
        self.assertEqual(req["target_drive"], "E:\\")

    def test_result_schema_v1(self):
        res = build_physical_usb_write_lab_result(adapter="physical-usb-write-lab")
        self.assertEqual(res["schema"], "bootforge.physical_usb_write_lab_result.v1")
        self.assertTrue(res["result_id"].startswith("phyres_"))
        self.assertTrue(res["blocked"])

    def test_verification_schema_v1(self):
        ver = build_physical_usb_write_lab_verification(target_drive="E:\\")
        self.assertEqual(
            ver["schema"], "bootforge.physical_usb_write_lab_verification.v1"
        )
        self.assertTrue(ver["verification_id"].startswith("phyver_"))
        self.assertEqual(ver["target_drive"], "E:\\")


class TestPhysicalUSBWriteLabConstants(unittest.TestCase):
    def test_env_var_name(self):
        self.assertEqual(
            PHYSICAL_USB_WRITE_ENV_VAR, "BOOTFORGE_ENABLE_PHYSICAL_USB_WRITE"
        )

    def test_env_var_value(self):
        self.assertEqual(
            PHYSICAL_USB_WRITE_ENV_VALUE, "I_ACCEPT_SACRIFICIAL_USB_WRITE_RISK"
        )

    def test_typed_confirmation(self):
        self.assertEqual(
            PHYSICAL_TYPED_CONFIRMATION,
            "I UNDERSTAND THIS WILL OVERWRITE THE SELECTED PHYSICAL USB DRIVE",
        )

    def test_destructive_acknowledgement(self):
        self.assertEqual(
            PHYSICAL_DESTRUCTIVE_ACKNOWLEDGEMENT,
            "I CONFIRM THIS IS A SACRIFICIAL REMOVABLE TEST USB DRIVE",
        )

    def test_final_irreversible(self):
        self.assertEqual(
            PHYSICAL_FINAL_IRREVERSIBLE,
            "I ACCEPT FULL RESPONSIBILITY FOR THIS TEST USB WRITE",
        )


class TestPhysicalUSBWriteLabGates(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(
            dir=os.path.join(os.path.dirname(__file__), "..")
        )
        self.old_env = os.environ.get(PHYSICAL_USB_WRITE_ENV_VAR)
        os.environ[PHYSICAL_USB_WRITE_ENV_VAR] = PHYSICAL_USB_WRITE_ENV_VALUE

        self.valid_request = build_physical_usb_write_lab_request(
            platform="win32",
            target_drive=r"\\.\PHYSICALDRIVE1",
            target_stable_id="usb_stable_001",
            target_identity_hash="hash_abc",
            latest_identity_hash="hash_abc",
            identity_lock_id="lock_001",
            preflight_id="preflight_001",
            dryrun_result_id="dryrun_001",
            readiness_gate_id="gate_001",
            session_id="session_001",
            ledger_path=os.path.join(self.test_dir, "ledger.jsonl"),
            image_path="C:\\mock.iso",
            image_sha256="sha256_mock",
            image_size_bytes=5242880,
            lab_mode=True,
            sacrificial_drive_confirmed=True,
            typed_confirmation=PHYSICAL_TYPED_CONFIRMATION,
            destructive_acknowledgement=PHYSICAL_DESTRUCTIVE_ACKNOWLEDGEMENT,
            final_irreversible_acknowledgement=PHYSICAL_FINAL_IRREVERSIBLE,
            environment_unlock_present=True,
            running_as_admin_or_root=True,
            physical_write_requested=True,
            physical_write_allowed=False,
            verify_after_write=True,
            target_confirmation=r"\\.\PHYSICALDRIVE1",
            target_is_removable=True,
            target_is_external=True,
            target_is_fixed=False,
            target_is_system_drive=False,
            target_size_bytes=1000000000,
            scanner_confidence="high",
            fresh_rescan_match=True,
            dryrun_wrote_zero_bytes=True,
            evidence_target_matches=True,
            evidence_image_matches=True,
            audit_passed=True,
            simulation_passed=True,
            physical_write_max_bytes=5242880,
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)
        if self.old_env is not None:
            os.environ[PHYSICAL_USB_WRITE_ENV_VAR] = self.old_env
        else:
            os.environ.pop(PHYSICAL_USB_WRITE_ENV_VAR, None)

    def test_all_gates_pass_returns_valid(self):
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertTrue(is_valid, f"Should pass all gates, but got: {reasons}")
        self.assertEqual(len(reasons), 0)

    def test_missing_env_var_blocks(self):
        os.environ.pop(PHYSICAL_USB_WRITE_ENV_VAR, None)
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("Environment variable" in r for r in reasons))

    def test_wrong_env_var_blocks(self):
        os.environ[PHYSICAL_USB_WRITE_ENV_VAR] = "wrong_value"
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("Environment variable" in r for r in reasons))

    def test_not_admin_blocks(self):
        self.valid_request["running_as_admin_or_root"] = False
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("admin/root" in r for r in reasons))

    def test_missing_target_drive_blocks(self):
        self.valid_request["target_drive"] = None
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("Target drive" in r for r in reasons))

    def test_missing_identity_lock_blocks(self):
        self.valid_request["identity_lock_id"] = None
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("Identity lock" in r for r in reasons))

    def test_identity_drift_blocks(self):
        self.valid_request["latest_identity_hash"] = "different_hash"
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("drift" in r.lower() for r in reasons))

    def test_wrong_typed_confirmation_blocks(self):
        self.valid_request["typed_confirmation"] = "wrong phrase"
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("Typed confirmation" in r for r in reasons))

    def test_wrong_destructive_ack_blocks(self):
        self.valid_request["destructive_acknowledgement"] = "wrong phrase"
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("Destructive acknowledgement" in r for r in reasons))

    def test_wrong_final_irreversible_blocks(self):
        self.valid_request["final_irreversible_acknowledgement"] = "wrong phrase"
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("Final irreversible" in r for r in reasons))

    def test_missing_image_path_blocks(self):
        self.valid_request["image_path"] = None
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("Image path" in r for r in reasons))

    def test_missing_preflight_blocks(self):
        self.valid_request["preflight_id"] = None
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("preflight" in r.lower() for r in reasons))

    def test_missing_dryrun_blocks(self):
        self.valid_request["dryrun_result_id"] = None
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("dry-run" in r.lower() for r in reasons))

    def test_missing_readiness_gate_blocks(self):
        self.valid_request["readiness_gate_id"] = None
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("Readiness gate" in r for r in reasons))

    def test_missing_lab_mode_blocks(self):
        self.valid_request["lab_mode"] = False
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("Lab mode" in r for r in reasons))

    def test_physical_write_not_requested_blocks(self):
        self.valid_request["physical_write_requested"] = False
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("not explicitly requested" in r for r in reasons))

    def test_non_win32_platform_blocks(self):
        self.valid_request["platform"] = "darwin"
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("not implemented" in r.lower() for r in reasons))

    def test_raw_device_path_required(self):
        self.valid_request["target_drive"] = "E:\\"
        self.valid_request["target_confirmation"] = "E:\\"
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("raw disk path" in r for r in reasons))

    def test_exact_target_confirmation_required(self):
        self.valid_request["target_confirmation"] = r"\\.\PHYSICALDRIVE2"
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("confirmation mismatch" in r for r in reasons))

    def test_fresh_rescan_match_required(self):
        self.valid_request["fresh_rescan_match"] = False
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("Fresh target re-scan" in r for r in reasons))

    def test_linux_platform_blocks(self):
        self.valid_request["platform"] = "linux"
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("not implemented" in r.lower() for r in reasons))

    def test_system32_ledger_path_blocks(self):
        self.valid_request["ledger_path"] = "C:\\Windows\\System32\\ledger.jsonl"
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("system32" in r.lower() for r in reasons))

    def test_null_request_blocks(self):
        is_valid, reasons = validate_physical_usb_write_lab_gates(None)
        self.assertFalse(is_valid)
        self.assertIn("Missing request payload.", reasons)

    def test_wrong_schema_blocks(self):
        self.valid_request["schema"] = "wrong.schema.v1"
        is_valid, reasons = validate_physical_usb_write_lab_gates(self.valid_request)
        self.assertFalse(is_valid)
        self.assertTrue(any("Invalid request schema" in r for r in reasons))


class TestPhysicalUSBWriteLabAdapter(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(
            dir=os.path.join(os.path.dirname(__file__), "..")
        )
        self.old_env = os.environ.get(PHYSICAL_USB_WRITE_ENV_VAR)
        os.environ[PHYSICAL_USB_WRITE_ENV_VAR] = PHYSICAL_USB_WRITE_ENV_VALUE
        self.adapter = PhysicalUSBWriteLabAdapter()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)
        if self.old_env is not None:
            os.environ[PHYSICAL_USB_WRITE_ENV_VAR] = self.old_env
        else:
            os.environ.pop(PHYSICAL_USB_WRITE_ENV_VAR, None)

    def _build_valid_request(self):
        return build_physical_usb_write_lab_request(
            platform="win32",
            target_drive=r"\\.\PHYSICALDRIVE1",
            target_stable_id="usb_stable_001",
            target_identity_hash="hash_abc",
            latest_identity_hash="hash_abc",
            identity_lock_id="lock_001",
            preflight_id="preflight_001",
            dryrun_result_id="dryrun_001",
            readiness_gate_id="gate_001",
            session_id="session_001",
            ledger_path=os.path.join(self.test_dir, "ledger.jsonl"),
            image_path="C:\\mock.iso",
            image_sha256="sha256_mock",
            image_size_bytes=5242880,
            lab_mode=True,
            sacrificial_drive_confirmed=True,
            typed_confirmation=PHYSICAL_TYPED_CONFIRMATION,
            destructive_acknowledgement=PHYSICAL_DESTRUCTIVE_ACKNOWLEDGEMENT,
            final_irreversible_acknowledgement=PHYSICAL_FINAL_IRREVERSIBLE,
            environment_unlock_present=True,
            running_as_admin_or_root=True,
            physical_write_requested=True,
            verify_after_write=True,
            target_confirmation=r"\\.\PHYSICALDRIVE1",
            target_is_removable=True,
            target_is_external=True,
            target_is_fixed=False,
            target_is_system_drive=False,
            target_size_bytes=1000000000,
            scanner_confidence="high",
            fresh_rescan_match=True,
            dryrun_wrote_zero_bytes=True,
            evidence_target_matches=True,
            evidence_image_matches=True,
            audit_passed=True,
            simulation_passed=True,
            physical_write_max_bytes=5242880,
        )

    def test_adapter_name(self):
        self.assertEqual(self.adapter.name, "physical-usb-write-lab")

    def test_adapter_blocks_when_gates_fail(self):
        req = build_physical_usb_write_lab_request(platform="win32")
        result = self.adapter.execute_write(req)
        self.assertTrue(result["blocked"])
        self.assertFalse(result["physical_write_attempted"])
        self.assertEqual(
            result["next_required_action"], "resolve_physical_write_blockers"
        )

    @patch("real_writer_interface._execute_windows_physical_usb_write")
    def test_adapter_invokes_windows_writer_after_all_gates(self, mock_execute):
        mock_execute.return_value = {"blocked": False, "bytes_written": 5242880}
        req = self._build_valid_request()
        result = self.adapter.execute_write(req)
        self.assertFalse(result["blocked"])
        mock_execute.assert_called_once()

    def test_adapter_does_not_write_when_gates_fail(self):
        req = self._build_valid_request()
        req["fresh_rescan_match"] = False
        result = self.adapter.execute_write(req)
        self.assertFalse(result["physical_write_attempted"])
        self.assertFalse(result["physical_write_allowed"])
        self.assertEqual(result["bytes_written"], 0)
        self.assertEqual(result["chunks_written"], 0)

    @patch("real_writer_interface._execute_windows_physical_usb_write")
    def test_adapter_preserves_target_info(self, mock_execute):
        mock_execute.return_value = {
            "target_drive": r"\\.\PHYSICALDRIVE1",
            "target_stable_id": "usb_stable_001",
            "adapter": "physical-usb-write-lab",
        }
        req = self._build_valid_request()
        result = self.adapter.execute_write(req)
        self.assertEqual(result["target_drive"], r"\\.\PHYSICALDRIVE1")
        self.assertEqual(result["target_stable_id"], "usb_stable_001")
        self.assertEqual(result["adapter"], "physical-usb-write-lab")


class TestPhysicalUSBWriteLabStatus(unittest.TestCase):
    def test_status_schema(self):
        status = build_physical_usb_write_lab_status()
        self.assertEqual(status["schema"], "bootforge.physical_usb_write_lab_status.v1")

    def test_status_unarmed_by_default(self):
        status = build_physical_usb_write_lab_status()
        self.assertTrue(status["blocked"])
        self.assertTrue(status["physical_write_implemented"])
        self.assertFalse(status["physical_write_allowed"])

    def test_status_dashboard_write_blocked(self):
        status = build_physical_usb_write_lab_status()
        self.assertTrue(status["dashboard_write_blocked"])
        self.assertTrue(status["physical_write_cli_only"])
        self.assertIn("CLI-only", status["dashboard_write_message"])

    def test_status_required_gates_list(self):
        status = build_physical_usb_write_lab_status()
        gates = status["required_gates"]
        self.assertIsInstance(gates, list)
        self.assertGreater(len(gates), 20)
        self.assertIn("environment_unlock", gates)
        self.assertIn("admin_or_root", gates)
        self.assertIn("typed_confirmations_match", gates)
        self.assertIn("no_identity_drift", gates)

    def test_status_next_action(self):
        status = build_physical_usb_write_lab_status()
        self.assertEqual(
            status["next_required_action"], "satisfy_cli_physical_write_gates"
        )


class TestPhysicalUSBWriteEngine(unittest.TestCase):
    def test_copy_engine_writes_exact_image_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            image_path = os.path.join(tmp, "image.bin")
            target_path = os.path.join(tmp, "target.bin")
            payload = (b"phoenix-key" * 1000) + b"!"
            with open(image_path, "wb") as image:
                image.write(payload)
            with open(target_path, "w+b") as target:
                written = _write_image_to_seekable_target(image_path, target, 257)
                target.seek(0)
                self.assertEqual(target.read(), payload)
            self.assertEqual(written, len(payload))

    def test_short_write_reports_partial_byte_count(self):
        class ShortTarget(io.BytesIO):
            def write(self, data):
                super().write(data[:3])
                return 3

        with tempfile.TemporaryDirectory() as tmp:
            image_path = os.path.join(tmp, "image.bin")
            with open(image_path, "wb") as image:
                image.write(b"0123456789")
            with self.assertRaises(RawWriteError) as raised:
                _write_image_to_seekable_target(image_path, ShortTarget(), 10)
            self.assertEqual(raised.exception.bytes_written, 3)


class TestPhysicalUSBWriteLabExportPath(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(
            dir=os.path.join(os.path.dirname(__file__), "..")
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_empty_path_raises(self):
        with self.assertRaises(ValueError):
            validate_physical_usb_write_lab_export_path("", "json")

    def test_unc_path_raises(self):
        with self.assertRaises(ValueError):
            validate_physical_usb_write_lab_export_path(
                "\\\\server\\share\\out.json", "json"
            )

    def test_system32_path_raises(self):
        with self.assertRaises(ValueError):
            validate_physical_usb_write_lab_export_path(
                "C:\\Windows\\System32\\out.json", "json"
            )

    def test_etc_path_raises(self):
        with self.assertRaises(ValueError):
            validate_physical_usb_write_lab_export_path("/etc/out.json", "json")

    def test_wrong_extension_json_raises(self):
        out = os.path.join(self.test_dir, "result.txt")
        with self.assertRaises(ValueError):
            validate_physical_usb_write_lab_export_path(out, "json")

    def test_wrong_extension_markdown_raises(self):
        out = os.path.join(self.test_dir, "result.txt")
        with self.assertRaises(ValueError):
            validate_physical_usb_write_lab_export_path(out, "markdown")

    def test_directory_path_raises(self):
        with self.assertRaises(ValueError):
            validate_physical_usb_write_lab_export_path(self.test_dir, "json")

    def test_overwrite_existing_raises(self):
        existing = os.path.join(self.test_dir, "existing.json")
        with open(existing, "w") as f:
            f.write("{}")
        with self.assertRaises(ValueError):
            validate_physical_usb_write_lab_export_path(existing, "json")

    def test_valid_json_path_passes(self):
        out = os.path.join(self.test_dir, "result.json")
        validate_physical_usb_write_lab_export_path(out, "json")

    def test_valid_markdown_path_passes(self):
        out = os.path.join(self.test_dir, "result.md")
        validate_physical_usb_write_lab_export_path(out, "markdown")


class TestPhysicalUSBWriteLabExportJSON(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(
            dir=os.path.join(os.path.dirname(__file__), "..")
        )
        self.sample_result = build_physical_usb_write_lab_result(
            adapter="physical-usb-write-lab",
            target_drive="E:\\",
            blocked=True,
            block_reasons=["physical_writer_not_safely_implemented"],
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_export_json_success(self):
        out = os.path.join(self.test_dir, "result.json")
        export = export_physical_usb_write_lab_json(self.sample_result, out)
        self.assertEqual(export["status"], "success")
        self.assertTrue(os.path.exists(out))
        with open(out) as f:
            data = json.load(f)
        self.assertEqual(data["schema"], "bootforge.physical_usb_write_lab_result.v1")

    def test_export_json_bad_path_fails(self):
        export = export_physical_usb_write_lab_json(self.sample_result, "")
        self.assertEqual(export["status"], "failed")
        self.assertIsNotNone(export["error"])


class TestPhysicalUSBWriteLabExportMarkdown(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(
            dir=os.path.join(os.path.dirname(__file__), "..")
        )
        self.sample_result = build_physical_usb_write_lab_result(
            adapter="physical-usb-write-lab",
            target_drive="E:\\",
            blocked=True,
            block_reasons=["physical_writer_not_safely_implemented"],
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_generate_markdown_contains_safety_assertion(self):
        md = generate_physical_usb_write_lab_markdown(self.sample_result)
        self.assertIn("CLI-only", md)
        self.assertIn("dashboard cannot start", md)
        self.assertIn("Fixed, internal, and system drives", md)

    def test_export_markdown_success(self):
        out = os.path.join(self.test_dir, "result.md")
        export = export_physical_usb_write_lab_markdown(self.sample_result, out)
        self.assertEqual(export["status"], "success")
        self.assertTrue(os.path.exists(out))
        with open(out) as f:
            content = f.read()
        self.assertIn("Physical USB Write Lab Report", content)

    def test_export_markdown_bad_path_fails(self):
        export = export_physical_usb_write_lab_markdown(self.sample_result, "")
        self.assertEqual(export["status"], "failed")


class TestPhysicalUSBWriteLabRequestFields(unittest.TestCase):
    def test_chunk_calculation(self):
        req = build_physical_usb_write_lab_request(
            image_size_bytes=5242880,
            chunk_size_bytes=1048576,
        )
        self.assertEqual(req["expected_chunk_count"], 5)

    def test_chunk_rounding(self):
        req = build_physical_usb_write_lab_request(
            image_size_bytes=5242881,
            chunk_size_bytes=1048576,
        )
        self.assertEqual(req["expected_chunk_count"], 6)

    def test_zero_image_size(self):
        req = build_physical_usb_write_lab_request(image_size_bytes=0)
        self.assertEqual(req["expected_chunk_count"], 0)


if __name__ == "__main__":
    unittest.main()
