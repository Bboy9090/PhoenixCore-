import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "restore_rehearsal",
    Path(__file__).resolve().parent.parent
    / "scripts/hardware/assess_restore_rehearsal.py",
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class RestoreRehearsalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        source = root / "backup.img"
        source.write_bytes(b"backup bytes")
        executor = root / "vm-executor"
        executor.write_bytes(b"fixture executable")
        executor.chmod(0o700)
        sandbox = root / "sandbox"
        sandbox.mkdir()
        self.args = dict(
            source=source,
            expected_sha256=hashlib.sha256(b"backup bytes").hexdigest(),
            sandbox=sandbox,
            destination=sandbox / "rehearsal.qcow2",
            image_architecture="x86_64",
            executor_architectures=("x86_64",),
            executor=executor,
        )

    def test_ready_only_allows_plan_review_and_does_not_create_image(self):
        result = module.assess_restore_rehearsal(**self.args)
        self.assertTrue(result["prerequisites_ready"])
        self.assertFalse(result["restore_executor_authorized"])
        self.assertFalse(result["boot_proven"])
        self.assertFalse(self.args["destination"].exists())

    def test_changed_source_blocks(self):
        self.args["source"].write_bytes(b"changed")
        self.assertIn(
            "source-integrity-mismatch",
            module.assess_restore_rehearsal(**self.args)["block_reasons"],
        )

    def test_existing_destination_blocks(self):
        self.args["destination"].write_bytes(b"valuable image")
        self.assertIn(
            "destination-must-be-new",
            module.assess_restore_rehearsal(**self.args)["block_reasons"],
        )

    def test_escape_and_physical_destination_block(self):
        self.args["destination"] = self.args["sandbox"].parent / "physical-drive"
        result = module.assess_restore_rehearsal(**self.args)
        self.assertIn("destination-not-direct-sandbox-child", result["block_reasons"])
        self.assertIn("destination-not-disposable-image", result["block_reasons"])

    def test_symlink_destination_blocks(self):
        try:
            self.args["destination"].symlink_to(self.args["source"])
        except OSError as exc:
            if getattr(exc, "winerror", None) == 1314:
                self.skipTest("Windows symlink creation privilege unavailable")
            raise
        self.assertFalse(
            module.assess_restore_rehearsal(**self.args)["prerequisites_ready"]
        )

    def test_missing_executor_and_architecture_mismatch_block(self):
        self.args["executor"] = self.args["sandbox"] / "missing"
        self.args["image_architecture"] = "aarch64"
        result = module.assess_restore_rehearsal(**self.args)
        self.assertIn("executor-unavailable", result["block_reasons"])
        self.assertIn("executor-architecture-unsupported", result["block_reasons"])

    def test_self_asserted_boot_receipt_never_proves_boot(self):
        baseline = module.assess_restore_rehearsal(**self.args)
        result = module.assess_restore_rehearsal(
            **self.args,
            boot_receipt={
                "assessment_binding_sha256": baseline["assessment_binding_sha256"],
                "boot_success": True,
            },
        )
        self.assertTrue(result["boot_receipt_binding_matches"])
        self.assertFalse(result["boot_receipt_trusted"])
        self.assertFalse(result["boot_proven"])


if __name__ == "__main__":
    unittest.main()
