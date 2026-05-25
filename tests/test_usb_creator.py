import os
import sys
import json
import unittest
import tempfile
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

# Adjust path to import usb_creator from parent directory
sys.path.append(str(Path(__file__).parent.parent))
import usb_creator

class TestUSBCreator(unittest.TestCase):

    def test_default_download_dir(self):
        """Verify the cross-platform download directory pathing is generated correctly."""
        expected = Path.home() / "PhoenixCore" / "downloads"
        actual = usb_creator.get_default_download_dir()
        self.assertEqual(expected, actual)

    def test_calculate_file_sha256(self):
        """Verify standard SHA256 checksum computation logic matches expected hashes."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            # Content: "PhoenixCore"
            tmp.write(b"PhoenixCore")
            
        try:
            # Expected sha256 of "PhoenixCore"
            expected_hash = hashlib.sha256(b"PhoenixCore").hexdigest()
            actual_hash = usb_creator.calculate_file_sha256(tmp_path)
            self.assertEqual(expected_hash, actual_hash)
        finally:
            # Clean up temp file
            if tmp_path.exists():
                tmp_path.unlink()

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

    def test_create_rescue_usb_structure_dry_run(self):
        """Verify dry-run mode creates absolutely ZERO files or directories on disk."""
        # Target a path that does not exist and should not be created
        simulated_path = "/nonexistent/dry/run/target/path"
        
        # Run in dry-run mode
        result = usb_creator.create_rescue_usb_structure(simulated_path, dry_run=True)
        
        # Assert returned True (since simulation ran successfully)
        self.assertTrue(result)
        
        # Verify absolutely no folders were actually written to disk
        self.assertFalse(Path(simulated_path).exists())

    def test_create_rescue_usb_structure_invalid_path(self):
        """Verify structure creation logs failure and returns False for non-existent drives."""
        # Non-existent target directory (without dry-run)
        invalid_path = "/nonexistent/drive/path/xyz"
        result = usb_creator.create_rescue_usb_structure(invalid_path, dry_run=False)
        self.assertFalse(result)

    @patch("urllib.request.urlopen")
    @patch("urllib.request.urlretrieve")
    def test_download_latest_oclp_mocked(self, mock_retrieve, mock_urlopen):
        """Verify Dortania GitHub release parsing, download, and checksum pipelines are accurate."""
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

        # Mock calculate_file_sha256 to prevent reading non-existent file
        with patch("usb_creator.calculate_file_sha256") as mock_sha:
            mock_sha.return_value = "1339b694899a0aec51dd32b20f9e7b84df6be08aac56837a94d2bfaf806c155e"
            
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

    def test_download_latest_oclp_dry_run(self):
        """Verify downloader dry-run skips network requests and logs expected output."""
        simulated_dir = "/mock/downloads"
        
        # Run downloader in dry-run mode
        result_path = usb_creator.download_latest_oclp(dest_dir=simulated_dir, dry_run=True)
        
        # Assert path returned is mapped inside target directory
        expected_path = Path(simulated_dir) / "OpenCore-Patcher-GUI.app.zip"
        self.assertEqual(str(expected_path), result_path)
        
        # Verify absolutely no directories or files were written to disk
        self.assertFalse(Path(simulated_dir).exists())

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

    def test_tool_registry_manifest(self):
        """Verify the manifests/tool_registry.json exists, parses cleanly, and maps correct schemas."""
        registry_path = Path(__file__).parent.parent / "manifests" / "tool_registry.json"
        self.assertTrue(registry_path.is_file(), "tool_registry.json manifest file must exist!")
        
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Assert core headers exist
            self.assertIn("name", data)
            self.assertIn("version", data)
            self.assertIn("tools", data)
            
            # Assert tools list has populated entries
            tools = data["tools"]
            self.assertGreater(len(tools), 0)
            
            for tool in tools:
                self.assertIn("id", tool)
                self.assertIn("name", tool)
                self.assertIn("version", tool)
                self.assertIn("expected_sha256", tool)
                self.assertIn("download_url", tool)
                self.assertTrue(isinstance(tool["verified"], bool))
        except Exception as e:
            self.fail(f"Failed parsing tool_registry.json manifest: {e}")

    def test_validate_tool_against_registry_unknown_tool(self):
        """Verify registry rejects unknown/unregistered tools immediately."""
        result = usb_creator.validate_tool_against_registry("malicious-unregistered-tool")
        self.assertFalse(result)

    def test_validate_tool_against_registry_url_mismatch(self):
        """Verify registry rejects tools with unapproved or altered download URLs."""
        tool_id = "opencore-legacy-patcher"
        bad_url = "https://untrusted-domain.com/hacked-patcher.zip"
        result = usb_creator.validate_tool_against_registry(tool_id, download_url=bad_url)
        self.assertFalse(result)

    @patch("usb_creator.calculate_file_sha256")
    def test_validate_tool_against_registry_checksum_success(self, mock_sha):
        """Verify registry validates and approves matching cryptographic checksums."""
        tool_id = "opencore-legacy-patcher"
        mock_sha.return_value = "1339b694899a0aec51dd32b20f9e7b84df6be08aac56837a94d2bfaf806c155e"
        
        # Create a mock empty file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            
        try:
            result = usb_creator.validate_tool_against_registry(tool_id, file_path=tmp_path)
            self.assertTrue(result)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_validate_tool_against_registry_checksum_failure(self):
        """Verify registry throws critical failure and rejects mismatched cryptographic signatures."""
        tool_id = "opencore-legacy-patcher"
        
        # Write custom content to cause checksum mismatch (expected empty file hash)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(b"untrusted hacked content")
            
        try:
            result = usb_creator.validate_tool_against_registry(tool_id, file_path=tmp_path)
            self.assertFalse(result)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_load_tool_registry_signature_success(self):
        """Verify the standard registry manifest detached signature verification is successful."""
        registry = usb_creator.load_tool_registry()
        self.assertIsNotNone(registry)
        self.assertEqual("BootForge Trusted Recovery Tool Registry", registry.get("name"))

    def test_load_tool_registry_signature_failure_on_tamper(self):
        """Verify that tampering with the tool registry JSON causes a critical security halt (SystemExit)."""
        registry_path = Path(usb_creator.__file__).parent / "manifests" / "tool_registry.json"
        if not registry_path.exists():
            registry_path = Path(usb_creator.__file__).parent.parent / "manifests" / "tool_registry.json"
            
        original_content = registry_path.read_bytes()
        tampered_content = original_content + b"\n# malicious append"
        
        # Temporarily mock the file read to simulate tampering
        with patch.object(Path, "read_bytes", return_value=tampered_content):
            with self.assertRaises(SystemExit) as context:
                usb_creator.load_tool_registry()
            self.assertEqual(1, context.exception.code)

    def test_load_tool_registry_signature_failure_on_missing_sig(self):
        """Verify that a missing detached signature file causes an immediate critical security halt."""
        call_count = 0
        
        def mock_exists(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # First two calls are for registry_path.exists()
            if call_count <= 2:
                return True
            # Third call is for sig_path.exists() -> simulate missing (.sig) file
            return False
            
        with patch.object(Path, "exists", side_effect=mock_exists):
            with self.assertRaises(SystemExit) as context:
                usb_creator.load_tool_registry()
            self.assertEqual(1, context.exception.code)

if __name__ == "__main__":
    unittest.main()
