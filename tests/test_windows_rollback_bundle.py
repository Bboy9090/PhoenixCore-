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

bundle_spec = importlib.util.spec_from_file_location("windows_rollback_bundle", BUNDLE_PATH)
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

    def test_complete_fixture_bundle_unlocks_only_with_all_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bcd = root / "bcd_store.bak"
            winre = root / "Winre.wim"
            bcd.write_bytes(b"BCD")
            winre.write_bytes(b"WINRE")
            bundle = windows_rollback_bundle.build_fixture_bundle(
                boot_state=self.snapshot(),
                output_dir=root,
                bcd_export_status={
                    "status": "persisted",
                    "path": str(bcd),
                    "sha256": windows_rollback_bundle.file_sha256(bcd),
                    "size_bytes": bcd.stat().st_size,
                },
                winre_status={
                    "status": "persisted",
                    "path": str(winre),
                    "sha256": windows_rollback_bundle.file_sha256(winre),
                    "size_bytes": winre.stat().st_size,
                },
                created_at="2026-09-17T22:01:00Z",
            )
            self.assertTrue(bundle["complete"])
            self.assertTrue(bundle["repair_unlock_ready"])
            self.assertFalse(bundle["system_configuration_mutated"])
            self.assertFalse(bundle["efi_mounted_by_bundle_tool"])

    def test_missing_winre_keeps_repair_locked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            bcd = root / "bcd_store.bak"
            bcd.write_bytes(b"BCD")
            bundle = windows_rollback_bundle.build_fixture_bundle(
                boot_state=self.snapshot(),
                output_dir=root,
                bcd_export_status={
                    "status": "persisted",
                    "path": str(bcd),
                    "sha256": windows_rollback_bundle.file_sha256(bcd),
                    "size_bytes": bcd.stat().st_size,
                },
                winre_status={
                    "status": "location-not-directly-accessible",
                    "path": None,
                    "sha256": None,
                    "size_bytes": None,
                },
            )
            self.assertFalse(bundle["complete"])
            self.assertFalse(bundle["repair_unlock_ready"])
            self.assertIn(
                "winre_image",
                bundle["missing_or_unverified_artifacts"],
            )

    def test_globalroot_winre_path_is_not_mounted_or_traversed(self):
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


if __name__ == "__main__":
    unittest.main()
