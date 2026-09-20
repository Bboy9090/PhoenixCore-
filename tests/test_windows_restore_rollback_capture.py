import binascii
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRIVE_MODULE_PATH = ROOT / "scripts" / "hardware" / "capture_windows_drive_evidence.py"
CAPTURE_MODULE_PATH = ROOT / "scripts" / "hardware" / "capture_windows_restore_rollback.py"

drive_spec = importlib.util.spec_from_file_location("windows_drive_evidence", DRIVE_MODULE_PATH)
assert drive_spec and drive_spec.loader
windows_drive_evidence = importlib.util.module_from_spec(drive_spec)
drive_spec.loader.exec_module(windows_drive_evidence)

capture_spec = importlib.util.spec_from_file_location("windows_restore_rollback", CAPTURE_MODULE_PATH)
assert capture_spec and capture_spec.loader
windows_restore_rollback = importlib.util.module_from_spec(capture_spec)
capture_spec.loader.exec_module(windows_restore_rollback)

SECTOR = 512
DISK_LBAS = 100
ENTRY_COUNT = 128
ENTRY_SIZE = 128
TABLE_BYTES = ENTRY_COUNT * ENTRY_SIZE
TABLE_SECTORS = TABLE_BYTES // SECTOR
TARGET = r"\\.\PHYSICALDRIVE7"


def gpt_header(*, current_lba, backup_lba, entries_lba, entries_crc):
    sector = bytearray(SECTOR)
    sector[0:8] = b"EFI PART"
    struct.pack_into("<I", sector, 8, 0x00010000)
    struct.pack_into("<I", sector, 12, 92)
    struct.pack_into("<I", sector, 16, 0)
    struct.pack_into("<I", sector, 20, 0)
    struct.pack_into("<Q", sector, 24, current_lba)
    struct.pack_into("<Q", sector, 32, backup_lba)
    struct.pack_into("<Q", sector, 40, 34)
    struct.pack_into("<Q", sector, 48, 66)
    sector[56:72] = bytes.fromhex("00112233445566778899aabbccddeeff")
    struct.pack_into("<Q", sector, 72, entries_lba)
    struct.pack_into("<I", sector, 80, ENTRY_COUNT)
    struct.pack_into("<I", sector, 84, ENTRY_SIZE)
    struct.pack_into("<I", sector, 88, entries_crc)
    crc = binascii.crc32(sector[:92]) & 0xFFFFFFFF
    struct.pack_into("<I", sector, 16, crc)
    return bytes(sector)


def synthetic_gpt_disk():
    image = bytearray(DISK_LBAS * SECTOR)
    image[510:512] = b"\x55\xaa"
    entries = bytes(TABLE_BYTES)
    entries_crc = binascii.crc32(entries) & 0xFFFFFFFF

    primary = gpt_header(
        current_lba=1,
        backup_lba=DISK_LBAS - 1,
        entries_lba=2,
        entries_crc=entries_crc,
    )
    backup_entries_lba = DISK_LBAS - 1 - TABLE_SECTORS
    backup = gpt_header(
        current_lba=DISK_LBAS - 1,
        backup_lba=1,
        entries_lba=backup_entries_lba,
        entries_crc=entries_crc,
    )

    image[SECTOR : 2 * SECTOR] = primary
    image[2 * SECTOR : (2 * SECTOR) + TABLE_BYTES] = entries
    backup_entries_offset = backup_entries_lba * SECTOR
    image[backup_entries_offset : backup_entries_offset + TABLE_BYTES] = entries
    backup_header_offset = (DISK_LBAS - 1) * SECTOR
    image[backup_header_offset : backup_header_offset + SECTOR] = backup
    return bytes(image)


def drive_receipt():
    raw = {
        "Number": 7,
        "FriendlyName": "Fixture GPT Disk",
        "SerialNumber": "RESTORE-TARGET-001",
        "UniqueId": "fixture-restore-target",
        "BusType": "USB",
        "SizeBytes": DISK_LBAS * SECTOR,
        "PartitionStyle": "GPT",
        "IsBoot": False,
        "IsSystem": False,
        "IsOffline": False,
        "IsReadOnly": False,
        "HealthStatus": "Healthy",
        "OperationalStatus": ["Online"],
        "Partitions": [
            {
                "PartitionNumber": 1,
                "DriveLetter": None,
                "Offset": 34 * SECTOR,
                "Size": 20 * SECTOR,
                "Type": "Basic",
                "GptType": "{EBD0A0A2-B9E5-4433-87C0-68B6B72699C7}",
                "MbrType": None,
                "IsBoot": False,
                "IsSystem": False,
            }
        ],
    }
    return windows_drive_evidence.build_receipt(
        target=TARGET,
        raw_disk=raw,
        evidence_source="fixture",
        source_commit="a" * 40,
        captured_at="2026-09-20T12:00:00Z",
    )


class WindowsRestoreRollbackCaptureTests(unittest.TestCase):
    def test_valid_gpt_capture_is_read_only_and_hashed(self):
        receipt = drive_receipt()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            disk_path = root / "disk.img"
            disk_path.write_bytes(synthetic_gpt_disk())
            output = root / "rollback"

            with disk_path.open("rb") as handle:
                artifacts, geometry = windows_restore_rollback.capture_gpt_artifacts(
                    handle=handle,
                    disk_size_bytes=DISK_LBAS * SECTOR,
                    logical_sector_size=SECTOR,
                    output_dir=output,
                )

            destination_identity = "c" * 64
            result = windows_restore_rollback.build_capture_receipt(
                target=TARGET,
                drive_evidence=receipt,
                output_dir=output,
                expected_target_snapshot_identity_sha256=receipt["disk"]["identity_sha256"],
                expected_target_stable_identity_sha256=receipt["disk"]["stable_identity_sha256"],
                expected_destination_stable_identity_sha256=destination_identity,
                destination_stable_identity_sha256=destination_identity,
                logical_sector_size=SECTOR,
                artifacts=artifacts,
                gpt_geometry=geometry,
                captured_at="2026-09-20T12:01:00Z",
            )

            self.assertFalse(result["restore_unlock_ready"])
            self.assertEqual([], result["restore_unlock_scope"])
            self.assertEqual(0, result["target_bytes_written"])
            self.assertFalse(result["target_write_attempted"])
            self.assertTrue(result["rollback_destination_files_written"])
            self.assertFalse(result["system_mutations_performed"])
            self.assertIn("target_partition_table_backup", result["captured_requirements"])
            self.assertIn("target_partition_manifest", result["captured_requirements"])
            self.assertIn("artifact_checksums", result["captured_requirements"])
            self.assertIn(
                "target_data_preservation_receipt_or_explicit_discard_decision",
                result["remaining_requirements"],
            )
            self.assertEqual(64, len(result["receipt_sha256"]))
            self.assertEqual(5, len([name for name in artifacts if name != "target_partition_manifest"]))
            for artifact in result["artifacts"].values():
                self.assertEqual(64, len(artifact["sha256"]))
                self.assertGreater(artifact["size_bytes"], 0)

    def test_partition_array_tamper_is_rejected(self):
        image = bytearray(synthetic_gpt_disk())
        image[(2 * SECTOR) + 7] ^= 0x01
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            disk_path = root / "disk.img"
            disk_path.write_bytes(image)
            with disk_path.open("rb") as handle:
                with self.assertRaises(windows_restore_rollback.RollbackCaptureError):
                    windows_restore_rollback.capture_gpt_artifacts(
                        handle=handle,
                        disk_size_bytes=DISK_LBAS * SECTOR,
                        logical_sector_size=SECTOR,
                        output_dir=root / "rollback",
                    )

    def test_same_destination_device_is_rejected(self):
        receipt = drive_receipt()
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            disk_path = root / "disk.img"
            disk_path.write_bytes(synthetic_gpt_disk())
            with disk_path.open("rb") as handle:
                artifacts, geometry = windows_restore_rollback.capture_gpt_artifacts(
                    handle=handle,
                    disk_size_bytes=DISK_LBAS * SECTOR,
                    logical_sector_size=SECTOR,
                    output_dir=root / "rollback",
                )
            stable = receipt["disk"]["stable_identity_sha256"]
            with self.assertRaises(windows_restore_rollback.RollbackCaptureError):
                windows_restore_rollback.build_capture_receipt(
                    target=TARGET,
                    drive_evidence=receipt,
                    output_dir=root / "rollback",
                    expected_target_snapshot_identity_sha256=receipt["disk"]["identity_sha256"],
                    expected_target_stable_identity_sha256=stable,
                    expected_destination_stable_identity_sha256=stable,
                    destination_stable_identity_sha256=stable,
                    logical_sector_size=SECTOR,
                    artifacts=artifacts,
                    gpt_geometry=geometry,
                )

    def test_tampered_drive_evidence_is_rejected(self):
        receipt = drive_receipt()
        receipt["disk"]["size_bytes"] += SECTOR
        with self.assertRaises(windows_restore_rollback.RollbackCaptureError):
            windows_restore_rollback.verify_drive_evidence(receipt)


if __name__ == "__main__":
    unittest.main()
