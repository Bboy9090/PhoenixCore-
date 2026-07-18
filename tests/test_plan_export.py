import sys
import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.append(str(Path(__file__).parent.parent))
import usb_creator


class TestPlanExport(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch("usb_creator.build_image_inspection_payload")
    @patch("usb_creator.build_drive_safety_payload")
    def test_export_success_json_and_markdown(
        self, mock_drive_safety, mock_image_inspect
    ):
        """Verify successful JSON and Markdown export for valid drive and image."""
        mock_drive_safety.return_value = {
            "schema": "bootforge.drive_safety.v1",
            "drive": {
                "requested_path": "E:\\",
                "root": "E:\\",
                "label": "USB Drive",
                "type": "Removable",
                "filesystem": "FAT32",
                "total_size_gb": 16.0,
                "free_size_gb": 15.0,
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
            "image": {
                "path": "debian.iso",
                "filename": "debian.iso",
                "extension": ".iso",
                "exists": True,
                "supported": True,
                "size_bytes": 1024 * 1024,
                "sha256": "abc123sha",
            },
            "error": None,
        }

        json_path = os.path.join(self.test_dir, "audit.json")
        md_path = os.path.join(self.test_dir, "audit.md")

        # 1. Test JSON export status payload
        json_res = usb_creator.build_audit_export_payload(
            "E:\\", "debian.iso", "json", json_path
        )
        self.assertEqual("success", json_res["status"])
        self.assertEqual("passed", json_res["audit_validation_status"])
        self.assertTrue(os.path.exists(json_path))

        with open(json_path, "r", encoding="utf-8") as f:
            saved_json = json.load(f)
            self.assertEqual("bootforge.write_plan_audit.v1", saved_json["schema"])
            self.assertEqual("passed", saved_json["validation_status"])

        # 2. Test Markdown export status payload
        md_res = usb_creator.build_audit_export_payload(
            "E:\\", "debian.iso", "markdown", md_path
        )
        self.assertEqual("success", md_res["status"])
        self.assertEqual("passed", md_res["audit_validation_status"])
        self.assertTrue(os.path.exists(md_path))

        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
            self.assertIn("PhoenixCore / BootForge Audit Evidence Report", md_content)
            self.assertIn(
                "This report is evidence of a dry-run audit only.", md_content
            )
            self.assertIn(
                "It does not indicate that a write, format, partition, or mount operation was performed.",
                md_content,
            )

    @patch("usb_creator.build_image_inspection_payload")
    @patch("usb_creator.build_drive_safety_payload")
    def test_export_blocks_if_output_exists(
        self, mock_drive_safety, mock_image_inspect
    ):
        """Export blocks if output path already exists (overwrite protection)."""
        mock_drive_safety.return_value = {
            "schema": "bootforge.drive_safety.v1",
            "drive": {"eligible_for_future_write": True, "warnings": []},
            "error": None,
        }
        mock_image_inspect.return_value = {
            "schema": "bootforge.image_inspection.v1",
            "image": {"exists": True, "supported": True, "sha256": "hash"},
            "error": None,
        }

        json_path = os.path.join(self.test_dir, "audit.json")
        # Create file in advance
        with open(json_path, "w") as f:
            f.write("{}")

        json_res = usb_creator.build_audit_export_payload(
            "E:\\", "debian.iso", "json", json_path
        )
        self.assertEqual("failed", json_res["status"])
        self.assertIn("already exists. Overwriting is blocked", json_res["error"])

    @patch("usb_creator.build_image_inspection_payload")
    @patch("usb_creator.build_drive_safety_payload")
    def test_export_blocks_if_on_target_drive(
        self, mock_drive_safety, mock_image_inspect
    ):
        """Export blocks if the output path resides on the target drive root."""
        mock_drive_safety.return_value = {
            "schema": "bootforge.drive_safety.v1",
            "drive": {"eligible_for_future_write": True, "warnings": []},
            "error": None,
        }
        mock_image_inspect.return_value = {
            "schema": "bootforge.image_inspection.v1",
            "image": {"exists": True, "supported": True, "sha256": "hash"},
            "error": None,
        }

        # Mock get_drive_root to simulate that target drive and export path reside on the same drive root (e.g. E:\)
        with patch("usb_creator.get_drive_root") as mock_root:
            mock_root.side_effect = lambda path: (
                "E:\\" if "E:" in str(path) or "audit" in str(path) else "/"
            )

            json_path = "E:\\audit.json"  # Resides on E:\
            json_res = usb_creator.build_audit_export_payload(
                "E:\\", "debian.iso", "json", json_path
            )

            self.assertEqual("failed", json_res["status"])
            self.assertIn("is on the target drive", json_res["error"])

    @patch("usb_creator.build_image_inspection_payload")
    @patch("usb_creator.build_drive_safety_payload")
    def test_export_blocks_if_extension_mismatch(
        self, mock_drive_safety, mock_image_inspect
    ):
        """Export blocks if extension does not match format (e.g. json format with .exe extension)."""
        mock_drive_safety.return_value = {
            "schema": "bootforge.drive_safety.v1",
            "drive": {"eligible_for_future_write": True, "warnings": []},
            "error": None,
        }
        mock_image_inspect.return_value = {
            "schema": "bootforge.image_inspection.v1",
            "image": {"exists": True, "supported": True, "sha256": "hash"},
            "error": None,
        }

        # JSON format with .exe
        bad_json_path = os.path.join(self.test_dir, "audit.exe")
        json_res = usb_creator.build_audit_export_payload(
            "E:\\", "debian.iso", "json", bad_json_path
        )
        self.assertEqual("failed", json_res["status"])
        self.assertIn("does not match format 'json'", json_res["error"])

        # Markdown format with .bat
        bad_md_path = os.path.join(self.test_dir, "audit.bat")
        md_res = usb_creator.build_audit_export_payload(
            "E:\\", "debian.iso", "markdown", bad_md_path
        )
        self.assertEqual("failed", md_res["status"])
        self.assertIn("does not match format 'markdown'", md_res["error"])

    @patch("usb_creator.build_image_inspection_payload")
    @patch("usb_creator.build_drive_safety_payload")
    def test_failed_audit_still_exports_correctly(
        self, mock_drive_safety, mock_image_inspect
    ):
        """Verify failed audits (blocked system drive or missing image) still write files successfully."""
        mock_drive_safety.return_value = {
            "schema": "bootforge.drive_safety.v1",
            "drive": {
                "requested_path": "C:\\",
                "root": "C:\\",
                "label": "SYSTEM",
                "type": "Fixed",
                "filesystem": "NTFS",
                "total_size_gb": 500.0,
                "free_size_gb": 100.0,
                "is_system_drive": True,
                "is_removable_or_external": False,
                "eligible_for_future_write": False,
                "risk_level": "high",
                "warnings": ["Drive is system drive."],
            },
            "error": None,
        }

        mock_image_inspect.return_value = {
            "schema": "bootforge.image_inspection.v1",
            "image": {
                "path": "nonexistent.iso",
                "filename": "nonexistent.iso",
                "extension": ".iso",
                "exists": False,
                "supported": True,
                "size_bytes": 0,
                "sha256": None,
            },
            "error": "Image path does not exist.",
        }

        json_path = os.path.join(self.test_dir, "failed_audit.json")
        md_path = os.path.join(self.test_dir, "failed_audit.md")

        with patch("usb_creator.get_drive_root") as mock_root:
            mock_root.side_effect = lambda path: (
                "C:\\" if str(path) == "C:\\" else "T:\\"
            )

            # Perform JSON export for failed plan
            json_res = usb_creator.build_audit_export_payload(
                "C:\\", "nonexistent.iso", "json", json_path
            )
            self.assertEqual("success", json_res["status"])
            self.assertEqual("failed", json_res["audit_validation_status"])
            self.assertTrue(os.path.exists(json_path))

            with open(json_path, "r", encoding="utf-8") as f:
                saved_json = json.load(f)
                self.assertEqual("failed", saved_json["validation_status"])
                self.assertFalse(saved_json["eligible"])
                self.assertTrue(saved_json["blocked"])

            # Perform Markdown export for failed plan
            md_res = usb_creator.build_audit_export_payload(
                "C:\\", "nonexistent.iso", "markdown", md_path
            )
            self.assertEqual("success", md_res["status"])
            self.assertEqual("failed", md_res["audit_validation_status"])
            self.assertTrue(os.path.exists(md_path))

            with open(md_path, "r", encoding="utf-8") as f:
                md_content = f.read()
                self.assertIn("validation status", md_content.lower())
                self.assertIn("\u274c failed", md_content.lower())
                self.assertIn(
                    "This report is evidence of a dry-run audit only.", md_content
                )
                self.assertIn(
                    "It does not indicate that a write, format, partition, or mount operation was performed.",
                    md_content,
                )

    @patch("usb_creator.build_image_inspection_payload")
    @patch("usb_creator.build_drive_safety_payload")
    def test_export_blocks_if_parent_directory_missing(
        self, mock_drive_safety, mock_image_inspect
    ):
        """Export blocks if the parent directory does not exist (no auto-creation)."""
        mock_drive_safety.return_value = {
            "schema": "bootforge.drive_safety.v1",
            "drive": {"eligible_for_future_write": True, "warnings": []},
            "error": None,
        }
        mock_image_inspect.return_value = {
            "schema": "bootforge.image_inspection.v1",
            "image": {"exists": True, "supported": True, "sha256": "hash"},
            "error": None,
        }

        bad_path = os.path.join(self.test_dir, "missing_subdir", "audit.json")
        json_res = usb_creator.build_audit_export_payload(
            "E:\\", "debian.iso", "json", bad_path
        )

        self.assertEqual("failed", json_res["status"])
        self.assertIn("directory of export path", json_res["error"])


if __name__ == "__main__":
    unittest.main()
