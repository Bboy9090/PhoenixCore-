import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ExternalQualificationInfraTests(unittest.TestCase):
    def setUp(self):
        self.aws = (ROOT / "infra/aws/buildspec-windows-release.yml").read_text(
            encoding="utf-8"
        )
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
        for name, source in (("aws", self.aws), ("google", self.google)):
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


if __name__ == "__main__":
    unittest.main()
