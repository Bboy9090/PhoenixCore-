import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import usb_creator


class RegistryFailClosedTests(unittest.TestCase):
    def test_validation_rejects_missing_registry_object(self):
        with patch("usb_creator.load_tool_registry", return_value=None):
            self.assertFalse(
                usb_creator.validate_tool_against_registry("any-tool")
            )

    def test_missing_registry_file_cannot_approve_tool(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir) / "usb_creator.py"
            with patch.object(usb_creator, "__file__", str(module_path)):
                self.assertFalse(
                    usb_creator.validate_tool_against_registry("any-tool")
                )

    def test_missing_signature_halts_registry_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir) / "usb_creator.py"
            manifests = Path(tmpdir) / "manifests"
            manifests.mkdir()
            (manifests / "tool_registry.json").write_text(
                '{"tools": []}', encoding="utf-8"
            )
            with patch.object(usb_creator, "__file__", str(module_path)):
                with self.assertRaises(SystemExit):
                    usb_creator.load_tool_registry()

    def test_invalid_signature_halts_registry_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir) / "usb_creator.py"
            manifests = Path(tmpdir) / "manifests"
            manifests.mkdir()
            (manifests / "tool_registry.json").write_text(
                '{"tools": []}', encoding="utf-8"
            )
            (manifests / "tool_registry.sig").write_text(
                "00" * 64, encoding="utf-8"
            )
            with patch.object(usb_creator, "__file__", str(module_path)):
                with self.assertRaises(SystemExit):
                    usb_creator.load_tool_registry()

    def test_malformed_signed_json_halts_registry_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir) / "usb_creator.py"
            manifests = Path(tmpdir) / "manifests"
            manifests.mkdir()
            (manifests / "tool_registry.json").write_text(
                "{not-json", encoding="utf-8"
            )
            (manifests / "tool_registry.sig").write_text(
                "11" * 64, encoding="utf-8"
            )
            with patch.object(usb_creator, "__file__", str(module_path),), patch(
                "usb_creator.ed25519_verify", return_value=True
            ):
                with self.assertRaises(SystemExit):
                    usb_creator.load_tool_registry()


if __name__ == "__main__":
    unittest.main()
