import sys
import unittest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.append(str(Path(__file__).parent.parent))
import usb_creator


class TestPlanAudit(unittest.TestCase):
    @patch("usb_creator.build_image_inspection_payload")
    @patch("usb_creator.build_drive_safety_payload")
    def test_audit_success(self, mock_drive_safety, mock_image_inspect):
        """Verify audit passes with clean drive and OS image inputs."""
        mock_drive_safety.return_value = {
            "schema": "bootforge.drive_safety.v1",
            "operation": "read_only_drive_safety_check",
            "drive": {
                "requested_path": "E:\\",
                "root": "E:\\",
                "label": "USB Key",
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
            "operation": "read_only_image_inspection",
            "image": {
                "path": "test.iso",
                "filename": "test.iso",
                "extension": ".iso",
                "exists": True,
                "supported": True,
                "size_bytes": 5000000000,
                "sha256": "439ea89255a8286a117b38d3883a9925e0892a09c256037a39d82bfdf16a908a",
            },
            "error": None,
        }

        payload = usb_creator.build_write_plan_audit_payload("E:\\", "test.iso")

        self.assertEqual("bootforge.write_plan_audit.v1", payload["schema"])
        self.assertEqual("passed", payload["validation_status"])
        self.assertTrue(payload["eligible"])
        self.assertFalse(payload["blocked"])
        self.assertTrue(payload["safe_mode"])
        self.assertFalse(payload["destructive"])
        self.assertIsNotNone(payload["plan_hash"])
        self.assertTrue(payload["plan_id"].startswith("bootforge-plan-"))

        # Verify all safety checklist checks passed
        for check in payload["checks"]:
            self.assertTrue(
                check["passed"], f"Check {check['id']} failed but should have passed"
            )

    @patch("usb_creator.build_write_plan_payload")
    def test_audit_fails_if_step_is_destructive(self, mock_write_plan):
        """Audit fails if any write plan step has destructive=true."""
        mock_write_plan.return_value = {
            "schema": "bootforge.write_plan.v1",
            "generated_at": "2026-06-19T20:00:00Z",
            "platform": sys.platform,
            "safe_mode": True,
            "destructive": False,
            "operation": "dry_run_write_plan",
            "actual_write_enabled": False,
            "requires_future_confirmation": True,
            "target_drive": "E:\\",
            "image_path": "test.iso",
            "eligible": True,
            "blocked": False,
            "block_reasons": [],
            "drive_safety": {"drive": {"eligible_for_future_write": True}},
            "image_inspection": {
                "image": {"exists": True, "supported": True, "sha256": "mocksha"}
            },
            "steps": [
                {
                    "id": "unsafe_nuke",
                    "label": "Accidental format",
                    "status": "planned",
                    "destructive": True,
                }
            ],
            "error": None,
        }

        payload = usb_creator.build_write_plan_audit_payload("E:\\", "test.iso")

        self.assertEqual("failed", payload["validation_status"])
        self.assertFalse(payload["eligible"])
        self.assertTrue(payload["blocked"])

        # Verify no_destructive_steps check failed
        destructive_check = next(
            (c for c in payload["checks"] if c["id"] == "no_destructive_steps"), None
        )
        self.assertIsNotNone(destructive_check)
        self.assertFalse(destructive_check["passed"])

        # Verify block reason list contains the safety failure
        self.assertTrue(
            any(
                "Safety Check Failed: All plan steps are non-destructive" in r
                for r in payload["block_reasons"]
            )
        )

    @patch("usb_creator.build_image_inspection_payload")
    @patch("usb_creator.build_drive_safety_payload")
    def test_audit_hash_stability(self, mock_drive_safety, mock_image_inspect):
        """Verify that the generated plan_hash is stable and deterministic."""
        drive_data = {
            "schema": "bootforge.drive_safety.v1",
            "operation": "read_only_drive_safety_check",
            "drive": {
                "requested_path": "E:\\",
                "root": "E:\\",
                "label": "USB Key",
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

        image_data = {
            "schema": "bootforge.image_inspection.v1",
            "operation": "read_only_image_inspection",
            "image": {
                "path": "test.iso",
                "filename": "test.iso",
                "extension": ".iso",
                "exists": True,
                "supported": True,
                "size_bytes": 5000000000,
                "sha256": "439ea89255a8286a117b38d3883a9925e0892a09c256037a39d82bfdf16a908a",
            },
            "error": None,
        }

        mock_drive_safety.return_value = drive_data
        mock_image_inspect.return_value = image_data

        payload_1 = usb_creator.build_write_plan_audit_payload("E:\\", "test.iso")

        # Re-run after altering a volatile, non-canonical field in mocked write plan response
        # E.g. simulated utc_now_iso will change generated_at timestamp.
        # The underlying code strips generated_at when doing hashing, so altering generated_at in
        # our simulated payload must NOT change the resulting hash.

        # We patch utc_now_iso to return different timestamps
        with patch("usb_creator.utc_now_iso") as mock_time:
            mock_time.return_value = "2026-06-19T20:15:00Z"
            payload_2 = usb_creator.build_write_plan_audit_payload("E:\\", "test.iso")

            mock_time.return_value = "2026-06-19T21:30:00Z"
            payload_3 = usb_creator.build_write_plan_audit_payload("E:\\", "test.iso")

        self.assertEqual(payload_1["plan_hash"], payload_2["plan_hash"])
        self.assertEqual(payload_1["plan_hash"], payload_3["plan_hash"])
        self.assertEqual(payload_1["plan_id"], payload_2["plan_id"])
        self.assertEqual(payload_1["plan_id"], payload_3["plan_id"])

    @patch("usb_creator.build_image_inspection_payload")
    @patch("usb_creator.build_drive_safety_payload")
    def test_audit_blocked_for_unsafe_targets(
        self, mock_drive_safety, mock_image_inspect
    ):
        """Verify audit still produces a full payload even when target drive is blocked or image is invalid."""
        mock_drive_safety.return_value = {
            "schema": "bootforge.drive_safety.v1",
            "operation": "read_only_drive_safety_check",
            "drive": {
                "requested_path": "C:\\",
                "root": "C:\\",
                "label": "SYSTEM",
                "type": "Fixed",
                "filesystem": "NTFS",
                "total_size_gb": 500.0,
                "free_size_gb": 200.0,
                "is_system_drive": True,
                "is_removable_or_external": False,
                "eligible_for_future_write": False,
                "risk_level": "high",
                "warnings": [
                    "Drive is the system boot volume. Writing is strictly blocked for safety."
                ],
            },
            "error": None,
        }

        mock_image_inspect.return_value = {
            "schema": "bootforge.image_inspection.v1",
            "operation": "read_only_image_inspection",
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

        payload = usb_creator.build_write_plan_audit_payload("C:\\", "nonexistent.iso")

        self.assertEqual("bootforge.write_plan_audit.v1", payload["schema"])
        self.assertEqual("failed", payload["validation_status"])
        self.assertFalse(payload["eligible"])
        self.assertTrue(payload["blocked"])
        self.assertTrue(len(payload["block_reasons"]) > 0)

        # Verify check flags
        safety_check = next(
            c for c in payload["checks"] if c["id"] == "drive_safety_eligible"
        )
        image_check = next(
            c for c in payload["checks"] if c["id"] == "image_inspection_valid"
        )

        self.assertFalse(safety_check["passed"])
        self.assertFalse(image_check["passed"])


if __name__ == "__main__":
    unittest.main()
