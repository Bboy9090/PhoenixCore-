import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = (
    ROOT / "scripts" / "hardware" / "capture_windows_restore_target_boot_metadata.py"
)

SPEC = importlib.util.spec_from_file_location(
    "restore_target_boot_metadata", MODULE_PATH
)
assert SPEC and SPEC.loader
restore_target_boot_metadata = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(restore_target_boot_metadata)

TARGET = r"\\.\PHYSICALDRIVE7"


def rollback_capture_receipt() -> dict:
    receipt = {
        "schema": "phoenix_key.restore_target_rollback_capture.v1",
        "target": TARGET,
        "target_snapshot_identity_sha256": "a" * 64,
        "target_stable_identity_sha256": "b" * 64,
        "rollback_destination_stable_identity_sha256": "c" * 64,
        "rollback_contract_sha256": "d" * 64,
        "output_directory": "E:/rollback",
        "captured_requirements": [
            "target_partition_table_backup",
            "target_partition_manifest",
            "artifact_checksums",
        ],
        "remaining_requirements": [
            "target_boot_metadata_backup_if_present",
            "target_data_preservation_receipt_or_explicit_discard_decision",
        ],
        "artifacts": {},
        "partition_manifest_sha256": "e" * 64,
        "restore_unlock_ready": False,
        "restore_unlock_scope": [],
        "always_blocked_by_this_capture": ["apply_system_image"],
        "target_bytes_written": 0,
        "target_write_attempted": False,
        "rollback_destination_files_written": True,
        "system_mutations_performed": False,
    }
    receipt["receipt_sha256"] = restore_target_boot_metadata.sha256_payload(receipt)
    return receipt


def target_disk() -> dict:
    return {
        "target": TARGET,
        "identity_sha256": "a" * 64,
        "stable_identity_sha256": "b" * 64,
    }


class RestoreTargetBootMetadataTests(unittest.TestCase):
    def test_accessible_efi_and_recovery_metadata_are_copied(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            efi_root = root / "efi-root"
            recovery_root = root / "recovery-root"
            output = root / "output"

            efi_bcd = efi_root / "EFI" / "Microsoft" / "Boot" / "BCD"
            efi_bcd.parent.mkdir(parents=True)
            efi_bcd.write_bytes(b"fixture-bcd")

            winre = recovery_root / "Recovery" / "WindowsRE" / "Winre.wim"
            reagent = recovery_root / "Recovery" / "WindowsRE" / "ReAgent.xml"
            winre.parent.mkdir(parents=True)
            winre.write_bytes(b"fixture-winre")
            reagent.write_text("<fixture />", encoding="utf-8")

            partitions = [
                {
                    "PartitionNumber": 1,
                    "DriveLetter": "S",
                    "Offset": 1024,
                    "Size": 4096,
                    "GptType": restore_target_boot_metadata.EFI_GUID,
                    "FixtureRoot": str(efi_root),
                },
                {
                    "PartitionNumber": 4,
                    "DriveLetter": "R",
                    "Offset": 8192,
                    "Size": 16384,
                    "GptType": restore_target_boot_metadata.RECOVERY_GUID,
                    "FixtureRoot": str(recovery_root),
                },
            ]

            inventory, artifacts, missing = (
                restore_target_boot_metadata.capture_partition_metadata(
                    partitions=partitions,
                    output_dir=output,
                    root_resolver=lambda item: Path(item["FixtureRoot"]),
                )
            )

            self.assertEqual([], missing)
            self.assertEqual(2, len(inventory))
            self.assertEqual("persisted", artifacts["efi_partition_1"]["status"])
            self.assertEqual("persisted", artifacts["winre_wim_partition_4"]["status"])
            self.assertEqual(
                "persisted", artifacts["winre_config_partition_4"]["status"]
            )

            receipt = restore_target_boot_metadata.build_receipt(
                target=TARGET,
                target_disk=target_disk(),
                rollback_capture=rollback_capture_receipt(),
                rollback_contract_sha256="d" * 64,
                output_dir=output,
                inventory=inventory,
                artifacts=artifacts,
                missing_or_unverified=missing,
            )
            self.assertTrue(receipt["resolved"])
            self.assertFalse(receipt["restore_unlock_ready"])
            self.assertEqual(0, receipt["target_bytes_written"])
            self.assertFalse(receipt["target_write_attempted"])
            self.assertFalse(receipt["partition_mount_or_assignment_attempted"])
            self.assertFalse(receipt["system_mutations_performed"])
            self.assertEqual(64, len(receipt["receipt_sha256"]))

    def test_unmounted_efi_partition_stays_blocked(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            partitions = [
                {
                    "PartitionNumber": 1,
                    "DriveLetter": None,
                    "Offset": 1024,
                    "Size": 4096,
                    "GptType": restore_target_boot_metadata.EFI_GUID,
                }
            ]
            inventory, artifacts, missing = (
                restore_target_boot_metadata.capture_partition_metadata(
                    partitions=partitions,
                    output_dir=root / "output",
                    root_resolver=lambda _item: None,
                )
            )
            self.assertEqual({}, artifacts)
            self.assertIn(
                "efi_system_partition_1_not_already_accessible",
                missing,
            )
            receipt = restore_target_boot_metadata.build_receipt(
                target=TARGET,
                target_disk=target_disk(),
                rollback_capture=rollback_capture_receipt(),
                rollback_contract_sha256="d" * 64,
                output_dir=root / "output",
                inventory=inventory,
                artifacts=artifacts,
                missing_or_unverified=missing,
            )
            self.assertFalse(receipt["resolved"])
            self.assertFalse(receipt["restore_unlock_ready"])

    def test_target_identity_change_is_rejected(self):
        capture = rollback_capture_receipt()
        disk = target_disk()
        disk["identity_sha256"] = "f" * 64
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(
                restore_target_boot_metadata.RestoreTargetBootMetadataError
            ):
                restore_target_boot_metadata.build_receipt(
                    target=TARGET,
                    target_disk=disk,
                    rollback_capture=capture,
                    rollback_contract_sha256="d" * 64,
                    output_dir=Path(tmpdir),
                    inventory=[],
                    artifacts={},
                    missing_or_unverified=[],
                )

    def test_tampered_rollback_capture_is_rejected(self):
        receipt = rollback_capture_receipt()
        receipt["target_bytes_written"] = 1
        with self.assertRaises(
            restore_target_boot_metadata.RestoreTargetBootMetadataError
        ):
            restore_target_boot_metadata.verify_rollback_capture(receipt)

    def test_live_boot_metadata_requires_live_upstream_chain(self):
        drive_receipt = {
            "evidence_source": "fixture",
            "hardware_observed": False,
        }
        rollback_receipt = rollback_capture_receipt()
        rollback_receipt["evidence_source"] = "fixture"
        rollback_receipt["hardware_observed"] = False

        with self.assertRaisesRegex(
            restore_target_boot_metadata.RestoreTargetBootMetadataError,
            "live target drive evidence",
        ):
            restore_target_boot_metadata.require_live_boot_metadata_inputs(
                drive_receipt,
                rollback_receipt,
            )

        drive_receipt["evidence_source"] = "live"
        drive_receipt["hardware_observed"] = True
        with self.assertRaisesRegex(
            restore_target_boot_metadata.RestoreTargetBootMetadataError,
            "live rollback-capture receipt",
        ):
            restore_target_boot_metadata.require_live_boot_metadata_inputs(
                drive_receipt,
                rollback_receipt,
            )

        rollback_receipt["evidence_source"] = "live"
        rollback_receipt["hardware_observed"] = True
        restore_target_boot_metadata.require_live_boot_metadata_inputs(
            drive_receipt,
            rollback_receipt,
        )


if __name__ == "__main__":
    unittest.main()
