import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "resolve_windows_source_disk.py"
)
SPEC = importlib.util.spec_from_file_location(
    "windows_source_disk_resolution", MODULE_PATH
)
assert SPEC and SPEC.loader
windows_source_disk_resolution = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(windows_source_disk_resolution)


class WindowsSourceDiskResolutionTests(unittest.TestCase):
    def test_drive_letter_is_normalized(self):
        self.assertEqual(
            "E",
            windows_source_disk_resolution.source_drive_letter(r"e:\backups\image.wim"),
        )

    def test_non_drive_letter_path_is_rejected(self):
        with self.assertRaises(
            windows_source_disk_resolution.SourceDiskResolutionError
        ):
            windows_source_disk_resolution.source_drive_letter(
                r"\\server\share\image.wim"
            )

    def test_normalized_record_maps_to_physical_drive(self):
        record = windows_source_disk_resolution.normalize_source_disk_record(
            source_path=r"E:\backups\image.wim",
            drive_letter="E",
            disk_number=7,
            partition_number=2,
            friendly_name="USB Recovery Disk",
            serial_number="SERIAL-123",
            unique_id="UNIQUE-123",
            bus_type="USB",
            size_bytes=64_000,
        )
        self.assertEqual(r"\\.\PHYSICALDRIVE7", record["physical_target"])
        self.assertEqual("phoenix_key.windows_source_disk.v2", record["schema"])
        self.assertTrue(record["stable_identity_available"])
        self.assertEqual(64, len(record["stable_identity_sha256"]))
        self.assertTrue(record["resolved"])
        self.assertTrue(record["read_only"])

    def test_stable_source_identity_survives_disk_number_change(self):
        common = dict(
            source_path=r"E:\backups\image.wim",
            drive_letter="E",
            partition_number=2,
            friendly_name="USB Recovery Disk",
            serial_number="SERIAL-123",
            unique_id="UNIQUE-123",
            bus_type="USB",
            size_bytes=64_000,
        )
        first = windows_source_disk_resolution.normalize_source_disk_record(
            disk_number=7,
            **common,
        )
        moved = windows_source_disk_resolution.normalize_source_disk_record(
            disk_number=9,
            **common,
        )
        self.assertNotEqual(first["identity_sha256"], moved["identity_sha256"])
        self.assertEqual(
            first["stable_identity_sha256"],
            moved["stable_identity_sha256"],
        )

    def test_same_physical_device_is_blocked(self):
        record = windows_source_disk_resolution.normalize_source_disk_record(
            source_path=r"E:\image.wim",
            drive_letter="E",
            disk_number=7,
            partition_number=1,
        )
        result = windows_source_disk_resolution.compare_source_and_target(
            record, r"\\.\physicaldrive7"
        )
        self.assertTrue(result["blocked"])
        self.assertFalse(result["source_target_distinct"])
        self.assertEqual(
            "source-and-target-same-physical-device", result["block_reason"]
        )

    def test_different_physical_device_is_allowed_by_collision_check(self):
        record = windows_source_disk_resolution.normalize_source_disk_record(
            source_path=r"E:\image.wim",
            drive_letter="E",
            disk_number=7,
            partition_number=1,
        )
        result = windows_source_disk_resolution.compare_source_and_target(
            record, r"\\.\PHYSICALDRIVE8"
        )
        self.assertFalse(result["blocked"])
        self.assertTrue(result["source_target_distinct"])
        self.assertIsNone(result["block_reason"])


if __name__ == "__main__":
    unittest.main()
