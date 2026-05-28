"""
Transactional Dry-Run & Simulation Engine verification tests
"""

import unittest
import sys
from pathlib import Path
import tempfile
import shutil

# Make sure we can import core components
sys.path.insert(0, str(Path(__file__).parent.parent / "desktop"))

from src.core.usb_builder import StorageBuilder, BuildProgress
from src.core.models import DeploymentRecipe, HardwareProfile, DeploymentType, PartitionScheme, FileSystem, PartitionInfo
from src.core.safety_validator import SafetyLevel

class TestTransactionalDryRun(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.recipe = DeploymentRecipe(
            name="Test Linux Recipe",
            description="Testing transactional dry-run features",
            deployment_type=DeploymentType.LINUX_AUTOMATED,
            partition_scheme=PartitionScheme.GPT,
            partitions=[
                PartitionInfo(name="EFI", size_mb=100, filesystem=FileSystem.FAT32, label="EFI", bootable=True),
                PartitionInfo(name="ROOT", size_mb=-1, filesystem=FileSystem.EXT4, label="ROOT", bootable=False)
            ],
            hardware_profiles=["generic"],
            required_files=[]
        )
        self.profile = HardwareProfile(
            name="generic_x86_64",
            platform="linux",
            model="generic",
            architecture="x86_64",
            year=2026
        )
        self.builder = StorageBuilder(safety_level=SafetyLevel.STANDARD)
        self.builder.dry_run = True

    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        if self.builder.temp_dir and self.builder.temp_dir.exists():
            shutil.rmtree(self.builder.temp_dir, ignore_errors=True)

    def test_dryrun_simulated_success(self):
        """Test that a complete dry run build finishes successfully without modifying physical drives"""
        self.builder.recipe = self.recipe
        self.builder.target_device = "/dev/sdy"
        self.builder.hardware_profile = self.profile
        self.builder.source_files = {}

        # Execute run directly to keep it in the test thread rather than spawn asynchronously
        self.builder.run()

        # Verify success indicators
        self.assertTrue(hasattr(self.builder, '_build_successful'))
        self.assertFalse(self.builder.is_cancelled)

        # Check that dry-run notifications were logged
        logs = "\n".join(self.builder.build_log)
        self.assertIn("[DRYRUN SIMULATION] Executed command", logs)

    def test_dryrun_mid_operation_cancellation(self):
        """Test that mid-operation cancellation triggers rollback operations and cleans up"""
        self.builder.recipe = self.recipe
        self.builder.target_device = "/dev/sdy"
        self.builder.hardware_profile = self.profile
        self.builder.source_files = {}

        # Let's insert a rollback operation
        rolled_back = False
        def mock_rollback():
            nonlocal rolled_back
            rolled_back = True

        self.builder._add_rollback_operation(mock_rollback)
        self.builder.cancel_build()

        self.builder.run()

        self.assertTrue(rolled_back)
        self.assertIn("Performing rollback operations...", "\n".join(self.builder.build_log))

    def test_dryrun_target_disconnect(self):
        """Test that target disconnect throws immediate IOError and initiates rollback"""
        self.builder.recipe = self.recipe
        self.builder.target_device = "/dev/sdy"
        self.builder.hardware_profile = self.profile
        self.builder.source_files = {}
        self.builder.mock_disconnect = True

        rolled_back = False
        def mock_rollback():
            nonlocal rolled_back
            rolled_back = True

        self.builder._add_rollback_operation(mock_rollback)

        self.builder.run()

        # Build should fail
        self.assertFalse(hasattr(self.builder, '_build_successful'))
        self.assertTrue(rolled_back)

        logs = "\n".join(self.builder.build_log)
        self.assertIn("suddenly disconnected", logs)

    def test_dryrun_subprocess_failure_trigger_rollback(self):
        """Test that formatting or shell failures trigger rollback operations"""
        self.builder.recipe = self.recipe
        self.builder.target_device = "/dev/sdy"
        self.builder.hardware_profile = self.profile
        self.builder.source_files = {}

        # Let's override _run_command_safe to raise an error during partition table creation
        def fail_parted(cmd_args, **kwargs):
            if "parted" in cmd_args or "diskutil" in cmd_args or "diskpart" in cmd_args:
                import subprocess
                return subprocess.CompletedProcess(args=cmd_args, returncode=1, stdout="", stderr="Mocked command failure")
            return subprocess.CompletedProcess(args=cmd_args, returncode=0, stdout="", stderr="")

        import subprocess
        self.builder._run_command_safe = fail_parted

        rolled_back = False
        def mock_rollback():
            nonlocal rolled_back
            rolled_back = True

        self.builder._add_rollback_operation(mock_rollback)

        self.builder.run()

        self.assertFalse(hasattr(self.builder, '_build_successful'))
        self.assertTrue(rolled_back)

if __name__ == "__main__":
    unittest.main()
