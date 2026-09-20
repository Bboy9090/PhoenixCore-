import importlib.util
import json
import unittest
from pathlib import Path

CAPTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "capture_windows_drive_evidence.py"
)
COMPARE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "compare_windows_drive_reenumeration.py"
)

capture_spec = importlib.util.spec_from_file_location(
    "windows_drive_evidence", CAPTURE_PATH
)
assert capture_spec and capture_spec.loader
windows_drive_evidence = importlib.util.module_from_spec(capture_spec)
capture_spec.loader.exec_module(windows_drive_evidence)

compare_spec = importlib.util.spec_from_file_location(
    "windows_drive_reenumeration", COMPARE_PATH
)
assert compare_spec and compare_spec.loader
windows_drive_reenumeration = importlib.util.module_from_spec(compare_spec)
compare_spec.loader.exec_module(windows_drive_reenumeration)


class WindowsDriveReenumerationTests(unittest.TestCase):
    def setUp(self):
        fixture_path = Path(__file__).parent / "fixtures" / "windows_disk_usb.json"
        self.fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    def receipt(self, number: int, serial: str | None = None):
        fixture = json.loads(json.dumps(self.fixture))
        fixture["Number"] = number
        if serial is not None:
            fixture["SerialNumber"] = serial
        return windows_drive_evidence.build_receipt(
            target=rf"\\.\PHYSICALDRIVE{number}",
            raw_disk=fixture,
            evidence_source="fixture",
            source_commit="a" * 40,
            captured_at="2026-09-20T01:00:00Z",
        )

    def test_same_snapshot_keeps_identity_continuity(self):
        before = self.receipt(1)
        after = self.receipt(1)
        result = windows_drive_reenumeration.compare_receipts(before, after)
        self.assertEqual("same-hardware-same-snapshot", result["classification"])
        self.assertTrue(result["same_hardware"])
        self.assertTrue(result["snapshot_identity_matches"])
        self.assertTrue(result["stable_identity_matches"])
        self.assertTrue(result["snapshot_continuity_verified"])
        self.assertFalse(result["stale_authorization_reusable"])
        self.assertTrue(result["fresh_snapshot_authorization_required"])
        self.assertFalse(result["system_mutations_performed"])

    def test_reenumeration_keeps_hardware_but_invalidates_snapshot_authorization(self):
        before = self.receipt(1)
        after = self.receipt(7)
        result = windows_drive_reenumeration.compare_receipts(before, after)
        self.assertEqual("same-hardware-reenumerated", result["classification"])
        self.assertTrue(result["same_hardware"])
        self.assertFalse(result["snapshot_identity_matches"])
        self.assertTrue(result["stable_identity_matches"])
        self.assertTrue(result["reenumerated"])
        self.assertFalse(result["stale_authorization_reusable"])
        self.assertTrue(result["fresh_snapshot_authorization_required"])
        self.assertEqual(
            "discard-stale-authorization-and-revalidate-fresh-snapshot",
            result["required_action"],
        )

    def test_different_capture_code_revisions_require_recapture(self):
        before = self.receipt(1)
        after = self.receipt(7)
        after["source_commit"] = "b" * 40
        canonical = dict(after)
        canonical.pop("receipt_sha256", None)
        after["receipt_sha256"] = windows_drive_reenumeration.sha256_payload(canonical)

        result = windows_drive_reenumeration.compare_receipts(before, after)
        self.assertEqual(
            "evidence-software-version-mismatch",
            result["classification"],
        )
        self.assertFalse(result["source_commit_matches"])
        self.assertFalse(result["comparison_trusted"])
        self.assertFalse(result["hardware_validation_complete"])
        self.assertEqual(
            "recapture-before-and-after-with-same-code-revision",
            result["required_action"],
        )

    def test_hardware_substitution_is_blocked(self):
        before = self.receipt(1)
        after = self.receipt(1, serial="DIFFERENT-DEVICE-SERIAL")
        result = windows_drive_reenumeration.compare_receipts(before, after)
        self.assertEqual(
            "hardware-substitution-or-mismatch",
            result["classification"],
        )
        self.assertFalse(result["same_hardware"])
        self.assertFalse(result["stable_identity_matches"])
        self.assertFalse(result["stale_authorization_reusable"])

    def test_tampered_receipt_is_rejected(self):
        before = self.receipt(1)
        after = self.receipt(1)
        after["disk"]["size_bytes"] += 1
        with self.assertRaises(windows_drive_reenumeration.ComparisonError):
            windows_drive_reenumeration.compare_receipts(before, after)

    def test_fixture_evidence_never_claims_real_hardware_validation(self):
        result = windows_drive_reenumeration.compare_receipts(
            self.receipt(1),
            self.receipt(7),
        )
        self.assertFalse(result["real_hardware_evidence"])
        self.assertFalse(result["hardware_validation_complete"])


if __name__ == "__main__":
    unittest.main()
