"""Mocked collector contract tests; these do not prove Windows hardware behavior."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.hardware import plan_windows_install_target as planner


class InstallTargetContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "payload").write_bytes(b"source")
        self.manifest = planner.media.capture_media_manifest(self.root)
        self.target = r"\\.\PHYSICALDRIVE7"
        self.raw = {
            "Number": 7,
            "SerialNumber": "usb",
            "UniqueId": "usb-id",
            "BusType": "USB",
            "SizeBytes": 8 * planner.LAYOUT_RESERVE_BYTES,
            "IsBoot": False,
            "IsSystem": False,
            "IsOffline": False,
            "IsReadOnly": False,
            "Partitions": [{"IsBoot": False, "IsSystem": False}],
            "HealthStatus": "Healthy",
        }
        disk = planner.drives.normalize_disk_record(self.raw, self.target)
        self.snapshot = disk["identity_sha256"]
        self.stable = disk["stable_identity_sha256"]

    def run_plan(self, source=None):
        with patch.object(planner.sys, "platform", "win32"), patch.object(
            planner.drives, "query_windows_disk", return_value=self.raw
        ), patch.object(
            planner.sources,
            "query_source_disk",
            return_value=source
            or {
                "physical_target": r"\\.\PHYSICALDRIVE0",
                "stable_identity_sha256": "a" * 64,
            },
        ), patch.object(
            planner.media, "plan_media", return_value={"ready_for_fat32_copy_now": True}
        ):
            return planner.plan_install_target(
                self.root, self.manifest, self.target, self.snapshot, self.stable
            )

    def test_plan_bound_and_deterministic_without_authorization(self):
        result = self.run_plan()
        self.assertEqual(result, self.run_plan())
        self.assertTrue(result["eligible_for_preparation"])
        self.assertFalse(result["write_authorized"])
        self.assertFalse(result["boot_proven"])

    def test_flags_unknown_offline_and_partition_system_block(self):
        del self.raw["IsBoot"]
        self.raw["IsOffline"] = True
        self.raw["Partitions"] = [{"IsBoot": False, "IsSystem": True}]
        result = self.run_plan()
        self.assertFalse(result["eligible_for_preparation"])
        self.assertIn("target_isboot_unknown", result["block_reasons"])
        self.assertIn("target_isoffline", result["block_reasons"])

    def test_substitution_and_source_collision_block(self):
        self.raw["SerialNumber"] = "replacement"
        result = self.run_plan(
            {"physical_target": self.target, "stable_identity_sha256": self.stable}
        )
        self.assertIn("target_snapshot_identity_mismatch", result["block_reasons"])
        self.assertIn("source_target_physical_collision", result["block_reasons"])

    def test_source_change_rejected(self):
        (self.root / "payload").write_bytes(b"changed")
        with self.assertRaises(planner.media.MediaPlanError):
            self.run_plan()

    def test_capacity_includes_reserve(self):
        self.raw["SizeBytes"] = planner.LAYOUT_RESERVE_BYTES
        disk = planner.drives.normalize_disk_record(self.raw, self.target)
        self.snapshot = disk["identity_sha256"]
        self.stable = disk["stable_identity_sha256"]
        self.assertIn(
            "target_capacity_insufficient_with_layout_reserve",
            self.run_plan()["block_reasons"],
        )

    def test_non_windows_refuses_collection(self):
        with patch.object(planner.sys, "platform", "linux"), patch.object(
            planner.drives, "query_windows_disk"
        ) as collector:
            with self.assertRaises(RuntimeError):
                planner.plan_install_target(
                    self.root, self.manifest, self.target, self.snapshot, self.stable
                )
            collector.assert_not_called()

    def test_empty_raw_partition_inventory_not_assumed_success(self):
        self.raw["PartitionStyle"] = "RAW"
        self.raw["Partitions"] = []
        self.assertIn(
            "target_empty_partition_inventory_not_independently_proven",
            self.run_plan()["block_reasons"],
        )

    def test_cli_emits_plan_and_blocked_exit_status(self):
        manifest_path = self.root / "manifest-input.json"
        manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        args = [
            "--source-root",
            str(self.root),
            "--manifest",
            str(manifest_path),
            "--target",
            self.target,
            "--expected-snapshot-sha256",
            self.snapshot,
            "--expected-stable-sha256",
            self.stable,
        ]
        for eligible, expected_exit in ((True, 0), (False, 2)):
            output = io.StringIO()
            with patch.object(
                planner,
                "plan_install_target",
                return_value={"eligible_for_preparation": eligible},
            ), contextlib.redirect_stdout(output):
                self.assertEqual(planner.main(args), expected_exit)
            self.assertEqual(
                json.loads(output.getvalue())["eligible_for_preparation"], eligible
            )

    def test_cli_non_windows_returns_structured_failure(self):
        manifest_path = self.root / "manifest-input.json"
        manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        output = io.StringIO()
        with patch.object(planner.sys, "platform", "linux"), contextlib.redirect_stdout(
            output
        ):
            code = planner.main(
                [
                    "--source-root",
                    str(self.root),
                    "--manifest",
                    str(manifest_path),
                    "--target",
                    self.target,
                    "--expected-snapshot-sha256",
                    self.snapshot,
                    "--expected-stable-sha256",
                    self.stable,
                ]
            )
        self.assertEqual(code, 2)
        self.assertFalse(json.loads(output.getvalue())["write_authorized"])
