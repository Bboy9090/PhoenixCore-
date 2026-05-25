import os
import sys
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Adjust path to import usb_creator from parent directory
sys.path.append(str(Path(__file__).parent.parent))
import usb_creator

class TestUSBCreator(unittest.TestCase):

    def test_default_download_dir(self):
        """Verify the cross-platform download directory pathing is generated correctly."""
        expected = Path.home() / "PhoenixCore" / "downloads"
        actual = usb_creator.get_default_download_dir()
        self.assertEqual(expected, actual)

    def test_create_rescue_usb_structure(self):
        """Verify directories and README.txt are safely and non-destructively created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Execute directories setup
            result = usb_creator.create_rescue_usb_structure(str(tmpdir_path))
            
            # Assert successful execution return code
            self.assertTrue(result)
            
            # Assert all 4 required directories were created
            expected_dirs = ["RescueTools", "BootCamp_Drivers", "OCLP_Patcher", "macOS_Installers"]
            for folder in expected_dirs:
                self.assertTrue((tmpdir_path / folder).is_dir())
                
            # Assert README instructions file is created and has correct contents
            readme = tmpdir_path / "README.txt"
            self.assertTrue(readme.is_file())
            content = readme.read_text(encoding="utf-8")
            self.assertIn("PhoenixCore Rescue USB System", content)
            self.assertIn("BootCamp_Drivers/", content)

    def test_create_rescue_usb_structure_invalid_path(self):
        """Verify structure creation logs failure and returns False for non-existent drives."""
        # Non-existent target directory
        invalid_path = "/nonexistent/drive/path/xyz"
        result = usb_creator.create_rescue_usb_structure(invalid_path)
        self.assertFalse(result)

    @patch("urllib.request.urlopen")
    @patch("urllib.request.urlretrieve")
    def test_download_latest_oclp_mocked(self, mock_retrieve, mock_urlopen):
        """Verify Dortania GitHub release parsing and download pipeline is accurate."""
        # Mock release metadata payload containing ZIP asset
        mock_payload = {
            "name": "v1.5.0 (Latest)",
            "assets": [
                {
                    "name": "OpenCore-Patcher-GUI.app.zip",
                    "browser_download_url": "https://github.com/dortania/OpenCore-Legacy-Patcher/releases/download/1.5.0/OpenCore-Patcher-GUI.app.zip"
                }
            ]
        }
        
        # Configure mocked urlopen response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_payload).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Call downloader
            result_path = usb_creator.download_latest_oclp(dest_dir=str(tmpdir_path))
            
            # Assert downloader targeted the correct file
            expected_dest = tmpdir_path / "OpenCore-Patcher-GUI.app.zip"
            self.assertEqual(str(expected_dest), result_path)
            
            # Assert urllib retriever was triggered with expected parameters
            mock_retrieve.assert_called_once_with(
                "https://github.com/dortania/OpenCore-Legacy-Patcher/releases/download/1.5.0/OpenCore-Patcher-GUI.app.zip",
                str(expected_dest)
            )

    @patch("sys.platform", "win32")
    @patch("ctypes.windll.kernel32.GetLogicalDrives")
    @patch("ctypes.windll.kernel32.GetDriveTypeW")
    @patch("ctypes.windll.kernel32.GetDiskFreeSpaceExW")
    @patch("ctypes.windll.kernel32.GetVolumeInformationW")
    def test_get_removable_drives_windows(self, mock_vol_info, mock_free_space, mock_drive_type, mock_drives_mask, *args):
        """Verify Windows logical drive search parses DRIVE_REMOVABLE disks correctly."""
        # Mock bitmask for drives: bit 3 set = Drive D:\
        mock_drives_mask.return_value = 8 
        
        # DRIVE_REMOVABLE = 2
        mock_drive_type.return_value = 2
        
        # Mock successful free space check
        mock_free_space.side_effect = lambda path, free, total, free_avail: True
        
        # Mock volume name
        mock_vol_info.side_effect = lambda path, buf, size, *args: setattr(buf, "value", "SanDiskRescue")

        drives = usb_creator.get_removable_drives()
        
        self.assertEqual(1, len(drives))
        self.assertEqual("D:\\", drives[0]["drive"])
        self.assertEqual("SanDiskRescue", drives[0]["label"])
        self.assertEqual("Removable", drives[0]["type"])

    @patch("sys.platform", "darwin")
    @patch("subprocess.check_output")
    def test_get_removable_drives_macos_empty(self, mock_subprocess):
        """Verify macOS disk list yields empty result gracefully if no external disks are attached."""
        # Mock empty AllDisks plist response
        mock_plist_list = b"""<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>AllDisks</key>
            <array/>
        </dict>
        </plist>"""
        
        mock_subprocess.return_value = mock_plist_list
        
        drives = usb_creator.get_removable_drives()
        self.assertEqual(0, len(drives))

if __name__ == "__main__":
    unittest.main()
