import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "inspect_windows_image_metadata.py"
)
SPEC = importlib.util.spec_from_file_location("windows_image_metadata", MODULE_PATH)
assert SPEC and SPEC.loader
windows_image_metadata = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(windows_image_metadata)


class FakeDism:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def __call__(self, command, **kwargs):
        self.calls.append(command)
        output = self.outputs.pop(0)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=output,
            stderr="",
        )


class WindowsImageMetadataTests(unittest.TestCase):
    def image(self, root, name="install.wim"):
        path = Path(root) / name
        path.write_bytes(b"fixture")
        return path

    def detail(self, index, name, architecture, edition):
        return (
            f"Index : {index}\n"
            f"Name : {name}\n"
            f"Description : {name}\n"
            f"Architecture : {architecture}\n"
            f"Edition : {edition}\n"
            "Product Name : Microsoft Windows Operating System\n"
            "Installation Type : Client\n"
            "Version : 10.0.26100\n"
        )

    def test_multi_index_wim_requires_explicit_selection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self.image(tmpdir)
            runner = FakeDism(
                [
                    "Index : 1\nName : Windows 11 Home\nIndex : 2\nName : Windows 11 Pro\n",
                    self.detail(1, "Windows 11 Home", "x64", "Core"),
                    self.detail(2, "Windows 11 Pro", "x64", "Professional"),
                ]
            )
            old_platform = windows_image_metadata.sys.platform
            windows_image_metadata.sys.platform = "win32"
            try:
                result = windows_image_metadata.inspect_windows_image(
                    path, runner=runner
                )
            finally:
                windows_image_metadata.sys.platform = old_platform
            self.assertTrue(result["selection_required"])
            self.assertFalse(result["restore_eligible"])
            self.assertIn(
                "explicit_image_index_selection_required",
                result["block_reasons"],
            )

    def test_selected_index_returns_architecture_and_edition(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self.image(tmpdir)
            runner = FakeDism(
                [
                    "Index : 1\nName : Windows 11 Home\nIndex : 2\nName : Windows 11 Pro\n",
                    self.detail(1, "Windows 11 Home", "x64", "Core"),
                    self.detail(2, "Windows 11 Pro", "x64", "Professional"),
                ]
            )
            old_platform = windows_image_metadata.sys.platform
            windows_image_metadata.sys.platform = "win32"
            try:
                result = windows_image_metadata.inspect_windows_image(
                    path, selected_index=2, runner=runner
                )
            finally:
                windows_image_metadata.sys.platform = old_platform
            self.assertTrue(result["restore_eligible"])
            self.assertEqual("Professional", result["selected_image"]["edition_id"])
            self.assertEqual("x64", result["selected_image"]["architecture"])

    def test_rust_x86_64_host_alias_matches_x64_image(self):
        metadata = {
            "selected_image": {
                "index": 1,
                "architecture": "x64",
            }
        }
        result = windows_image_metadata.assess_architecture_compatibility(
            metadata, "x86_64"
        )
        self.assertTrue(result["compatible"])
        self.assertEqual("x64", result["target_architecture"])

    def test_image_size_is_parsed_for_capacity_gating(self):
        self.assertEqual(
            20_000_000_000,
            windows_image_metadata.parse_size_bytes("20,000,000,000 bytes"),
        )

    def test_architecture_mismatch_blocks_restore(self):
        metadata = {
            "selected_image": {
                "index": 1,
                "architecture": "x64",
            }
        }
        result = windows_image_metadata.assess_architecture_compatibility(
            metadata, "arm64"
        )
        self.assertFalse(result["compatible"])
        self.assertIn(
            "source_target_architecture_mismatch",
            result["block_reasons"],
        )

    def test_vhdx_uses_required_index_one_without_unindexed_probe(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self.image(tmpdir, "windows.vhdx")
            runner = FakeDism([self.detail(1, "Windows 11 Pro", "x64", "Professional")])
            old_platform = windows_image_metadata.sys.platform
            windows_image_metadata.sys.platform = "win32"
            try:
                result = windows_image_metadata.inspect_windows_image(
                    path, runner=runner
                )
            finally:
                windows_image_metadata.sys.platform = old_platform
            self.assertTrue(result["restore_eligible"])
            self.assertEqual(1, result["selected_index"])
            self.assertEqual(1, len(runner.calls))
            self.assertIn("/Index:1", runner.calls[0])

    def test_iso_is_never_mounted_for_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self.image(tmpdir, "windows.iso")
            result = windows_image_metadata.inspect_windows_image(path)
            self.assertFalse(result["metadata_verified"])
            self.assertFalse(result["restore_eligible"])
            self.assertIn(
                "iso_requires_extracted_install_wim_or_esd",
                result["block_reasons"],
            )

    def test_single_split_wim_segment_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self.image(tmpdir, "install.swm")
            result = windows_image_metadata.inspect_windows_image(path)
            self.assertFalse(result["restore_eligible"])
            self.assertEqual(1, result["split_wim"]["segment_count"])
            self.assertIn(
                "split_wim_requires_multiple_segments",
                result["block_reasons"],
            )

    def test_split_wim_gap_is_blocked_before_dism(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = self.image(root, "install.swm")
            self.image(root, "install3.swm")
            result = windows_image_metadata.inspect_windows_image(path)
            self.assertFalse(result["restore_eligible"])
            self.assertEqual([2], result["split_wim"]["missing_segments"])
            self.assertIn("split_wim_segment_gap", result["block_reasons"])

    def test_complete_split_wim_set_can_be_inspected_read_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = self.image(root, "install.swm")
            self.image(root, "install2.swm")
            runner = FakeDism(
                [
                    "Index : 1\nName : Windows 11 Pro\n",
                    self.detail(1, "Windows 11 Pro", "x64", "Professional"),
                ]
            )
            old_platform = windows_image_metadata.sys.platform
            windows_image_metadata.sys.platform = "win32"
            try:
                result = windows_image_metadata.inspect_windows_image(
                    path, selected_index=1, runner=runner
                )
            finally:
                windows_image_metadata.sys.platform = old_platform
            self.assertTrue(result["split_wim"]["complete"])
            self.assertEqual(2, result["split_wim"]["segment_count"])
            self.assertTrue(result["restore_eligible"])
            self.assertTrue(runner.calls[0][-1].lower().endswith("install.swm"))


if __name__ == "__main__":
    unittest.main()
