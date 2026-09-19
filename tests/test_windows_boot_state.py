import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "capture_windows_boot_state.py"
)
SPEC = importlib.util.spec_from_file_location("windows_boot_state", MODULE_PATH)
assert SPEC and SPEC.loader
windows_boot_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(windows_boot_state)


class WindowsBootStateTests(unittest.TestCase):
    def partition_payload(self):
        return {
            "SecureBootEnabled": True,
            "Partitions": [
                {
                    "DiskNumber": 0,
                    "PartitionNumber": 1,
                    "DriveLetter": None,
                    "Offset": 1048576,
                    "Size": 272629760,
                    "GptType": "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}",
                },
                {
                    "DiskNumber": 0,
                    "PartitionNumber": 3,
                    "DriveLetter": "C",
                    "Offset": 300000000,
                    "Size": 1000000000,
                    "GptType": "{basic-data}",
                },
            ],
        }

    def command(self, name, stdout, returncode=0):
        return {
            "command": name,
            "arguments": [],
            "returncode": returncode,
            "stdout": stdout,
            "stderr": "",
            "stdout_sha256": windows_boot_state.sha256_text(stdout),
            "stderr_sha256": windows_boot_state.sha256_text(""),
        }

    def target_evidence(self):
        return {
            "schema_version": "bws.physical-drive-evidence/v1",
            "disk": {
                "target": r"\\.\PHYSICALDRIVE7",
                "identity_sha256": "a" * 64,
                "stable_identity_sha256": "d" * 64,
                "size_bytes": 64000000000,
                "partition_style": "GPT",
                "is_boot": True,
                "is_system": True,
                "partitions": [
                    {
                        "partition_number": 1,
                        "offset_bytes": 1048576,
                        "size_bytes": 272629760,
                        "type": "System",
                    }
                ],
            },
        }

    def test_boot_snapshot_is_read_only_and_hashed(self):
        snapshot = windows_boot_state.build_boot_state_snapshot(
            partition_payload=self.partition_payload(),
            bcd_record=self.command("bcdedit.exe", "BCD DATA"),
            winre_record=self.command("reagentc.exe", "Windows RE status: Enabled"),
            captured_at="2026-09-17T21:00:00Z",
        )
        self.assertTrue(snapshot["complete"])
        self.assertEqual(1, len(snapshot["efi_system_partitions"]))
        self.assertFalse(snapshot["efi_write_attempted"])
        self.assertFalse(snapshot["bcd_write_attempted"])
        self.assertEqual(0, snapshot["bytes_written_to_system"])
        self.assertEqual(64, len(snapshot["snapshot_sha256"]))

    def test_rollback_manifest_stays_locked_until_backups_exist(self):
        snapshot = windows_boot_state.build_boot_state_snapshot(
            partition_payload=self.partition_payload(),
            bcd_record=self.command("bcdedit.exe", "BCD DATA"),
            winre_record=self.command("reagentc.exe", "Windows RE status: Enabled"),
            captured_at="2026-09-17T21:00:00Z",
        )
        manifest = windows_boot_state.build_rollback_manifest(
            source_identity_sha256="b" * 64,
            source_path=r"E:\backup\install.wim",
            target_evidence=self.target_evidence(),
            boot_state=snapshot,
            created_at="2026-09-17T21:01:00Z",
        )
        self.assertFalse(manifest["repair_unlock_ready"])
        self.assertFalse(manifest["system_mutations_performed"])
        self.assertIn(
            "bcd_store_export",
            manifest["required_backup_artifacts_before_repair"],
        )
        self.assertEqual("a" * 64, manifest["target"]["identity_sha256"])
        self.assertEqual("d" * 64, manifest["target"]["stable_identity_sha256"])
        self.assertEqual(64, len(manifest["manifest_sha256"]))

    def test_missing_stable_target_identity_is_rejected(self):
        snapshot = windows_boot_state.build_boot_state_snapshot(
            partition_payload=self.partition_payload(),
            bcd_record=self.command("bcdedit.exe", "BCD DATA"),
            winre_record=self.command("reagentc.exe", "Windows RE status: Enabled"),
        )
        evidence = self.target_evidence()
        evidence["disk"]["stable_identity_sha256"] = None
        with self.assertRaises(windows_boot_state.BootStateError):
            windows_boot_state.build_rollback_manifest(
                source_identity_sha256="d" * 64,
                target_evidence=evidence,
                boot_state=snapshot,
            )

    def test_external_target_cannot_be_bound_to_online_boot_state(self):
        snapshot = windows_boot_state.build_boot_state_snapshot(
            partition_payload=self.partition_payload(),
            bcd_record=self.command("bcdedit.exe", "BCD DATA"),
            winre_record=self.command("reagentc.exe", "Windows RE status: Enabled"),
        )
        evidence = self.target_evidence()
        evidence["disk"]["is_boot"] = False
        evidence["disk"]["is_system"] = False
        with self.assertRaises(windows_boot_state.BootStateError):
            windows_boot_state.build_rollback_manifest(
                source_identity_sha256="d" * 64,
                target_evidence=evidence,
                boot_state=snapshot,
            )

    def test_missing_source_identity_is_rejected(self):
        snapshot = windows_boot_state.build_boot_state_snapshot(
            partition_payload=self.partition_payload(),
            bcd_record=self.command("bcdedit.exe", "BCD DATA"),
            winre_record=self.command("reagentc.exe", "Windows RE status: Enabled"),
        )
        with self.assertRaises(windows_boot_state.BootStateError):
            windows_boot_state.build_rollback_manifest(
                source_identity_sha256="not-a-digest",
                target_evidence=self.target_evidence(),
                boot_state=snapshot,
            )

    def test_atomic_manifest_round_trip(self):
        snapshot = windows_boot_state.build_boot_state_snapshot(
            partition_payload=self.partition_payload(),
            bcd_record=self.command("bcdedit.exe", "BCD DATA"),
            winre_record=self.command("reagentc.exe", "Windows RE status: Enabled"),
        )
        manifest = windows_boot_state.build_rollback_manifest(
            source_identity_sha256="c" * 64,
            target_evidence=self.target_evidence(),
            boot_state=snapshot,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "rollback" / "manifest.json"
            windows_boot_state.write_json_atomic(manifest, output)
            self.assertEqual(
                manifest,
                json.loads(output.read_text(encoding="utf-8")),
            )


if __name__ == "__main__":
    unittest.main()
