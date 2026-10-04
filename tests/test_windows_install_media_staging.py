import importlib.util
import tempfile
import unittest
from pathlib import Path
from tests.test_fat32_windows_media_plan import make_tree, write_wim

SPEC = importlib.util.spec_from_file_location("staging", Path(__file__).resolve().parents[1]
                                            / "scripts/hardware/stage_windows_install_media.py")
staging = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(staging)


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        write_wim(make_tree(self.source) / "install.wim")
        self.manifest = staging.media.capture_media_manifest(self.source)

    def tearDown(self):
        self.tmp.cleanup()

    def test_actual_bytes_are_readback_verified(self):
        progress = []
        receipt = staging.stage_media(self.source, self.root, "out", self.manifest,
                                      progress=lambda done, total: progress.append((done, total)))
        self.assertTrue(receipt["staging_verified"])
        self.assertFalse(receipt["boot_verified"])
        self.assertFalse(receipt["raw_disk_operations_performed"])
        self.assertTrue(receipt["staging_files_written"])
        self.assertEqual(progress[-1], (self.manifest["total_bytes"], self.manifest["total_bytes"]))
        self.assertEqual((self.root / "out/setup.exe").read_bytes(), b"setup")

    def test_stale_manifest_and_existing_destination_rejected(self):
        (self.source / "setup.exe").write_bytes(b"different")
        with self.assertRaises(staging.StagingError):
            staging.stage_media(self.source, self.root, "out", self.manifest)
        self.assertFalse((self.root / "out").exists())
        self.manifest = staging.media.capture_media_manifest(self.source)
        (self.root / "out").mkdir()
        with self.assertRaises(staging.StagingError):
            staging.stage_media(self.source, self.root, "out", self.manifest)

    def test_cancellation_retains_explicit_unresolved_directory(self):
        calls = 0
        def cancel():
            nonlocal calls
            calls += 1
            return calls >= 3
        with self.assertRaises(staging.StagingError) as caught:
            staging.stage_media(self.source, self.root, "out", self.manifest, cancelled=cancel)
        self.assertTrue(caught.exception.unresolved)
        self.assertEqual(caught.exception.partial_directory, self.root / "out")
        self.assertTrue((self.root / "out").exists())

    def test_source_overlap_and_symlink_parent_rejected(self):
        with self.assertRaises(staging.StagingError):
            staging.stage_media(self.source, self.source / ".." / "source", "out", self.manifest)
        with self.assertRaises(staging.StagingError):
            staging.stage_media(self.source, self.source, "out", self.manifest)
        (self.root / "link").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(staging.StagingError):
            staging.stage_media(self.source, self.root / "link", "out", self.manifest)

    def test_windows_unsafe_names_rejected(self):
        for name in ("CON", "nul.txt", "trailing.", "trailing ", "bad?name"):
            with self.subTest(name=name), self.assertRaises(staging.StagingError):
                staging.stage_media(self.source, self.root, name, self.manifest)

    def test_blocked_media_never_creates_destination(self):
        (self.source / "setup.exe").unlink()
        self.manifest = staging.media.capture_media_manifest(self.source)
        with self.assertRaises(staging.StagingError):
            staging.stage_media(self.source, self.root, "out", self.manifest)
        self.assertFalse((self.root / "out").exists())


if __name__ == "__main__":
    unittest.main()
