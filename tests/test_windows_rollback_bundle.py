import importlib.util
import tempfile
import unittest
from pathlib import Path

BOOT_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "capture_windows_boot_state.py"
)
BUNDLE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "persist_windows_rollback_bundle.py"
)

boot_spec = importlib.util.spec_from_file_location("windows_boot_state", BOOT_PATH)
assert boot_spec and boot_spec.loader
windows_boot_state = importlib.util.module_from_spec(boot_spec)
boot_spec.loader.exec_module(windows_boot_state)

bundle_spec = importlib.util.spec_from_file_location(
    "windows_rollback_bundle", BUNDLE_PATH
)
assert bundle_spec and bundle_spec.loader
windows_rollback_bundle = importlib.util.module_from_spec(bundle_spec)
bundle_spec.loader.exec_module(windows_rollback_bundle)


class WindowsRollbackBundleTests(unittest.TestCase):
    def snapshot(self):
        partition_payload = {
            "SecureBootEnabled": True,
            "Partitions": [
                {
                    "DiskNumber": 0,
                    "PartitionNumber": 1,
                    "DriveLetter": None,
                    "Offset": 1048576,
                    "Size": 272629760,
                    "GptType": "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}",
                }
            ],
        }
        command = lambda name, stdout: {
            "command": name,
            "arguments": [],
            "returncode": 0,
            "stdout": stdout,
            "stderr": "",
            "stdout_sha256": windows_boot_state.sha256_text(stdout),
            "stderr_sha256": windows_boot_state.sha256_text(""),
        }
        return windows_boot_state.build_boot_state_snapshot(
            partition_payload=partition_payload,
            bcd_record=command("bcdedit.exe", "BCD DATA"),
            winre_record=command(
                "reagentc.exe",
                "Windows RE status: Enabled\nWindows RE location: "
                r"\\?\GLOBALROOT\device\harddisk0\partition4\Recovery\WindowsRE",
            ),
            captured_at="2026-09-17T22:00:00Z",
        )

    def rollback_manifest(self, snapshot):
        manifest = {
            "schema": "phoenix_key.rollback_manifest.v1",
            "created_at": "2026-09-17T22:00:30Z",
            "source": {
                "path": r"E:\backup\install.wim",
                "identity_sha256": "b" * 64,
            },
            "target": {
                "scope": "online_current_windows_boot_repair",
                "physical_target": r"\\.\PHYSICALDRIVE7",
                "identity_sha256": "a" * 64,
                "size_bytes": 64000000000,
                "partition_style": "GPT",
                "partitions": [],
            },
            "boot_state_snapshot_sha256": snapshot["snapshot_sha256"],
            "boot_state_complete": True,
            "required_backup_artifacts_before_repair": [
                "partition_table_backup",
                "efi_system_partition_file_backup",
                "bcd_store_export",
                "winre_configuration_and_image_identity",
            ],
            "repair_unlock_ready": False,
            "repair_unlock_block_reasons": ["fixture"],
            "system_mutations_performed": False,
        }
        manifest["manifest_sha256"] = windows_rollback_bundle.sha256_payload(manifest)
        return manifest

    def persisted_file_status(self, path):
        path.write_bytes(b"fixture")
        return {
            "status": "persisted",
            "path": str(path),
            "sha256": windows_rollback_bundle.file_sha256(path),
            "size_bytes": path.stat().st_size,
        }

    def persisted_tree_status(self, root):
        source = root / "efi-source"
        destination = root / "efi-backup"
        source.mkdir()
        (source / "bootmgfw.efi").write_bytes(b"efi-fixture")
        return windows_rollback_bundle.copy_tree_with_hashes(source, destination)

    def test_complete_fixture_bundle_unlocks_only_repair_scope(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            snapshot = self.snapshot()
            bundle = windows_rollback_bundle.build_fixture_bundle(
                boot_state=snapshot,
                rollback_manifest=self.rollback_manifest(snapshot),
                output_dir=root,
                bcd_export_status=self.persisted_file_status(root / "bcd_store.bak"),
                efi_backup_status=self.persisted_tree_status(root),
                winre_config_status=self.persisted_file_status(root / "ReAgent.xml"),
                winre_status=self.persisted_file_status(root / "Winre.wim"),
                created_at="2026-09-17T22:01:00Z",
            )
            self.assertTrue(bundle["complete"])
            self.assertTrue(bundle["repair_unlock_ready"])
            self.assertEqual(
                ["bcd_repair", "winre_repair", "efi_file_repair"],
                bundle["repair_unlock_scope"],
            )
            self.assertIn("repartition_disk", bundle["always_blocked_by_this_bundle"])
            self.assertFalse(bundle["system_configuration_mutated"])
            self.assertFalse(bundle["efi_mounted_by_bundle_tool"])

    def test_missing_efi_backup_keeps_repair_locked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            snapshot = self.snapshot()
            bundle = windows_rollback_bundle.build_fixture_bundle(
                boot_state=snapshot,
                rollback_manifest=self.rollback_manifest(snapshot),
                output_dir=root,
                bcd_export_status=self.persisted_file_status(root / "bcd_store.bak"),
                efi_backup_status={
                    "status": "not-directly-accessible",
                    "path": None,
                    "manifest_sha256": None,
                    "file_count": 0,
                },
                winre_config_status=self.persisted_file_status(root / "ReAgent.xml"),
                winre_status=self.persisted_file_status(root / "Winre.wim"),
            )
            self.assertFalse(bundle["complete"])
            self.assertFalse(bundle["repair_unlock_ready"])
            self.assertIn(
                "efi_file_backup",
                bundle["missing_or_unverified_artifacts"],
            )

    def test_globalroot_winre_path_is_not_traversed(self):
        path = windows_rollback_bundle.windows_path_from_winre_location(
            r"\\?\GLOBALROOT\device\harddisk0\partition4\Recovery\WindowsRE"
        )
        self.assertIsNone(path)

    def test_drive_letter_winre_location_can_be_resolved_without_mounting(self):
        path = windows_rollback_bundle.windows_path_from_winre_location(
            r"R:\Recovery\WindowsRE"
        )
        self.assertEqual(Path(r"R:\Recovery\WindowsRE") / "Winre.wim", path)

    def test_tampered_boot_snapshot_is_rejected(self):
        snapshot = self.snapshot()
        snapshot["secure_boot_enabled"] = False
        with self.assertRaises(windows_rollback_bundle.RollbackBundleError):
            windows_rollback_bundle.verify_boot_state(snapshot)

    def test_wrong_rollback_scope_is_rejected(self):
        snapshot = self.snapshot()
        manifest = self.rollback_manifest(snapshot)
        manifest["target"]["scope"] = "full_disk_restore"
        manifest["manifest_sha256"] = windows_rollback_bundle.sha256_payload(manifest)
        with self.assertRaises(windows_rollback_bundle.RollbackBundleError):
            windows_rollback_bundle.verify_rollback_manifest(manifest, snapshot)

    def test_rollback_manifest_must_match_boot_snapshot(self):
        snapshot = self.snapshot()
        manifest = self.rollback_manifest(snapshot)
        manifest["boot_state_snapshot_sha256"] = "c" * 64
        manifest["manifest_sha256"] = windows_rollback_bundle.sha256_payload(manifest)
        with self.assertRaises(windows_rollback_bundle.RollbackBundleError):
            windows_rollback_bundle.verify_rollback_manifest(manifest, snapshot)


if __name__ == "__main__":
    unittest.main()
