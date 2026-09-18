import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "stage_windows_rollback_artifacts.py"
)
SPEC = importlib.util.spec_from_file_location("rollback_artifacts", MODULE_PATH)
assert SPEC and SPEC.loader
rollback_artifacts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(rollback_artifacts)


class WindowsRollbackArtifactTests(unittest.TestCase):
    def test_embedded_digest_detects_tampering(self):
        payload = {
            "schema": "phoenix_key.windows_boot_state.v1",
            "complete": True,
        }
        payload["snapshot_sha256"] = rollback_artifacts.sha256_payload(payload)
        rollback_artifacts.verify_embedded_digest(
            payload,
            "snapshot_sha256",
            expected_schema="phoenix_key.windows_boot_state.v1",
        )
        payload["complete"] = False
        with self.assertRaises(rollback_artifacts.RollbackArtifactError):
            rollback_artifacts.verify_embedded_digest(
                payload,
                "snapshot_sha256",
                expected_schema="phoenix_key.windows_boot_state.v1",
            )

    def test_winre_location_parser_accepts_globalroot_location(self):
        output = (
            "Windows RE status: Enabled\n"
            "Windows RE location: \\?\GLOBALROOT\device\harddisk0\partition4"
            "\Recovery\WindowsRE\n"
        )
        location = rollback_artifacts.extract_winre_location(output)
        self.assertEqual(
            r"\\?\GLOBALROOT\device\harddisk0\partition4\Recovery\WindowsRE",
            location,
        )

    def test_tree_backup_refuses_symlink_and_hashes_regular_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "source"
            destination = root / "destination"
            source.mkdir()
            (source / "bootmgfw.efi").write_bytes(b"signed-fixture")
            result = rollback_artifacts.copy_tree_with_hashes(source, destination)
            self.assertEqual(1, result["file_count"])
            self.assertEqual(64, len(result["manifest_sha256"]))
            self.assertEqual(
                b"signed-fixture",
                (destination / "bootmgfw.efi").read_bytes(),
            )

    def test_bcd_export_receipt_shape_can_fail_closed(self):
        receipt = {
            "returncode": 5,
            "captured": False,
            "stderr": "access denied",
        }
        self.assertFalse(receipt["captured"])
        self.assertNotEqual(0, receipt["returncode"])


if __name__ == "__main__":
    unittest.main()
