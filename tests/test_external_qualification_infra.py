import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ExternalQualificationInfraTests(unittest.TestCase):
    def setUp(self):
        self.aws = (ROOT / "infra/aws/buildspec-windows-release.yml").read_text(
            encoding="utf-8"
        )
        self.aws_portable = (
            ROOT / "infra/aws/buildspec-portable-release.yml"
        ).read_text(encoding="utf-8")
        self.google = (
            ROOT / "infra/google/cloudbuild-independent.yaml"
        ).read_text(encoding="utf-8")

    def test_cloud_lanes_never_run_destructive_disk_commands(self):
        forbidden = (
            "Clear-Disk",
            "Format-Volume",
            "Remove-Partition",
            "diskpart",
            "provision_windows_installer_disk.py",
            "write_windows_sacrificial_drive.py",
        )
        for name, source in (
            ("aws", self.aws),
            ("aws-portable", self.aws_portable),
            ("google", self.google),
        ):
            with self.subTest(name=name):
                for token in forbidden:
                    self.assertNotIn(token, source)

    def test_aws_lane_is_exact_head_locked_and_emits_only_build_evidence(self):
        self.assertIn("git rev-parse HEAD", self.aws)
        self.assertIn("git diff --exit-code", self.aws)
        self.assertIn("--gate aws_windows_build", self.aws)
        self.assertIn("cargo test --locked", self.aws)
        self.assertIn("test_windows*.py", self.aws)

    def test_google_lane_is_independent_and_retains_receipt(self):
        self.assertIn("--gate google_independent_build", self.google)
        self.assertIn("$COMMIT_SHA", self.google)
        self.assertIn("cargo", self.google)
        self.assertIn("gs://${_EVIDENCE_BUCKET}", self.google)

    def test_aws_portable_lane_is_supplemental_exact_head_evidence(self):
        self.assertIn('git rev-parse HEAD', self.aws_portable)
        self.assertIn('ARCWYRE_EXPECTED_COMMIT', self.aws_portable)
        self.assertIn('--gate aws_portable_build', self.aws_portable)
        self.assertIn('CODEBUILD_BUILD_SUCCEEDING', self.aws_portable)
        self.assertIn('--default-toolchain 1.98.1', self.aws_portable)
        self.assertIn('test_windows*.py', self.aws_portable)
        self.assertIn('cargo test --locked', self.aws_portable)
        self.assertIn('s3://$ARCWYRE_EVIDENCE_BUCKET/$ARCWYRE_EVIDENCE_KEY', self.aws_portable)

    def test_portable_receipt_cannot_satisfy_native_or_hardware_levels(self):
        gate_source = (
            ROOT / "scripts/release/evaluate_arcwyre_release_gate.py"
        ).read_text(encoding="utf-8")
        self.assertIn('"aws_portable_build"', gate_source)
        self.assertIn('"aws_windows_build"', gate_source)
        self.assertIn('"physical_boot"', gate_source)


if __name__ == "__main__":
    unittest.main()
