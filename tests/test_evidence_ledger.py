from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "scripts" / "evidence" / "evidence_ledger.py"

spec = importlib.util.spec_from_file_location("evidence_ledger", LEDGER_PATH)
ledger_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["evidence_ledger"] = ledger_module
spec.loader.exec_module(ledger_module)


class EvidenceLedgerTests(unittest.TestCase):
    def test_append_creates_contiguous_hash_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ledger.jsonl"
            ledger = ledger_module.EvidenceLedger(path)

            first = ledger.append(
                "DRIVE.IDENTITY",
                {"target": "disk/by-id/example", "bytes_written": 0},
                timestamp="2026-07-24T00:00:00Z",
            )
            second = ledger.append(
                "DRIVE.WRITE_READBACK",
                {"sha256": "a" * 64, "bytes_written": 4096},
                timestamp="2026-07-24T00:01:00Z",
            )

            records = ledger.verify()
            self.assertEqual([record.sequence for record in records], [1, 2])
            self.assertEqual(first.previous_hash, "0" * 64)
            self.assertEqual(second.previous_hash, first.record_hash)
            self.assertEqual(records[-1].record_hash, second.record_hash)

    def test_payload_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ledger.jsonl"
            ledger = ledger_module.EvidenceLedger(path)
            ledger.append(
                "BOOT.OBSERVED",
                {"classification": "hardware-partial-boot-observed"},
                timestamp="2026-07-24T00:00:00Z",
            )

            record = json.loads(path.read_text(encoding="utf-8"))
            record["payload"]["classification"] = "hardware-validated"
            path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(
                ledger_module.EvidenceLedgerError, "record hash is invalid"
            ):
                ledger.verify()

    def test_deletion_or_reorder_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ledger.jsonl"
            ledger = ledger_module.EvidenceLedger(path)
            ledger.append("A.EVENT", {"value": 1}, timestamp="2026-07-24T00:00:00Z")
            ledger.append("B.EVENT", {"value": 2}, timestamp="2026-07-24T00:01:00Z")

            lines = path.read_text(encoding="utf-8").splitlines()
            path.write_text(lines[1] + "\n", encoding="utf-8")

            with self.assertRaisesRegex(
                ledger_module.EvidenceLedgerError, "sequence is not contiguous"
            ):
                ledger.verify()

    def test_invalid_event_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ledger.jsonl"
            ledger = ledger_module.EvidenceLedger(path)
            with self.assertRaisesRegex(
                ledger_module.EvidenceLedgerError, "uppercase identifier"
            ):
                ledger.append("bad event", {"value": 1})

    def test_nan_payload_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ledger.jsonl"
            ledger = ledger_module.EvidenceLedger(path)
            with self.assertRaises(ValueError):
                ledger.append("BAD.NAN", {"temperature": float("nan")})

    def test_cli_append_and_verify_summary(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger_path = Path(temp_dir) / "ledger.jsonl"
            summary_path = Path(temp_dir) / "summary.json"
            append = subprocess.run(
                [
                    sys.executable,
                    str(LEDGER_PATH),
                    "append",
                    "--ledger",
                    str(ledger_path),
                    "--event-type",
                    "USB.IDENTITY",
                    "--payload-json",
                    '{"target":"usb-test","bytes_written":0}',
                    "--timestamp",
                    "2026-07-24T00:00:00Z",
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            appended = json.loads(append.stdout)
            self.assertEqual(appended["sequence"], 1)

            verify = subprocess.run(
                [
                    sys.executable,
                    str(LEDGER_PATH),
                    "verify",
                    "--ledger",
                    str(ledger_path),
                    "--summary",
                    str(summary_path),
                ],
                check=True,
                text=True,
                capture_output=True,
            )
            verified = json.loads(verify.stdout)
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertTrue(verified["verified"])
            self.assertEqual(summary["record_count"], 1)
            self.assertEqual(summary["head_hash"], appended["record_hash"])


if __name__ == "__main__":
    unittest.main()
