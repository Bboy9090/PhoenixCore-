import json
import tempfile
import unittest
from pathlib import Path

from scripts.release import evaluate_arcwyre_release_gate as gate
from scripts.release import emit_arcwyre_release_evidence as emitter


class ArcwyreReleaseGateTests(unittest.TestCase):
    source_commit = "a" * 40

    def receipt(self, name, status="passed"):
        payload = {
            "schema": gate.SCHEMA,
            "gate": name,
            "status": status,
            "source_commit": self.source_commit,
            "executor": "fixture-executor",
            "observed_at": "2026-10-26T09:00:00Z",
            "evidence_uri": "fixture://retained-evidence",
        }
        payload["receipt_sha256"] = gate.canonical_sha256(payload)
        return payload

    def write(self, directory, name, payload):
        (Path(directory) / name).write_text(
            json.dumps(payload), encoding="utf-8"
        )

    def test_integrated_requires_all_four_exact_commit_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in gate.LEVELS["integrated"]:
                self.write(directory, f"{name}.json", self.receipt(name))
            report = gate.evaluate(
                evidence_dir=Path(directory),
                source_commit=self.source_commit,
                target_level="integrated",
            )
        self.assertTrue(report["promoted"])
        self.assertEqual("integrated", report["classification"])
        self.assertEqual([], report["missing_gates"])

    def test_missing_or_blocked_hardware_proof_never_promotes(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in gate.LEVELS["hardware_validated"]:
                if name == "physical_boot":
                    continue
                status = "blocked" if name == "usb_provisioning" else "passed"
                self.write(directory, f"{name}.json", self.receipt(name, status))
            report = gate.evaluate(
                evidence_dir=Path(directory),
                source_commit=self.source_commit,
                target_level="hardware_validated",
            )
        self.assertFalse(report["promoted"])
        self.assertIn("physical_boot", report["missing_gates"])
        self.assertIn("usb_provisioning", report["not_passed_gates"])

    def test_tampered_wrong_commit_and_duplicate_receipts_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = self.receipt("windows_native_suite")
            payload["executor"] = "tampered"
            self.write(directory, "tampered.json", payload)

            wrong = self.receipt("aws_windows_build")
            wrong["source_commit"] = "b" * 40
            wrong["receipt_sha256"] = gate.canonical_sha256(wrong)
            self.write(directory, "wrong.json", wrong)

            duplicate = self.receipt("google_independent_build")
            self.write(directory, "duplicate-a.json", duplicate)
            self.write(directory, "duplicate-b.json", duplicate)

            report = gate.evaluate(
                evidence_dir=Path(directory),
                source_commit=self.source_commit,
                target_level="integrated",
            )
        self.assertFalse(report["promoted"])
        self.assertEqual(4, len(report["rejected_receipts"]))

    def test_atomic_output_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            gate.write_json_atomic(output, {"status": "first"})
            with self.assertRaisesRegex(gate.EvidenceError, "already exists"):
                gate.write_json_atomic(output, {"status": "second"})
            self.assertEqual("first", json.loads(output.read_text())["status"])

    def test_invalid_source_commit_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(gate.EvidenceError, "source commit"):
                gate.evaluate(
                    evidence_dir=Path(directory),
                    source_commit="not-a-sha",
                    target_level="integrated",
                )

    def test_emitter_output_is_accepted_by_evaluator(self):
        from argparse import Namespace

        args = Namespace(
            gate="windows_native_suite",
            status="passed",
            source_commit=self.source_commit,
            executor="DESKTOP-3T2DJIM",
            observed_at="2026-10-26T09:00:00Z",
            evidence_uri="file://retained/native-suite.log",
        )
        payload = emitter.build_receipt(args)
        self.assertEqual(payload["receipt_sha256"], gate.canonical_sha256(payload))


if __name__ == "__main__":
    unittest.main()
