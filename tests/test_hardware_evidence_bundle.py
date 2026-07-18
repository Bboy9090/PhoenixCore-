import unittest
import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).parent.parent))

from real_writer_interface import (
    build_hardware_evidence_bundle,
    generate_hardware_evidence_markdown,
    export_hardware_evidence_json,
    export_hardware_evidence_markdown,
)


def _mock_scan_result(devices=None):
    return {
        "schema": "bootforge.device_scan.v2",
        "scan_id": "scan_test_001",
        "detection_source": "mock",
        "device_count": len(devices) if devices else 0,
        "devices": devices or [],
        "scan_warnings": [],
    }


def _mock_removable_usb():
    return {
        "drive_path": "E:\\",
        "display_name": "SanDisk Cruzer 64GB",
        "volume_label": "BOOTFORGE",
        "size_bytes": 64000000000,
        "size_gb": 59.6,
        "filesystem": "exFAT",
        "is_removable": True,
        "is_external": False,
        "is_fixed": False,
        "is_system": False,
        "is_boot_drive": False,
        "bus_protocol": "USB",
        "platform": "win32",
        "detection_source": "wmi",
        "stable_id": "USB\\VID_0781&PID_5583\\20060266212F",
        "serial": "20060266212F",
        "confidence": "high",
        "eligible_for_lab_write": True,
        "warnings": [],
        "block_reasons": [],
    }


def _mock_fixed_drive():
    return {
        "drive_path": "C:\\",
        "display_name": "System Drive",
        "volume_label": "Windows",
        "size_bytes": 512000000000,
        "size_gb": 476.8,
        "filesystem": "NTFS",
        "is_removable": False,
        "is_external": False,
        "is_fixed": True,
        "is_system": True,
        "is_boot_drive": True,
        "bus_protocol": "SATA",
        "platform": "win32",
        "detection_source": "wmi",
        "stable_id": "SATA\\SAMSUNG_SSD\\S1234",
        "serial": "S1234",
        "confidence": "high",
        "eligible_for_lab_write": False,
        "warnings": [],
        "block_reasons": [],
    }


def _mock_low_confidence_usb():
    return {
        "drive_path": "F:\\",
        "display_name": "Generic USB Device",
        "volume_label": "",
        "size_bytes": 8000000000,
        "size_gb": 7.5,
        "filesystem": "FAT32",
        "is_removable": True,
        "is_external": False,
        "is_fixed": False,
        "is_system": False,
        "is_boot_drive": False,
        "bus_protocol": "USB",
        "platform": "win32",
        "detection_source": "wmi",
        "stable_id": None,
        "serial": None,
        "confidence": "low",
        "eligible_for_lab_write": False,
        "warnings": ["No serial number detected."],
        "block_reasons": [],
    }


class TestHardwareEvidenceBundleSchema(unittest.TestCase):
    def test_schema_is_v1(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        self.assertEqual(bundle["schema"], "bootforge.hardware_evidence_bundle.v1")

    def test_physical_write_allowed_false(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        self.assertFalse(bundle["physical_write_allowed"])

    def test_physical_write_attempted_false(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        self.assertFalse(bundle["physical_write_attempted"])

    def test_bytes_written_zero(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        self.assertEqual(bundle["bytes_written"], 0)

    def test_dashboard_write_available_false(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        self.assertFalse(bundle["dashboard_write_available"])


class TestHardwareEvidenceBundleTargetResolution(unittest.TestCase):
    def test_no_target_produces_blocked_bundle(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(scan_payload=scan)
        self.assertFalse(bundle["target_resolved"])
        self.assertEqual(bundle["resolution_reason"], "no_target_selected")
        self.assertFalse(bundle["physical_write_allowed"])
        self.assertFalse(bundle["eligible"])

    def test_ambiguous_target_produces_blocked_bundle(self):
        usb1 = _mock_removable_usb()
        usb2 = _mock_removable_usb()
        usb2["serial"] = "DIFFERENT_SERIAL"
        scan = _mock_scan_result([usb1, usb2])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        self.assertFalse(bundle["target_resolved"])
        self.assertEqual(bundle["resolution_reason"], "ambiguous_target")
        self.assertFalse(bundle["physical_write_allowed"])

    def test_fixed_internal_system_target_blocked(self):
        scan = _mock_scan_result([_mock_fixed_drive()])
        bundle = build_hardware_evidence_bundle(
            target_drive="C:\\", scan_payload=scan
        )
        self.assertTrue(bundle["target_resolved"])
        self.assertEqual(
            bundle["resolution_reason"], "fixed_internal_or_system_target"
        )
        self.assertFalse(bundle["eligible"])
        self.assertFalse(bundle["physical_write_allowed"])

    def test_removable_high_confidence_eligible_not_write_allowed(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        self.assertTrue(bundle["target_resolved"])
        self.assertTrue(bundle["eligible"])
        self.assertFalse(bundle["physical_write_allowed"])

    def test_target_not_found(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="Z:\\", scan_payload=scan
        )
        self.assertFalse(bundle["target_resolved"])
        self.assertEqual(bundle["resolution_reason"], "target_not_found")


class TestHardwareEvidenceBundleConfidence(unittest.TestCase):
    def test_low_confidence_blocks_eligibility(self):
        scan = _mock_scan_result([_mock_low_confidence_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="F:\\", scan_payload=scan
        )
        self.assertTrue(bundle["target_resolved"])
        self.assertFalse(bundle["eligible"])
        self.assertIn(
            "Scanner confidence is low; identity lock is unreliable for lab eligibility.",
            bundle["scanner_block_reasons"],
        )


class TestHardwareEvidenceBundleIdentity(unittest.TestCase):
    def test_identity_hash_stable_for_same_evidence(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        b1 = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        b2 = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        self.assertEqual(b1["identity_hash"], b2["identity_hash"])
        self.assertIsNotNone(b1["identity_hash"])

    def test_identity_drift_appears_when_scan_differs(self):
        usb1 = _mock_removable_usb()
        scan1 = _mock_scan_result([usb1])
        bundle1 = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan1
        )

        usb2 = _mock_removable_usb()
        usb2["serial"] = "CHANGED_SERIAL_999"
        usb2["stable_id"] = "USB\\CHANGED\\999"
        scan2 = _mock_scan_result([usb2])
        bundle2 = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan2
        )

        self.assertNotEqual(bundle1["identity_hash"], bundle2["identity_hash"])


class TestHardwareEvidenceBundleRedaction(unittest.TestCase):
    def test_serial_redaction_removes_raw_serial_json(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan, redact_serials=True
        )
        self.assertEqual(bundle["serial"], "REDACTED")
        self.assertTrue(bundle["redacted"])
        json_str = json.dumps(bundle)
        self.assertNotIn("20060266212F", json_str)

    def test_serial_redaction_removes_raw_serial_markdown(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan, redact_serials=True
        )
        md = generate_hardware_evidence_markdown(bundle)
        self.assertNotIn("20060266212F", md)

    def test_stable_id_hashed_when_redacted(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan, redact_serials=True
        )
        self.assertNotEqual(
            bundle["stable_id"], "USB\\VID_0781&PID_5583\\20060266212F"
        )
        self.assertEqual(len(bundle["stable_id"]), 16)


class TestHardwareEvidenceBundleExport(unittest.TestCase):
    def setUp(self):
        base = os.path.join(Path.home(), ".bootforge_test_tmp")
        os.makedirs(base, exist_ok=True)
        self.test_dir = tempfile.mkdtemp(dir=base)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    def test_json_export_valid(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        out_path = os.path.join(self.test_dir, "evidence.json")
        res = export_hardware_evidence_json(bundle, out_path)
        self.assertEqual(res["status"], "success")
        with open(out_path, "r") as f:
            data = json.load(f)
        self.assertEqual(data["schema"], "bootforge.hardware_evidence_bundle.v1")

    def test_markdown_export_includes_safety_contract(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        out_path = os.path.join(self.test_dir, "evidence.md")
        res = export_hardware_evidence_markdown(bundle, out_path)
        self.assertEqual(res["status"], "success")
        with open(out_path, "r") as f:
            md = f.read()
        self.assertIn("read-only", md)
        self.assertIn("Physical Writing Added", md)


class TestHardwareEvidenceBundleScannerFailure(unittest.TestCase):
    def test_scanner_failure_degrades_into_warning(self):
        scan = _mock_scan_result()
        scan["scan_warnings"] = ["Scanner unavailable: test failure"]
        bundle = build_hardware_evidence_bundle(scan_payload=scan)
        self.assertIn(
            "Scanner unavailable: test failure",
            bundle["scan_summary"]["scan_warnings"],
        )
        self.assertFalse(bundle["physical_write_allowed"])


class TestHardwareEvidenceBundlePreviews(unittest.TestCase):
    def test_identity_lock_preview_present(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        self.assertIsNotNone(bundle["identity_lock_preview"])
        self.assertIn("identity_lock_id", bundle["identity_lock_preview"])

    def test_preflight_preview_present(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        self.assertIsNotNone(bundle["preflight_preview"])
        self.assertFalse(bundle["preflight_preview"]["physical_writer_allowed"])

    def test_dryrun_preview_present(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        bundle = build_hardware_evidence_bundle(
            target_drive="E:\\", scan_payload=scan
        )
        self.assertIsNotNone(bundle["dryrun_preview"])
        self.assertTrue(bundle["dryrun_preview"]["dry_run_only"])
        self.assertFalse(bundle["dryrun_preview"]["physical_write_allowed"])
        self.assertFalse(bundle["dryrun_preview"]["physical_write_attempted"])
        self.assertEqual(bundle["dryrun_preview"]["bytes_written"], 0)


class TestHardwareEvidenceBundleDashboard(unittest.TestCase):
    def test_dashboard_no_forbidden_labels(self):
        app_jsx_path = os.path.join(
            Path(__file__).parent.parent, "dashboard", "src", "App.jsx"
        )
        if os.path.exists(app_jsx_path):
            with open(app_jsx_path, "r", encoding="utf-8") as f:
                content = f.read()
            FORBIDDEN = [
                "Write USB", "Burn USB", "Flash USB", "Start Write",
                "Format USB", "Erase Drive", "Arm Writer", "Execute Write",
                "Destructive Write", "Write Now",
            ]
            for phrase in FORBIDDEN:
                self.assertNotIn(f">{phrase}<", content)


class TestHardwareEvidenceBundleNoDestructive(unittest.TestCase):
    def test_no_destructive_call_sites(self):
        import inspect
        source = inspect.getsource(build_hardware_evidence_bundle)
        for forbidden in ["subprocess", "os.system", "Popen", "dd ", "mkfs",
                          "diskpart", "CreateFile", "WriteFile", "DeviceIoControl"]:
            self.assertNotIn(forbidden, source)


class TestHardwareEvidenceBundleCLI(unittest.TestCase):
    @patch("usb_creator.get_normalized_scan")
    def test_cli_evidence_bundle_returns_json(self, mock_scan):
        mock_scan.return_value = _mock_scan_result([_mock_removable_usb()])
        import subprocess
        cmd = [
            sys.executable,
            os.path.join(Path(__file__).parent.parent, "usb_creator.py"),
            "--export-hardware-evidence-bundle",
            "--hardware-evidence-target", "E:\\",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["schema"], "bootforge.hardware_evidence_bundle.v1")
        self.assertFalse(data["physical_write_allowed"])


if __name__ == "__main__":
    unittest.main()
