import unittest
import os
import json
import tempfile
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from real_writer_interface import (
    build_removable_target_identity_lock,
    validate_removable_target_identity_lock,
    rescan_and_compare_target_identity,
    build_physical_writer_preflight_result,
    validate_hardware_preflight_export_path,
    export_hardware_preflight_json,
    export_hardware_preflight_markdown
)

class TestHardwareWriterPreflight(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)
        
    def test_01_hardware_preflight_schema(self):
        """1. Hardware preflight schema is bootforge.hardware_writer_preflight.v1."""
        lock = build_removable_target_identity_lock("E:\\")
        preflight = build_physical_writer_preflight_result(lock)
        self.assertEqual(preflight["schema"], "bootforge.hardware_writer_preflight.v1")

    def test_02_identity_lock_schema(self):
        """2. Identity lock schema is bootforge.removable_target_identity_lock.v1."""
        lock = build_removable_target_identity_lock("E:\\")
        self.assertEqual(lock["schema"], "bootforge.removable_target_identity_lock.v1")

    def test_03_identity_lock_id_is_deterministic(self):
        """3. Identity lock ID is deterministic."""
        l1 = build_removable_target_identity_lock("E:\\")
        l2 = build_removable_target_identity_lock("E:\\")
        self.assertEqual(l1["identity_lock_id"], l2["identity_lock_id"])
        self.assertTrue(l1["identity_lock_id"].startswith("lock_"))

    def test_04_identity_lock_blocks_fixed_internal_targets(self):
        """4. Identity lock blocks internal fixed targets."""
        scan = {
            "drives": [
                {
                    "path": "C:\\",
                    "is_fixed": True,
                    "is_system_drive": False,
                    "device_identity_hash": "fixed_hash",
                    "size_bytes": 100000
                }
            ]
        }
        lock = build_removable_target_identity_lock("C:\\", scan)
        self.assertTrue(lock["blocked"])
        self.assertIn("Target drive is fixed/internal.", lock["block_reasons"])

    def test_05_identity_lock_blocks_missing_identity_hash(self):
        """5. Identity lock blocks missing identity hash."""
        scan = {
            "drives": [
                {
                    "path": "E:\\",
                    "is_fixed": False,
                    "is_removable": True,
                    "device_identity_hash": None,
                    "size_bytes": 100000
                }
            ]
        }
        lock = build_removable_target_identity_lock("E:\\", scan)
        self.assertTrue(lock["blocked"])
        self.assertIn("Target identity hash is missing.", lock["block_reasons"])

    def test_06_identity_lock_blocks_missing_size(self):
        """6. Identity lock blocks missing size."""
        scan = {
            "drives": [
                {
                    "path": "E:\\",
                    "is_fixed": False,
                    "is_removable": True,
                    "device_identity_hash": "some_hash",
                    "size_bytes": 0
                }
            ]
        }
        lock = build_removable_target_identity_lock("E:\\", scan)
        self.assertTrue(lock["blocked"])
        self.assertIn("Target size is unknown or invalid.", lock["block_reasons"])

    def test_07_identity_lock_passes_mock_removable_target(self):
        """7. Identity lock passes for valid mock target."""
        scan = {
            "drives": [
                {
                    "path": "E:\\",
                    "is_fixed": False,
                    "is_removable": True,
                    "device_identity_hash": "valid_hash",
                    "size_bytes": 1024000
                }
            ]
        }
        lock = build_removable_target_identity_lock("E:\\", scan)
        self.assertFalse(lock["blocked"])
        self.assertTrue(validate_removable_target_identity_lock(lock))

    def test_08_preflight_preserves_physical_writer_allowed_false(self):
        """8. Preflight preserves physical_writer_allowed false."""
        lock = build_removable_target_identity_lock("E:\\")
        preflight = build_physical_writer_preflight_result(lock)
        self.assertFalse(preflight["physical_writer_allowed"])

    def test_09_preflight_preserves_physical_write_attempted_false(self):
        """9. Preflight preserves physical_write_attempted false."""
        lock = build_removable_target_identity_lock("E:\\")
        preflight = build_physical_writer_preflight_result(lock)
        self.assertFalse(preflight["physical_write_attempted"])

    def test_10_preflight_blocks_identity_drift(self):
        """10. Preflight detects identity hash mismatch."""
        scan1 = {
            "drives": [
                {
                    "path": "E:\\",
                    "is_fixed": False,
                    "is_removable": True,
                    "device_identity_hash": "hash1",
                    "size_bytes": 1000
                }
            ]
        }
        scan2 = {
            "drives": [
                {
                    "path": "E:\\",
                    "is_fixed": False,
                    "is_removable": True,
                    "device_identity_hash": "hash2",
                    "size_bytes": 1000
                }
            ]
        }
        lock = build_removable_target_identity_lock("E:\\", scan1)
        cmp_res = rescan_and_compare_target_identity(lock, scan2)
        self.assertTrue(cmp_res["drift_detected"])
        self.assertFalse(cmp_res["match"])

    def test_11_rescan_compare_passes_when_matches(self):
        """11. Re-scan match check passes when identity hash matches."""
        scan = {
            "drives": [
                {
                    "path": "E:\\",
                    "is_fixed": False,
                    "is_removable": True,
                    "device_identity_hash": "hash1",
                    "size_bytes": 1000
                }
            ]
        }
        lock = build_removable_target_identity_lock("E:\\", scan)
        cmp_res = rescan_and_compare_target_identity(lock, scan)
        self.assertTrue(cmp_res["match"])
        self.assertFalse(cmp_res["drift_detected"])

    def test_12_json_export_writes_evidence(self):
        """12. Export JSON builds and writes JSON evidence."""
        lock = build_removable_target_identity_lock("E:\\")
        preflight = build_physical_writer_preflight_result(lock)
        out_path = os.path.join(self.test_dir, "preflight.json")
        res = export_hardware_preflight_json(preflight, out_path)
        self.assertEqual(res["status"], "success")
        self.assertTrue(os.path.exists(out_path))

    def test_13_markdown_export_writes_evidence(self):
        """13. Export Markdown builds and writes Markdown evidence."""
        lock = build_removable_target_identity_lock("E:\\")
        preflight = build_physical_writer_preflight_result(lock)
        out_path = os.path.join(self.test_dir, "preflight.md")
        res = export_hardware_preflight_markdown(preflight, out_path)
        self.assertEqual(res["status"], "success")
        self.assertTrue(os.path.exists(out_path))

    def test_14_export_rejects_raw_device_paths(self):
        """14. Export rejects raw UNC namespace and raw device paths before resolve."""
        bad_paths = [
            "\\\\.\\PhysicalDrive0\\preflight.json",
            "//./PhysicalDrive0/preflight.json"
        ]
        for p in bad_paths:
            with self.assertRaises(ValueError):
                validate_hardware_preflight_export_path(p, "json")

    def test_15_export_rejects_target_drive_root(self):
        """15. Export rejects target-drive root path."""
        with self.assertRaises(ValueError):
            validate_hardware_preflight_export_path("E:\\preflight.json", "json", "E:\\")

    def test_16_cli_preflight_returns_json(self):
        """16. CLI hardware preflight check outputs valid JSON."""
        import subprocess
        cmd = [
            sys.executable,
            "usb_creator.py",
            "--hardware-writer-preflight",
            "--target-drive", "E:\\"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["schema"], "bootforge.hardware_writer_preflight.v1")

    def test_17_dashboard_source_excludes_forbidden_labels(self):
        """17. Dashboard App.jsx source must not contain forbidden UI labels."""
        app_jsx_path = os.path.join(Path(__file__).parent.parent, "dashboard", "src", "App.jsx")
        if os.path.exists(app_jsx_path):
            with open(app_jsx_path, "r", encoding="utf-8") as f:
                content = f.read()
            FORBIDDEN = [
                "Write USB", "Burn USB", "Flash USB", "Start Write",
                "Format USB", "Erase Drive", "Arm Writer", "Execute Write",
                "Destructive Write", "Write Now"
            ]
            for phrase in FORBIDDEN:
                # App.jsx may contain the list of forbidden phrases to test against,
                # but it should not have them as UI button titles.
                self.assertNotIn(f">{phrase}<", content)

if __name__ == "__main__":
    unittest.main()
