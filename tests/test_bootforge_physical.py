#!/usr/bin/env python3
"""
PR41A - Physical USB Boot Validation Test Suite
Validates physical USB boot logs, device safety characteristics, and boot readiness.
Supports mock execution in CI environment and real hardware log analysis in the lab.
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

from src.core.safety_validator import SafetyValidator, SafetyLevel, ValidationResult, DeviceRisk
from src.core.usb_builder import StorageBuilder
from src.core.models import DeploymentRecipe, HardwareProfile

class TestBootForgePhysical(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_path = Path(self.temp_dir) / "phoenix_boot.log"

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def write_mock_boot_log(self, lines):
        """Helper to write mock boot log content"""
        with open(self.log_path, 'w') as f:
            f.write('\n'.join(lines))

    def test_parse_successful_boot_log(self):
        """Verify that a standard successful boot log passes physical validation"""
        mock_log = [
            "[00:00:01] PhoenixOS boot sequence initiated.",
            "[00:00:02] Loading ACPI tables... OK",
            "[00:00:03] Mounting root filesystem... OK",
            "[00:00:05] Launching recovery application...",
            "[00:00:06] BOOT_SUCCESS: PhoenixOS Recovery fully loaded."
        ]
        self.write_mock_boot_log(mock_log)

        # Act & Assert
        has_success, error = self.verify_boot_log(self.log_path)
        self.assertTrue(has_success)
        self.assertIsNone(error)

    def test_boot_log_missing_success_marker(self):
        """Verify that a boot log lacking BOOT_SUCCESS fails validation"""
        mock_log = [
            "[00:00:01] PhoenixOS boot sequence initiated.",
            "[00:00:02] Loading ACPI tables... OK",
            "[00:00:03] Mounting root filesystem... OK",
            "[00:00:05] Launching recovery application..."
        ]
        self.write_mock_boot_log(mock_log)

        # Act & Assert
        has_success, error = self.verify_boot_log(self.log_path)
        self.assertFalse(has_success)
        self.assertIn("BOOT_SUCCESS marker not found", error)

    def test_boot_log_detects_kernel_panic(self):
        """Verify that a boot log containing kernel panics fails validation with explicit error"""
        mock_log = [
            "[00:00:01] PhoenixOS boot sequence initiated.",
            "[00:00:02] Loading ACPI tables... OK",
            "[00:00:03] Kernel panic - not syncing: Attempted to kill init!",
            "[00:00:04] CPU: 0 PID: 1 Comm: init Not tainted"
        ]
        self.write_mock_boot_log(mock_log)

        # Act & Assert
        has_success, error = self.verify_boot_log(self.log_path)
        self.assertFalse(has_success)
        self.assertIn("Kernel panic detected", error)

    def test_boot_log_detects_mount_failure(self):
        """Verify that a boot log containing filesystem mount failures fails validation"""
        mock_log = [
            "[00:00:01] PhoenixOS boot sequence initiated.",
            "[00:00:02] Loading ACPI tables... OK",
            "[00:00:03] EXT4-fs error (device sda2): ext4_lookup: deleted inode",
            "[00:00:04] failed to mount root filesystem"
        ]
        self.write_mock_boot_log(mock_log)

        # Act & Assert
        has_success, error = self.verify_boot_log(self.log_path)
        self.assertFalse(has_success)
        self.assertIn("Mount failure detected", error)

    @patch('src.core.safety_validator.os.path.exists')
    @patch('src.core.safety_validator.SafetyValidator._is_device_removable')
    @patch('src.core.safety_validator.SafetyValidator._is_system_disk')
    @patch('src.core.safety_validator.SafetyValidator._is_boot_disk')
    @patch('src.core.safety_validator.SafetyValidator._get_device_size_gb')
    @patch('src.core.safety_validator.SafetyValidator._get_device_mount_points')
    def test_physical_target_removable_safety_gate(self, mock_mounts, mock_size, mock_boot, mock_sys, mock_removable, mock_exists):
        """Verify that physical target device matches safety validator requirements for standard write operations"""
        # Mock a physical 32GB removable USB stick
        mock_exists.return_value = True
        mock_removable.return_value = True
        mock_sys.return_value = False
        mock_boot.return_value = False
        mock_size.return_value = 32.0
        mock_mounts.return_value = []

        validator = SafetyValidator(SafetyLevel.STANDARD)
        risk = validator.validate_device_safety("/dev/disk4")

        self.assertEqual(risk.overall_risk, ValidationResult.SAFE)
        self.assertTrue(risk.is_removable)
        self.assertFalse(risk.is_system_disk)
        self.assertEqual(len(risk.risk_factors), 0)

    def verify_boot_log(self, file_path: Path) -> tuple[bool, str | None]:
        """
        Parses and verifies the given boot log for PR41A validation.
        """
        if not file_path.exists():
            return False, f"Boot log file does not exist: {file_path}"

        with open(file_path, 'r') as f:
            content = f.read()

        # Check for kernel panics
        panic_keywords = ["panic", "kernel panic", "Kernel panic", "bug:", "BUG:"]
        for kw in panic_keywords:
            if kw in content:
                # Find line containing the panic keyword
                for line in content.splitlines():
                    if kw in line:
                        return False, f"Kernel panic detected: '{line.strip()}'"

        # Check for filesystem mount errors
        mount_keywords = ["failed to mount", "EXT4-fs error", "failed to mount root"]
        for kw in mount_keywords:
            if kw in content:
                for line in content.splitlines():
                    if kw in line:
                        return False, f"Mount failure detected: '{line.strip()}'"

        # Check for success marker
        if "BOOT_SUCCESS" not in content:
            return False, "BOOT_SUCCESS marker not found in log"

        return True, None

if __name__ == "__main__":
    unittest.main()
