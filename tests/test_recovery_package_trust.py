import importlib.util
import hashlib
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "inspect_recovery_package_trust.py"
)
SPEC = importlib.util.spec_from_file_location("recovery_package_trust", MODULE_PATH)
assert SPEC and SPEC.loader
recovery_package_trust = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(recovery_package_trust)


class RecoveryPackageTrustTests(unittest.TestCase):
    def package(self, root: Path, name: str, content: bytes = b"package") -> Path:
        path = root / name
        path.write_bytes(content)
        return path

    def digest(self, content: bytes = b"package") -> str:
        return hashlib.sha256(content).hexdigest()

    def valid_signature(self, subject="CN=Microsoft Windows"):
        return {
            "checked": True,
            "status": "Valid",
            "status_message": "Signature verified.",
            "signer_subject": subject,
            "signer_thumbprint": "A" * 40,
        }

    def test_missing_expected_hash_never_verifies(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = self.package(Path(tmpdir), "recovery.iso")
            result = recovery_package_trust.evaluate_package_trust(
                package,
                expected_sha256=None,
            )
            self.assertFalse(result["verified_for_use"])
            self.assertIn("expected_sha256_missing", result["block_reasons"])

    def test_wrong_hash_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = self.package(Path(tmpdir), "recovery.wim")
            result = recovery_package_trust.evaluate_package_trust(
                package,
                expected_sha256="0" * 64,
            )
            self.assertFalse(result["verified_for_use"])
            self.assertIn("sha256_mismatch", result["block_reasons"])

    def test_disk_image_can_verify_against_external_hash_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = self.package(Path(tmpdir), "recovery.iso")
            result = recovery_package_trust.evaluate_package_trust(
                package,
                expected_sha256=self.digest(),
            )
            self.assertTrue(result["verified_for_use"])
            self.assertEqual("external_hash_manifest", result["trust_route"])

    def test_signed_windows_binary_requires_valid_authenticode(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = self.package(Path(tmpdir), "driver.exe")
            result = recovery_package_trust.evaluate_package_trust(
                package,
                expected_sha256=self.digest(),
                expected_signer_contains="Microsoft",
                signature_record=self.valid_signature(),
            )
            self.assertTrue(result["verified_for_use"])
            self.assertTrue(result["signer_matches"])

    def test_invalid_signature_blocks_windows_binary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = self.package(Path(tmpdir), "driver.sys")
            invalid = self.valid_signature()
            invalid["status"] = "HashMismatch"
            result = recovery_package_trust.evaluate_package_trust(
                package,
                expected_sha256=self.digest(),
                signature_record=invalid,
            )
            self.assertFalse(result["verified_for_use"])
            self.assertIn(
                "authenticode_signature_not_valid",
                result["block_reasons"],
            )

    def test_expected_signer_mismatch_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            package = self.package(Path(tmpdir), "firmware.exe")
            result = recovery_package_trust.evaluate_package_trust(
                package,
                expected_sha256=self.digest(),
                expected_signer_contains="HP Inc.",
                signature_record=self.valid_signature("CN=Unknown Vendor"),
            )
            self.assertFalse(result["verified_for_use"])
            self.assertIn("signer_subject_mismatch", result["block_reasons"])


if __name__ == "__main__":
    unittest.main()
