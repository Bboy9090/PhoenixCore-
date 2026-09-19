import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "plan_fat32_windows_media.py"
)
SPEC = importlib.util.spec_from_file_location("fat32_media", MODULE_PATH)
assert SPEC and SPEC.loader
media = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(media)


def write_wim(path: Path, size: int = media.WIM_HEADER_SIZE) -> None:
    header = bytearray(media.WIM_HEADER_SIZE)
    header[:8] = b"MSWIM\0\0\0"
    header[8:12] = media.WIM_HEADER_SIZE.to_bytes(4, "little")
    path.write_bytes(header)
    if size > len(header):
        with path.open("r+b") as stream:
            stream.truncate(size)


def make_tree(root: Path) -> Path:
    sources = root / "sources"
    efi = root / "EFI" / "Boot"
    sources.mkdir(parents=True)
    efi.mkdir(parents=True)
    (root / "setup.exe").write_bytes(b"setup")
    write_wim(sources / "boot.wim")
    (efi / "bootx64.efi").write_bytes(b"efi")
    return sources


class Fat32WindowsMediaPlanTests(unittest.TestCase):
    def setUp(self):
        self.real_fat32_max = media.FAT32_MAX_FILE_BYTES
        media.FAT32_MAX_FILE_BYTES = 1023

    def tearDown(self):
        media.FAT32_MAX_FILE_BYTES = self.real_fat32_max

    def test_small_wim_media_is_ready_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sources = make_tree(root)
            write_wim(sources / "install.wim")
            result = media.plan_media(root)
            self.assertTrue(result["ready_for_fat32_copy_now"])
            self.assertFalse(result["split_required"])
            self.assertTrue(result["uefi_boot_evidence_present"])
            self.assertFalse(result["source_modified"])
            self.assertFalse(result["target_disk_modified"])

    def test_oversized_install_wim_gets_official_split_plan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sources = make_tree(root)
            install = sources / "install.wim"
            write_wim(install, media.FAT32_MAX_FILE_BYTES + 1)
            result = media.plan_media(root)
            self.assertTrue(result["split_required"])
            self.assertTrue(result["ready_for_fat32_copy_after_split"])
            command = result["split_command_preview"]
            self.assertEqual("Dism", command[0])
            self.assertIn("/Split-Image", command)
            self.assertIn("/SWMFile:" + str(sources / "install.swm"), command)
            self.assertIn("/FileSize:3800", command)
            self.assertIn("/CheckIntegrity", command)
            self.assertFalse(result["execution_performed"])

    def test_other_oversized_file_blocks_fat32_plan(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sources = make_tree(root)
            write_wim(sources / "install.wim")
            other = root / "payload.bin"
            other.write_bytes(b"x")
            with other.open("r+b") as stream:
                stream.truncate(media.FAT32_MAX_FILE_BYTES + 1)
            result = media.plan_media(root)
            self.assertFalse(result["ready_for_fat32_copy_now"])
            self.assertIn(
                "other_media_file_exceeds_fat32_limit",
                result["block_reasons"],
            )

    def test_oversized_esd_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sources = make_tree(root)
            install = sources / "install.esd"
            write_wim(install, media.FAT32_MAX_FILE_BYTES + 1)
            result = media.plan_media(root)
            self.assertIn(
                "oversized_install_esd_requires_supported_conversion",
                result["block_reasons"],
            )
            self.assertIsNone(result["split_command_preview"])

    def test_contiguous_split_wim_set_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sources = make_tree(root)
            write_wim(sources / "install.swm")
            write_wim(sources / "install2.swm")
            write_wim(sources / "install3.swm")
            result = media.plan_media(root)
            self.assertEqual("split_wim", result["image_mode"])
            self.assertTrue(result["ready_for_fat32_copy_now"])
            self.assertEqual(3, len(result["split_segments"]))

    def test_missing_split_segment_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sources = make_tree(root)
            write_wim(sources / "install.swm")
            write_wim(sources / "install3.swm")
            result = media.plan_media(root)
            self.assertIn(
                "split_wim_sequence_incomplete",
                result["block_reasons"],
            )

    def test_missing_uefi_boot_file_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sources = make_tree(root)
            write_wim(sources / "install.wim")
            (root / "EFI" / "Boot" / "bootx64.efi").unlink()
            result = media.plan_media(root)
            self.assertIn("uefi_boot_file_missing", result["block_reasons"])


if __name__ == "__main__":
    unittest.main()
