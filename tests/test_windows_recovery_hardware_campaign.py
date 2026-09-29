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


def comparison_receipt(candidate: dict, *, baseline: dict | None = None) -> dict:
    return campaign.drive_compare.compare_receipts(
        baseline or drive_receipt(7),
        candidate,
    )


def evidence_disk_record(
    *,
    stable_identity_sha256: str = "d" * 64,
    physical_target: str = r"\\.\PHYSICALDRIVE20",
) -> dict:
    return {
        "schema": "phoenix_key.windows_source_disk.v2",
        "source_path": "D:/PhoenixKeyEvidence/campaign-001",
        "drive_letter": "D",
        "disk_number": 20,
        "partition_number": 1,
        "physical_target": physical_target,
        "friendly_name": "Evidence Disk",
        "serial_number": "EVIDENCE-001",
        "unique_id": "EVIDENCE-UNIQUE-001",
        "bus_type": "USB",
        "size_bytes": 128_000,
        "identity_sha256": "e" * 64,
        "stable_identity_sha256": stable_identity_sha256,
        "stable_identity_available": True,
        "resolved": True,
        "read_only": True,
    }


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
        "rollback_capture_receipt_sha256": (
            (manifest.get("rollback_capture") or {}).get("receipt_sha256") or "f" * 64
        ),
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
    def test_preflight_requires_distinct_evidence_disk(self):
        target = drive_receipt(7)
        target_stable = target["disk"]["stable_identity_sha256"]
        blocked = campaign.build_preflight_report(
            target,
            evidence_disk_record(stable_identity_sha256=target_stable),
            campaign_dir="D:/PhoenixKeyEvidence/campaign-001",
        )
        self.assertFalse(blocked["ready_for_hardware_campaign"])
        self.assertIn(
            "evidence_disk_distinct_from_target",
            blocked["block_reasons"],
        )
        self.assertFalse(blocked["restore_executor_authorized"])
        self.assertFalse(blocked["system_mutations_performed"])

    def test_preflight_accepts_distinct_live_external_gpt_target(self):
        report = campaign.build_preflight_report(
            drive_receipt(7),
            evidence_disk_record(),
            campaign_dir="D:/PhoenixKeyEvidence/campaign-001",
        )
        self.assertTrue(report["ready_for_hardware_campaign"])
        self.assertEqual([], report["block_reasons"])
        self.assertTrue(report["checks"]["target_live_hardware"])
        self.assertTrue(report["checks"]["target_partition_style_gpt"])
        self.assertTrue(report["checks"]["evidence_disk_distinct_from_target"])
        self.assertFalse(report["target_write_attempted"])

    def test_preflight_blocks_boot_system_or_non_gpt_target(self):
        raw = raw_disk(7)
        raw["IsBoot"] = True
        raw["IsSystem"] = True
        raw["PartitionStyle"] = "MBR"
        receipt = drive.build_receipt(
            target=r"\\.\PHYSICALDRIVE7",
            raw_disk=raw,
            evidence_source="live",
            source_commit="a" * 40,
            captured_at="2026-09-23T20:07:00Z",
        )
        report = campaign.build_preflight_report(
            receipt,
            evidence_disk_record(),
            campaign_dir="D:/PhoenixKeyEvidence/campaign-001",
        )
        self.assertFalse(report["ready_for_hardware_campaign"])
        self.assertIn("target_not_boot_disk", report["block_reasons"])
        self.assertIn("target_not_system_disk", report["block_reasons"])
        self.assertIn("target_partition_style_gpt", report["block_reasons"])

    def test_preflight_report_is_checksum_bound(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            report = campaign.build_preflight_report(
                drive_receipt(7),
                evidence_disk_record(),
                campaign_dir=str(root),
            )
            self.assertEqual(64, len(report["preflight_sha256"]))
            tampered = dict(report)
            tampered["target"] = r"\\.\PHYSICALDRIVE99"
            with self.assertRaisesRegex(
                campaign.HardwareCampaignError,
                "checksum",
            ):
                campaign.verify_preflight_report(
                    tampered,
                    campaign_dir=root,
                    target_receipt=drive_receipt(7),
                )

    def test_preflight_binding_rejects_different_target_snapshot(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            report = campaign.build_preflight_report(
                drive_receipt(7),
                evidence_disk_record(),
                campaign_dir=str(root),
            )
            with self.assertRaisesRegex(
                campaign.HardwareCampaignError,
                "target path|snapshot",
            ):
                campaign.verify_preflight_report(
                    report,
                    campaign_dir=root,
                    target_receipt=drive_receipt(9),
                )

    def test_preflight_binding_accepts_same_fresh_target(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir).resolve()
            receipt = drive_receipt(7)
            report = campaign.build_preflight_report(
                receipt,
                evidence_disk_record(),
                campaign_dir=str(root),
            )
            campaign.verify_preflight_report(
                report,
                campaign_dir=root,
                target_receipt=receipt,
            )

    def test_fixture_baseline_never_counts_as_live_hardware(self):
        manifest = campaign.build_campaign_manifest(
            drive_receipt(7, evidence_source="fixture")
        )
        self.assertFalse(manifest["gates"]["baseline_live_hardware"])
        self.assertFalse(manifest["hardware_campaign_complete"])
        self.assertFalse(manifest["restore_executor_authorized"])
        self.assertFalse(manifest["system_mutations_performed"])

    def test_live_chain_reaches_hardware_campaign_complete(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        manifest = campaign.record_rollback_capture(
            manifest,
            rollback_receipt(manifest),
        )
        reconnect_receipt = drive_receipt(9)
        manifest = campaign.record_reconnect(
            manifest,
            reconnect_receipt,
            comparison_receipt(reconnect_receipt),
            operator_confirmed=True,
        )
        substitution_receipt = drive_receipt(
            12,
            serial="OTHER-002",
            unique_id="OTHER-UNIQUE-002",
        )
        manifest = campaign.record_substitution(
            manifest,
            substitution_receipt,
            comparison_receipt(substitution_receipt),
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
        self.assertTrue(manifest["hardware_campaign_complete"])
        self.assertEqual([], manifest["outstanding_requirements"])
        self.assertEqual(
            "resolve_data_preservation_then_run_final_non_executable_preflight",
            manifest["next_required_action"],
        )
        self.assertFalse(manifest["restore_executor_authorized"])
        self.assertEqual(64, len(manifest["manifest_sha256"]))

    def test_reconnect_same_snapshot_does_not_prove_reenumeration(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        reconnect_receipt = drive_receipt(7)
        manifest = campaign.record_reconnect(
            manifest,
            reconnect_receipt,
            comparison_receipt(reconnect_receipt),
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
            reconnect_receipt = drive_receipt(9)
            campaign.record_reconnect(
                manifest,
                reconnect_receipt,
                comparison_receipt(reconnect_receipt),
                operator_confirmed=False,
            )

    def test_substitution_same_hardware_is_rejected(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        with self.assertRaisesRegex(
            campaign.HardwareCampaignError,
            "baseline target",
        ):
            substitution_receipt = drive_receipt(9)
            campaign.record_substitution(
                manifest,
                substitution_receipt,
                comparison_receipt(substitution_receipt),
                operator_confirmed=True,
            )

    def test_boot_metadata_requires_recorded_rollback_capture(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        with self.assertRaisesRegex(
            campaign.HardwareCampaignError,
            "rollback capture first",
        ):
            campaign.record_boot_metadata(
                manifest,
                boot_receipt(manifest),
            )

    def test_boot_metadata_rejects_different_snapshot(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        manifest = campaign.record_rollback_capture(
            manifest,
            rollback_receipt(manifest),
        )
        receipt = boot_receipt(manifest)
        receipt["target_snapshot_identity_sha256"] = "0" * 64
        receipt["receipt_sha256"] = campaign.sha256_payload(
            {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        )
        with self.assertRaisesRegex(
            campaign.HardwareCampaignError,
            "baseline target",
        ):
            campaign.record_boot_metadata(manifest, receipt)

    def test_boot_metadata_rejects_different_rollback_capture(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        manifest = campaign.record_rollback_capture(
            manifest,
            rollback_receipt(manifest),
        )
        receipt = boot_receipt(manifest)
        receipt["rollback_capture_receipt_sha256"] = "0" * 64
        receipt["receipt_sha256"] = campaign.sha256_payload(
            {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        )
        with self.assertRaisesRegex(
            campaign.HardwareCampaignError,
            "recorded rollback capture",
        ):
            campaign.record_boot_metadata(manifest, receipt)

    def test_boot_metadata_rejects_different_rollback_contract(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        manifest = campaign.record_rollback_capture(
            manifest,
            rollback_receipt(manifest),
        )
        receipt = boot_receipt(manifest)
        receipt["rollback_contract_sha256"] = "0" * 64
        receipt["receipt_sha256"] = campaign.sha256_payload(
            {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        )
        with self.assertRaisesRegex(
            campaign.HardwareCampaignError,
            "rollback contract",
        ):
            campaign.record_boot_metadata(manifest, receipt)

    def test_reconnect_rejects_untrusted_comparison(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        current = drive_receipt(9)
        before = drive_receipt(7)
        current["source_commit"] = "b" * 40
        current["receipt_sha256"] = campaign.sha256_payload(
            {key: value for key, value in current.items() if key != "receipt_sha256"}
        )
        comparison = campaign.drive_compare.compare_receipts(before, current)
        with self.assertRaisesRegex(
            campaign.HardwareCampaignError,
            "not trusted",
        ):
            campaign.record_reconnect(
                manifest,
                current,
                comparison,
                operator_confirmed=True,
            )

    def test_substitution_requires_comparator_classification(self):
        manifest = campaign.build_campaign_manifest(drive_receipt(7))
        candidate = drive_receipt(
            12,
            serial="OTHER-002",
            unique_id="OTHER-UNIQUE-002",
        )
        comparison = comparison_receipt(candidate)
        comparison["classification"] = "same-hardware-same-snapshot"
        with self.assertRaisesRegex(
            campaign.HardwareCampaignError,
            "did not classify",
        ):
            campaign.record_substitution(
                manifest,
                candidate,
                comparison,
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
