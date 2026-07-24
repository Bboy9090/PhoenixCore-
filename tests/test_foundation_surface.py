import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import usb_creator


class FoundationSurfaceTests(unittest.TestCase):
    def test_sha256_identity(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"PhoenixCore foundation")
            path = Path(tmp.name)
        try:
            self.assertEqual(
                hashlib.sha256(b"PhoenixCore foundation").hexdigest(),
                usb_creator.calculate_file_sha256(path),
            )
        finally:
            path.unlink(missing_ok=True)

    @patch("usb_creator.get_normalized_scan")
    def test_drive_scan_payload_is_read_only(self, mock_scan):
        mock_scan.return_value = {
            "schema": "bootforge.device_scan.v2",
            "scan_id": "foundation-scan",
            "detection_source": "fixture",
            "device_count": 1,
            "devices": [
                {
                    "drive_path": "D:\\",
                    "display_name": "Sacrificial Test Drive",
                    "volume_label": "BWS-LAB",
                    "size_gb": 64.0,
                    "is_removable": True,
                    "is_external": False,
                }
            ],
            "scan_warnings": [],
        }

        payload = usb_creator.build_drive_scan_payload()

        self.assertEqual("bootforge.drive_scan.v2", payload["schema"])
        self.assertTrue(payload["safe_mode"])
        self.assertFalse(payload["destructive"])
        self.assertEqual("read_only_drive_scan", payload["operation"])
        self.assertEqual(1, len(payload["devices"]))

    @patch("usb_creator.get_normalized_scan")
    def test_rescue_structure_dry_run_writes_nothing(self, mock_scan):
        mock_scan.return_value = {
            "schema": "bootforge.device_scan.v2",
            "devices": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            target = Path(tmpdir) / "not-created"
            self.assertTrue(
                usb_creator.create_rescue_usb_structure(str(target), dry_run=True)
            )
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
