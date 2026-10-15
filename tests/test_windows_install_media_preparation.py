"""Mocked tool contract tests; not runtime DISM or Windows boot proof."""

import importlib.util
import tempfile
import unittest
import contextlib
import io
import json
from pathlib import Path
from unittest.mock import patch
from unittest.mock import MagicMock
from tests.test_fat32_windows_media_plan import make_tree, write_wim

SPEC = importlib.util.spec_from_file_location(
    "prepare",
    Path(__file__).resolve().parents[1]
    / "scripts/hardware/prepare_windows_install_media.py",
)
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        write_wim(make_tree(self.source) / "install.wim", 2048)
        self.manifest = prepare.media.capture_media_manifest(self.source)
        self.limit = prepare.media.FAT32_MAX_FILE_BYTES
        prepare.media.FAT32_MAX_FILE_BYTES = 1023

    def tearDown(self):
        prepare.media.FAT32_MAX_FILE_BYTES = self.limit
        self.tmp.cleanup()

    def run_prepare(self, runner, cancelled=lambda: False):
        with patch.object(
            prepare, "_system_dism", return_value=Path("C:/Windows/System32/dism.exe")
        ), patch.object(prepare, "_run_dism", side_effect=runner):
            return prepare.prepare_media(
                self.source, self.root, "prepared", self.manifest, cancelled
            )

    def test_success_checks_actual_output_and_preserves_source(self):
        def runner(command, log, cancel):
            self.assertIn("/CheckIntegrity", command)
            output = Path(
                next(
                    arg.split(":", 1)[1]
                    for arg in command
                    if arg.startswith("/SWMFile:")
                )
            )
            write_wim(output)
            write_wim(output.with_name("install2.swm"))
            log.write_bytes(b"mock contract")

        receipt = self.run_prepare(runner)
        self.assertTrue(receipt["split_structural_checks_passed"])
        self.assertFalse(receipt["independent_image_integrity_verified"])
        self.assertFalse(receipt["boot_verified"])
        self.assertEqual(
            receipt["manifest_sha256"], receipt["prepared_manifest"]["manifest_sha256"]
        )
        self.assertEqual(
            receipt["verified_bytes"], receipt["prepared_manifest"]["total_bytes"]
        )
        self.assertTrue((self.source / "sources/install.wim").exists())
        self.assertFalse((self.root / "prepared/sources/install.wim").exists())
        self.assertTrue((self.root / "prepared/sources/install.swm").exists())
        self.assertFalse(
            any("evidence" in f["path"] for f in receipt["prepared_manifest"]["files"])
        )

    def test_nonsplit_preparation_binds_independently_readback_manifest(self):
        prepare.media.FAT32_MAX_FILE_BYTES = self.limit
        receipt = prepare.prepare_media(
            self.source, self.root, "prepared", self.manifest
        )
        actual = prepare.media.capture_media_manifest(self.root / "prepared")
        self.assertEqual(receipt["schema"], "arcwyre.windows_install_preparation.v1")
        self.assertEqual(receipt["prepared_manifest"], actual)
        self.assertEqual(receipt["manifest_sha256"], actual["manifest_sha256"])
        self.assertEqual(receipt["verified_bytes"], actual["total_bytes"])
        self.assertFalse(receipt["split_performed"])
        self.assertFalse(receipt["dism_check_integrity_requested"])
        self.assertIsNone(receipt["dism_exit_code"])
        self.assertFalse(receipt["boot_verified"])

    def test_failed_tool_retains_copied_wim(self):
        def runner(*args):
            raise prepare.staging.StagingError("DISM failed")

        with self.assertRaises(prepare.staging.StagingError) as caught:
            self.run_prepare(runner)
        self.assertTrue(caught.exception.unresolved)
        self.assertTrue((self.root / "prepared/sources/install.wim").exists())

    def test_ten_segments_use_numeric_sequence_order(self):
        def runner(command, log, cancel):
            output = Path(
                next(
                    arg.split(":", 1)[1]
                    for arg in command
                    if arg.startswith("/SWMFile:")
                )
            )
            for index in range(1, 12):
                write_wim(
                    output.with_name(
                        "install.swm" if index == 1 else f"install{index}.swm"
                    )
                )

        self.assertTrue(self.run_prepare(runner)["split_structural_checks_passed"])

    def test_added_staged_file_is_rejected_before_replacement(self):
        def runner(command, log, cancel):
            output = Path(
                next(
                    arg.split(":", 1)[1]
                    for arg in command
                    if arg.startswith("/SWMFile:")
                )
            )
            write_wim(output)
            (self.root / "prepared/extra").write_bytes(b"unexpected")

        with self.assertRaises(prepare.staging.StagingError):
            self.run_prepare(runner)
        self.assertTrue((self.root / "prepared/sources/install.wim").exists())

    def test_invalid_or_oversized_segments_rejected_before_wim_removal(self):
        for mode in ("invalid", "oversized", "missing_sequence"):
            with self.subTest(mode=mode):
                # Separate output name prevents interference between retained failures.
                name = "prepared-" + mode

                def runner(command, log, cancel):
                    output = Path(
                        next(
                            arg.split(":", 1)[1]
                            for arg in command
                            if arg.startswith("/SWMFile:")
                        )
                    )
                    if mode == "invalid":
                        output.write_bytes(b"bad")
                    else:
                        write_wim(output, 2048 if mode == "oversized" else 208)
                        if mode == "missing_sequence":
                            write_wim(output.with_name("install3.swm"))

                with patch.object(
                    prepare, "_system_dism", return_value=Path("dism.exe")
                ), patch.object(
                    prepare, "_run_dism", side_effect=runner
                ), self.assertRaises(
                    prepare.staging.StagingError
                ):
                    prepare.prepare_media(self.source, self.root, name, self.manifest)
                self.assertTrue((self.root / name / "sources/install.wim").exists())

    def test_cancel_during_tool_retains_unresolved_staging(self):
        def runner(*args):
            raise prepare.staging.StagingError("Cancelled during DISM split")

        with self.assertRaises(prepare.staging.StagingError) as caught:
            self.run_prepare(runner)
        self.assertTrue(caught.exception.unresolved)

    def test_cli_emits_structured_failure_and_nonzero_exit(self):
        manifest_path = self.root / "manifest.json"
        manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        output = io.StringIO()
        with patch.object(
            prepare,
            "prepare_media",
            side_effect=prepare.staging.StagingError("failure", self.root / "partial"),
        ), contextlib.redirect_stdout(output):
            code = prepare.main(
                [
                    "--source-root",
                    str(self.source),
                    "--staging-parent",
                    str(self.root),
                    "--name",
                    "prepared",
                    "--expected-manifest-json",
                    str(manifest_path),
                ]
            )
        receipt = json.loads(output.getvalue())
        self.assertEqual(code, 2)
        self.assertFalse(receipt["complete"])
        self.assertTrue(receipt["unresolved"])

    def test_cli_emits_structured_success(self):
        manifest_path = self.root / "manifest.json"
        manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        output = io.StringIO()
        with patch.object(
            prepare,
            "prepare_media",
            return_value={"schema": "test", "boot_verified": False},
        ), contextlib.redirect_stdout(output):
            code = prepare.main(
                [
                    "--source-root",
                    str(self.source),
                    "--staging-parent",
                    str(self.root),
                    "--name",
                    "prepared",
                    "--expected-manifest-json",
                    str(manifest_path),
                ]
            )
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())["complete"])

    def test_cli_cancel_signal_stops_before_staging(self):
        prepare.media.FAT32_MAX_FILE_BYTES = self.limit
        manifest_path = self.root / "manifest.json"
        manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        signal = self.root / "cancel.signal"
        signal.write_bytes(b"cancel")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = prepare.main(
                [
                    "--source-root",
                    str(self.source),
                    "--staging-parent",
                    str(self.root),
                    "--name",
                    "prepared",
                    "--expected-manifest-json",
                    str(manifest_path),
                    "--cancel-file",
                    str(signal),
                ]
            )
        receipt = json.loads(output.getvalue())
        self.assertEqual(code, 2)
        self.assertTrue(receipt["cancelled"])
        self.assertFalse((self.root / "prepared").exists())

    def test_dism_cancellation_terminates_and_waits(self):
        process = MagicMock()
        process.poll.side_effect = [None, 0]
        process.wait.return_value = -1
        with patch.object(
            prepare.subprocess, "Popen", return_value=process
        ) as popen, self.assertRaises(prepare.staging.StagingError):
            prepare._run_dism(
                ["dism.exe", "/Split-Image"], self.root / "transcript", lambda: True
            )
        process.terminate.assert_called_once()
        process.wait.assert_called_once_with(timeout=10)
        self.assertFalse(popen.call_args.kwargs["shell"])

    def test_cli_late_cancel_cannot_publish_success(self):
        manifest_path = self.root / "manifest.json"
        manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        signal = self.root / "cancel.signal"

        def finish(*args, **kwargs):
            signal.write_bytes(b"cancel")
            return {"staging_directory": str(self.root / "prepared"), "complete": True}

        output = io.StringIO()
        with patch.object(
            prepare, "prepare_media", side_effect=finish
        ), contextlib.redirect_stdout(output):
            code = prepare.main(
                [
                    "--source-root",
                    str(self.source),
                    "--staging-parent",
                    str(self.root),
                    "--name",
                    "prepared",
                    "--expected-manifest-json",
                    str(manifest_path),
                    "--cancel-file",
                    str(signal),
                ]
            )
        receipt = json.loads(output.getvalue())
        self.assertEqual(code, 2)
        self.assertFalse(receipt["complete"])
        self.assertTrue(receipt["cancelled"])


if __name__ == "__main__":
    unittest.main()
