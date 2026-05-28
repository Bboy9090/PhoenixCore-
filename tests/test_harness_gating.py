#!/usr/bin/env python3
"""
Unit tests for centralized safety validation gating in DiskManager and DiskWriter
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add project root and desktop to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../desktop")))
from src.core.safety_validator import (
    validate_target_safety,
    SafetyVerdict,
    SafetySeverity,
    DeviceProbe
)
from src.core.disk_manager import DiskManager, DiskWriter


class TestSafetyGating(unittest.TestCase):
    """Test safety gating blocks formatting and writing on unsafe drives"""

    @patch('src.core.safety_validator.enumerate_host_devices')
    def test_central_format_gating_blocks_unsafe(self, mock_enumerate):
        """Verify format_device immediately refuses unsafe targets centrally"""
        # Mock unsafe system disk probe
        mock_probe = DeviceProbe(
            device_path="/dev/disk3",
            is_host_root_parent=True,
            is_removable=False
        )
        mock_enumerate.return_value = [mock_probe]

        manager = DiskManager()
        
        # Act: attempt to format /dev/disk3 (unsafe)
        result = manager.format_device("/dev/disk3", "fat32")
        
        # Assert format was blocked and returned False
        self.assertFalse(result)

    @patch('src.core.safety_validator.enumerate_host_devices')
    def test_central_write_gating_blocks_unsafe(self, mock_enumerate):
        """Verify DiskWriter thread target validation refuses unsafe targets centrally"""
        # Mock unsafe internal SSD probe
        mock_probe = DeviceProbe(
            device_path="/dev/disk0",
            is_apfs_system_container=True,
            is_removable=False
        )
        mock_enumerate.return_value = [mock_probe]

        writer = DiskWriter()
        writer.target_device = "/dev/disk0"
        
        # Act & Assert: target validation must refuse raw block write
        self.assertFalse(writer._validate_target_device())


if __name__ == "__main__":
    unittest.main()
