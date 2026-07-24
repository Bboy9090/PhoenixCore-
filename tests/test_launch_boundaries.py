from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_launch_boundaries",
    ROOT / "scripts" / "validate_launch_boundaries.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LaunchBoundaryTests(unittest.TestCase):
    def matrix(self) -> dict:
        return json.loads(
            (ROOT / "docs" / "LAUNCH_CLAIMS_MATRIX.json").read_text(encoding="utf-8")
        )

    def test_current_matrix_is_truthful_and_blocked(self) -> None:
        report = MODULE.validate_matrix(self.matrix())
        self.assertTrue(report["valid"])
        self.assertFalse(report["launch_eligible"])

    def test_production_claim_is_rejected(self) -> None:
        data = self.matrix()
        data["claims"]["production_release"] = True
        with self.assertRaisesRegex(MODULE.BoundaryError, "production_release"):
            MODULE.validate_matrix(data)

    def test_product_ownership_overlap_is_rejected(self) -> None:
        data = self.matrix()
        data["products"]["PhoenixCore"]["does_not_own"].append("diagnostics")
        with self.assertRaisesRegex(MODULE.BoundaryError, "ownership overlap"):
            MODULE.validate_matrix(data)

    def test_required_hardware_blocker_is_enforced(self) -> None:
        data = self.matrix()
        data["blockers"].remove("issue-135-hardware-validation")
        with self.assertRaisesRegex(MODULE.BoundaryError, "hardware blocker"):
            MODULE.validate_matrix(data)

    def test_documents_preserve_locked_boundaries(self) -> None:
        MODULE.validate_docs(ROOT)


if __name__ == "__main__":
    unittest.main()
