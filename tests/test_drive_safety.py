import sys
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.append(str(Path(__file__).parent.parent))
import usb_creator


class TestDriveSafety(unittest.TestCase):
    @patch("sys.platform", "win32")
    @patch("usb_creator.get_normalized_scan")
    @patch("os.path.exists")
    def test_windows_physical_drive_resolves_from_trusted_scanner(
        self, mock_exists, mock_scan
    ):
        mock_scan.return_value = {
            "devices": [
                {
                    "drive_path": "\\\\.\\PHYSICALDRIVE1",
                    "display_name": "Kingston USB",
                    "volume_label": None,
                    "filesystem": None,
                    "size_gb": 32.0,
                    "is_removable": True,
                    "is_external": True,
                    "is_fixed": False,
                    "is_system": False,
                    "is_eligible": True,
                    "block_reasons": [],
                    "confidence": "high",
                    "stable_id": "win32_disk1_SN",
                    "detection_source": "powershell_win32_diskdrive",
                }
            ]
        }

        payload = usb_creator.build_drive_safety_payload("\\\\.\\PHYSICALDRIVE1")

        mock_exists.assert_not_called()
        self.assertIsNone(payload["error"])
        self.assertEqual("\\\\.\\PHYSICALDRIVE1", payload["drive"]["root"])
        self.assertTrue(payload["drive"]["eligible_for_future_write"])
        self.assertEqual("high", payload["drive"]["confidence"])

    @patch("sys.platform", "win32")
    @patch("usb_creator.get_normalized_scan")
    def test_windows_physical_drive_missing_from_scanner_fails_closed(self, mock_scan):
        mock_scan.return_value = {"devices": []}

        payload = usb_creator.build_drive_safety_payload("\\\\.\\PHYSICALDRIVE7")

        self.assertIsNone(payload["drive"])
        self.assertIn("trusted Windows scanner evidence", payload["error"])

    @patch("sys.platform", "win32")
    @patch("usb_creator.get_normalized_scan")
    def test_windows_large_physical_drive_preserves_capacity_block(self, mock_scan):
        mock_scan.return_value = {
            "devices": [
                {
                    "drive_path": "\\\\.\\PHYSICALDRIVE1",
                    "display_name": "JMicron Tech SCSI Disk Device",
                    "size_gb": 931.5,
                    "is_removable": True,
                    "is_external": True,
                    "is_fixed": False,
                    "is_system": False,
                    "is_eligible": False,
                    "block_reasons": [
                        "Drive capacity exceeds the 256.0 GB safety limit for removable media."
                    ],
                    "confidence": "high",
                    "stable_id": "win32_disk1_SN",
                    "detection_source": "powershell_win32_diskdrive",
                }
            ]
        }

        payload = usb_creator.build_drive_safety_payload("\\\\.\\PHYSICALDRIVE1")

        self.assertIsNone(payload["error"])
        self.assertFalse(payload["drive"]["eligible_for_future_write"])
        self.assertTrue(
            any("256.0 GB" in warning for warning in payload["drive"]["warnings"])
        )

    @patch("sys.platform", "win32")
    @patch("usb_creator.build_image_inspection_payload")
    @patch("usb_creator.get_normalized_scan")
    def test_write_plan_accepts_scanner_proven_physical_drive(
        self, mock_scan, mock_image
    ):
        mock_scan.return_value = {
            "devices": [
                {
                    "drive_path": "\\\\.\\PHYSICALDRIVE1",
                    "display_name": "SanDisk USB",
                    "size_gb": 32.0,
                    "is_removable": True,
                    "is_external": True,
                    "is_fixed": False,
                    "is_system": False,
                    "is_eligible": True,
                    "block_reasons": [],
                    "confidence": "high",
                    "stable_id": "win32_disk1_SN",
                    "detection_source": "powershell_win32_diskdrive",
                }
            ]
        }
        mock_image.return_value = {
            "error": None,
            "image": {
                "exists": True,
                "supported": True,
                "extension": ".iso",
            },
        }

        payload = usb_creator.build_write_plan_payload(
            "\\\\.\\PHYSICALDRIVE1", "C:\\images\\phoenix.iso"
        )

        self.assertTrue(payload["eligible"])
        self.assertFalse(payload["blocked"])
        self.assertEqual([], payload["block_reasons"])
        self.assertFalse(payload["actual_write_enabled"])

    @patch("sys.platform", "win32")
    @patch("os.path.exists")
    @patch("ctypes.windll.kernel32.GetDriveTypeW")
    @patch("ctypes.windll.kernel32.GetVolumeInformationW")
    @patch("ctypes.windll.kernel32.GetDiskFreeSpaceExW")
    @patch("ctypes.byref", lambda x: x)
    @patch("usb_creator.get_removable_drives")
    @patch("os.environ", {"SystemDrive": "C:"})
    def test_windows_system_boot_drive(
        self,
        mock_get_removable,
        mock_free_space,
        mock_volume_info,
        mock_drive_type,
        mock_exists,
    ):
        """Verify Windows system drive (C:) is flagged as high risk and blocked from writing."""
        mock_exists.return_value = True
        mock_drive_type.return_value = 3  # DRIVE_FIXED
        mock_get_removable.return_value = []

        def vol_side_effect(path, vol_buf, vol_size, p1, p2, p3, fs_buf, fs_size):
            vol_buf.value = "BOOTCAMP"
            fs_buf.value = "NTFS"
            return True

        mock_volume_info.side_effect = vol_side_effect

        def space_side_effect(path, p1, total_bytes, free_bytes):
            total_bytes.value = 465 * (1024**3)
            free_bytes.value = 100 * (1024**3)
            return True

        mock_free_space.side_effect = space_side_effect

        payload = usb_creator.build_drive_safety_payload("C:\\")

        self.assertEqual("bootforge.drive_safety.v1", payload["schema"])
        self.assertFalse(payload["drive"]["eligible_for_future_write"])
        self.assertEqual("high", payload["drive"]["risk_level"])
        self.assertTrue(payload["drive"]["is_system_drive"])
        self.assertFalse(payload["drive"]["is_removable_or_external"])
        self.assertTrue(
            any("system boot volume" in w for w in payload["drive"]["warnings"])
        )

    @patch("sys.platform", "win32")
    @patch("os.path.exists")
    @patch("ctypes.windll.kernel32.GetDriveTypeW")
    @patch("ctypes.windll.kernel32.GetVolumeInformationW")
    @patch("ctypes.windll.kernel32.GetDiskFreeSpaceExW")
    @patch("ctypes.byref", lambda x: x)
    @patch("usb_creator.get_removable_drives")
    @patch("os.environ", {"SystemDrive": "C:"})
    def test_windows_eligible_removable_drive(
        self,
        mock_get_removable,
        mock_free_space,
        mock_volume_info,
        mock_drive_type,
        mock_exists,
    ):
        """Verify an external removable drive under 64 GB is eligible and low risk."""
        mock_exists.return_value = True
        mock_drive_type.return_value = 2  # DRIVE_REMOVABLE
        mock_get_removable.return_value = [
            {
                "drive": "E:\\",
                "label": "USB Drive",
                "total_size_gb": 32.0,
                "free_size_gb": 30.0,
                "type": "Removable",
            }
        ]

        def vol_side_effect(path, vol_buf, vol_size, p1, p2, p3, fs_buf, fs_size):
            vol_buf.value = "USB Drive"
            fs_buf.value = "FAT32"
            return True

        mock_volume_info.side_effect = vol_side_effect

        def space_side_effect(path, p1, total_bytes, free_bytes):
            total_bytes.value = 32 * (1024**3)
            free_bytes.value = 30 * (1024**3)
            return True

        mock_free_space.side_effect = space_side_effect

        payload = usb_creator.build_drive_safety_payload("E:\\")

        self.assertTrue(payload["drive"]["eligible_for_future_write"])
        self.assertEqual("low", payload["drive"]["risk_level"])
        self.assertTrue(payload["drive"]["is_removable_or_external"])
        self.assertEqual(0, len(payload["drive"]["warnings"]))

    @patch("sys.platform", "win32")
    @patch("os.path.exists")
    @patch("ctypes.windll.kernel32.GetDriveTypeW")
    @patch("ctypes.windll.kernel32.GetVolumeInformationW")
    @patch("ctypes.windll.kernel32.GetDiskFreeSpaceExW")
    @patch("ctypes.byref", lambda x: x)
    @patch("usb_creator.get_removable_drives")
    @patch("os.environ", {"SystemDrive": "C:"})
    def test_windows_large_blocked_removable_drive(
        self,
        mock_get_removable,
        mock_free_space,
        mock_volume_info,
        mock_drive_type,
        mock_exists,
    ):
        """Verify a removable drive > 256 GB is blocked and flagged as high risk (backup safety rule)."""
        mock_exists.return_value = True
        mock_drive_type.return_value = 2  # DRIVE_REMOVABLE
        mock_get_removable.return_value = [
            {
                "drive": "F:\\",
                "label": "My Backup",
                "total_size_gb": 500.0,
                "free_size_gb": 100.0,
                "type": "Removable",
            }
        ]

        def vol_side_effect(path, vol_buf, vol_size, p1, p2, p3, fs_buf, fs_size):
            vol_buf.value = "My Backup"
            fs_buf.value = "NTFS"
            return True

        mock_volume_info.side_effect = vol_side_effect

        def space_side_effect(path, p1, total_bytes, free_bytes):
            total_bytes.value = 500 * (1024**3)
            free_bytes.value = 100 * (1024**3)
            return True

        mock_free_space.side_effect = space_side_effect

        payload = usb_creator.build_drive_safety_payload("F:\\")

        self.assertFalse(payload["drive"]["eligible_for_future_write"])
        self.assertEqual("high", payload["drive"]["risk_level"])
        self.assertTrue(
            any(
                "Writing is blocked to protect personal backups" in w
                for w in payload["drive"]["warnings"]
            )
        )

    @patch("sys.platform", "win32")
    @patch("os.path.exists")
    @patch("ctypes.windll.kernel32.GetDriveTypeW")
    @patch("ctypes.windll.kernel32.GetVolumeInformationW")
    @patch("ctypes.windll.kernel32.GetDiskFreeSpaceExW")
    @patch("ctypes.byref", lambda x: x)
    @patch("usb_creator.get_removable_drives")
    @patch("os.environ", {"SystemDrive": "C:"})
    def test_windows_small_blocked_drive(
        self,
        mock_get_removable,
        mock_free_space,
        mock_volume_info,
        mock_drive_type,
        mock_exists,
    ):
        """Verify a drive < 2 GB is blocked and high risk."""
        mock_exists.return_value = True
        mock_drive_type.return_value = 2  # DRIVE_REMOVABLE
        mock_get_removable.return_value = [
            {
                "drive": "G:\\",
                "label": "Tiny Key",
                "total_size_gb": 1.5,
                "free_size_gb": 0.5,
                "type": "Removable",
            }
        ]

        def vol_side_effect(path, vol_buf, vol_size, p1, p2, p3, fs_buf, fs_size):
            vol_buf.value = "Tiny Key"
            fs_buf.value = "FAT16"
            return True

        mock_volume_info.side_effect = vol_side_effect

        def space_side_effect(path, p1, total_bytes, free_bytes):
            total_bytes.value = int(1.5 * (1024**3))
            free_bytes.value = int(0.5 * (1024**3))
            return True

        mock_free_space.side_effect = space_side_effect

        payload = usb_creator.build_drive_safety_payload("G:\\")

        self.assertFalse(payload["drive"]["eligible_for_future_write"])
        self.assertEqual("high", payload["drive"]["risk_level"])
        self.assertTrue(
            any("below the minimum required" in w for w in payload["drive"]["warnings"])
        )

    @patch("sys.platform", "linux")
    @patch("os.path.exists")
    @patch("shutil.disk_usage")
    @patch("usb_creator.get_removable_drives")
    def test_posix_system_root(self, mock_removable, mock_disk_usage, mock_exists):
        """Verify POSIX system root is blocked and high risk."""
        mock_exists.return_value = True
        mock_removable.return_value = []

        mock_usage = MagicMock()
        mock_usage.total = 100 * (1024**3)
        mock_usage.free = 50 * (1024**3)
        mock_disk_usage.return_value = mock_usage

        payload = usb_creator.build_drive_safety_payload("/")

        self.assertFalse(payload["drive"]["eligible_for_future_write"])
        self.assertEqual("high", payload["drive"]["risk_level"])
        self.assertTrue(
            any("system boot volume" in w for w in payload["drive"]["warnings"])
        )


if __name__ == "__main__":
    unittest.main()
