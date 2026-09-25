import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARDWARE_DIR = ROOT / "scripts" / "hardware"
if str(HARDWARE_DIR) not in sys.path:
    sys.path.insert(0, str(HARDWARE_DIR))

CAMPAIGN_PATH = HARDWARE_DIR / "run_windows_recovery_hardware_campaign.py"
DRIVE_PATH = HARDWARE_DIR / "capture_windows_drive_evidence.py"

campaign_spec = importlib.util.spec_from_file_location(
    "windows_recovery_hardware_campaign", CAMPAIGN_PATH
)
assert campaign_spec and campaign_spec.loader
campaign = importlib.util.module_from_spec(campaign_spec)
campaign_spec.loader.exec_module(campaign)

drive_spec = importlib.util.spec_from_file_location(
    "windows_drive_evidence_campaign_test", DRIVE_PATH
)
assert drive_spec and drive_spec.loader
drive = importlib.util.module_from_spec(drive_spec)
drive_spec.loader.exec_module(drive)


def raw_disk(
    number: int,
    *,
    serial: str = "TARGET-001",
    unique_id: str = "UNIQUE-001",
) -> dict:
    return {
        "Number": number,
        "FriendlyName": "Campaign Test Disk",
        "SerialNumber": serial,
        "UniqueId": unique_id,
        "BusType": "USB",
        "SizeBytes": 64_000,
        "LogicalSectorSize": 512,
        "PhysicalSectorSize": 4096,
        "PartitionStyle": "GPT",
        "IsBoot": False,
        "IsSystem": False,
        "IsOffline": False,
        "IsReadOnly": False,
        "HealthStatus": "Healthy",
        "OperationalStatus": ["Online"],
        "Partitions": [],
    }


def drive_receipt(
    number: int,
    *,
    evidence_source: str = "live",
    serial: str = "TARGET-001",
    unique_id: str = "UNIQUE-001",
) -> dict:
    target = rf"\\.\PHYSICALDRIVE{number}"
    return drive.build_receipt(
        target=target,
        raw_disk=raw_disk(
            number,
            serial=serial,
            unique_id=unique_id,
        ),
        evidence_source=evidence_source,
        source_commit="a" * 40,
        captured_at=f"2026-09-23T20:{number:02d}:00Z",
    )


def rollback_receipt(manifest: dict, *, evidence_source: str = "live") -> dict:
    baseline = manifest["baseline"]
    payload = {
        "schema": campaign.ROLLBACK_SCHEMA,
        "captured_at": "2026-09-23T21:00:00Z",
        "evidence_source": evidence_source,
        "hardware_observed": evidence_source == "live",
        "target": baseline["target"],
        "target_snapshot_identity_sha256": baseline["snapshot_identity_sha256"],
        "target_stable_identity_sha256": baseline["stable_identity_sha256"],
        "rollback_destination_stable_identity_sha256": "d" * 64,
        "rollback_contract_sha256": "e" * 64,
        "output_directory": "D:/rollback",
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
        "partition_manifest_sha256": "f" * 64,
        "restore_unlock_ready": False,
        "restore_unlock_scope": [],
        "always_blocked_by_this_capture": ["apply_system_image"],
        "target_bytes_written": 0,
        "target_write_attempted": False,
        "rollback_destination_files_written": True,
        "system_mutations_performed": False,
    }
    payload["receipt_sha256"] = campaign.sha256_payload(payload)
    return payload


def authority_report(*, complete: bool = True) -> dict:
    payload = {
        "schema": "phoenix_key.recovery_hardware_campaign_report.v1",
        "target_live_observed": complete,
        "rollback_destination_separate": complete,
        "rollback_capture_live_zero_write": complete,
        "reconnect_same_hardware_proven": complete,
        "stale_snapshot_authorization_rejected": complete,
        "post_reanalysis_fresh_identity_proven": complete,
        "substitution_rejected": complete,
        "boot_metadata_live_resolved": complete,
        "data_preservation_resolved": complete,
        "fixture_evidence_rejected": True,
        "campaign_complete": complete,
        "restore_executable": False,
        "destructive_authorization_granted": False,
        "system_mutations_performed": False,
        "blockers": [] if complete else ["post_reconnect_reanalysis_not_proven"],
    }
    payload["report_sha256"] = campaign.sha256_payload(payload)
    return payload


def boot_receipt(manifest: dict, *, evidence_source: str = "live") -> dict:
    baseline = manifest["baseline"]
    payload = {
        "schema": campaign.BOOT_METADATA_SCHEMA,
        "evidence_source": evidence_source,
        "hardware_observed": evidence_source == "live",
        "target": baseline["target"],
        "target_snapshot_identity_sha256": baseline["snapshot_identity_sha256"],
        "target_stable_identity_sha256": baseline["stable_identity_sha256"],
        "rollback_contract_sha256": "e" * 64,
        "rollback_capture_receipt_sha256": "f" * 64,
        "output_directory": "D:/rollback/boot",
        "partition_inventory": [],
        "artifacts": {},
        "resolved": True,
        "missing_or_unverified": [],
        "restore_unlock_ready": False,
        "target_bytes_written": 0,
        "target_write_attempted": False,
        "partition_mount_or_assignment_attempted": False,
        "system_mutations_performed": False,
    }
    payload["receipt_sha256"] = campaign.sha256_payload(payload)
    return payload


class WindowsRecoveryHardwareCampaignTests(unittest.TestCase):
    def test_fixture_baseline_never_counts_as_live_hardware(self):
        manifest = campaign.build_campaign_manifest(
            drive_receipt(7, evidence_source="fixture")
        )
        self.assertFalse(manifest["gates"]["baseline_live_hardware"])
        self.assertFalse(manifest["hardware_campaign_complete"])
        self.assertFalse(manifest["restore_executor_authorized"])
        self.assertFalse(manifest["system_mutations_performed"])

    def test_live_collection_requires_authority_before_campaign_complete(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        manifest = campaign.record_rollback_capture(
            manifest,
            rollback_receipt(manifest),
        )
        manifest = campaign.record_reconnect(
            manifest,
            drive_receipt(9),
            operator_confirmed=True,
        )
        manifest = campaign.record_substitution(
            manifest,
            drive_receipt(
                12,
                serial="OTHER-002",
                unique_id="OTHER-UNIQUE-002",
            ),
            operator_confirmed=True,
        )
        manifest = campaign.record_boot_metadata(
            manifest,
            boot_receipt(manifest),
        )

        self.assertTrue(manifest["gates"]["baseline_live_hardware"])
        self.assertTrue(manifest["gates"]["rollback_live_zero_write"])
        self.assertTrue(manifest["gates"]["reconnect_same_hardware"])
        self.assertTrue(manifest["gates"]["reenumeration_observed"])
        self.assertTrue(manifest["gates"]["substitution_rejection_proven"])
        self.assertTrue(manifest["gates"]["boot_metadata_live_read_only"])
        self.assertTrue(manifest["collection_complete"])
        self.assertFalse(manifest["hardware_campaign_complete"])
        self.assertIn(
            "hardware_campaign_authority_report",
            manifest["outstanding_requirements"],
        )
        self.assertEqual(
            "generate_hardware_campaign_authority_report",
            manifest["next_required_action"],
        )

        manifest = campaign.record_authority_report(
            manifest,
            authority_report(),
        )
        self.assertTrue(manifest["hardware_campaign_complete"])
        self.assertEqual([], manifest["outstanding_requirements"])
        self.assertEqual(
            "run_final_non_executable_preflight",
            manifest["next_required_action"],
        )
        self.assertFalse(manifest["restore_executor_authorized"])
        self.assertEqual(64, len(manifest["manifest_sha256"]))

    def test_reconnect_same_snapshot_does_not_prove_reenumeration(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        manifest = campaign.record_reconnect(
            manifest,
            drive_receipt(7),
            operator_confirmed=True,
        )
        self.assertTrue(manifest["gates"]["reconnect_same_hardware"])
        self.assertFalse(manifest["gates"]["reenumeration_observed"])
        self.assertFalse(manifest["hardware_campaign_complete"])

    def test_reconnect_requires_explicit_operator_confirmation(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        with self.assertRaisesRegex(
            campaign.HardwareCampaignError,
            "explicitly confirmed",
        ):
            campaign.record_reconnect(
                manifest,
                drive_receipt(9),
                operator_confirmed=False,
            )

    def test_substitution_same_hardware_is_rejected(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        with self.assertRaisesRegex(
            campaign.HardwareCampaignError,
            "baseline target",
        ):
            campaign.record_substitution(
                manifest,
                drive_receipt(9),
                operator_confirmed=True,
            )

    def test_fixture_rollback_and_boot_receipts_do_not_satisfy_live_gates(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        manifest = campaign.record_rollback_capture(
            manifest,
            rollback_receipt(manifest, evidence_source="fixture"),
        )
        manifest = campaign.record_boot_metadata(
            manifest,
            boot_receipt(manifest, evidence_source="fixture"),
        )
        self.assertFalse(manifest["gates"]["rollback_live_zero_write"])
        self.assertFalse(manifest["gates"]["boot_metadata_live_read_only"])
        self.assertFalse(manifest["hardware_campaign_complete"])

    def test_incomplete_authority_cannot_complete_campaign(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        manifest = campaign.record_rollback_capture(
            manifest,
            rollback_receipt(manifest),
        )
        manifest = campaign.record_reconnect(
            manifest,
            drive_receipt(9),
            operator_confirmed=True,
        )
        manifest = campaign.record_substitution(
            manifest,
            drive_receipt(
                12,
                serial="OTHER-002",
                unique_id="OTHER-UNIQUE-002",
            ),
            operator_confirmed=True,
        )
        manifest = campaign.record_boot_metadata(
            manifest,
            boot_receipt(manifest),
        )
        manifest = campaign.record_authority_report(
            manifest,
            authority_report(complete=False),
        )
        self.assertTrue(manifest["collection_complete"])
        self.assertFalse(manifest["hardware_campaign_complete"])
        self.assertIn(
            "hardware_campaign_authority_report",
            manifest["outstanding_requirements"],
        )

    def test_tampered_manifest_is_rejected_on_reload(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            path = root / "hardware-campaign-manifest.json"
            campaign.write_json_atomic(manifest, path)
            loaded = campaign.load_json(path)
            loaded["baseline"]["target"] = r"\\.\PHYSICALDRIVE99"
            campaign.write_json_atomic(loaded, path)
            with self.assertRaisesRegex(
                campaign.HardwareCampaignError,
                "checksum",
            ):
                campaign.load_manifest(root)


if __name__ == "__main__":
    unittest.main()
