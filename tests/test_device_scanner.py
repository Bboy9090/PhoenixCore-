import unittest
import json
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.append(str(Path(__file__).parent.parent))

from device_scanner import (
    SCANNER_SCHEMA,
    _build_device_record,
    _human_size,
    parse_windows_scan_output,
    parse_macos_disk_list,
    parse_macos_disk_info,
    build_macos_device_from_info,
    read_sysfs_file,
    parse_udevadm_output,
    scan_linux_sysblock,
    scan_devices,
    get_device_by_path,
    get_eligible_devices,
)

MOCK_WINDOWS_PS_OUTPUT = json.dumps(
    [
        {
            "DeviceID": "\\\\.\\PHYSICALDRIVE1",
            "Model": "Kingston DataTraveler 3.0 USB Device",
            "SerialNumber": "KT123456789",
            "Size": 15728640000,
            "MediaType": "Removable Media",
            "InterfaceType": "USB",
            "Partitions": 1,
            "Status": "OK",
            "Caption": "Kingston DataTraveler 3.0 USB Device",
        },
        {
            "DeviceID": "\\\\.\\PHYSICALDRIVE0",
            "Model": "Samsung SSD 970 EVO",
            "SerialNumber": "S4EVNG0123456",
            "Size": 500107862016,
            "MediaType": "Fixed hard disk media",
            "InterfaceType": "SCSI",
            "Partitions": 4,
            "Status": "OK",
            "Caption": "Samsung SSD 970 EVO",
        },
    ]
)

MOCK_WINDOWS_SINGLE = json.dumps(
    {
        "DeviceID": "\\\\.\\PHYSICALDRIVE2",
        "Model": "SanDisk Ultra USB",
        "SerialNumber": "SD9876",
        "Size": 32000000000,
        "MediaType": "Removable Media",
        "InterfaceType": "USB",
        "Partitions": 1,
        "Status": "OK",
        "Caption": "SanDisk Ultra USB",
    }
)

MOCK_MACOS_LIST_PLIST = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>WholeDisks</key>
    <array>
        <string>disk2</string>
    </array>
</dict>
</plist>"""

MOCK_MACOS_INFO_PLIST = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>DeviceNode</key>
    <string>/dev/disk2</string>
    <key>Removable</key>
    <false/>
    <key>RemovableMedia</key>
    <true/>
    <key>External</key>
    <true/>
    <key>Internal</key>
    <false/>
    <key>SystemImage</key>
    <false/>
    <key>TotalSize</key>
    <integer>15728640000</integer>
    <key>MediaName</key>
    <string>Kingston DataTraveler 3.0</string>
    <key>VolumeName</key>
    <string>BOOTFORGE</string>
    <key>FilesystemType</key>
    <string>msdos</string>
    <key>BusProtocol</key>
    <string>USB</string>
    <key>IORegistryEntryName</key>
    <string>Kingston DataTraveler 3.0 Media</string>
</dict>
</plist>"""

MOCK_MACOS_SYSTEM_PLIST = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>DeviceNode</key>
    <string>/dev/disk0</string>
    <key>Removable</key>
    <false/>
    <key>RemovableMedia</key>
    <false/>
    <key>External</key>
    <false/>
    <key>Internal</key>
    <true/>
    <key>SystemImage</key>
    <true/>
    <key>TotalSize</key>
    <integer>500107862016</integer>
    <key>MediaName</key>
    <string>APPLE SSD</string>
</dict>
</plist>"""

MOCK_UDEVADM_OUTPUT = """DEVPATH=/devices/pci0000:00/0000:00:14.0/usb1/1-1/1-1:1.0/host0/target0:0:0/0:0:0:0/block/sdb
DEVNAME=/dev/sdb
DEVTYPE=disk
ID_SERIAL=Kingston_DataTraveler_3.0_KT123456789
ID_SERIAL_SHORT=KT123456789
ID_VENDOR=Kingston
ID_MODEL=DataTraveler_3.0
ID_BUS=usb
"""


class TestBuildDeviceRecord(unittest.TestCase):
    def test_removable_usb_eligible(self):
        rec = _build_device_record(
            drive_path="/dev/sdb",
            display_name="Kingston USB",
            stable_id="linux_sdb_KT123",
            serial="KT123",
            size_bytes=15728640000,
            is_removable=True,
            is_external=True,
            is_fixed=False,
            is_system=False,
        )
        self.assertTrue(rec["is_eligible"])
        self.assertEqual(rec["confidence"], "high")
        self.assertEqual(len(rec["block_reasons"]), 0)

    def test_fixed_internal_blocked(self):
        rec = _build_device_record(
            drive_path="/dev/sda",
            display_name="Samsung SSD",
            stable_id="linux_sda_S4EVN",
            serial="S4EVN",
            size_bytes=500107862016,
            is_removable=False,
            is_external=False,
            is_fixed=True,
            is_system=False,
        )
        self.assertFalse(rec["is_eligible"])
        self.assertTrue(any("fixed" in r.lower() for r in rec["block_reasons"]))

    def test_system_drive_blocked(self):
        rec = _build_device_record(
            drive_path="C:\\",
            display_name="System SSD",
            stable_id="win_0_SYS123",
            serial="SYS123",
            size_bytes=500107862016,
            is_removable=False,
            is_fixed=True,
            is_system=True,
        )
        self.assertFalse(rec["is_eligible"])
        self.assertTrue(any("system" in r.lower() for r in rec["block_reasons"]))

    def test_missing_serial_lowers_confidence(self):
        rec = _build_device_record(
            drive_path="/dev/sdb",
            display_name="No-serial USB",
            stable_id=None,
            serial=None,
            size_bytes=15728640000,
            is_removable=True,
            is_external=True,
            is_fixed=False,
            is_system=False,
        )
        self.assertEqual(rec["confidence"], "low")
        self.assertTrue(any("serial" in w.lower() for w in rec["warnings"]))

    def test_stable_id_only_medium_confidence(self):
        rec = _build_device_record(
            drive_path="/dev/sdb",
            display_name="USB Drive",
            stable_id="linux_sdb_fallback",
            serial=None,
            size_bytes=15728640000,
            is_removable=True,
            is_external=True,
            is_fixed=False,
            is_system=False,
        )
        self.assertEqual(rec["confidence"], "medium")

    def test_zero_size_blocked(self):
        rec = _build_device_record(
            drive_path="/dev/sdb",
            display_name="Empty USB",
            stable_id="linux_sdb_EMPTY",
            serial="EMPTY",
            size_bytes=0,
            is_removable=True,
            is_external=True,
            is_fixed=False,
            is_system=False,
        )
        self.assertFalse(rec["is_eligible"])
        self.assertTrue(any("zero" in r.lower() for r in rec["block_reasons"]))

    def test_large_external_drive_allowed_for_read_only_planning(self):
        rec = _build_device_record(
            drive_path="\\\\.\\PHYSICALDRIVE1",
            display_name="External Backup Drive",
            stable_id="win_1_BACKUP",
            serial="BACKUP",
            size_bytes=1000 * 1024**3,
            is_removable=True,
            is_external=True,
            is_fixed=False,
            is_system=False,
        )
        self.assertTrue(rec["is_eligible"])
        self.assertTrue(
            any("large-capacity" in warning.lower() for warning in rec["warnings"])
        )

    def test_all_normalized_fields_present(self):
        rec = _build_device_record(
            drive_path="/dev/sdb",
            display_name="Test",
            stable_id="test",
            serial="S123",
            size_bytes=1024,
            is_removable=True,
            is_external=True,
            is_fixed=False,
            is_system=False,
            filesystem="fat32",
            volume_label="BOOT",
            bus_protocol="USB",
            platform="linux",
            detection_source="test",
        )
        for field in [
            "drive_path",
            "display_name",
            "stable_id",
            "serial",
            "size_bytes",
            "size_gb",
            "size_human",
            "filesystem",
            "volume_label",
            "is_removable",
            "is_external",
            "is_fixed",
            "is_system",
            "bus_protocol",
            "platform",
            "detection_source",
            "confidence",
            "is_eligible",
            "warnings",
            "block_reasons",
        ]:
            self.assertIn(field, rec, f"Missing field: {field}")


class TestWindowsScanner(unittest.TestCase):
    def test_parse_multiple_disks(self):
        devices = parse_windows_scan_output(MOCK_WINDOWS_PS_OUTPUT)
        self.assertEqual(len(devices), 2)

        usb = next(d for d in devices if "Kingston" in d["display_name"])
        self.assertTrue(usb["is_removable"])
        self.assertTrue(usb["is_eligible"])
        self.assertEqual(usb["serial"], "KT123456789")
        self.assertEqual(usb["bus_protocol"], "USB")
        self.assertEqual(usb["detection_source"], "powershell_win32_diskdrive")

        ssd = next(d for d in devices if "Samsung" in d["display_name"])
        self.assertFalse(ssd["is_removable"])
        self.assertTrue(ssd["is_fixed"])
        self.assertFalse(ssd["is_eligible"])

    def test_parse_single_disk(self):
        devices = parse_windows_scan_output(MOCK_WINDOWS_SINGLE)
        self.assertEqual(len(devices), 1)
        self.assertTrue(devices[0]["is_removable"])

    def test_parse_empty_output(self):
        self.assertEqual(parse_windows_scan_output(""), [])
        self.assertEqual(parse_windows_scan_output(None), [])
        self.assertEqual(parse_windows_scan_output("not json"), [])

    def test_stable_id_includes_serial(self):
        devices = parse_windows_scan_output(MOCK_WINDOWS_SINGLE)
        self.assertIn("SD9876", devices[0]["stable_id"])


class TestMacOSScanner(unittest.TestCase):
    def test_parse_disk_list(self):
        disk_ids = parse_macos_disk_list(MOCK_MACOS_LIST_PLIST)
        self.assertEqual(disk_ids, ["disk2"])

    def test_parse_disk_info(self):
        info = parse_macos_disk_info(MOCK_MACOS_INFO_PLIST)
        self.assertEqual(info["DeviceNode"], "/dev/disk2")
        self.assertTrue(info["RemovableMedia"])
        self.assertTrue(info["External"])

    def test_build_removable_device(self):
        info = parse_macos_disk_info(MOCK_MACOS_INFO_PLIST)
        device = build_macos_device_from_info("disk2", info)
        self.assertTrue(device["is_removable"])
        self.assertTrue(device["is_external"])
        self.assertFalse(device["is_system"])
        self.assertTrue(device["is_eligible"])
        self.assertEqual(device["filesystem"], "msdos")
        self.assertEqual(device["volume_label"], "BOOTFORGE")
        self.assertEqual(device["bus_protocol"], "USB")
        self.assertEqual(device["detection_source"], "diskutil_plist")

    def test_build_system_device_blocked(self):
        info = parse_macos_disk_info(MOCK_MACOS_SYSTEM_PLIST)
        device = build_macos_device_from_info("disk0", info)
        self.assertFalse(device["is_eligible"])
        self.assertTrue(device["is_system"])
        self.assertTrue(any("system" in r.lower() for r in device["block_reasons"]))

    def test_parse_invalid_plist(self):
        self.assertEqual(parse_macos_disk_list(b"not a plist"), [])
        self.assertEqual(parse_macos_disk_info(b"not a plist"), {})


class TestLinuxScanner(unittest.TestCase):
    def test_parse_udevadm_output(self):
        props = parse_udevadm_output(MOCK_UDEVADM_OUTPUT)
        self.assertEqual(props["ID_SERIAL_SHORT"], "KT123456789")
        self.assertEqual(props["ID_VENDOR"], "Kingston")
        self.assertEqual(props["ID_BUS"], "usb")

    def test_parse_empty_udevadm(self):
        self.assertEqual(parse_udevadm_output(""), {})
        self.assertEqual(parse_udevadm_output(None), {})

    def test_read_sysfs_nonexistent(self):
        self.assertIsNone(
            read_sysfs_file("/sys/block/definitely_not_a_device/removable")
        )


class TestScanDevicesAPI(unittest.TestCase):
    @patch("device_scanner.scan_windows")
    def test_scan_windows_platform(self, mock_scan):
        mock_scan.return_value = (
            [
                _build_device_record(
                    drive_path="\\\\.\\PHYSICALDRIVE1",
                    display_name="USB Drive",
                    stable_id="win_1_SN",
                    serial="SN",
                    size_bytes=16000000000,
                    is_removable=True,
                    is_external=True,
                    is_fixed=False,
                    is_system=False,
                    platform="win32",
                    detection_source="powershell_win32_diskdrive",
                )
            ],
            [],
        )
        result = scan_devices(platform_override="win32")
        self.assertEqual(result["schema"], SCANNER_SCHEMA)
        self.assertEqual(result["platform"], "win32")
        self.assertEqual(result["device_count"], 1)
        self.assertTrue(result["safe_mode"])
        self.assertFalse(result["destructive"])

    @patch("device_scanner.scan_macos")
    def test_scan_macos_platform(self, mock_scan):
        mock_scan.return_value = ([], [])
        result = scan_devices(platform_override="darwin")
        self.assertEqual(result["platform"], "darwin")
        self.assertEqual(result["detection_source"], "diskutil_plist")

    @patch("device_scanner.scan_linux")
    def test_scan_linux_platform(self, mock_scan):
        mock_scan.return_value = ([], [])
        result = scan_devices(platform_override="linux")
        self.assertEqual(result["platform"], "linux")

    def test_unsupported_platform(self):
        result = scan_devices(platform_override="freebsd")
        self.assertEqual(result["device_count"], 0)
        self.assertTrue(any("Unsupported" in w for w in result["scan_warnings"]))

    def test_result_json_serializable(self):
        result = scan_devices(platform_override="freebsd")
        serialized = json.dumps(result)
        self.assertIsInstance(serialized, str)

    def test_scan_id_present(self):
        result = scan_devices(platform_override="freebsd")
        self.assertTrue(result["scan_id"].startswith("scan_"))
        self.assertIsNotNone(result["created_at"])


class TestGetDeviceByPath(unittest.TestCase):
    def test_find_existing_device(self):
        scan = {
            "devices": [
                {"drive_path": "/dev/sda", "display_name": "SSD"},
                {"drive_path": "/dev/sdb", "display_name": "USB"},
            ]
        }
        device = get_device_by_path(scan, "/dev/sdb")
        self.assertEqual(device["display_name"], "USB")

    def test_missing_device_returns_none(self):
        scan = {"devices": [{"drive_path": "/dev/sda"}]}
        self.assertIsNone(get_device_by_path(scan, "/dev/sdc"))


class TestGetEligibleDevices(unittest.TestCase):
    def test_filters_eligible_only(self):
        scan = {
            "devices": [
                {"drive_path": "/dev/sda", "is_eligible": False},
                {"drive_path": "/dev/sdb", "is_eligible": True},
                {"drive_path": "/dev/sdc", "is_eligible": True},
            ]
        }
        eligible = get_eligible_devices(scan)
        self.assertEqual(len(eligible), 2)


class TestAmbiguousTarget(unittest.TestCase):
    def test_plain_path_not_in_scan_returns_none(self):
        scan = {
            "devices": [
                {"drive_path": "/dev/sdb", "is_eligible": True},
            ]
        }
        self.assertIsNone(get_device_by_path(scan, "E:\\"))
        self.assertIsNone(get_device_by_path(scan, "/dev/disk2"))


class TestNoDestructiveCallSites(unittest.TestCase):
    def test_scanner_source_has_no_destructive_calls(self):
        scanner_path = Path(__file__).parent.parent / "device_scanner.py"
        with open(scanner_path, "r", encoding="utf-8") as f:
            content = f.read().lower()
        self.assertNotIn("diskpart", content)
        self.assertNotIn("mkfs", content)
        self.assertNotIn("unmount", content)
        self.assertNotIn("createfile", content)
        self.assertNotIn("writefile", content)
        self.assertNotIn("deviceiocontrol", content)


class TestDashboardNoForbiddenLabels(unittest.TestCase):
    def test_dashboard_has_no_forbidden_labels(self):
        dashboard_path = Path(__file__).parent.parent / "dashboard" / "src" / "App.jsx"
        if not dashboard_path.exists():
            self.skipTest("Dashboard source not found")
        with open(dashboard_path, "r", encoding="utf-8") as f:
            content = f.read()
        forbidden = [
            "Write USB",
            "Burn USB",
            "Flash USB",
            "Start Write",
            "Format USB",
            "Erase Drive",
            "Arm Writer",
            "Execute Write",
            "Destructive Write",
            "Write Now",
        ]
        for label in forbidden:
            self.assertNotIn(label, content, f"Forbidden label found: {label}")


class TestCommandFailureSafety(unittest.TestCase):
    @patch("device_scanner.scan_windows")
    def test_windows_failure_returns_safe_result(self, mock_scan):
        mock_scan.return_value = ([], ["PowerShell scan failed (code 1): error"])
        result = scan_devices(platform_override="win32")
        self.assertEqual(result["device_count"], 0)
        self.assertTrue(len(result["scan_warnings"]) > 0)
        self.assertEqual(result["schema"], SCANNER_SCHEMA)

    @patch("device_scanner.scan_macos")
    def test_macos_failure_returns_safe_result(self, mock_scan):
        mock_scan.return_value = ([], ["diskutil failed"])
        result = scan_devices(platform_override="darwin")
        self.assertEqual(result["device_count"], 0)
        self.assertTrue(len(result["scan_warnings"]) > 0)

    @patch("device_scanner.scan_linux")
    def test_linux_failure_returns_safe_result(self, mock_scan):
        mock_scan.return_value = ([], ["sysblock read failed"])
        result = scan_devices(platform_override="linux")
        self.assertEqual(result["device_count"], 0)


class TestHumanSize(unittest.TestCase):
    def test_zero(self):
        self.assertEqual(_human_size(0), "0 B")

    def test_bytes(self):
        self.assertEqual(_human_size(500), "500.0 B")

    def test_gigabytes(self):
        result = _human_size(15728640000)
        self.assertIn("GB", result)


if __name__ == "__main__":
    unittest.main()
