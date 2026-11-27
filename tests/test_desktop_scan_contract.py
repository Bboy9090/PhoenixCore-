"""Read-only desktop contract tests; scanner fixtures are isolated and not hardware evidence."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "desktop_suite"))
import app_engine
import usb_creator

class DesktopContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        bundle = Path(self.tmp.name)
        (bundle / "real_app").mkdir()
        (bundle / "real_app" / "index.html").write_text("<html>fixture</html>", encoding="utf-8")
        self.client = app_engine.create_app(bundle, {"title": "Test fixture"}).test_client()
        self.payload = {"schema": "bootforge.drive_scan.v2", "operation": "read_only_drive_scan",
                        "destructive": False, "drives": [], "scan_warnings": []}

    def test_empty_success_is_json(self):
        with patch.object(usb_creator, "build_drive_scan_payload", return_value=self.payload) as scan:
            r = self.client.get("/api/usb/scan")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.is_json)
        self.assertEqual(r.json, self.payload)
        scan.assert_called_once_with()

    def test_incomplete_scan_is_failure(self):
        with patch.object(usb_creator, "build_drive_scan_payload",
                          return_value={**self.payload, "scan_warnings": ["scanner failed"]}):
            r = self.client.get("/api/usb/scan")
        self.assertEqual(r.status_code, 503)
        self.assertIn("error", r.json)

    def test_exception_is_failure(self):
        with patch.object(usb_creator, "build_drive_scan_payload", side_effect=RuntimeError("fixture")):
            r = self.client.get("/api/usb/scan")
        self.assertEqual(r.status_code, 503)
        self.assertTrue(r.is_json)

    def test_invalid_payload_is_rejected(self):
        with patch.object(usb_creator, "build_drive_scan_payload", return_value={"drives": []}):
            r = self.client.get("/api/usb/scan")
        self.assertEqual(r.status_code, 502)

    def test_unknown_api_never_returns_spa(self):
        r = self.client.get("/api/not-implemented")
        self.assertEqual(r.status_code, 404)
        self.assertTrue(r.is_json)

    def test_missing_asset_never_returns_spa(self):
        for path in ("/assets/missing.glb", "/missing.js"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_spa_navigation_still_works(self):
        r = self.client.get("/dashboard")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"<html>", r.data)

    def test_capacity_does_not_masquerade_as_free_space(self):
        scan = {"devices": [{"is_removable": True, "size_gb": 32, "drive_path": "fixture"}]}
        with patch.object(usb_creator, "get_normalized_scan", return_value=scan):
            result = usb_creator.build_drive_scan_payload()
        self.assertEqual(result["drives"][0]["total_size_gb"], 32)
        self.assertIsNone(result["drives"][0]["free_size_gb"])

if __name__ == "__main__":
    unittest.main()
