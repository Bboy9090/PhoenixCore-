import importlib.util
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
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


class WindowsStatIdentityTests(unittest.TestCase):
    def test_cross_acquisition_creation_time_preserves_file_identity(self):
        common = dict(st_dev=12, st_ino=34, st_size=56, st_mtime_ns=78, st_birthtime_ns=90)
        path = SimpleNamespace(**common, st_ctime_ns=90)
        descriptor = SimpleNamespace(**common, st_ctime_ns=100)
        with patch.object(media.os, "name", "nt"):
            self.assertEqual(media.file_stat_identity(path), media.file_stat_identity(descriptor))
            replaced = SimpleNamespace(**{**common, "st_ino": 35}, st_ctime_ns=100)
            self.assertNotEqual(media.file_stat_identity(path), media.file_stat_identity(replaced))

    def test_missing_windows_creation_time_fails_closed(self):
        info = SimpleNamespace(st_dev=12, st_ino=34, st_size=56, st_mtime_ns=78, st_ctime_ns=90)
        with patch.object(media.os, "name", "nt"), self.assertRaises(media.MediaPlanError):
            media.file_stat_identity(info)

    def test_posix_change_time_remains_part_of_identity(self):
        common = dict(st_dev=12, st_ino=34, st_size=56, st_mtime_ns=78)
        with patch.object(media.os, "name", "posix"):
            self.assertNotEqual(media.file_stat_identity(SimpleNamespace(**common, st_ctime_ns=90)),
                                media.file_stat_identity(SimpleNamespace(**common, st_ctime_ns=100)))


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
    def test_manifest_rejects_windows_unsafe_names(self):
        for name in ("payload:stream", "CON.txt", "LPT1", "bad?name", "bad\\name"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                if media.os.name == "nt" and "\\" in name:
                    continue  # Backslash is a separator, not a representable filename.
                with patch.object(media, "_walk_regular_files_nofollow", return_value=[(root / name, root.stat())]), self.assertRaises(media.MediaPlanError):
                    media.capture_media_manifest(root)

    @unittest.skipUnless(media.os.name == "nt", "Named data streams require Windows")
    def test_actual_named_file_and_directory_streams_block_manifest(self):
        for target in ("file", "directory"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                payload = root / "payload"
                payload.write_bytes(b"data")
                stream_path = payload if target == "file" else root
                try:
                    Path(str(stream_path) + ":arcwyre-test").write_bytes(b"hidden data")
                except OSError as exc:
                    self.skipTest(f"Filesystem cannot create named streams: {exc}")
                with self.assertRaises(media.MediaPlanError):
                    media.capture_media_manifest(root)

    def test_manifest_verification_rejects_added_missing_and_changed_files(self):
        for mutation in ("added", "missing", "changed"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                (root / "payload").write_bytes(b"original")
                expected = media.capture_media_manifest(root)
                self.assertEqual(expected, media.verify_media_manifest(root, expected))
                if mutation == "added":
                    (root / "extra").write_bytes(b"extra")
                elif mutation == "missing":
                    (root / "payload").unlink()
                else:
                    (root / "payload").write_bytes(b"modified")
                with self.assertRaises(media.MediaPlanError):
                    media.verify_media_manifest(root, expected)

    def test_manifest_binds_actual_source_bytes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sources = make_tree(root)
            write_wim(sources / "install.wim")
            first = media.capture_media_manifest(root)
            self.assertEqual(first, media.capture_media_manifest(root))
            (root / "setup.exe").write_bytes(b"changed")
            self.assertNotEqual(first["manifest_sha256"], media.capture_media_manifest(root)["manifest_sha256"])
            self.assertFalse(first["provenance_verified"])

    def test_manifest_rejects_case_collisions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "Setup.exe").write_bytes(b"one")
            (root / "setup.exe").write_bytes(b"two")
            if (root / "Setup.exe").samefile(root / "setup.exe"):
                self.skipTest("Filesystem cannot represent distinct case-colliding files")
            with self.assertRaises(media.MediaPlanError):
                media.capture_media_manifest(root)

    def test_competing_image_families_are_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sources = make_tree(root)
            write_wim(sources / "install.wim")
            write_wim(sources / "install.esd")
            result = media.plan_media(root)
            self.assertIn("multiple_windows_install_image_families", result["block_reasons"])
            self.assertFalse(result["ready_for_fat32_copy_now"])
            self.assertFalse(result["ready_for_fat32_copy_after_split"])

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
            swm_argument = next(
                value for value in command if value.startswith("/SWMFile:")
            )
            self.assertTrue(
                swm_argument.replace("\\", "/")
                .casefold()
                .endswith("/sources/install.swm")
            )
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

    def test_nested_symlink_directory_is_rejected_before_traversal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "media"
            root.mkdir()
            sources = make_tree(root)
            write_wim(sources / "install.wim")
            outside = Path(tmpdir) / "outside"
            outside.mkdir()
            (outside / "payload.bin").write_bytes(b"outside")
            link = root / "linked-outside"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaises(media.MediaPlanError) as caught:
                media.plan_media(root)
            self.assertRegex(
                str(caught.exception),
                r"symbolic links|junctions|reparse points",
            )

    def test_symlinked_media_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            actual = Path(tmpdir) / "actual"
            actual.mkdir()
            sources = make_tree(actual)
            write_wim(sources / "install.wim")
            link = Path(tmpdir) / "media-link"
            try:
                link.symlink_to(actual, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"symlink creation unavailable: {exc}")
            with self.assertRaises(media.MediaPlanError) as caught:
                media.plan_media(link)
            self.assertRegex(
                str(caught.exception),
                r"symbolic links|junctions|reparse points",
            )

    def test_special_files_are_rejected_in_media_tree(self):
        if not hasattr(__import__("os"), "mkfifo"):
            self.skipTest("FIFO creation unavailable on this platform")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            sources = make_tree(root)
            write_wim(sources / "install.wim")
            fifo = root / "unexpected.pipe"
            try:
                __import__("os").mkfifo(fifo)
            except OSError as exc:
                self.skipTest(f"FIFO creation unavailable: {exc}")
            with self.assertRaises(media.MediaPlanError) as caught:
                media.plan_media(root)
            self.assertIn("regular files and directories", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
