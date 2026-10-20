"""Existing evidence must survive a competing create after path validation."""

from contextlib import ExitStack
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import usb_creator
import writer_safety_contract
import real_writer_interface


class EvidenceExportRaceTests(unittest.TestCase):
    def test_all_evidence_exporters_preserve_concurrently_created_file(self):
        families = [
            (usb_creator, "audit", "validate_export_safety"),
            (
                writer_safety_contract,
                "writer_contract",
                "validate_writer_contract_export_path",
            ),
            (
                real_writer_interface,
                "hardware_preflight",
                "validate_hardware_preflight_export_path",
            ),
            (
                real_writer_interface,
                "physical_writer_dryrun",
                "validate_physical_writer_dryrun_export_path",
            ),
            (
                real_writer_interface,
                "physical_usb_write_lab",
                "validate_physical_usb_write_lab_export_path",
            ),
            (
                real_writer_interface,
                "hardware_evidence",
                "validate_hardware_evidence_export_path",
            ),
        ]
        with tempfile.TemporaryDirectory() as folder:
            for module, family, validator in families:
                for fmt, extension in (("json", "json"), ("markdown", "md")):
                    with self.subTest(family=family, format=fmt):
                        path = Path(folder) / f"{family}.{extension}"
                        sentinel = b"Existing forensic evidence must survive."

                        def concurrent_create(*args, **kwargs):
                            path.write_bytes(sentinel)

                        with ExitStack() as stack:
                            stack.enter_context(
                                patch.object(
                                    module, validator, side_effect=concurrent_create
                                )
                            )
                            if fmt == "markdown":
                                stack.enter_context(
                                    patch.object(
                                        module,
                                        f"generate_{family}_markdown",
                                        return_value="new evidence",
                                    )
                                )
                            exporter = getattr(module, f"export_{family}_{fmt}")
                            if module is usb_creator:
                                with self.assertRaises(FileExistsError):
                                    exporter({}, str(path))
                            else:
                                result = exporter({}, str(path))
                                self.assertEqual("failed", result["status"])
                                self.assertIn("exist", result["error"].lower())
                        self.assertEqual(sentinel, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
