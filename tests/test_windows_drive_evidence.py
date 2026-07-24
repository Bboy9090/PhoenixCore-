import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "capture_windows_drive_evidence.py"
)
SPEC = importlib.util.spec_from_file_location("windows_drive_evidence", MODULE_PATH)
assert SPEC and SPEC.loader
windows_drive_evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(windows_drive_evidence)


class WindowsDriveEvidenceTests(unittest.TestCase):
    def setUp(self):
        fixture_path = Path(__file__).parent / "fixtures" / "windows_disk_usb.json"
        self.fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        self.target = r"\\.\PHYSICALDRIVE1"

    def test_exact_raw_target_is_required(self):
        self.assertEqual(1, windows_drive_evidence.parse_raw_target(self.target))
        for invalid in ("E:\\", "PHYSICALDRIVE1", r"\\.\PHYSICALDRIVE1\extra"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(windows_drive_evidence.EvidenceError):
                    windows_drive_evidence.parse_raw_target(invalid)

    def test_external_usb_fixture_is_candidate_but_not_validated(self):
        receipt = windows_drive_evidence.build_receipt(
            target=self.target,
            raw_disk=self.fixture,
            evidence_source="fixture",
            source_commit="a" * 40,
            captured_at="2026-07-24T01:00:00Z",
        )

        self.assertEqual("bws.physical-drive-evidence/v1", receipt["schema_version"])
        self.assertEqual("fixture-validated", receipt["classification"])
        self.assertTrue(receipt["disk"]["write_candidate"])
        self.assertEqual([], receipt["disk"]["write_block_reasons"])
        self.assertFalse(receipt["hardware_observed"])
        self.assertFalse(receipt["hardware_validated"])
        self.assertFalse(receipt["physical_write_attempted"])
        self.assertEqual(0, receipt["bytes_written"])
        self.assertEqual(64, len(receipt["disk"]["identity_sha256"]))
        self.assertEqual(64, len(receipt["receipt_sha256"]))

    def test_system_disk_is_never_a_write_candidate(self):
        fixture = dict(self.fixture)
        fixture.update(
            {
                "Number": 0,
                "BusType": "NVMe",
                "IsBoot": True,
                "IsSystem": True,
                "SerialNumber": "SYSTEM-DISK",
            }
        )
        receipt = windows_drive_evidence.build_receipt(
            target=r"\\.\PHYSICALDRIVE0",
            raw_disk=fixture,
            evidence_source="fixture",
            source_commit="b" * 40,
            captured_at="2026-07-24T01:00:00Z",
        )

        self.assertFalse(receipt["disk"]["write_candidate"])
        self.assertIn("target-is-boot-disk", receipt["disk"]["write_block_reasons"])
        self.assertIn("target-is-system-disk", receipt["disk"]["write_block_reasons"])
        self.assertIn(
            "target-not-proven-external-removable",
            receipt["disk"]["write_block_reasons"],
        )
        self.assertEqual("resolve-write-block-reasons", receipt["next_required_action"])

    def test_missing_stable_identity_blocks_candidate(self):
        fixture = dict(self.fixture)
        fixture["SerialNumber"] = None
        fixture["UniqueId"] = None
        record = windows_drive_evidence.normalize_disk_record(fixture, self.target)
        self.assertFalse(record["write_candidate"])
        self.assertIn("stable-device-identity-missing", record["write_block_reasons"])

    def test_nonzero_write_observation_is_rejected(self):
        with self.assertRaises(windows_drive_evidence.EvidenceError):
            windows_drive_evidence.build_receipt(
                target=self.target,
                raw_disk=self.fixture,
                evidence_source="fixture",
                source_commit="c" * 40,
                exclusive_probe={
                    "requested": True,
                    "status": "invalid-test-observation",
                    "raw_handle_opened": True,
                    "bytes_read": 0,
                    "bytes_written": 1,
                    "winerror": None,
                },
                captured_at="2026-07-24T01:00:00Z",
            )

    def test_atomic_receipt_round_trip(self):
        receipt = windows_drive_evidence.build_receipt(
            target=self.target,
            raw_disk=self.fixture,
            evidence_source="fixture",
            source_commit="d" * 40,
            captured_at="2026-07-24T01:00:00Z",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "evidence" / "drive.json"
            windows_drive_evidence.write_receipt_atomic(receipt, output)
            self.assertEqual(receipt, json.loads(output.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
