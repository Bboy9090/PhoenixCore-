#!/usr/bin/env python3
"""
PR41B - Safety Enforcement Validation Test Suite
Validates that safety gates (write-gating, central-format gating) are rigorously enforced.
Generates safety_report.json as the formal release engineering evidence package.
"""

import os
import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root and desktop to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../desktop")))

from src.core.safety_validator import SafetyValidator, SafetyLevel, ValidationResult, DeviceRisk

class TestSafetyGating(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.validator = SafetyValidator(SafetyLevel.STANDARD)
        self.report_path = Path("safety_report.json")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        if self.report_path.exists() and self._testMethodName != "test_export_safety_report":
            try:
                self.report_path.unlink()
            except OSError:
                pass

    @patch('src.core.safety_validator.os.path.exists')
    @patch('src.core.safety_validator.SafetyValidator._is_device_removable')
    @patch('src.core.safety_validator.SafetyValidator._is_system_disk')
    @patch('src.core.safety_validator.SafetyValidator._is_boot_disk')
    @patch('src.core.safety_validator.SafetyValidator._get_device_size_gb')
    def test_block_non_removable_drive(self, mock_size, mock_boot, mock_sys, mock_removable, mock_exists):
        """Verify safety gate blocks write operations to non-removable internal drives"""
        mock_exists.return_value = True
        mock_removable.return_value = False
        mock_sys.return_value = False
        mock_boot.return_value = False
        mock_size.return_value = 256.0

        risk = self.validator.validate_device_safety("/dev/disk1")
        self.assertEqual(risk.overall_risk, ValidationResult.BLOCKED)
        self.assertIn("Device is not removable", risk.risk_factors)

    @patch('src.core.safety_validator.os.path.exists')
    @patch('src.core.safety_validator.SafetyValidator._is_device_removable')
    @patch('src.core.safety_validator.SafetyValidator._is_system_disk')
    @patch('src.core.safety_validator.SafetyValidator._is_boot_disk')
    @patch('src.core.safety_validator.SafetyValidator._get_device_size_gb')
    def test_block_system_disk(self, mock_size, mock_boot, mock_sys, mock_removable, mock_exists):
        """Verify safety gate blocks operations targeting active system disk"""
        mock_exists.return_value = True
        mock_removable.return_value = True
        mock_sys.return_value = True
        mock_boot.return_value = False
        mock_size.return_value = 512.0

        risk = self.validator.validate_device_safety("/dev/disk0")
        self.assertEqual(risk.overall_risk, ValidationResult.BLOCKED)
        self.assertIn("Device contains system files", risk.risk_factors)

    @patch('src.core.safety_validator.os.path.exists')
    @patch('src.core.safety_validator.SafetyValidator._is_device_removable')
    @patch('src.core.safety_validator.SafetyValidator._is_system_disk')
    @patch('src.core.safety_validator.SafetyValidator._is_boot_disk')
    @patch('src.core.safety_validator.SafetyValidator._get_device_size_gb')
    def test_block_boot_disk(self, mock_size, mock_boot, mock_sys, mock_removable, mock_exists):
        """Verify safety gate blocks operations targeting the active boot volume"""
        mock_exists.return_value = True
        mock_removable.return_value = True
        mock_sys.return_value = False
        mock_boot.return_value = True
        mock_size.return_value = 1000.0

        risk = self.validator.validate_device_safety("/dev/disk0s2")
        self.assertEqual(risk.overall_risk, ValidationResult.BLOCKED)
        self.assertIn("Device is boot disk", risk.risk_factors)

    @patch('src.core.safety_validator.os.path.exists')
    @patch('src.core.safety_validator.SafetyValidator._is_device_removable')
    @patch('src.core.safety_validator.SafetyValidator._is_system_disk')
    @patch('src.core.safety_validator.SafetyValidator._is_boot_disk')
    @patch('src.core.safety_validator.SafetyValidator._get_device_size_gb')
    def test_warning_oversized_drive(self, mock_size, mock_boot, mock_sys, mock_removable, mock_exists):
        """Verify safety gate flags exceptionally large drives (> 2TB) as warning/dangerous"""
        mock_exists.return_value = True
        mock_removable.return_value = True
        mock_sys.return_value = False
        mock_boot.return_value = False
        mock_size.return_value = 3000.0  # 3 TB

        risk = self.validator.validate_device_safety("/dev/disk3")
        self.assertIn(risk.overall_risk, [ValidationResult.WARNING, ValidationResult.DANGEROUS])
        self.assertTrue(any("very large" in f for f in risk.risk_factors))

    @patch('src.core.safety_validator.os.path.exists')
    @patch('src.core.safety_validator.SafetyValidator._is_device_removable')
    @patch('src.core.safety_validator.SafetyValidator._is_system_disk')
    @patch('src.core.safety_validator.SafetyValidator._is_boot_disk')
    @patch('src.core.safety_validator.SafetyValidator._get_device_size_gb')
    def test_export_safety_report(self, mock_size, mock_boot, mock_sys, mock_removable, mock_exists):
        """Execute complete safety gate evaluation and export formal safety_report.json evidence"""
        # Define mock behaviors
        mock_exists.return_value = True
        mock_removable.side_effect = lambda dev: dev == "/dev/disk4"
        mock_sys.return_value = False
        mock_boot.return_value = False
        mock_size.return_value = 32.0

        # Validate different scenarios
        risk_internal = self.validator.validate_device_safety("/dev/disk1")
        risk_usb = self.validator.validate_device_safety("/dev/disk4")

        # Compile safety report
        report_data = {
            "milestone": "PR41B",
            "policy": "SAFETY_GATES_v1",
            "results": {
                "internal_drive_blocked": risk_internal.overall_risk == ValidationResult.BLOCKED,
                "usb_drive_allowed": risk_usb.overall_risk == ValidationResult.SAFE
            },
            "status": "PASS" if (risk_internal.overall_risk == ValidationResult.BLOCKED and risk_usb.overall_risk == ValidationResult.SAFE) else "FAIL"
        }

        # Export report to current working directory
        with open(self.report_path, 'w') as f:
            json.dump(report_data, f, indent=4)

        self.assertTrue(self.report_path.exists())
        with open(self.report_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["status"], "PASS")
            self.assertTrue(data["results"]["internal_drive_blocked"])
            self.assertTrue(data["results"]["usb_drive_allowed"])

if __name__ == "__main__":
    unittest.main()
