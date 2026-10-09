import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "windows_media_result_report",
    Path(__file__).resolve().parent.parent
    / "scripts/hardware/windows_media_result_report.py",
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class ResultReportTests(unittest.TestCase):
    def staging(self):
        return {
            "schema": "arcwyre.windows_install_staging.v1",
            "verified_bytes": 42,
            "staging_directory": "staged/media",
            "staging_verified": True,
            "raw_disk_operations_performed": False,
            "boot_verified": False,
        }

    def test_readback_is_reported_without_boot_or_rescue_claims(self):
        result = module.build_result_report(staging=self.staging())
        self.assertEqual(42, result["reported_staging_verified_bytes"])
        self.assertFalse(result["boot_proven"])
        self.assertFalse(result["data_rescue_verified"])
        self.assertIn("Reported staging", result["text"])

    def test_bad_shapes_fail_safely(self):
        for bad in (False, [], "success", {"schema": "wrong"}):
            self.assertTrue(
                module.build_result_report(staging=bad)["unresolved_reasons"]
            )

    def test_boolean_and_negative_bytes_rejected(self):
        for bad in (True, -1, "42"):
            staging = self.staging()
            staging["verified_bytes"] = bad
            self.assertIsNone(
                module.build_result_report(staging=staging)[
                    "reported_staging_verified_bytes"
                ]
            )

    def test_forged_boot_claim_rejected(self):
        staging = self.staging()
        staging["boot_verified"] = True
        result = module.build_result_report(staging=staging)
        self.assertTrue(result["unresolved_reasons"])
        self.assertIsNone(result["reported_staging_verified_bytes"])

    def test_failure_retains_partial_path_and_next_step(self):
        result = module.build_result_report(
            failure={"message": "cancelled", "partial_directory": "partial/output"}
        )
        self.assertEqual("partial/output", result["output_path"])
        self.assertTrue(result["output_requires_review"])
        self.assertIn("preserve partial", result["next_step"])

    def test_malformed_reasons_rejected(self):
        result = module.build_result_report(
            compatibility={
                "schema": module.SCHEMAS["compatibility"],
                "block_reasons": "none",
            }
        )
        self.assertTrue(result["unresolved_reasons"])

    def test_resume_bytes_never_count_as_staging_verification(self):
        result = module.build_result_report(
            resume={
                "schema": module.SCHEMAS["resume"],
                "verified_completed_bytes": 10,
                "source_total_bytes": 5,
            }
        )
        self.assertTrue(result["unresolved_reasons"])
        self.assertIsNone(result["reported_staging_verified_bytes"])

    def test_preparation_bytes_do_not_prove_image_integrity(self):
        prepared = self.staging()
        prepared["schema"] = module.SCHEMAS["preparation"]
        prepared["original_source_modified"] = False
        result = module.build_result_report(preparation=prepared)
        self.assertEqual(42, result["reported_preparation_verified_bytes"])
        self.assertIsNone(result["reported_staging_verified_bytes"])
        self.assertTrue(result["unresolved_reasons"])
        self.assertFalse(result["boot_proven"])


if __name__ == "__main__":
    unittest.main()
