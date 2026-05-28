#!/usr/bin/env python3
"""
PR41D - Apple EFI / T2 / Legacy Mac Behavior Test Suite
Validates recovery boot configuration, EFI layouts, T2 Secure Boot bypass rules,
and parsed boot matrix compliance on Apple hardware profiles.
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root and desktop to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../desktop")))

from src.core.models import HardwareProfile, DeploymentRecipe, PartitionScheme, FileSystem
from src.core.hardware_profiles import get_mac_model_data

class TestAppleEFI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.efi_dir = Path(self.temp_dir) / "EFI"
        self.efi_dir.mkdir(parents=True, exist_ok=True)
        self.boot_log_path = Path(self.temp_dir) / "efi_boot.log"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def write_mock_efi_layout(self):
        """Helper to create simulated OpenCore/EFI structure"""
        boot_dir = self.efi_dir / "BOOT"
        boot_dir.mkdir(parents=True, exist_ok=True)
        (boot_dir / "BOOTX64.EFI").touch()

        oc_dir = self.efi_dir / "OC"
        oc_dir.mkdir(parents=True, exist_ok=True)
        (oc_dir / "OpenCore.efi").touch()
        (oc_dir / "config.plist").touch()

    def test_hardware_profile_apple_characteristics(self):
        """Verify that known Apple hardware profiles expose proper T2 & OCLP metadata"""
        # Load real Mac model data
        mac_data = get_mac_model_data()

        # Test modern T2 Mac (MacBookPro15,1)
        if "MacBookPro15,1" in mac_data:
            profile = HardwareProfile.from_mac_model("MacBookPro15,1")
            self.assertEqual(profile.platform, "mac")
            self.assertEqual(profile.architecture, "x86_64")
            self.assertEqual(profile.secure_boot_model, "j132")  # T2 MBP 15,1
            self.assertEqual(profile.sip_requirements, "disabled")
            self.assertTrue(profile.oclp_compatibility in ["fully_supported", "partially_supported"])

        # Test legacy non-T2 Mac (iMacPro1,1)
        if "iMacPro1,1" in mac_data:
            profile = HardwareProfile.from_mac_model("iMacPro1,1")
            self.assertEqual(profile.platform, "mac")
            self.assertEqual(profile.architecture, "x86_64")
            self.assertEqual(profile.secure_boot_model, "j137")  # T2 iMacPro
            self.assertEqual(profile.sip_requirements, "disabled")

    def test_efi_layout_validation(self):
        """Verify EFI bootloader layout is compliant with Apple EFI firmware specs"""
        self.write_mock_efi_layout()

        # Act & Assert
        has_bootloader, error = self.verify_efi_layout(self.efi_dir)
        self.assertTrue(has_bootloader)
        self.assertIsNone(error)

    def test_efi_layout_missing_critical_component(self):
        """Verify that layout validation fails if OpenCore config is missing"""
        boot_dir = self.efi_dir / "BOOT"
        boot_dir.mkdir(parents=True, exist_ok=True)
        (boot_dir / "BOOTX64.EFI").touch()

        oc_dir = self.efi_dir / "OC"
        oc_dir.mkdir(parents=True, exist_ok=True)
        (oc_dir / "OpenCore.efi").touch()

        # Act & Assert
        has_bootloader, error = self.verify_efi_layout(self.efi_dir)
        self.assertFalse(has_bootloader)
        self.assertIn("config.plist missing", error)

    def test_apple_efi_boot_log_success(self):
        """Verify Apple EFI boot log parsing for successful boot marker"""
        mock_log = [
            "Apple EFI Firmware v2.0",
            "SecureBoot status: Bypass Enabled (T2 Mode)",
            "OpenCore: Load started...",
            "OC: Booting macOS Recovery installer...",
            "macx_swapon SUCCESS",
            "EFI_BOOT_SUCCESS"
        ]
        with open(self.boot_log_path, 'w') as f:
            f.write('\n'.join(mock_log))

        # Act & Assert
        has_success, error = self.verify_apple_boot_log(self.boot_log_path)
        self.assertTrue(has_success)
        self.assertIsNone(error)

    def test_apple_efi_boot_log_graphics_panic(self):
        """Verify Apple EFI boot log parsing catches standard Apple frame-buffer panics"""
        mock_log = [
            "Apple EFI Firmware v2.0",
            "OpenCore: Load started...",
            "panic(cpu 0 caller 0xffffff800021c3d6): \"AppleIntelFramebufferController::start failed\""
        ]
        with open(self.boot_log_path, 'w') as f:
            f.write('\n'.join(mock_log))

        # Act & Assert
        has_success, error = self.verify_apple_boot_log(self.boot_log_path)
        self.assertFalse(has_success)
        self.assertIn("Framebuffer Controller panic detected", error)

    def verify_efi_layout(self, path: Path) -> tuple[bool, str | None]:
        """Validates that Path contains a valid bootable EFI folder structure"""
        if not path.exists():
            return False, f"EFI path does not exist: {path}"

        bootx64 = path / "BOOT" / "BOOTX64.EFI"
        if not bootx64.exists():
            return False, "BOOTX64.EFI missing under BOOT directory"

        oc_core = path / "OC" / "OpenCore.efi"
        if not oc_core.exists():
            return False, "OpenCore.efi missing under OC directory"

        oc_config = path / "OC" / "config.plist"
        if not oc_config.exists():
            return False, "config.plist missing under OC directory"

        return True, None

    def verify_apple_boot_log(self, file_path: Path) -> tuple[bool, str | None]:
        """Parses and verifies the given Apple EFI boot log for PR41D validation"""
        if not file_path.exists():
            return False, f"Apple boot log file does not exist: {file_path}"

        with open(file_path, 'r') as f:
            content = f.read()

        # Check for Apple-specific bootloader/graphics panics
        if "AppleIntelFramebuffer" in content or "FramebufferController" in content:
            return False, "Graphics Framebuffer Controller panic detected in EFI log"

        if "MACH Reboot" in content:
            return False, "Mach reboot cycle detected"

        # Check for success marker
        if "EFI_BOOT_SUCCESS" not in content:
            return False, "EFI_BOOT_SUCCESS marker not found in Apple log"

        return True, None

if __name__ == "__main__":
    unittest.main()
