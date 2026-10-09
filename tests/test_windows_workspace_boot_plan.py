import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location(
    "workspace_boot_plan",
    Path(__file__).resolve().parent.parent
    / "scripts/hardware/plan_windows_workspace_boot.py",
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class WorkspaceBootPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        applied = self.root / "applied-files"
        template = applied / "Windows/System32/config/BCD-Template"
        template.parent.mkdir(parents=True)
        template.write_bytes(b"fixture template")
        image = self.root / "source.wim"
        image.write_bytes(b"fixture source")
        self.vhd = self.root / "workspace.vhdx"
        self.vhd.write_bytes(b"vhdxfile" + bytes(64))
        self.receipt = {
            "schema": "arcwyre.windows_offline_image_application.v1",
            "workspace_directory": str(self.root),
            "applied_directory": str(applied),
            "raw_disk_operations_performed": False,
            "source_sha256": module.application._hash(image),
            "applied_manifest": module.application.preparation.media.capture_media_manifest(
                applied
            ),
        }
        self.facts = {
            "disk_unique_id": "fixture disk",
            "bus_type": "File Backed Virtual",
            "is_boot": False,
            "is_system": False,
            "partition_style": "GPT",
            "esp_partition_number": 1,
            "windows_partition_number": 2,
            "esp_filesystem": "FAT32",
            "windows_filesystem": "NTFS",
            "image_path": str(self.vhd),
        }

    def test_deterministic_plan_never_authorizes_execution(self):
        first = module.plan_workspace_boot(self.receipt, self.vhd, self.facts)
        second = module.plan_workspace_boot(self.receipt, self.vhd, self.facts)
        self.assertEqual(first, second)
        self.assertFalse(first["execution_authorized"])
        self.assertFalse(first["windows_to_go_ready"])

    def test_cli_emits_same_read_only_plan(self):
        receipt_path = self.root / "application.json"
        facts_path = self.root / "facts.json"
        receipt_path.write_text(json.dumps(self.receipt), encoding="utf-8")
        facts_path.write_text(json.dumps(self.facts), encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = module.main(
                [
                    "--receipt-json",
                    str(receipt_path),
                    "--vhd-path",
                    str(self.vhd),
                    "--volume-facts-json",
                    str(facts_path),
                ]
            )
        plan = json.loads(output.getvalue())
        self.assertEqual(result, 0)
        self.assertEqual(
            plan, module.plan_workspace_boot(self.receipt, self.vhd, self.facts)
        )
        self.assertFalse(plan["execution_authorized"])
        self.assertFalse(plan["physical_writes_authorized"])
        self.assertFalse(plan["boot_proven"])

    def test_caller_drive_letters_rejected(self):
        self.facts["drive_letter"] = "C"
        with self.assertRaises(RuntimeError):
            module.plan_workspace_boot(self.receipt, self.vhd, self.facts)

    def test_changed_applied_bytes_rejected(self):
        template = self.root / "applied-files/Windows/System32/config/BCD-Template"
        template.write_bytes(b"changed")
        with self.assertRaises(RuntimeError):
            module.plan_workspace_boot(self.receipt, self.vhd, self.facts)

    def test_physical_system_or_equal_partitions_rejected(self):
        for field, value in (
            ("bus_type", "USB"),
            ("is_system", True),
            ("windows_partition_number", 1),
        ):
            facts = {**self.facts, field: value}
            with self.assertRaises(RuntimeError):
                module.plan_workspace_boot(self.receipt, self.vhd, facts)

    def test_vhd_header_and_workspace_scope_required(self):
        self.vhd.write_bytes(b"not vhdx")
        with self.assertRaises(RuntimeError):
            module.plan_workspace_boot(self.receipt, self.vhd, self.facts)


if __name__ == "__main__":
    unittest.main()
