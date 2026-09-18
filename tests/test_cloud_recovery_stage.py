import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "stage_cloud_recovery_payload.py"
)
SPEC = importlib.util.spec_from_file_location("cloud_recovery_stage", MODULE_PATH)
assert SPEC and SPEC.loader
cloud_recovery_stage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cloud_recovery_stage)


class CloudRecoveryStageTests(unittest.TestCase):
    def digests(self, content):
        return (
            hashlib.md5(content).hexdigest(),
            hashlib.sha256(content).hexdigest(),
        )

    def test_complete_stage_requires_trusted_sha256_for_recovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            content = b"cloud-backup" * 1024
            source = root / "provider.bin"
            source.write_bytes(content)
            md5, sha256 = self.digests(content)
            result = cloud_recovery_stage.stage_cloud_payload(
                source_file=source,
                destination=root / "staged.vhdx",
                provider="google-drive",
                provider_file_id="file-123",
                provider_name="backup.vhdx",
                provider_size_bytes=len(content),
                provider_md5=md5,
                expected_sha256=sha256,
            )
            self.assertTrue(result["transfer_integrity_verified"])
            self.assertTrue(result["recovery_trust_verified"])
            self.assertTrue(result["recovery_eligible"])
            self.assertFalse(result["cloud_original_modified"])
            self.assertEqual(content, source.read_bytes())
            self.assertEqual(content, (root / "staged.vhdx").read_bytes())

    def test_md5_only_proves_transfer_not_recovery_trust(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            content = b"cloud-backup"
            source = root / "provider.bin"
            source.write_bytes(content)
            md5, _ = self.digests(content)
            result = cloud_recovery_stage.stage_cloud_payload(
                source_file=source,
                destination=root / "staged.vhdx",
                provider="google-drive",
                provider_file_id="file-123",
                provider_name="backup.vhdx",
                provider_size_bytes=len(content),
                provider_md5=md5,
            )
            self.assertTrue(result["transfer_integrity_verified"])
            self.assertFalse(result["recovery_trust_verified"])
            self.assertFalse(result["recovery_eligible"])
            self.assertIn("trusted_sha256_not_verified", result["block_reasons"])

    def test_interrupted_stage_resumes_only_after_prefix_verification(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            content = b"0123456789" * 1000
            source = root / "provider.bin"
            source.write_bytes(content)
            md5, sha256 = self.digests(content)
            first = cloud_recovery_stage.stage_cloud_payload(
                source_file=source,
                destination=root / "staged.vhdx",
                provider="google-drive",
                provider_file_id="file-123",
                provider_name="backup.vhdx",
                provider_size_bytes=len(content),
                provider_md5=md5,
                expected_sha256=sha256,
                stop_after_bytes=2048,
            )
            self.assertTrue(first["interrupted"])
            self.assertFalse(first["recovery_eligible"])
            self.assertEqual(2048, first["staged_size_bytes"])

            second = cloud_recovery_stage.stage_cloud_payload(
                source_file=source,
                destination=root / "staged.vhdx",
                provider="google-drive",
                provider_file_id="file-123",
                provider_name="backup.vhdx",
                provider_size_bytes=len(content),
                provider_md5=md5,
                expected_sha256=sha256,
            )
            self.assertEqual(2048, second["resume_offset_bytes"])
            self.assertTrue(second["recovery_eligible"])

    def test_corrupt_partial_is_rejected_instead_of_resumed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            content = b"0123456789" * 100
            source = root / "provider.bin"
            source.write_bytes(content)
            destination = root / "staged.vhdx"
            partial = root / "staged.vhdx.partial"
            partial.write_bytes(b"wrong-prefix")
            _, sha256 = self.digests(content)
            with self.assertRaises(cloud_recovery_stage.CloudStageError):
                cloud_recovery_stage.stage_cloud_payload(
                    source_file=source,
                    destination=destination,
                    provider="google-drive",
                    provider_file_id="file-123",
                    provider_name="backup.vhdx",
                    provider_size_bytes=len(content),
                    expected_sha256=sha256,
                )

    def test_destination_cannot_replace_cloud_materialized_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            content = b"cloud-original"
            source = root / "provider.bin"
            source.write_bytes(content)
            _, sha256 = self.digests(content)
            with self.assertRaisesRegex(
                cloud_recovery_stage.CloudStageError,
                "destination must be distinct",
            ):
                cloud_recovery_stage.stage_cloud_payload(
                    source_file=source,
                    destination=source,
                    provider="google-drive",
                    provider_file_id="file-123",
                    provider_name="backup.vhdx",
                    provider_size_bytes=len(content),
                    expected_sha256=sha256,
                )
            self.assertEqual(content, source.read_bytes())

    def test_partial_path_cannot_alias_cloud_materialized_source(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            content = b"cloud-original"
            destination = root / "staged.vhdx"
            source = root / "staged.vhdx.partial"
            source.write_bytes(content)
            _, sha256 = self.digests(content)
            with self.assertRaisesRegex(
                cloud_recovery_stage.CloudStageError,
                "destination must be distinct",
            ):
                cloud_recovery_stage.stage_cloud_payload(
                    source_file=source,
                    destination=destination,
                    provider="google-drive",
                    provider_file_id="file-123",
                    provider_name="backup.vhdx",
                    provider_size_bytes=len(content),
                    expected_sha256=sha256,
                )
            self.assertEqual(content, source.read_bytes())

    def test_provider_size_mismatch_fails_before_staging(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "provider.bin"
            source.write_bytes(b"1234")
            with self.assertRaises(cloud_recovery_stage.CloudStageError):
                cloud_recovery_stage.stage_cloud_payload(
                    source_file=source,
                    destination=root / "staged.vhdx",
                    provider="google-drive",
                    provider_file_id="file-123",
                    provider_name="backup.vhdx",
                    provider_size_bytes=999,
                    expected_sha256="a" * 64,
                )


if __name__ == "__main__":
    unittest.main()
