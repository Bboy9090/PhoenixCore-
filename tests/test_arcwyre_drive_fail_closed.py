import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ecosystem.bootforge_builder import BootForgeBuilder
from ecosystem.flash_validator import BareMetalFlashValidator
from ecosystem.multiboot_engine import MultiBootPayloadEngine


class ArcwyreDriveFailClosedTests(unittest.TestCase):
    def test_iso_manifest_is_not_packaging_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            kernel = root / "kernel.bin"
            apps = root / "apps"
            output = root / "arcwyre.iso"
            kernel.write_bytes(b"kernel")
            apps.mkdir()

            self.assertFalse(
                BootForgeBuilder(root).assemble_hybrid_iso(kernel, apps, output)
            )
            manifest = json.loads((root / "bootforge-manifest.json").read_text())
            self.assertNotIn("output_iso_sha256", manifest)

    def test_multiboot_manifest_hashes_real_payloads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "linux.iso"
            payload.write_bytes(b"verified-payload")
            engine = MultiBootPayloadEngine(str(root))
            engine.add_payload("Linux", str(payload), "linux")

            manifest_path = Path(
                engine.write_manifest({"target_identity": "test-fixture"})
            )
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(
                manifest["payloads"][0]["sha256"],
                hashlib.sha256(b"verified-payload").hexdigest(),
            )

    def test_multiboot_manifest_rejects_missing_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = MultiBootPayloadEngine(directory)
            engine.add_payload("Missing", str(Path(directory) / "missing.iso"), "linux")
            with self.assertRaises(FileNotFoundError):
                engine.write_manifest({"target_identity": "test-fixture"})

    def test_multiboot_manifest_requires_target_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = MultiBootPayloadEngine(directory)
            with self.assertRaises(ValueError):
                engine.write_manifest({})

    def test_flash_validator_never_passes_missing_target(self):
        self.assertFalse(
            BareMetalFlashValidator("/definitely/missing").verify_sector_integrity(
                "0" * 64
            )
        )

    def test_flash_validator_hashes_actual_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "target.img"
            image.write_bytes(b"readback")
            expected = hashlib.sha256(b"readback").hexdigest()
            self.assertTrue(
                BareMetalFlashValidator(str(image)).verify_sector_integrity(expected)
            )
            self.assertFalse(
                BareMetalFlashValidator(str(image)).verify_sector_integrity("0" * 64)
            )


if __name__ == "__main__":
    unittest.main()
