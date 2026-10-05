import importlib.util
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

SPEC = importlib.util.spec_from_file_location("workspace_preparation",
    Path(__file__).resolve().parent.parent / "scripts/hardware/prepare_windows_workspace.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class WorkspacePreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "source.wim"
        self.image = b"MSWIM\0\0\0" + (208).to_bytes(4, "little") + bytes(196)
        self.source.write_bytes(self.image)
        self.sha = hashlib.sha256(self.image).hexdigest()

    def test_checksum_mismatch_prevents_tool_resolution(self):
        with patch.object(module.preparation, "_system_dism") as tool:
            with self.assertRaises(RuntimeError):
                module.prepare_workspace(self.source, "0" * 64, 1)
            tool.assert_not_called()

    def test_boolean_index_rejected(self):
        with self.assertRaises(RuntimeError):
            module.prepare_workspace(self.source, self.sha, True)

    def test_no_arbitrary_apply_destination_parameter(self):
        with self.assertRaises(TypeError):
            module.prepare_workspace(self.source, self.sha, 1, destination="C:\\")

    def test_symlink_source_rejected(self):
        link = Path(self.temp.name) / "linked.wim"
        try:
            link.symlink_to(self.source)
        except OSError as exc:
            if getattr(exc, "winerror", None) == 1314:
                self.skipTest("Windows account lacks symbolic-link creation privilege")
            raise
        with self.assertRaises(RuntimeError):
            module.prepare_workspace(link, self.sha, 1)

    def test_mocked_native_command_only_proves_fixture_file_application(self):
        work = Path(self.temp.name) / "workspace"
        work.mkdir()
        outputs = ["Index : 1\n", "Name : Windows\nArchitecture : x64\nEdition : Professional\n"]
        def inspect(tool, args, logs, label, cancelled):
            self.assertEqual(Path("/native/tool"), tool)
            return outputs.pop(0)
        def apply(command, transcript, cancelled):
            self.assertIn("/CheckIntegrity", command)
            self.assertIn("/Verify", command)
            destination = Path(next(x.split(":", 1)[1] for x in command if x.startswith("/ApplyDir:")))
            self.assertEqual(work / "applied-files", destination)
            for relative in ("Windows/System32/ntoskrnl.exe", "Windows/System32/config/SYSTEM",
                             "Windows/System32/config/SOFTWARE"):
                path = destination / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"fixture")
        with patch.object(module.preparation, "_system_dism", return_value=Path("/native/tool")), \
             patch.object(module.tempfile, "mkdtemp", return_value=str(work)), \
             patch.object(module, "_inspect_metadata", side_effect=inspect), \
             patch.object(module.preparation, "_run_dism", side_effect=apply):
            result = module.prepare_workspace(self.source, self.sha, 1)
        self.assertFalse(result["windows_to_go_ready"])
        self.assertFalse(result["boot_verified"])
        self.assertEqual(21, result["applied_file_readback_bytes"])

    def test_missing_native_index_blocks_application_retains_workspace(self):
        work = Path(self.temp.name) / "missing-index-workspace"
        work.mkdir()
        with patch.object(module.preparation, "_system_dism", return_value=Path("/native/tool")), \
             patch.object(module.tempfile, "mkdtemp", return_value=str(work)), \
             patch.object(module, "_inspect_metadata", return_value="Index : 2\n"), \
             patch.object(module.preparation, "_run_dism") as apply:
            with self.assertRaises(RuntimeError) as failure:
                module.prepare_workspace(self.source, self.sha, 1)
            apply.assert_not_called()
        self.assertEqual(work, failure.exception.partial_directory)

    def test_cancel_before_allocation(self):
        with patch.object(module.preparation, "_system_dism", return_value=Path("/native/tool")), \
             patch.object(module.tempfile, "mkdtemp") as allocate:
            with self.assertRaises(RuntimeError):
                module.prepare_workspace(self.source, self.sha, 1, cancelled=lambda: True)
            allocate.assert_not_called()

    def test_non_wim_bytes_rejected_before_tool_resolution(self):
        self.source.write_bytes(b"not a wim")
        with patch.object(module.preparation, "_system_dism") as tool:
            with self.assertRaises(RuntimeError):
                module.prepare_workspace(self.source, hashlib.sha256(b"not a wim").hexdigest(), 1)
            tool.assert_not_called()

    @unittest.skipUnless(hasattr(__import__("os"), "mkfifo"), "FIFO requires Unix")
    def test_fifo_rejected_without_blocking(self):
        import os
        fifo = Path(self.temp.name) / "pipe.wim"
        os.mkfifo(fifo)
        with self.assertRaises(RuntimeError):
            module.prepare_workspace(fifo, self.sha, 1)

    def test_cli_structured_failure_retains_partial_directory(self):
        output = io.StringIO()
        error = module.preparation.staging.StagingError("apply failed", Path("partial-workspace"))
        with patch.object(module, "prepare_workspace", side_effect=error), redirect_stdout(output):
            code = module.main([str(self.source), "--sha256", self.sha, "--index", "1"])
        result = json.loads(output.getvalue())
        self.assertEqual(2, code)
        self.assertTrue(result["partial_output_unresolved"])
        self.assertEqual("partial-workspace", result["partial_directory"])
        self.assertFalse(result["windows_to_go_ready"])

    def test_cli_real_signal_requests_cancellation_and_restores_handler(self):
        import signal
        previous = signal.getsignal(signal.SIGINT)
        output = io.StringIO()
        def interrupted(*args, cancelled):
            signal.raise_signal(signal.SIGINT)
            self.assertTrue(cancelled())
            raise RuntimeError("cancelled")
        with patch.object(module, "prepare_workspace", side_effect=interrupted), redirect_stdout(output):
            code = module.main([str(self.source), "--sha256", self.sha, "--index", "1"])
        self.assertEqual(130, code)
        self.assertEqual("cancelled", json.loads(output.getvalue())["status"])
        self.assertEqual(previous, signal.getsignal(signal.SIGINT))

    def test_cli_success_is_applied_files_only(self):
        output = io.StringIO()
        with patch.object(module, "prepare_workspace", return_value={"boot_verified": False, "windows_to_go_ready": False}), redirect_stdout(output):
            self.assertEqual(0, module.main([str(self.source), "--sha256", self.sha, "--index", "1"]))
        self.assertEqual("applied_files_verified_boot_unresolved", json.loads(output.getvalue())["status"])

    def test_metadata_uses_cancellable_logged_native_runner(self):
        logs = Path(self.temp.name)
        def run(command, transcript, cancelled):
            self.assertEqual(str(Path("/native/tool")), command[0])
            self.assertIn("/English", command)
            self.assertFalse(cancelled())
            transcript.write_text("Index : 1\n")
        with patch.object(module.preparation, "_run_dism", side_effect=run):
            result = module._inspect_metadata(Path("/native/tool"), ["/Get-ImageInfo"], logs, "metadata", lambda: False)
        self.assertEqual("Index : 1\n", result)

    def test_cli_cancel_file_is_combined_with_signal_callback(self):
        cancel = Path(self.temp.name) / "cancel.signal"
        cancel.touch()
        def interrupted(*args, cancelled):
            self.assertTrue(cancelled())
            raise RuntimeError("cancelled")
        output = io.StringIO()
        with patch.object(module, "prepare_workspace", side_effect=interrupted), redirect_stdout(output):
            code = module.main([str(self.source), "--sha256", self.sha, "--index", "1", "--cancel-file", str(cancel)])
        self.assertEqual(130, code)
        self.assertEqual("cancelled", json.loads(output.getvalue())["status"])

    def test_final_cancel_file_prevents_success_receipt(self):
        cancel = Path(self.temp.name) / "late-cancel.signal"
        def completed(*args, cancelled):
            cancel.touch()
            return {"workspace_directory": str(self.temp.name)}
        output = io.StringIO()
        with patch.object(module, "prepare_workspace", side_effect=completed), redirect_stdout(output):
            code = module.main([str(self.source), "--sha256", self.sha, "--index", "1", "--cancel-file", str(cancel)])
        receipt = json.loads(output.getvalue())
        self.assertEqual(130, code)
        self.assertEqual("cancelled", receipt["status"])
        self.assertTrue(receipt["partial_output_unresolved"])


if __name__ == "__main__":
    unittest.main()
