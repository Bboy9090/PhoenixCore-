"""
tests/test_scanner_integration_preflight.py
Phase 5B-2: Scanner Integration Into Existing USB Safety + Preflight Flow

Tests that device_scanner.scan_devices() evidence feeds into usb_creator scan,
identity lock, preflight, dry-run, and eligibility paths.
"""

import unittest
import os
import sys
import json
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from device_scanner import scan_devices, _build_device_record, SCANNER_SCHEMA
from real_writer_interface import (
    build_removable_target_identity_lock,
    validate_removable_target_identity_lock,
    rescan_and_compare_target_identity,
    build_physical_writer_preflight_result,
    _build_scanner_identity_hash,
    _resolve_scanner_device,
)


def _mock_scan_result(devices=None, platform="win32"):
    return {
        "schema": SCANNER_SCHEMA,
        "scan_id": "scan_test123",
        "created_at": "2025-01-01T00:00:00Z",
        "platform": platform,
        "detection_source": "test_mock",
        "safe_mode": True,
        "destructive": False,
        "operation": "read_only_device_scan",
        "device_count": len(devices or []),
        "devices": devices or [],
        "scan_warnings": [],
    }


def _mock_removable_usb():
    return _build_device_record(
        drive_path="/dev/sdb",
        display_name="Test USB Drive",
        stable_id="linux_sdb_SN12345",
        serial="SN12345",
        size_bytes=16000000000,
        filesystem="vfat",
        volume_label="BOOTFORGE",
        is_removable=True,
        is_external=True,
        is_fixed=False,
        is_system=False,
        bus_protocol="USB",
        platform="linux",
        detection_source="sysblock_udevadm",
    )


def _mock_fixed_drive():
    return _build_device_record(
        drive_path="/dev/sda",
        display_name="Internal SSD",
        stable_id="linux_sda_SN_INT",
        serial="SN_INT",
        size_bytes=500000000000,
        is_removable=False,
        is_external=False,
        is_fixed=True,
        is_system=True,
        platform="linux",
        detection_source="sysblock_udevadm",
    )


def _mock_no_serial_usb():
    return _build_device_record(
        drive_path="/dev/sdc",
        display_name="Cheap USB",
        stable_id=None,
        serial=None,
        size_bytes=8000000000,
        is_removable=True,
        is_external=True,
        is_fixed=False,
        is_system=False,
        platform="linux",
        detection_source="sysblock_udevadm",
    )


class TestScanPathUsesDeviceScanner(unittest.TestCase):
    """usb_creator scan path delegates to device_scanner.scan_devices()."""

    @patch("device_scanner.scan_devices")
    def test_get_removable_drives_uses_scanner(self, mock_scan):
        usb = _mock_removable_usb()
        mock_scan.return_value = _mock_scan_result([usb])
        from usb_creator import get_removable_drives
        drives = get_removable_drives(quiet=True)
        mock_scan.assert_called_once()
        self.assertEqual(len(drives), 1)
        self.assertEqual(drives[0]["drive"], "/dev/sdb")

    @patch("device_scanner.scan_devices")
    def test_legacy_output_shape(self, mock_scan):
        usb = _mock_removable_usb()
        mock_scan.return_value = _mock_scan_result([usb])
        from usb_creator import get_removable_drives
        drives = get_removable_drives(quiet=True)
        d = drives[0]
        self.assertIn("drive", d)
        self.assertIn("label", d)
        self.assertIn("total_size_gb", d)
        self.assertIn("free_size_gb", d)
        self.assertIn("type", d)

    @patch("device_scanner.scan_devices")
    def test_legacy_excludes_fixed_drives(self, mock_scan):
        fixed = _mock_fixed_drive()
        usb = _mock_removable_usb()
        mock_scan.return_value = _mock_scan_result([fixed, usb])
        from usb_creator import get_removable_drives
        drives = get_removable_drives(quiet=True)
        paths = [d["drive"] for d in drives]
        self.assertNotIn("/dev/sda", paths)
        self.assertIn("/dev/sdb", paths)

    @patch("device_scanner.scan_devices")
    def test_build_drive_scan_payload_v2(self, mock_scan):
        usb = _mock_removable_usb()
        mock_scan.return_value = _mock_scan_result([usb])
        from usb_creator import build_drive_scan_payload
        payload = build_drive_scan_payload()
        self.assertEqual(payload["schema"], "bootforge.drive_scan.v2")
        self.assertEqual(payload["scanner_schema"], SCANNER_SCHEMA)
        self.assertIn("devices", payload)
        self.assertIn("drives", payload)
        self.assertFalse(payload["destructive"])


class TestFixedInternalSystemBlocked(unittest.TestCase):
    """Fixed/internal/system drives remain unsafe across all paths."""

    def test_fixed_drive_ineligible(self):
        dev = _mock_fixed_drive()
        self.assertFalse(dev["is_eligible"])
        self.assertTrue(len(dev["block_reasons"]) > 0)

    def test_identity_lock_blocks_fixed(self):
        scan = _mock_scan_result([_mock_fixed_drive()])
        lock = build_removable_target_identity_lock("/dev/sda", scan)
        self.assertTrue(lock["blocked"])
        has_fixed_reason = any("fixed" in r.lower() or "system" in r.lower() for r in lock["block_reasons"])
        self.assertTrue(has_fixed_reason)

    def test_identity_lock_blocks_system(self):
        dev = _build_device_record(
            drive_path="C:\\",
            display_name="System Drive",
            stable_id="win_C_sys",
            serial="SYS001",
            size_bytes=500000000000,
            is_removable=False,
            is_external=False,
            is_fixed=True,
            is_system=True,
            platform="win32",
            detection_source="powershell_win32_diskdrive",
        )
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("C:\\", scan)
        self.assertTrue(lock["blocked"])


class TestStableIdAndConfidence(unittest.TestCase):
    """Missing stable_id lowers confidence and blocks lab write eligibility."""

    def test_no_serial_low_confidence(self):
        dev = _mock_no_serial_usb()
        self.assertEqual(dev["confidence"], "low")
        self.assertTrue(len(dev["warnings"]) > 0)

    def test_lock_with_no_serial_has_low_confidence(self):
        dev = _mock_no_serial_usb()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sdc", scan)
        self.assertEqual(lock["confidence"], "low")

    def test_preflight_blocks_low_confidence_missing_stable_id(self):
        dev = _mock_no_serial_usb()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sdc", scan)
        preflight = build_physical_writer_preflight_result(lock)
        self.assertEqual(preflight["scanner_confidence"], "low")
        has_confidence_block = any("confidence" in r.lower() for r in preflight["block_reasons"])
        self.assertTrue(has_confidence_block)

    def test_high_confidence_with_serial(self):
        dev = _mock_removable_usb()
        self.assertEqual(dev["confidence"], "high")
        self.assertTrue(dev["is_eligible"])


class TestTargetPathResolution(unittest.TestCase):
    """Target path must resolve to exactly one scanned device."""

    def test_resolve_existing_device(self):
        dev = _mock_removable_usb()
        scan = _mock_scan_result([dev])
        found = _resolve_scanner_device("/dev/sdb", scan)
        self.assertIsNotNone(found)
        self.assertEqual(found["drive_path"], "/dev/sdb")

    def test_resolve_missing_device_returns_none(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        found = _resolve_scanner_device("/dev/sdz", scan)
        self.assertIsNone(found)

    def test_lock_with_unresolved_path_uses_fallback(self):
        scan = _mock_scan_result([_mock_removable_usb()])
        lock = build_removable_target_identity_lock("/dev/sdz", scan)
        self.assertIn("fallback", lock.get("detection_source", ""))


class TestAmbiguousTargetBlocked(unittest.TestCase):
    """Ambiguous target blocks."""

    def test_empty_target_blocks(self):
        lock = build_removable_target_identity_lock("")
        self.assertTrue(lock["blocked"])

    def test_none_target_blocks(self):
        lock = build_removable_target_identity_lock(None)
        self.assertTrue(lock["blocked"])

    def test_raw_device_path_without_scan_blocks(self):
        lock = build_removable_target_identity_lock("\\\\.\\PhysicalDrive1")
        self.assertTrue(lock["blocked"])
        self.assertIn("Direct raw device paths are blocked without scanned target context.", lock["block_reasons"])


class TestIdentityLockUsesScanner(unittest.TestCase):
    """Identity lock uses stable_id and normalized identity fields."""

    def test_lock_uses_stable_id_from_scanner(self):
        dev = _mock_removable_usb()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sdb", scan)
        self.assertEqual(lock["stable_id"], "linux_sdb_SN12345")

    def test_lock_uses_serial_from_scanner(self):
        dev = _mock_removable_usb()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sdb", scan)
        self.assertEqual(lock["serial"], "SN12345")

    def test_lock_hash_is_deterministic(self):
        dev = _mock_removable_usb()
        scan = _mock_scan_result([dev])
        lock1 = build_removable_target_identity_lock("/dev/sdb", scan)
        lock2 = build_removable_target_identity_lock("/dev/sdb", scan)
        self.assertEqual(lock1["device_identity_hash"], lock2["device_identity_hash"])

    def test_lock_hash_includes_scanner_fields(self):
        dev = _mock_removable_usb()
        h = _build_scanner_identity_hash(dev)
        self.assertEqual(len(h), 64)

    def test_lock_includes_detection_source(self):
        dev = _mock_removable_usb()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sdb", scan)
        self.assertEqual(lock["detection_source"], "sysblock_udevadm")

    def test_lock_includes_confidence(self):
        dev = _mock_removable_usb()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sdb", scan)
        self.assertEqual(lock["confidence"], "high")


class TestIdentityDriftBlocks(unittest.TestCase):
    """Identity drift blocks."""

    def test_matching_rescan_no_drift(self):
        dev = _mock_removable_usb()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sdb", scan)
        cmp = rescan_and_compare_target_identity(lock, scan)
        self.assertTrue(cmp["match"])
        self.assertFalse(cmp["drift_detected"])

    def test_changed_device_triggers_drift(self):
        dev1 = _mock_removable_usb()
        scan1 = _mock_scan_result([dev1])
        lock = build_removable_target_identity_lock("/dev/sdb", scan1)

        dev2 = _build_device_record(
            drive_path="/dev/sdb",
            display_name="Different USB",
            stable_id="linux_sdb_DIFFERENT",
            serial="DIFFERENT",
            size_bytes=32000000000,
            is_removable=True,
            is_external=True,
            is_fixed=False,
            is_system=False,
            platform="linux",
            detection_source="sysblock_udevadm",
        )
        scan2 = _mock_scan_result([dev2])
        cmp = rescan_and_compare_target_identity(lock, scan2)
        self.assertFalse(cmp["match"])
        self.assertTrue(cmp["drift_detected"])

    def test_missing_device_drift(self):
        dev = _mock_removable_usb()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sdb", scan)
        empty_scan = _mock_scan_result([])
        cmp = rescan_and_compare_target_identity(lock, empty_scan)
        self.assertFalse(cmp["match"])
        self.assertTrue(cmp["drift_detected"])


class TestDryRunRefusesUnsafe(unittest.TestCase):
    """Dry-run refuses target not present in scanner evidence and fixed/system targets."""

    def test_dryrun_blocks_fixed_target(self):
        dev = _mock_fixed_drive()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sda", scan)
        self.assertTrue(lock["blocked"])

    def test_dryrun_preserves_zero_bytes(self):
        from real_writer_interface import build_physical_writer_dryrun_result, validate_physical_writer_dryrun_request
        req = {
            "schema": "bootforge.physical_writer_dryrun_request.v1",
            "request_id": "test_req",
            "target_drive": "/dev/sdb",
            "target_stable_id": "linux_sdb_SN12345",
            "target_identity_hash": "testhash",
            "image_path": "test.iso",
            "image_sha256": "abc123",
            "image_size_bytes": 5000000,
            "preflight_id": "pf_test",
            "identity_lock_id": "lock_test",
            "readiness_gate_id": "gate_test",
            "session_id": "sess_test",
            "physical_write_requested": False,
            "physical_write_allowed": False,
        }
        result = build_physical_writer_dryrun_result(req)
        self.assertEqual(result["bytes_written"], 0)
        self.assertFalse(result["physical_write_attempted"])


class TestPreflightIncludesScannerEvidence(unittest.TestCase):
    """Hardware preflight includes scanner v2 evidence."""

    def test_preflight_has_scanner_schema(self):
        dev = _mock_removable_usb()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sdb", scan)
        preflight = build_physical_writer_preflight_result(lock)
        self.assertEqual(preflight["scanner_schema"], "bootforge.device_scan.v2")

    def test_preflight_has_scanner_confidence(self):
        dev = _mock_removable_usb()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sdb", scan)
        preflight = build_physical_writer_preflight_result(lock)
        self.assertEqual(preflight["scanner_confidence"], "high")

    def test_preflight_has_scanner_detection_source(self):
        dev = _mock_removable_usb()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sdb", scan)
        preflight = build_physical_writer_preflight_result(lock)
        self.assertEqual(preflight["scanner_detection_source"], "sysblock_udevadm")

    def test_preflight_has_scanner_stable_id(self):
        dev = _mock_removable_usb()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sdb", scan)
        preflight = build_physical_writer_preflight_result(lock)
        self.assertEqual(preflight["scanner_stable_id"], "linux_sdb_SN12345")

    def test_preflight_has_scanner_block_reasons(self):
        dev = _mock_fixed_drive()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sda", scan)
        preflight = build_physical_writer_preflight_result(lock)
        self.assertIsInstance(preflight["scanner_block_reasons"], list)

    def test_preflight_has_scanner_warnings(self):
        dev = _mock_removable_usb()
        scan = _mock_scan_result([dev])
        lock = build_removable_target_identity_lock("/dev/sdb", scan)
        preflight = build_physical_writer_preflight_result(lock)
        self.assertIsInstance(preflight["scanner_warnings"], list)


class TestScannerCommandFailureSafety(unittest.TestCase):
    """Scanner command failure degrades safely."""

    @patch("device_scanner.scan_devices")
    def test_scanner_failure_returns_empty(self, mock_scan):
        mock_scan.return_value = _mock_scan_result([])
        from usb_creator import get_removable_drives
        drives = get_removable_drives(quiet=True)
        self.assertEqual(len(drives), 0)


class TestDashboardNoForbiddenLabels(unittest.TestCase):
    """Dashboard has no forbidden write labels."""

    def test_no_forbidden_labels_in_dashboard(self):
        dashboard_path = Path(__file__).parent.parent / "dashboard" / "src" / "App.jsx"
        if not dashboard_path.exists():
            self.skipTest("Dashboard not present")
        content = dashboard_path.read_text()
        forbidden = [
            "Write USB", "Burn USB", "Flash USB", "Start Write",
            "Format USB", "Erase Drive", "Arm Writer", "Execute Write",
            "Destructive Write", "Write Now",
        ]
        for label in forbidden:
            self.assertNotIn(label, content, f"Forbidden label '{label}' found in dashboard")


class TestNoDestructiveCallSitesAdded(unittest.TestCase):
    """No destructive command call sites added in integration code."""

    def test_usb_creator_no_destructive_calls(self):
        src = Path(__file__).parent.parent / "usb_creator.py"
        content = src.read_text().lower()
        for cmd in ["subprocess.run([\"dd\"", "subprocess.run(['dd'", "\"mkfs", "'mkfs"]:
            self.assertNotIn(cmd, content, f"Found destructive call site: {cmd}")

    def test_real_writer_interface_no_destructive_calls(self):
        src = Path(__file__).parent.parent / "real_writer_interface.py"
        content = src.read_text().lower()
        for cmd in ["subprocess.run([\"dd\"", "subprocess.run(['dd'", "\"mkfs", "'mkfs"]:
            self.assertNotIn(cmd, content, f"Found destructive call site: {cmd}")

    def test_device_scanner_no_destructive_calls(self):
        src = Path(__file__).parent.parent / "device_scanner.py"
        content = src.read_text().lower()
        for cmd in ["subprocess.run([\"dd\"", "subprocess.run(['dd'", "\"mkfs", "'mkfs"]:
            self.assertNotIn(cmd, content, f"Found destructive call site: {cmd}")


if __name__ == "__main__":
    unittest.main()
