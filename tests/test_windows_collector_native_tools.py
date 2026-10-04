"""Mocked native collector contracts; no Windows acquisition proof."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.hardware import capture_windows_drive_evidence as drives
from scripts.hardware import resolve_windows_source_disk as sources
from scripts.hardware import windows_system_tools as tools


class NativeCollectorContractTests(unittest.TestCase):
    def test_drive_collector_uses_resolved_binary_and_checks_before_casts(self):
        result = subprocess.CompletedProcess([], 0, '{"Number":7}', '')
        with patch.object(drives.sys, "platform", "win32"), patch.object(drives, "system_tool_path", return_value="C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"), patch.object(drives.subprocess, "run", return_value=result) as run:
            self.assertEqual(drives.query_windows_disk(7), {"Number": 7})
        command = run.call_args.args[0]
        self.assertEqual(command[0], "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
        script = command[-1]
        self.assertLess(script.index("$property.Value -isnot [bool]"), script.index("IsBoot = [bool]$disk.IsBoot"))
        self.assertIn("Missing or non-boolean partition safety fact", script)
        self.assertIn("Get-Partition -DiskNumber 7 -ErrorAction Stop", script)

    def test_invalid_disk_number_never_reaches_native_command(self):
        with patch.object(drives.sys, "platform", "win32"), patch.object(drives.subprocess, "run") as run:
            for number in (True, -1, "1;Remove-Item"):
                with self.assertRaises(drives.EvidenceError):
                    drives.query_windows_disk(number)
            run.assert_not_called()

    def test_source_collector_uses_resolved_binary(self):
        with tempfile.TemporaryDirectory() as directory:
            raw = {"DiskNumber": 1, "PartitionNumber": 2, "SerialNumber": "source", "BusType": "SATA", "SizeBytes": 1000}
            result = subprocess.CompletedProcess([], 0, json.dumps(raw), '')
            with patch.object(sources.sys, "platform", "win32"), patch.object(sources, "source_drive_letter", return_value="C"), patch.object(sources, "system_tool_path", return_value="C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe"), patch.object(sources.subprocess, "run", return_value=result) as run:
                record = sources.query_source_disk(directory)
            self.assertEqual(record["disk_number"], 1)
            self.assertEqual(run.call_args.args[0][0], "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")

    def test_missing_partition_flags_block_candidate(self):
        raw = json.loads((Path(__file__).parent / "fixtures/windows_disk_usb.json").read_text())
        for field in ("IsBoot", "IsSystem"):
            partition = dict(raw["Partitions"][0])
            del partition[field]
            record = drives.normalize_disk_record(dict(raw, Partitions=[partition]), r"\\.\PHYSICALDRIVE1")
            self.assertFalse(record["write_candidate"])
            self.assertIn("partition-safety-fact-unknown-" + field.lower(), record["write_block_reasons"])

    def test_system_tool_allowlist_refuses_arbitrary_paths(self):
        with self.assertRaises(ValueError):
            tools.system_tool_path("../evil.exe")
