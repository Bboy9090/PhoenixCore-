import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "inspect_bootcamp_driver_package.py"
)
SPEC = importlib.util.spec_from_file_location("bootcamp_driver_package", MODULE_PATH)
assert SPEC and SPEC.loader
bootcamp_driver_package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootcamp_driver_package)


class BootCampDriverPackageTests(unittest.TestCase):
    def valid_signature(self, path):
        return {
            "checked": True,
            "status": "Valid",
            "signer_subject": "CN=Apple Inc.",
        }

    def pending_signature(self, path):
        return {
            "checked": False,
            "status": "pending-windows-signature-check",
            "signer_subject": None,
        }

    def package(self, root):
        driver_dir = root / "BootCamp" / "Drivers"
        driver_dir.mkdir(parents=True)
        (driver_dir / "AppleKeyboard.sys").write_bytes(b"driver")
        (driver_dir / "BootCamp.msi").write_bytes(b"installer")
        (root / "ReadMe.txt").write_text("support software", encoding="utf-8")
        return root

    def test_manifest_requires_expected_hash(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = self.package(Path(tmpdir))
            first = bootcamp_driver_package.build_driver_manifest(
                root,
                mac_model="MacBookPro16,1",
                signature_inspector=self.valid_signature,
            )
            self.assertFalse(first["verified_for_model"])
            self.assertIn(
                "expected_manifest_sha256_missing",
                first["block_reasons"],
            )

    def test_exact_manifest_and_valid_signatures_verify(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = self.package(Path(tmpdir))
            first = bootcamp_driver_package.build_driver_manifest(
                root,
                mac_model="MacBookPro16,1",
                signature_inspector=self.valid_signature,
            )
            result = bootcamp_driver_package.build_driver_manifest(
                root,
                mac_model="MacBookPro16,1",
                expected_manifest_sha256=first["manifest_sha256"],
                signature_inspector=self.valid_signature,
            )
            self.assertTrue(result["verified_for_model"])
            self.assertEqual("MacBookPro16,1", result["mac_model_identifier"])

    def test_pending_signatures_keep_package_locked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = self.package(Path(tmpdir))
            first = bootcamp_driver_package.build_driver_manifest(
                root,
                mac_model="MacBookPro16,1",
                signature_inspector=self.pending_signature,
            )
            result = bootcamp_driver_package.build_driver_manifest(
                root,
                mac_model="MacBookPro16,1",
                expected_manifest_sha256=first["manifest_sha256"],
                signature_inspector=self.pending_signature,
            )
            self.assertFalse(result["verified_for_model"])
            self.assertIn(
                "driver_signature_verification_pending_on_windows",
                result["block_reasons"],
            )

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "real.sys"
            source.write_bytes(b"driver")
            link = root / "linked.sys"
            try:
                link.symlink_to(source)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaises(bootcamp_driver_package.BootCampDriverError):
                bootcamp_driver_package.build_driver_manifest(
                    root,
                    mac_model="MacBookPro16,1",
                    signature_inspector=self.valid_signature,
                )


if __name__ == "__main__":
    unittest.main()
