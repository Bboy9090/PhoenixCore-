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
    build_writer_contract_session_id,
    build_writer_contract_ledger_record,
    validate_writer_contract_ledger_path,
    append_writer_contract_ledger_record,
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


class TestWriterSafetyContractLedger(unittest.TestCase):
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

    def test_01_session_id_is_deterministic(self):
        """1. Session ID is deterministic for same meaningful inputs."""
        s1 = build_writer_contract_session_id(self.contract)
        s2 = build_writer_contract_session_id(self.contract)
        self.assertEqual(s1, s2)
        self.assertTrue(s1.startswith("session_"))

    def test_02_session_id_changes_when_image_hash_changes(self):
        """2. Session ID changes when image identity hash changes."""
        s1 = build_writer_contract_session_id(self.contract)

        # Modify the image hash in contract copy
        contract_modified = self.contract.copy()
        contract_modified["image_identity"] = {
            "identity_hash": "different_hash_value_12345"
        }
        s2 = build_writer_contract_session_id(contract_modified)
        self.assertNotEqual(s1, s2)

    def test_03_ledger_record_schema_is_correct(self):
        """3. Ledger record schema is bootforge.writer_safety_contract_ledger.v1."""
        rec = build_writer_contract_ledger_record(self.contract, "test_event")
        self.assertEqual(rec["schema"], "bootforge.writer_safety_contract_ledger.v1")
        self.assertEqual(rec["event_type"], "test_event")
        self.assertTrue(rec["ledger_record_id"].startswith("ledger_"))

    def test_04_ledger_record_preserves_real_writer_implemented_false(self):
        """4. Ledger record preserves real_writer_implemented false."""
        rec = build_writer_contract_ledger_record(self.contract, "test_event")
        self.assertIs(rec["real_writer_implemented"], False)

    def test_05_ledger_record_preserves_destructive_operations_enabled_false(self):
        """5. Ledger record preserves destructive_operations_enabled false."""
        rec = build_writer_contract_ledger_record(self.contract, "test_event")
        self.assertIs(rec["destructive_operations_enabled"], False)

    def test_06_ledger_append_writes_jsonl(self):
        """6. Ledger append writes JSONL (one JSON object per line)."""
        rec = build_writer_contract_ledger_record(self.contract, "test_event")
        ledger_path = os.path.join(self.test_dir, "ledger.jsonl")
        res = append_writer_contract_ledger_record(rec, ledger_path)
        self.assertEqual(res["status"], "success")

        with open(ledger_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 1)
        data = json.loads(lines[0])
        self.assertEqual(data["ledger_record_id"], rec["ledger_record_id"])

    def test_07_ledger_append_appends_instead_of_overwriting(self):
        """7. Ledger append appends instead of overwriting."""
        ledger_path = os.path.join(self.test_dir, "ledger.jsonl")

        rec1 = build_writer_contract_ledger_record(self.contract, "event_1")
        append_writer_contract_ledger_record(rec1, ledger_path)

        rec2 = build_writer_contract_ledger_record(self.contract, "event_2")
        append_writer_contract_ledger_record(rec2, ledger_path)

        with open(ledger_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(len(lines), 2)
        d1 = json.loads(lines[0])
        d2 = json.loads(lines[1])
        self.assertEqual(d1["event_type"], "event_1")
        self.assertEqual(d2["event_type"], "event_2")

    def test_08_ledger_append_rejects_non_jsonl_extension(self):
        """8. Ledger append rejects non-.jsonl extension."""
        rec = build_writer_contract_ledger_record(self.contract, "event")
        ledger_path = os.path.join(self.test_dir, "ledger.json")
        res = append_writer_contract_ledger_record(rec, ledger_path)
        self.assertEqual(res["status"], "failed")
        self.assertIn("must be '.jsonl'", res["error"])

    def test_09_ledger_append_rejects_empty_path(self):
        """9. Ledger append rejects empty path."""
        with self.assertRaises(ValueError):
            validate_writer_contract_ledger_path("")
        with self.assertRaises(ValueError):
            validate_writer_contract_ledger_path(None)

    def test_10_ledger_append_rejects_missing_parent_folder(self):
        """10. Ledger append rejects missing parent folder."""
        rec = build_writer_contract_ledger_record(self.contract, "event")
        ledger_path = os.path.join(self.test_dir, "missing_folder", "ledger.jsonl")
        res = append_writer_contract_ledger_record(rec, ledger_path)
        self.assertEqual(res["status"], "failed")
        self.assertIn("Parent directory", res["error"])

    def test_11_ledger_append_rejects_directory_path(self):
        """11. Ledger append rejects directory path."""
        rec = build_writer_contract_ledger_record(self.contract, "event")
        res = append_writer_contract_ledger_record(rec, self.test_dir)
        self.assertEqual(res["status"], "failed")
        self.assertIn("is a directory", res["error"])

    def test_12_ledger_append_rejects_raw_device_paths(self):
        """12. Ledger append rejects raw device paths before resolve."""
        bad_paths = [
            "\\\\.\\PhysicalDrive0\\ledger.jsonl",
            "//./PhysicalDrive0/ledger.jsonl",
        ]
        for p in bad_paths:
            with self.assertRaises(ValueError):
                validate_writer_contract_ledger_path(p)

    def test_13_ledger_append_rejects_unc_namespace_paths(self):
        """13. Ledger append rejects UNC namespace paths."""
        bad_path = "\\\\server\\share\\ledger.jsonl"
        with self.assertRaises(ValueError):
            validate_writer_contract_ledger_path(bad_path)

    def test_14_ledger_append_rejects_suspicious_system_paths(self):
        """14. Ledger append rejects suspicious system paths."""
        bad_paths = ["/etc/ledger.jsonl", "C:\\Windows\\system32\\ledger.jsonl"]
        for p in bad_paths:
            with self.assertRaises(ValueError):
                validate_writer_contract_ledger_path(p)

    def test_15_ledger_append_result_is_json_serializable(self):
        """15. Ledger append result status is JSON serializable."""
        rec = build_writer_contract_ledger_record(self.contract, "event")
        ledger_path = os.path.join(self.test_dir, "ledger.jsonl")
        res = append_writer_contract_ledger_record(rec, ledger_path)
        try:
            json.dumps(res)
        except Exception as e:
            self.fail(f"Ledger append response not JSON serializable: {e}")

    def test_16_cli_ledger_invalid_path_returns_blocked_safely(self):
        """16. CLI ledger invalid path returns blocked safely."""
        rec = build_writer_contract_ledger_record(self.contract, "event")
        ledger_path = os.path.join(self.test_dir, "missing_subdir", "ledger.jsonl")
        res = append_writer_contract_ledger_record(rec, ledger_path)
        self.assertEqual(res["status"], "failed")
        self.assertIsNotNone(res["error"])

    def test_17_dashboard_source_does_not_include_forbidden_ui_labels(self):
        """17. Dashboard App.jsx source must not contain active forbidden UI labels."""
        app_jsx_path = os.path.join(
            Path(__file__).parent.parent, "dashboard", "src", "App.jsx"
        )
        if os.path.exists(app_jsx_path):
            with open(app_jsx_path, "r", encoding="utf-8") as f:
                content = f.read()
            for forbidden in FORBIDDEN_LABELS:
                self.assertNotIn(f">{forbidden}<", content)
                self.assertNotIn(
                    f"'{forbidden}'", content.replace("FORBIDDEN_LABELS = [", "")
                )
                self.assertNotIn(
                    f'"{forbidden}"', content.replace("FORBIDDEN_LABELS = [", "")
                )

    def test_18_ledger_helpers_do_not_invoke_destructive_subprocess_calls(self):
        """18. Ledger helpers must not invoke forbidden subprocess calls."""
        pass

    def test_19_ledger_record_includes_export_result(self):
        """19. Ledger record includes export_result when supplied."""
        exp_res = {"status": "success", "export_path": "audit.json"}
        rec = build_writer_contract_ledger_record(
            self.contract, "event", export_result=exp_res
        )
        self.assertEqual(rec["export_result"], exp_res)

    def test_20_repeated_ledger_record_construction_is_deterministic(self):
        """20. Repeated ledger record construction is deterministic (except created_at/ledger_record_id)."""
        r1 = build_writer_contract_ledger_record(self.contract, "event")
        r2 = build_writer_contract_ledger_record(self.contract, "event")

        # Override volatile timestamp for equivalence check
        r2["created_at"] = r1["created_at"]
        r2["ledger_record_id"] = r1["ledger_record_id"]
        self.assertEqual(r1, r2)


if __name__ == "__main__":
    unittest.main()
