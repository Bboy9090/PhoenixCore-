import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.append(str(Path(__file__).parent.parent))
import usb_creator


class TestWritePlan(unittest.TestCase):
    @patch("usb_creator.build_image_inspection_payload")
    @patch("usb_creator.build_drive_safety_payload")
    def test_write_plan_success(self, mock_drive_safety, mock_image_inspect):
        """Verify successful dry-run plan generation for compatible target drive and image."""
        mock_drive_safety.return_value = {
            "schema": "bootforge.drive_safety.v1",
            "operation": "read_only_drive_safety_check",
            "drive": {
                "requested_path": "E:\\",
                "root": "E:\\",
                "label": "USB Key",
                "type": "Removable",
                "filesystem": "FAT32",
                "total_size_gb": 32.0,
                "free_size_gb": 30.0,
                "is_system_drive": False,
                "is_removable_or_external": True,
                "eligible_for_future_write": True,
                "risk_level": "low",
                "warnings": [],
            },
            "error": None,
        }

        mock_image_inspect.return_value = {
            "schema": "bootforge.image_inspection.v1",
            "operation": "read_only_image_inspection",
            "image": {
                "path": "debian.iso",
                "filename": "debian.iso",
                "extension": ".iso",
                "exists": True,
                "supported": True,
                "size_bytes": 1024 * 1024,
                "sha256": "abc123hash",
            },
            "error": None,
        }

        payload = usb_creator.build_write_plan_payload("E:\\", "debian.iso")

        self.assertEqual("bootforge.write_plan.v1", payload["schema"])
        self.assertTrue(payload["eligible"])
        self.assertFalse(payload["blocked"])
        self.assertEqual("low", payload["drive_safety"]["drive"]["risk_level"])
        self.assertEqual(6, len(payload["steps"]))
        self.assertEqual("verify_image", payload["steps"][0]["id"])
        self.assertEqual("planned", payload["steps"][0]["status"])

    @patch("usb_creator.build_image_inspection_payload")
    @patch("usb_creator.build_drive_safety_payload")
    def test_write_plan_blocked_system_drive(
        self, mock_drive_safety, mock_image_inspect
    ):
        """Verify plan is blocked when drive is not eligible (e.g. system boot drive)."""
        mock_drive_safety.return_value = {
            "schema": "bootforge.drive_safety.v1",
            "operation": "read_only_drive_safety_check",
            "drive": {
                "requested_path": "C:\\",
                "root": "C:\\",
                "label": "BOOTCAMP",
                "type": "Fixed",
                "filesystem": "NTFS",
                "total_size_gb": 500.0,
                "is_system_drive": True,
                "is_removable_or_external": False,
                "eligible_for_future_write": False,
                "risk_level": "high",
                "warnings": ["Drive is the system boot volume."],
            },
            "error": None,
        }

        mock_image_inspect.return_value = {
            "schema": "bootforge.image_inspection.v1",
            "operation": "read_only_image_inspection",
            "image": {
                "path": "debian.iso",
                "filename": "debian.iso",
                "extension": ".iso",
                "exists": True,
                "supported": True,
            },
            "error": None,
        }

        payload = usb_creator.build_write_plan_payload("C:\\", "debian.iso")

        self.assertFalse(payload["eligible"])
        self.assertTrue(payload["blocked"])
        self.assertIn("Drive is the system boot volume.", payload["block_reasons"][0])

    @patch("usb_creator.build_image_inspection_payload")
    @patch("usb_creator.build_drive_safety_payload")
    def test_write_plan_blocked_unsupported_image(
        self, mock_drive_safety, mock_image_inspect
    ):
        """Verify plan is blocked when image is unsupported or missing."""
        mock_drive_safety.return_value = {
            "schema": "bootforge.drive_safety.v1",
            "drive": {"eligible_for_future_write": True, "warnings": []},
            "error": None,
        }

        mock_image_inspect.return_value = {
            "schema": "bootforge.image_inspection.v1",
            "image": {
                "path": "invalid.txt",
                "filename": "invalid.txt",
                "extension": ".txt",
                "exists": True,
                "supported": False,
            },
            "error": None,
        }

        payload = usb_creator.build_write_plan_payload("E:\\", "invalid.txt")

        self.assertFalse(payload["eligible"])
        self.assertTrue(payload["blocked"])
        self.assertIn("not supported", payload["block_reasons"][0])


if __name__ == "__main__":
    unittest.main()
