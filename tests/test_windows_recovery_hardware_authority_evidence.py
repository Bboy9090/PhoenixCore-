import importlib.util
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = (
    ROOT
    / "scripts"
    / "hardware"
    / "assemble_windows_recovery_hardware_authority_evidence.py"
)
SPEC = importlib.util.spec_from_file_location(
    "hardware_authority_evidence", MODULE_PATH
)
assert SPEC and SPEC.loader
authority = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(authority)


def write_json(root: Path, name: str, payload: dict) -> Path:
    path = root / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def live_drive(target: str, snapshot: str, stable: str) -> dict:
    return {
        "schema_version": authority.DRIVE_SCHEMA,
        "evidence_source": "live",
        "platform": "windows",
        "hardware_observed": True,
        "bytes_written": 0,
        "physical_write_attempted": False,
        "disk": {
            "target": target,
            "identity_sha256": snapshot,
            "stable_identity_sha256": stable,
        },
    }


def args_for(root: Path) -> Namespace:
    baseline = live_drive(
        r"\\.\PHYSICALDRIVE7",
        "a" * 64,
        "b" * 64,
    )
    reconnect = live_drive(
        r"\\.\PHYSICALDRIVE9",
        "c" * 64,
        "b" * 64,
    )
    substitution = live_drive(
        r"\\.\PHYSICALDRIVE11",
        "e" * 64,
        "f" * 64,
    )
    return Namespace(
        baseline_target_drive=write_json(root, "baseline.json", baseline),
        rollback_destination=write_json(
            root,
            "rollback-destination.json",
            {
                "ready_for_hardware_rollback_capture": True,
                "separate_physical_device": True,
                "target_identity_matches_expected": True,
                "target_stable_identity_sha256": "b" * 64,
                "system_mutations_performed": False,
            },
        ),
        rollback_capture=write_json(
            root,
            "rollback-capture.json",
            {
                "schema": authority.ROLLBACK_CAPTURE_SCHEMA,
                "evidence_source": "live",
                "hardware_observed": True,
                "target_snapshot_identity_sha256": "a" * 64,
                "target_stable_identity_sha256": "b" * 64,
                "rollback_destination_stable_identity_sha256": "d" * 64,
                "rollback_contract_sha256": "1" * 64,
                "target_bytes_written": 0,
                "target_write_attempted": False,
                "restore_unlock_ready": False,
                "system_mutations_performed": False,
                "receipt_sha256": "2" * 64,
            },
        ),
        reconnect_target_drive=write_json(root, "reconnect-drive.json", reconnect),
        reconnect_receipt=write_json(
            root,
            "reconnect-receipt.json",
            {
                "schema": authority.REENUMERATION_SCHEMA,
                "same_stable_hardware": True,
                "stale_authorization_rejected": True,
                "reanalysis_required": True,
                "substitution_detected": False,
                "system_mutations_performed": False,
                "receipt_sha256": "3" * 64,
            },
        ),
        post_reanalysis_target_safety=write_json(
            root,
            "post-safety.json",
            {
                "safe_to_prepare": True,
                "source_target_distinct": True,
                "target_identity_sha256": "c" * 64,
                "target_stable_identity_sha256": "b" * 64,
            },
        ),
        post_reanalysis_target_verification=write_json(
            root,
            "post-verification.json",
            {
                "matches": True,
                "reanalysis_required": False,
                "observed_snapshot_identity_sha256": "c" * 64,
                "observed_stable_identity_sha256": "b" * 64,
                "system_mutations_performed": False,
            },
        ),
        substitution_target_drive=write_json(
            root, "substitution-drive.json", substitution
        ),
        substitution_receipt=write_json(
            root,
            "substitution-receipt.json",
            {
                "schema": authority.REENUMERATION_SCHEMA,
                "same_stable_hardware": False,
                "stale_authorization_rejected": False,
                "reanalysis_required": True,
                "substitution_detected": True,
                "system_mutations_performed": False,
                "receipt_sha256": "4" * 64,
            },
        ),
        boot_metadata=write_json(
            root,
            "boot-metadata.json",
            {
                "schema": authority.BOOT_METADATA_SCHEMA,
                "evidence_source": "live",
                "hardware_observed": True,
                "resolved": True,
                "target_bytes_written": 0,
                "target_write_attempted": False,
                "partition_mount_or_assignment_attempted": False,
                "restore_unlock_ready": False,
                "system_mutations_performed": False,
                "receipt_sha256": "5" * 64,
            },
        ),
        data_preservation=write_json(
            root,
            "data-preservation.json",
            {
                "schema": authority.DATA_PRESERVATION_SCHEMA,
                "resolved": True,
                "restore_unlock_ready": False,
                "system_mutations_performed": False,
                "receipt_sha256": "6" * 64,
            },
        ),
        output=root / "authority-package.json",
    )


class HardwareAuthorityEvidenceTests(unittest.TestCase):
    def test_live_read_only_package_assembles_without_unlocking_restore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            args = args_for(Path(tmpdir))
            package = authority.build_package(args)
            self.assertEqual(authority.SCHEMA, package["schema"])
            self.assertFalse(package["fixture_evidence_allowed"])
            self.assertFalse(package["restore_executable"])
            self.assertFalse(package["destructive_authorization_granted"])
            self.assertFalse(package["system_mutations_performed"])
            self.assertEqual(64, len(package["package_sha256"]))

    def test_fixture_drive_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            args = args_for(root)
            payload = json.loads(
                args.reconnect_target_drive.read_text(encoding="utf-8")
            )
            payload["evidence_source"] = "fixture"
            payload["hardware_observed"] = False
            payload["platform"] = "fixture"
            args.reconnect_target_drive.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                authority.AuthorityEvidenceError,
                "not live observed hardware evidence",
            ):
                authority.build_package(args)

    def test_nonzero_target_write_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            args = args_for(root)
            payload = json.loads(args.rollback_capture.read_text(encoding="utf-8"))
            payload["target_bytes_written"] = 512
            args.rollback_capture.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                authority.AuthorityEvidenceError,
                "zero-write safety boundary",
            ):
                authority.build_package(args)

    def test_restore_unlock_claim_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            args = args_for(root)
            payload = json.loads(args.boot_metadata.read_text(encoding="utf-8"))
            payload["restore_unlock_ready"] = True
            args.boot_metadata.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                authority.AuthorityEvidenceError,
                "read-only safety boundary",
            ):
                authority.build_package(args)


if __name__ == "__main__":
    unittest.main()
