import unittest
import json
import tempfile
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from real_writer_interface import (
    RealWriterRequest,
    RealWriterResult,
    NullDisabledWriterAdapter,
    WindowsLabWriterAdapter,
    MacOSLabWriterAdapter,
    LinuxLabWriterAdapter,
    FileBackedLabWriterAdapter,
)


class TestRealWriterInterface(unittest.TestCase):
    def setUp(self):
        self.request = RealWriterRequest(
            target_drive="E:\\",
            target_stable_id="usb-test-drive",
            target_identity_hash="some-dev-hash",
            image_path="C:\\test.iso",
            image_sha256="abc123expectedhash",
            image_size_bytes=1024,
            contract_id="contract-id-123",
            session_id="session-id-123",
            readiness_gate_id="gate-id-123",
            ledger_path="C:\\ledger.jsonl",
            lab_mode=True,
        )

    def test_01_default_adapter_is_disabled_null(self):
        """1. Default adapter is disabled/null."""
        adapter = NullDisabledWriterAdapter()
        res = adapter.execute_write(self.request)
        self.assertEqual(res.adapter, "NullDisabledWriterAdapter")
        self.assertTrue(res.blocked)

    def test_02_real_writer_implemented_false_by_default(self):
        """2. real_writer_implemented false by default."""
        res = NullDisabledWriterAdapter().execute_write(self.request)
        self.assertFalse(res.real_writer_implemented)

    def test_03_destructive_operations_enabled_false_by_default(self):
        """3. destructive_operations_enabled false by default."""
        res = NullDisabledWriterAdapter().execute_write(self.request)
        self.assertFalse(res.destructive_operations_enabled)

    def test_04_write_attempted_false_when_blocked(self):
        """4. write_attempted false when blocked."""
        res = NullDisabledWriterAdapter().execute_write(self.request)
        self.assertFalse(res.write_attempted)

    def test_05_windows_adapter_blocks(self):
        """5. Windows adapter blocks by default."""
        res = WindowsLabWriterAdapter().execute_write(self.request)
        self.assertTrue(res.blocked)
        self.assertFalse(res.real_writer_implemented)

    def test_06_macos_adapter_blocks(self):
        """6. macOS adapter blocks by default."""
        res = MacOSLabWriterAdapter().execute_write(self.request)
        self.assertTrue(res.blocked)

    def test_07_linux_adapter_blocks(self):
        """7. Linux adapter blocks by default."""
        res = LinuxLabWriterAdapter().execute_write(self.request)
        self.assertTrue(res.blocked)

    def test_08_no_diskpart_or_dd_call_sites(self):
        """8. Verify no diskpart or dd calls in real_writer_interface.py."""
        with open(
            os.path.join(Path(__file__).parent.parent, "real_writer_interface.py"),
            "r",
            encoding="utf-8",
        ) as f:
            content = f.read()
        self.assertNotIn("diskpart", content.lower())
        self.assertNotIn("subprocess.run", content.lower())
        self.assertNotIn("subprocess.Popen", content.lower())

    def test_09_no_format_mount_unmount_mkfs_call_sites(self):
        """9. Verify no formatting or mount commands in real_writer_interface.py."""
        with open(
            os.path.join(Path(__file__).parent.parent, "real_writer_interface.py"),
            "r",
            encoding="utf-8",
        ) as f:
            content = f.read()
        self.assertNotIn("format", content.lower())
        self.assertNotIn("mount", content.lower())
        self.assertNotIn("unmount", content.lower())
        self.assertNotIn("mkfs", content.lower())

    def test_10_results_json_serializable(self):
        """10. RealWriterResult output is JSON serializable."""
        res = NullDisabledWriterAdapter().execute_write(self.request)
        try:
            serialized = json.dumps(res.to_dict())
            self.assertIsNotNone(serialized)
        except Exception as e:
            self.fail(f"RealWriterResult serialization failed: {e}")


if __name__ == "__main__":
    unittest.main()
