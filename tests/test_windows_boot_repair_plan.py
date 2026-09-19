import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "hardware"
    / "plan_windows_boot_repair.py"
)
SPEC = importlib.util.spec_from_file_location("windows_boot_repair_plan", MODULE_PATH)
assert SPEC and SPEC.loader
windows_boot_repair_plan = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(windows_boot_repair_plan)


class WindowsBootRepairPlanTests(unittest.TestCase):
    def readiness(self):
        payload = {
            "schema": "phoenix_key.windows_recovery_readiness.v1",
            "repair_planning_ready": True,
            "destructive_restore_unlocked": False,
            "allowed_next_stage": "build-checkpointed-repair-plan",
            "source_identity_sha256": "1" * 64,
            "target_identity_sha256": "2" * 64,
            "boot_state_snapshot_sha256": "3" * 64,
            "rollback_bundle_sha256": "4" * 64,
            "block_reasons": [],
            "system_mutations_performed": False,
        }
        payload["readiness_sha256"] = windows_boot_repair_plan.sha256_payload(payload)
        return payload

    def test_bcd_repair_plan_is_checkpointed_and_non_executable(self):
        plan = windows_boot_repair_plan.build_repair_plan(
            readiness=self.readiness(),
            repair_kind="bcd_repair",
        )
        self.assertFalse(plan["execution_enabled"])
        self.assertFalse(plan["destructive_restore_unlocked"])
        self.assertFalse(plan["system_mutations_performed"])
        self.assertIn(
            "recheck_target_identity_immediately_before_repair",
            plan["checkpoints"],
        )
        self.assertIn("bcd_store_export", plan["required_rollback_artifacts"])

    def test_winre_repair_requires_winre_backup(self):
        plan = windows_boot_repair_plan.build_repair_plan(
            readiness=self.readiness(),
            repair_kind="winre_relink",
        )
        self.assertIn("winre_image", plan["required_rollback_artifacts"])
        self.assertIn("identify_existing_winre_image", plan["planned_actions"])

    def test_efi_repair_requires_signed_boot_verification(self):
        plan = windows_boot_repair_plan.build_repair_plan(
            readiness=self.readiness(),
            repair_kind="efi_boot_files_repair",
        )
        self.assertIn("verify_signed_windows_boot_files", plan["planned_actions"])
        self.assertIn("verify_secure_boot_compatibility", plan["planned_actions"])

    def test_tampered_readiness_is_rejected(self):
        readiness = self.readiness()
        readiness["target_identity_sha256"] = "9" * 64
        with self.assertRaises(windows_boot_repair_plan.RepairPlanError):
            windows_boot_repair_plan.build_repair_plan(
                readiness=readiness,
                repair_kind="bcd_repair",
            )

    def test_destructive_unlock_state_is_rejected(self):
        readiness = self.readiness()
        readiness["destructive_restore_unlocked"] = True
        readiness.pop("readiness_sha256")
        readiness["readiness_sha256"] = windows_boot_repair_plan.sha256_payload(
            readiness
        )
        with self.assertRaises(windows_boot_repair_plan.RepairPlanError):
            windows_boot_repair_plan.build_repair_plan(
                readiness=readiness,
                repair_kind="bcd_repair",
            )

    def test_unsupported_repair_kind_is_rejected(self):
        with self.assertRaises(windows_boot_repair_plan.RepairPlanError):
            windows_boot_repair_plan.build_repair_plan(
                readiness=self.readiness(),
                repair_kind="firmware_password_bypass",
            )


if __name__ == "__main__":
    unittest.main()
