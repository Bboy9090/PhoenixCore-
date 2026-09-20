import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARDWARE_DIR = ROOT / "scripts" / "hardware"
MODULE_PATH = HARDWARE_DIR / "find_windows_drive_by_stable_identity.py"
sys.path.insert(0, str(HARDWARE_DIR))

SPEC = importlib.util.spec_from_file_location("stable_target_locator", MODULE_PATH)
assert SPEC and SPEC.loader
stable_target_locator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stable_target_locator)


def raw_disk(number: int, serial: str, unique_id: str) -> dict:
    return {
        "Number": number,
        "FriendlyName": "Fixture USB",
        "SerialNumber": serial,
        "UniqueId": unique_id,
        "BusType": "USB",
        "SizeBytes": 64_000,
        "LogicalSectorSize": 512,
        "PhysicalSectorSize": 4096,
        "PartitionStyle": "GPT",
        "IsBoot": False,
        "IsSystem": False,
        "IsOffline": False,
        "IsReadOnly": False,
        "HealthStatus": "Healthy",
        "OperationalStatus": ["Online"],
        "Partitions": [],
    }


def stable_identity(raw: dict) -> str:
    import capture_windows_drive_evidence as drive_evidence

    target = rf"\\.\PHYSICALDRIVE{raw['Number']}"
    return drive_evidence.normalize_disk_record(raw, target)["stable_identity_sha256"]


class WindowsStableTargetLocatorTests(unittest.TestCase):
    def test_unique_match_survives_disk_number_change(self):
        original = raw_disk(7, "SERIAL-001", "UNIQUE-001")
        expected = stable_identity(original)
        moved = dict(original)
        moved["Number"] = 9
        other = raw_disk(3, "SERIAL-OTHER", "UNIQUE-OTHER")

        result = stable_target_locator.normalize_candidates([other, moved], expected)

        self.assertTrue(result["unique_match"])
        self.assertFalse(result["ambiguous"])
        self.assertEqual("unique_match", result["classification"])
        self.assertEqual(1, result["match_count"])
        self.assertEqual(r"\\.\PHYSICALDRIVE9", result["match"]["target"])
        self.assertEqual(expected, result["match"]["stable_identity_sha256"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["system_mutations_performed"])

    def test_no_match_is_explicit(self):
        expected = stable_identity(raw_disk(7, "SERIAL-001", "UNIQUE-001"))
        other = raw_disk(3, "SERIAL-OTHER", "UNIQUE-OTHER")

        result = stable_target_locator.normalize_candidates([other], expected)

        self.assertFalse(result["unique_match"])
        self.assertFalse(result["ambiguous"])
        self.assertEqual("not_found", result["classification"])
        self.assertEqual(0, result["match_count"])
        self.assertIsNone(result["match"])

    def test_duplicate_stable_identity_is_ambiguous(self):
        first = raw_disk(7, "SERIAL-001", "UNIQUE-001")
        expected = stable_identity(first)
        duplicate = dict(first)
        duplicate["Number"] = 9

        result = stable_target_locator.normalize_candidates([first, duplicate], expected)

        self.assertFalse(result["unique_match"])
        self.assertTrue(result["ambiguous"])
        self.assertEqual("ambiguous_multiple_matches", result["classification"])
        self.assertEqual(2, result["match_count"])
        self.assertIsNone(result["match"])

    def test_invalid_expected_digest_is_rejected(self):
        with self.assertRaises(stable_target_locator.StableIdentityLocatorError):
            stable_target_locator.normalize_candidates(
                [raw_disk(7, "SERIAL-001", "UNIQUE-001")],
                "bad",
            )


if __name__ == "__main__":
    unittest.main()
