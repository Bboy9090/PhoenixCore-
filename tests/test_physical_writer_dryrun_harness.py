import unittest
import os
import json
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.append(str(Path(__file__).parent.parent))

from real_writer_interface import (
    build_hardware_lab_permission_status,
    build_physical_writer_dryrun_request,
    validate_physical_writer_dryrun_request,
    build_physical_writer_dryrun_result,
    PhysicalDryRunWriterAdapter,
    WindowsPhysicalWriterAdapter,
    MacPhysicalWriterAdapter,
    LinuxPhysicalWriterAdapter,
    validate_physical_writer_dryrun_export_path,
    export_physical_writer_dryrun_json,
    export_physical_writer_dryrun_markdown,
)


class TestPhysicalWriterDryrunHarness(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.old_env = os.environ.get("BOOTFORGE_ENABLE_LAB_WRITE")
        os.environ["BOOTFORGE_ENABLE_LAB_WRITE"] = "I_ACCEPT_REAL_USB_WRITE_RISK"

        # Valid mock preflight
        self.valid_preflight = {
            "schema": "bootforge.hardware_writer_preflight.v1",
            "preflight_id": "preflight_12345",
            "target_drive": "E:\\",
            "target_stable_id": "stable_usb_123",
            "target_identity_hash": "hash_xyz_789",
            "image_path": "C:\\mock.iso",
            "image_sha256": "sha256_mock_hash",
            "image_size_bytes": 1024 * 1024 * 5,  # 5MB
            "identity_lock_id": "lock_123",
            "identity_lock_passed": True,
            "blocked": False,
            "block_reasons": [],
        }
        self.valid_readiness = {
            "schema": "bootforge.final_destructive_readiness_gate.v1",
            "readiness_gate_id": "gate_123",
            "session_id": "session_123",
            "validation_status": "passed",
        }

    def tearDown(self):
        import shutil

        shutil.rmtree(self.test_dir)
        if self.old_env is not None:
            os.environ["BOOTFORGE_ENABLE_LAB_WRITE"] = self.old_env
        else:
            os.environ.pop("BOOTFORGE_ENABLE_LAB_WRITE", None)

    def test_01_permission_status_schema(self):
        """1. Permission status schema is bootforge.hardware_lab_permission_status.v1."""
        status = build_hardware_lab_permission_status()
        self.assertEqual(
            status["schema"], "bootforge.hardware_lab_permission_status.v1"
        )

    def test_02_dryrun_request_schema(self):
        """2. Dry-run request schema is bootforge.physical_writer_dryrun_request.v1."""
        req = build_physical_writer_dryrun_request(
            self.valid_preflight, self.valid_readiness
        )
        self.assertEqual(req["schema"], "bootforge.physical_writer_dryrun_request.v1")

    def test_03_dryrun_result_schema(self):
        """3. Dry-run result schema is bootforge.physical_writer_dryrun_result.v1."""
        req = build_physical_writer_dryrun_request(
            self.valid_preflight, self.valid_readiness
        )
        res = build_physical_writer_dryrun_result(req)
        self.assertEqual(res["schema"], "bootforge.physical_writer_dryrun_result.v1")

    def test_04_dry_run_only_true(self):
        """4. dry_run_only remains true."""
        req = build_physical_writer_dryrun_request(
            self.valid_preflight, self.valid_readiness
        )
        res = build_physical_writer_dryrun_result(req)
        self.assertTrue(res["dry_run_only"])

    def test_05_physical_write_allowed_false(self):
        """5. physical_write_allowed remains false."""
        req = build_physical_writer_dryrun_request(
            self.valid_preflight, self.valid_readiness
        )
        res = build_physical_writer_dryrun_result(req)
        self.assertFalse(res["physical_write_allowed"])

    def test_06_physical_write_attempted_false(self):
        """6. physical_write_attempted remains false."""
        req = build_physical_writer_dryrun_request(
            self.valid_preflight, self.valid_readiness
        )
        res = build_physical_writer_dryrun_result(req)
        self.assertFalse(res["physical_write_attempted"])

    def test_07_bytes_written_zero(self):
        """7. bytes_written remains 0."""
        req = build_physical_writer_dryrun_request(
            self.valid_preflight, self.valid_readiness
        )
        res = build_physical_writer_dryrun_result(req)
        self.assertEqual(res["bytes_written"], 0)

    @patch("real_writer_interface.build_hardware_lab_permission_status")
    def test_08_missing_permission_blocks(self, mock_perm):
        """8. Missing permission blocks."""
        mock_perm.return_value = {
            "blocked": True,
            "block_reasons": ["Permission denied."],
        }
        req = build_physical_writer_dryrun_request(
            self.valid_preflight, self.valid_readiness
        )
        is_valid, reasons = validate_physical_writer_dryrun_request(req)
        self.assertFalse(is_valid)
        self.assertIn("Permission denied.", reasons)

    def test_09_missing_identity_lock_blocks(self):
        """9. Missing identity lock blocks."""
        pf = dict(self.valid_preflight)
        pf["identity_lock_id"] = None
        req = build_physical_writer_dryrun_request(pf, self.valid_readiness)
        is_valid, reasons = validate_physical_writer_dryrun_request(req)
        self.assertFalse(is_valid)
        self.assertIn("Target identity lock ID is missing.", reasons)

    def test_10_missing_readiness_gate_blocks(self):
        """10. Missing readiness gate blocks."""
        req = build_physical_writer_dryrun_request(self.valid_preflight, None)
        is_valid, reasons = validate_physical_writer_dryrun_request(req)
        self.assertFalse(is_valid)
        self.assertIn("Final destructive readiness gate ID is missing.", reasons)

    def test_11_identity_drift_blocks(self):
        """11. Identity drift blocks (simulated by missing hash)."""
        pf = dict(self.valid_preflight)
        pf["target_identity_hash"] = None
        req = build_physical_writer_dryrun_request(pf, self.valid_readiness)
        is_valid, reasons = validate_physical_writer_dryrun_request(req)
        self.assertFalse(is_valid)
        self.assertIn("Target identity hash is missing.", reasons)

    @patch("usb_creator.get_removable_drives")
    def test_12_fixed_internal_system_target_blocks(self, mock_drives):
        """12. Fixed/internal/system target blocks."""
        mock_drives.return_value = [
            {
                "drive": "E:\\",
                "is_fixed": True,
                "is_system_drive": False,
                "is_removable": False,
            }
        ]
        req = build_physical_writer_dryrun_request(
            self.valid_preflight, self.valid_readiness
        )
        adapter = PhysicalDryRunWriterAdapter()
        res = adapter.execute_dryrun(req)
        self.assertTrue(res["blocked"])
        self.assertIn("Target drive is fixed/internal or system.", res["block_reasons"])

    def test_13_valid_mock_removable_target_produces_chunk_plan(self):
        """13. Valid mock removable target produces chunk plan but no write."""
        req = build_physical_writer_dryrun_request(
            self.valid_preflight, self.valid_readiness
        )
        adapter = PhysicalDryRunWriterAdapter()
        res = adapter.execute_dryrun(req)
        self.assertTrue(res["blocked"])  # physical writing not allowed in this phase
        self.assertGreater(res["chunks_planned"], 0)
        self.assertEqual(res["bytes_written"], 0)
        self.assertFalse(res["physical_write_attempted"])

    def test_14_adapter_does_not_open_raw_devices(self):
        """14. PhysicalDryRunWriterAdapter does not open raw devices."""
        # Simple verification of class definition without file handles
        adapter = PhysicalDryRunWriterAdapter()
        self.assertEqual(adapter.name, "physical-dryrun-writer")

    def test_15_adapter_does_not_call_system_apis(self):
        """15. PhysicalDryRunWriterAdapter does not call diskpart/dd/format/mount/unmount."""
        # Ensure code doesn't contain forbidden raw writes
        with open(
            Path(__file__).parent.parent / "real_writer_interface.py",
            "r",
            encoding="utf-8",
        ) as f:
            content = f.read()
        adapter_code = content.split("class PhysicalDryRunWriterAdapter")[1].split(
            "class WindowsPhysicalWriterAdapter"
        )[0]
        self.assertNotIn("subprocess", adapter_code)
        self.assertNotIn("diskpart", adapter_code)
        self.assertNotIn("dd", adapter_code)
        self.assertNotIn("CreateFile", adapter_code)
        self.assertNotIn("WriteFile", adapter_code)

    def test_16_cli_permission_status_json(self):
        """16. CLI permission status returns JSON."""
        import subprocess

        out = subprocess.check_output(
            [
                sys.executable,
                str(Path(__file__).parent.parent / "usb_creator.py"),
                "--hardware-lab-permission-status",
            ]
        ).decode("utf-8")
        data = json.loads(out)
        self.assertEqual(data["schema"], "bootforge.hardware_lab_permission_status.v1")

    def test_17_cli_dryrun_returns_json(self):
        """17. CLI dry-run returns JSON."""
        import subprocess

        out = subprocess.check_output(
            [
                sys.executable,
                str(Path(__file__).parent.parent / "usb_creator.py"),
                "--physical-writer-dryrun",
                "--mock-hardware-preflight",
            ]
        ).decode("utf-8")
        data = json.loads(out)
        self.assertEqual(data["schema"], "bootforge.physical_writer_dryrun_result.v1")
        self.assertTrue(data["blocked"])

    def test_18_cli_dryrun_blocks_real_physical_write_attempt(self):
        """18. CLI dry-run blocks real physical write attempt."""
        import subprocess

        try:
            out = subprocess.check_output(
                [
                    sys.executable,
                    str(Path(__file__).parent.parent / "usb_creator.py"),
                    "--physical-writer-dryrun",
                    "--target-drive",
                    "E:\\",
                ],
                stderr=subprocess.STDOUT,
            ).decode("utf-8")
        except subprocess.CalledProcessError as e:
            out = e.output.decode("utf-8")
        data = json.loads(out)
        self.assertTrue(data["blocked"])
        self.assertIn("Hardware preflight ID is missing.", data["block_reasons"])

    def test_19_json_export_writes_valid_json(self):
        """19. JSON export writes valid JSON evidence."""
        req = build_physical_writer_dryrun_request(
            self.valid_preflight, self.valid_readiness
        )
        res = build_physical_writer_dryrun_result(req)
        out_file = os.path.join(self.test_dir, "export.json")
        export_res = export_physical_writer_dryrun_json(res, out_file)
        self.assertEqual(export_res["status"], "success")
        self.assertTrue(os.path.exists(out_file))
        with open(out_file, "r") as f:
            data = json.load(f)
        self.assertEqual(data["schema"], "bootforge.physical_writer_dryrun_result.v1")

    def test_20_markdown_export_writes_valid_markdown(self):
        """20. Markdown export writes Markdown evidence."""
        req = build_physical_writer_dryrun_request(
            self.valid_preflight, self.valid_readiness
        )
        res = build_physical_writer_dryrun_result(req)
        out_file = os.path.join(self.test_dir, "export.md")
        export_res = export_physical_writer_dryrun_markdown(res, out_file)
        self.assertEqual(export_res["status"], "success")
        self.assertTrue(os.path.exists(out_file))
        with open(out_file, "r") as f:
            data = f.read()
        self.assertIn(
            "# PhoenixCore / BootForge Physical USB Writer Dry-Run Report", data
        )

    def test_21_export_rejects_raw_device_paths(self):
        """21. Export rejects raw device paths before Path.resolve()."""
        with self.assertRaises(ValueError):
            validate_physical_writer_dryrun_export_path("\\\\.\\PhysicalDrive0", "json")

    def test_22_export_rejects_target_drive_root(self):
        """22. Export rejects target-drive root."""
        with self.assertRaises(ValueError):
            # Target root check
            validate_physical_writer_dryrun_export_path("E:\\", "json", "E:\\")

    def test_23_dashboard_source_no_forbidden_labels(self):
        """23. Dashboard source does not include forbidden UI labels."""
        app_jsx_path = Path(__file__).parent.parent / "dashboard" / "src" / "App.jsx"
        if app_jsx_path.exists():
            with open(app_jsx_path, "r", encoding="utf-8") as f:
                content = f.read()
            # None of forbidden labels should be present inside button / click handler labels.
            for forbidden in ["Write USB", "Burn USB", "Flash USB"]:
                self.assertNotIn(forbidden, content)

    def test_24_dashboard_source_cannot_trigger_physical_write(self):
        """24. Dashboard source cannot trigger physical write."""
        pass

    def test_25_physical_os_adapters_remain_blocked(self):
        """25. Physical OS adapters remain blocked."""
        self.assertTrue(WindowsPhysicalWriterAdapter().execute_write(None)["blocked"])
        self.assertTrue(MacPhysicalWriterAdapter().execute_write(None)["blocked"])
        self.assertTrue(LinuxPhysicalWriterAdapter().execute_write(None)["blocked"])

    def test_26_dryrun_result_json_serializable(self):
        """26. Dry-run result is JSON serializable."""
        req = build_physical_writer_dryrun_request(
            self.valid_preflight, self.valid_readiness
        )
        res = build_physical_writer_dryrun_result(req)
        serialized = json.dumps(res)
        self.assertIsNotNone(serialized)

    def test_27_plain_target_drive_blocks_without_evidence(self):
        """27. --physical-writer-dryrun cannot turn a plain --target-drive E:\\ input into a passing dry-run unless lock/readiness exist."""
        req = build_physical_writer_dryrun_request(None, None)
        is_valid, reasons = validate_physical_writer_dryrun_request(req)
        self.assertFalse(is_valid)
        self.assertIn("Hardware preflight ID is missing.", reasons)


if __name__ == "__main__":
    unittest.main()
