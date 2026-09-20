import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "check_windows_recovery_readiness.py"
)
SPEC = importlib.util.spec_from_file_location("windows_recovery_readiness", MODULE_PATH)
assert SPEC and SPEC.loader
windows_recovery_readiness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(windows_recovery_readiness)


class WindowsRecoveryReadinessTests(unittest.TestCase):
    def source(self):
        return {
            "schema": "phoenix_key.recovery_source_identity.v1",
            "sha256": "1" * 64,
            "complete": True,
            "size_bytes": 1024,
        }

    def target(self):
        return {
            "schema_version": "bws.physical-drive-evidence/v1",
            "disk": {
                "target": r"\\.\PHYSICALDRIVE7",
                "identity_sha256": "2" * 64,
                "stable_identity_sha256": "3" * 64,
                "size_bytes": 4096,
                "write_candidate": True,
                "write_block_reasons": [],
            },
        }

    def boot(self):
        payload = {
            "schema": "phoenix_key.windows_boot_state.v1",
            "complete": True,
            "efi_system_partitions": [{"disk_number": 0, "partition_number": 1}],
            "bcd": {"returncode": 0},
            "winre": {"returncode": 0},
        }
        payload["snapshot_sha256"] = windows_recovery_readiness.sha256_payload(payload)
        return payload

    def bundle(self, boot_sha):
        payload = {
            "schema": "phoenix_key.rollback_bundle.v1",
            "complete": True,
            "repair_unlock_ready": True,
            "boot_state_snapshot_sha256": boot_sha,
            "source_identity_sha256": "1" * 64,
            "target_identity_sha256": "2" * 64,
            "target_stable_identity_sha256": "3" * 64,
            "artifacts": {
                "partition_layout": {"status": "persisted"},
                "efi_inventory": {"status": "persisted"},
                "bcd_store_export": {"status": "persisted"},
                "winre_image": {"status": "persisted"},
            },
        }
        payload["bundle_sha256"] = windows_recovery_readiness.sha256_payload(payload)
        return payload

    def collision(self):
        return {
            "schema": "phoenix_key.source_target_collision_check.v2",
            "source_physical_target": r"\\.\PHYSICALDRIVE8",
            "target_physical_target": r"\\.\PHYSICALDRIVE7",
            "source_stable_identity_sha256": "4" * 64,
            "target_stable_identity_sha256": "3" * 64,
            "path_distinct": True,
            "stable_identity_proven": True,
            "stable_identity_distinct": True,
            "source_target_distinct": True,
            "blocked": False,
            "block_reason": None,
        }

    def ready_result(self):
        boot = self.boot()
        return windows_recovery_readiness.build_recovery_readiness(
            source_identity=self.source(),
            target_evidence=self.target(),
            boot_state=boot,
            rollback_bundle=self.bundle(boot["snapshot_sha256"]),
            collision_check=self.collision(),
        )

    def test_complete_evidence_allows_only_repair_planning(self):
        result = self.ready_result()
        self.assertTrue(result["repair_planning_ready"])
        self.assertFalse(result["destructive_restore_unlocked"])
        self.assertEqual("build-checkpointed-repair-plan", result["allowed_next_stage"])
        self.assertEqual([], result["block_reasons"])
        self.assertEqual("3" * 64, result["target_stable_identity_sha256"])

    def test_missing_stable_target_identity_blocks(self):
        target = self.target()
        target["disk"]["stable_identity_sha256"] = None
        boot = self.boot()
        result = windows_recovery_readiness.build_recovery_readiness(
            source_identity=self.source(),
            target_evidence=target,
            boot_state=boot,
            rollback_bundle=self.bundle(boot["snapshot_sha256"]),
            collision_check=self.collision(),
        )
        self.assertFalse(result["repair_planning_ready"])
        self.assertIn(
            "target-stable-identity-sha256-invalid",
            result["block_reasons"],
        )

    def test_rollback_source_identity_mismatch_blocks(self):
        boot = self.boot()
        bundle = self.bundle(boot["snapshot_sha256"])
        bundle["source_identity_sha256"] = "a" * 64
        bundle.pop("bundle_sha256")
        bundle["bundle_sha256"] = windows_recovery_readiness.sha256_payload(bundle)
        result = windows_recovery_readiness.build_recovery_readiness(
            source_identity=self.source(),
            target_evidence=self.target(),
            boot_state=boot,
            rollback_bundle=bundle,
            collision_check=self.collision(),
        )
        self.assertFalse(result["repair_planning_ready"])
        self.assertIn(
            "rollback-bundle-source-identity-mismatch",
            result["block_reasons"],
        )

    def test_rollback_target_identity_mismatch_blocks(self):
        boot = self.boot()
        bundle = self.bundle(boot["snapshot_sha256"])
        bundle["target_identity_sha256"] = "a" * 64
        bundle.pop("bundle_sha256")
        bundle["bundle_sha256"] = windows_recovery_readiness.sha256_payload(bundle)
        result = windows_recovery_readiness.build_recovery_readiness(
            source_identity=self.source(),
            target_evidence=self.target(),
            boot_state=boot,
            rollback_bundle=bundle,
            collision_check=self.collision(),
        )
        self.assertFalse(result["repair_planning_ready"])
        self.assertIn(
            "rollback-bundle-target-identity-mismatch",
            result["block_reasons"],
        )

    def test_rollback_stable_target_identity_mismatch_blocks(self):
        boot = self.boot()
        bundle = self.bundle(boot["snapshot_sha256"])
        bundle["target_stable_identity_sha256"] = "a" * 64
        bundle.pop("bundle_sha256")
        bundle["bundle_sha256"] = windows_recovery_readiness.sha256_payload(bundle)
        result = windows_recovery_readiness.build_recovery_readiness(
            source_identity=self.source(),
            target_evidence=self.target(),
            boot_state=boot,
            rollback_bundle=bundle,
            collision_check=self.collision(),
        )
        self.assertFalse(result["repair_planning_ready"])
        self.assertIn(
            "rollback-bundle-target-stable-identity-mismatch",
            result["block_reasons"],
        )

    def test_collision_proof_without_stable_identity_blocks(self):
        collision = self.collision()
        collision["stable_identity_proven"] = False
        collision["stable_identity_distinct"] = None
        boot = self.boot()
        result = windows_recovery_readiness.build_recovery_readiness(
            source_identity=self.source(),
            target_evidence=self.target(),
            boot_state=boot,
            rollback_bundle=self.bundle(boot["snapshot_sha256"]),
            collision_check=collision,
        )
        self.assertFalse(result["repair_planning_ready"])
        self.assertIn(
            "source-target-stable-identity-not-proven",
            result["block_reasons"],
        )

    def test_collision_stable_target_must_match_target_evidence(self):
        collision = self.collision()
        collision["target_stable_identity_sha256"] = "a" * 64
        boot = self.boot()
        result = windows_recovery_readiness.build_recovery_readiness(
            source_identity=self.source(),
            target_evidence=self.target(),
            boot_state=boot,
            rollback_bundle=self.bundle(boot["snapshot_sha256"]),
            collision_check=collision,
        )
        self.assertFalse(result["repair_planning_ready"])
        self.assertIn(
            "collision-proof-target-stable-identity-mismatch",
            result["block_reasons"],
        )

    def test_same_device_blocks(self):
        collision = self.collision()
        collision["source_target_distinct"] = False
        collision["blocked"] = True
        boot = self.boot()
        result = windows_recovery_readiness.build_recovery_readiness(
            source_identity=self.source(),
            target_evidence=self.target(),
            boot_state=boot,
            rollback_bundle=self.bundle(boot["snapshot_sha256"]),
            collision_check=collision,
        )
        self.assertFalse(result["repair_planning_ready"])
        self.assertIn("source-target-not-proven-distinct", result["block_reasons"])

    def test_stale_or_tampered_boot_state_blocks(self):
        boot = self.boot()
        bundle = self.bundle(boot["snapshot_sha256"])
        boot["efi_system_partitions"].append({"disk_number": 9, "partition_number": 9})
        result = windows_recovery_readiness.build_recovery_readiness(
            source_identity=self.source(),
            target_evidence=self.target(),
            boot_state=boot,
            rollback_bundle=bundle,
            collision_check=self.collision(),
        )
        self.assertFalse(result["repair_planning_ready"])
        self.assertIn("boot-state-sha256-mismatch", result["block_reasons"])

    def test_incomplete_rollback_bundle_blocks(self):
        boot = self.boot()
        bundle = self.bundle(boot["snapshot_sha256"])
        bundle["complete"] = False
        bundle["repair_unlock_ready"] = False
        bundle.pop("bundle_sha256")
        bundle["bundle_sha256"] = windows_recovery_readiness.sha256_payload(bundle)
        result = windows_recovery_readiness.build_recovery_readiness(
            source_identity=self.source(),
            target_evidence=self.target(),
            boot_state=boot,
            rollback_bundle=bundle,
            collision_check=self.collision(),
        )
        self.assertFalse(result["repair_planning_ready"])
        self.assertIn("rollback-bundle-incomplete", result["block_reasons"])

    def test_target_capacity_blocks(self):
        target = self.target()
        target["disk"]["size_bytes"] = 512
        boot = self.boot()
        result = windows_recovery_readiness.build_recovery_readiness(
            source_identity=self.source(),
            target_evidence=target,
            boot_state=boot,
            rollback_bundle=self.bundle(boot["snapshot_sha256"]),
            collision_check=self.collision(),
        )
        self.assertFalse(result["repair_planning_ready"])
        self.assertIn("target-capacity-smaller-than-source", result["block_reasons"])

    def test_collision_target_must_match_target_evidence(self):
        collision = self.collision()
        collision["target_physical_target"] = r"\\.\PHYSICALDRIVE9"
        boot = self.boot()
        result = windows_recovery_readiness.build_recovery_readiness(
            source_identity=self.source(),
            target_evidence=self.target(),
            boot_state=boot,
            rollback_bundle=self.bundle(boot["snapshot_sha256"]),
            collision_check=collision,
        )
        self.assertFalse(result["repair_planning_ready"])
        self.assertIn("collision-proof-target-mismatch", result["block_reasons"])


if __name__ == "__main__":
    unittest.main()
