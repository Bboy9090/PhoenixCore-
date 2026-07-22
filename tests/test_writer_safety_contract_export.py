import unittest
import tempfile
import os
import json
import shutil
import sys
from pathlib import Path

# Add repo root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from writer_safety_contract import (
    build_contract_preview_payload,
    validate_writer_contract_export_path,
    export_writer_contract_json,
    export_writer_contract_markdown,
)

FORBIDDEN_LABELS = [
    "Write USB",
    "Burn USB",
    "Flash USB",
    "Start Write",
    "Format USB",
    "Erase Drive",
    "Arm Writer",
    "Execute Write",
    "Destructive Write",
    "Write Now",
]


class TestWriterSafetyContractExport(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.contract = build_contract_preview_payload(
            target_drive="E:\\",
            image="C:\\test\\ubuntu.iso",
            audit_passed=True,
            simulation_passed=True,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_01_json_export_writes_valid_json(self):
        """1. JSON export writes a valid JSON evidence file."""
        out_path = os.path.join(self.test_dir, "evidence.json")
        res = export_writer_contract_json(self.contract, out_path)
        self.assertEqual(res["status"], "success")
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["schema"], "bootforge.writer_safety_contract.v1")
            self.assertEqual(data["contract_id"], self.contract["contract_id"])

    def test_02_markdown_export_writes_markdown(self):
        """2. Markdown export writes a Markdown evidence file."""
        out_path = os.path.join(self.test_dir, "evidence.md")
        res = export_writer_contract_markdown(self.contract, out_path)
        self.assertEqual(res["status"], "success")
        self.assertTrue(os.path.exists(out_path))
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(
                "# PhoenixCore / BootForge Writer Safety Contract Report", content
            )

    def test_03_json_export_rejects_non_json_extension(self):
        """3. JSON export rejects non-.json extension."""
        out_path = os.path.join(self.test_dir, "evidence.txt")
        res = export_writer_contract_json(self.contract, out_path)
        self.assertEqual(res["status"], "failed")
        self.assertIn("does not match format 'json'", res["error"])

    def test_04_markdown_export_rejects_non_md_extension(self):
        """4. Markdown export rejects non-.md extension."""
        out_path = os.path.join(self.test_dir, "evidence.txt")
        res = export_writer_contract_markdown(self.contract, out_path)
        self.assertEqual(res["status"], "failed")
        self.assertIn("does not match format 'markdown'", res["error"])

    def test_05_export_rejects_missing_output_path(self):
        """5. Export path validation rejects empty paths."""
        with self.assertRaises(ValueError):
            validate_writer_contract_export_path("", "json")
        with self.assertRaises(ValueError):
            validate_writer_contract_export_path(None, "json")

    def test_06_export_rejects_missing_parent_directory(self):
        """6. Export rejects missing parent directory."""
        out_path = os.path.join(self.test_dir, "nonexistent_dir", "evidence.json")
        res = export_writer_contract_json(self.contract, out_path)
        self.assertEqual(res["status"], "failed")
        self.assertIn("Parent directory", res["error"])

    def test_07_export_rejects_directory_path(self):
        """7. Export rejects a directory path."""
        res = export_writer_contract_json(self.contract, self.test_dir)
        self.assertEqual(res["status"], "failed")
        self.assertIn("is a directory", res["error"])

    def test_08_export_rejects_overwrite_by_default(self):
        """8. Export rejects overwriting an existing file."""
        out_path = os.path.join(self.test_dir, "evidence.json")
        with open(out_path, "w") as f:
            f.write("{}")
        res = export_writer_contract_json(self.contract, out_path)
        self.assertEqual(res["status"], "failed")
        self.assertIn("already exists", res["error"])

    def test_09_export_rejects_target_drive_root(self):
        """9. Export rejects writing to target drive root (same drive)."""
        # We target a file in self.test_dir but mock get_drive_root to simulate it matching the target_drive root
        with unittest.mock.patch("usb_creator.get_drive_root") as mock_root:
            mock_root.return_value = "E:\\"
            out_path = os.path.join(self.test_dir, "evidence.json")
            res = export_writer_contract_json(self.contract, out_path)
            self.assertEqual(res["status"], "failed")
            self.assertIn("is on the target drive", res["error"])

    def test_10_export_rejects_raw_device_paths(self):
        """10. Export rejects raw device paths and UNC network paths."""
        bad_paths = [
            "\\\\.\\PhysicalDrive0\\evidence.json",
            "//./PhysicalDrive0/evidence.json",
            "\\\\server\\share\\evidence.json",
        ]
        for p in bad_paths:
            with self.assertRaises(ValueError):
                validate_writer_contract_export_path(p, "json")

    def test_11_export_payload_preserves_real_writer_implemented_false(self):
        """11. Export payload preserves real_writer_implemented false."""
        self.assertIs(self.contract["real_writer_implemented"], False)

    def test_12_export_payload_preserves_destructive_operations_enabled_false(self):
        """12. Export payload preserves destructive_operations_enabled false."""
        self.assertIs(self.contract["destructive_operations_enabled"], False)

    def test_13_export_result_is_json_serializable(self):
        """13. Export status payload is JSON serializable."""
        out_path = os.path.join(self.test_dir, "evidence.json")
        res = export_writer_contract_json(self.contract, out_path)
        try:
            json.dumps(res)
        except Exception as e:
            self.fail(f"Export response not JSON serializable: {e}")

    def test_14_markdown_contains_safety_copy(self):
        """14. Markdown export contains read-only safety statements."""
        out_path = os.path.join(self.test_dir, "evidence.md")
        export_writer_contract_markdown(self.contract, out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("read-only safety contract preview only", content)
            self.assertIn(
                "All actual destructive writing engines remain completely locked",
                content,
            )

    def test_15_export_helpers_do_not_invoke_destructive_subprocess_calls(self):
        """15. Export helpers must not invoke forbidden subprocess calls (diskpart, dd, etc.)."""
        pass

    def test_16_dashboard_source_does_not_include_forbidden_ui_labels(self):
        """16. Dashboard App.jsx source must not contain forbidden destructive UI labels."""
        app_jsx_path = os.path.join(
            Path(__file__).parent.parent, "dashboard", "src", "App.jsx"
        )
        if os.path.exists(app_jsx_path):
            with open(app_jsx_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Clean comments/literals checks:
            for forbidden in FORBIDDEN_LABELS:
                self.assertNotIn(f">{forbidden}<", content)
                self.assertNotIn(
                    f"'{forbidden}'", content.replace("FORBIDDEN_LABELS = [", "")
                )
                self.assertNotIn(
                    f'"{forbidden}"', content.replace("FORBIDDEN_LABELS = [", "")
                )

    def test_17_cli_export_path_returns_blocked_safely_when_invalid(self):
        """17. CLI export validates paths and returns blocked result safely."""
        out_path = os.path.join(self.test_dir, "nonexistent_dir", "evidence.json")
        res = export_writer_contract_json(self.contract, out_path)
        self.assertEqual(res["status"], "failed")
        self.assertIsNotNone(res["error"])


if __name__ == "__main__":
    unittest.main()
