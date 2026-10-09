import copy
import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "resume",
    Path(__file__).resolve().parents[1]
    / "scripts/hardware/assess_windows_media_resume.py",
)
resume = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(resume)


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.file = {
            "path": "sources/install.wim",
            "size_bytes": 4,
            "sha256": hashlib.sha256(b"real").hexdigest(),
        }
        entries = [self.file]
        self.source = {
            "files": entries,
            "manifest_sha256": hashlib.sha256(
                json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
        }
        self.target = {
            "stable_id": "usb-1",
            "serial_number": "serial-1",
            "capacity_bytes": 64 * 1024**3,
            "logical_sector_bytes": 512,
            "is_system": False,
            "is_read_only": False,
            "is_removable": True,
        }
        self.journal = {
            "schema": resume.SCHEMA,
            "operation_version": 1,
            "operation": "windows_installer_file_copy",
            "plan_sha256": "a" * 64,
            "state": "interrupted",
            "phase": "file_copy",
            "in_flight_mutation": False,
            "target_identity": copy.deepcopy(self.target),
            "source_manifest": copy.deepcopy(self.source),
            "completed_files": [self.file],
        }

    def assess(self, observations=None):
        return resume.assess_resume(
            self.journal,
            self.source,
            self.target,
            [self.file] if observations is None else observations,
            "a" * 64,
        )

    def test_eligible_is_not_authority_or_boot_proof(self):
        result = self.assess()
        self.assertTrue(result["resume_eligible"])
        self.assertEqual(result["verified_completed_bytes"], 4)
        for flag in (
            "automatic_resume_allowed",
            "boot_verified",
            "target_disk_modified",
        ):
            self.assertFalse(result[flag])
        self.assertTrue(result["requires_fresh_authorization"])

    def test_journal_hash_without_independent_readback_is_rejected(self):
        self.assertFalse(self.assess([])["resume_eligible"])

    def test_changed_target_and_system_disk_are_blocked(self):
        for key, value in (
            ("serial_number", "other"),
            ("is_system", True),
            ("is_removable", False),
        ):
            with self.subTest(key=key):
                old = self.target[key]
                self.target[key] = value
                self.assertFalse(self.assess()["resume_eligible"])
                self.target[key] = old

    def test_changed_source_bytes_are_blocked_even_with_valid_checksum(self):
        self.source["files"] = [{**self.file, "sha256": "b" * 64}]
        self.source["manifest_sha256"] = hashlib.sha256(
            json.dumps(
                self.source["files"], sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()
        self.assertIn("source_changed", self.assess()["block_reasons"])

    def test_unsafe_phases_and_active_writes_cannot_resume(self):
        for phase in ("partitioning", "image_application", "boot_configuration"):
            self.journal["phase"] = phase
            self.assertFalse(self.assess()["resume_eligible"])
        self.journal["phase"] = "file_copy"
        self.journal["in_flight_mutation"] = True
        self.assertFalse(self.assess()["resume_eligible"])

    def test_version_plan_and_running_state_are_blocked(self):
        for key, value in (
            ("operation_version", 2),
            ("plan_sha256", "c" * 64),
            ("state", "running"),
        ):
            old = self.journal[key]
            self.journal[key] = value
            self.assertFalse(self.assess()["resume_eligible"])
            self.journal[key] = old

    def test_duplicate_and_unaccounted_records_are_blocked(self):
        self.assertFalse(self.assess([self.file, self.file])["resume_eligible"])
        self.assertFalse(
            self.assess([self.file, {**self.file, "path": "extra"}])["resume_eligible"]
        )

    def test_unverified_files_remain_pending_without_claiming_progress(self):
        self.journal["completed_files"] = []
        result = self.assess([])
        self.assertTrue(result["resume_eligible"])
        self.assertEqual(result["verified_completed_bytes"], 0)
        self.assertEqual(result["remaining_files"], [self.file["path"]])


if __name__ == "__main__":
    unittest.main()
