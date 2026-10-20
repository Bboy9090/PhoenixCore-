"""Portable file/PE qualification; no Windows firmware boot proof."""

import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "installer_readback",
    Path(__file__).resolve().parents[1]
    / "scripts/hardware/verify_windows_installer_readback.py",
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def efi_image(architecture="x64"):
    _, machine, magic = module.EFI_TARGETS[architecture]
    data = bytearray(1024)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 60, 128)
    data[128:132] = b"PE\0\0"
    struct.pack_into("<HH", data, 132, machine, 1)
    struct.pack_into("<HH", data, 148, 240, 2)
    struct.pack_into("<H", data, 152, magic)
    struct.pack_into("<I", data, 168, 0x1000)
    struct.pack_into("<I", data, 208, 0x2000)
    struct.pack_into("<H", data, 220, 10)
    struct.pack_into("<IIII", data, 400, 512, 0x1000, 512, 512)
    struct.pack_into("<I", data, 428, 0x20000000)
    return data


class InstallerReadbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "source"
        self.destination = Path(self.temp.name) / "destination"
        loader = self.source / "EFI/Boot/bootx64.efi"
        loader.parent.mkdir(parents=True)
        loader.write_bytes(efi_image())
        (self.source / "setup.exe").write_bytes(b"fixture-only")
        sources = self.source / "sources"
        sources.mkdir()
        wim = b"MSWIM\0\0\0" + (208).to_bytes(4, "little") + bytes(196)
        for name in ("boot.wim", "install.wim"):
            (sources / name).write_bytes(wim)
        shutil.copytree(self.source, self.destination)
        self.manifest = module.media.capture_media_manifest(self.source)

    def test_complete_readback_keeps_boot_and_identity_unproven(self):
        result = module.verify_installer_readback(
            self.source, self.destination, self.manifest, "x64"
        )
        self.assertEqual(4, result["verified_files"])
        self.assertTrue(result["efi_loader"]["pe_header_checks_passed"])
        for flag in (
            "boot_proven",
            "disk_identity_verified",
            "partition_layout_verified",
            "bcd_verified",
            "secure_boot_trust_verified",
            "write_authorized",
        ):
            self.assertFalse(result[flag])

    def test_cli_outputs_file_only_receipt_and_cancellation(self):
        manifest = Path(self.temp.name) / "manifest.json"
        manifest.write_text(json.dumps(self.manifest))
        args = [
            "--source-root",
            str(self.source),
            "--readback-root",
            str(self.destination),
            "--manifest",
            str(manifest),
            "--architecture",
            "x64",
        ]
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(0, module.main(args))
        self.assertFalse(json.loads(output.getvalue())["boot_proven"])
        cancel = Path(self.temp.name) / "cancel"
        cancel.touch()
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(130, module.main(args + ["--cancel-file", str(cancel)]))
        self.assertEqual("cancelled", json.loads(output.getvalue())["status"])

    def test_changed_missing_or_extra_destination_bytes_rejected(self):
        for change in ("changed", "missing", "extra"):
            with self.subTest(change=change):
                shutil.rmtree(self.destination)
                shutil.copytree(self.source, self.destination)
                if change == "missing":
                    (self.destination / "setup.exe").unlink()
                else:
                    (
                        self.destination
                        / ("extra" if change == "extra" else "setup.exe")
                    ).write_bytes(b"bad")
                with self.assertRaises(RuntimeError):
                    module.verify_installer_readback(
                        self.source, self.destination, self.manifest, "x64"
                    )

    def test_same_or_nested_directory_rejected(self):
        for destination in (self.source, self.source / "nested"):
            destination.mkdir(exist_ok=True)
            with self.assertRaises(ValueError):
                module.verify_installer_readback(
                    self.source, destination, self.manifest, "x64"
                )

    def test_cancellation_prevents_success(self):
        with self.assertRaises(RuntimeError):
            module.verify_installer_readback(
                self.source, self.destination, self.manifest, "x64", lambda: True
            )

    def test_source_change_during_efi_inspection_rejected(self):
        original = module.inspect_efi_application

        def inspect(*args):
            result = original(*args)
            (self.source / "setup.exe").write_bytes(b"changed")
            return result

        with patch.object(module, "inspect_efi_application", side_effect=inspect):
            with self.assertRaises(RuntimeError):
                module.verify_installer_readback(
                    self.source, self.destination, self.manifest, "x64"
                )

    def test_all_supported_machine_headers(self):
        for architecture in module.EFI_TARGETS:
            with self.subTest(architecture=architecture):
                path = Path(self.temp.name) / (architecture + ".efi")
                path.write_bytes(efi_image(architecture))
                self.assertEqual(
                    architecture,
                    module.inspect_efi_application(path, architecture)["architecture"],
                )

    def test_matching_hash_does_not_accept_fake_efi_loader(self):
        for root in (self.source, self.destination):
            (root / "EFI/Boot/bootx64.efi").write_bytes(b"not an EFI application")
        manifest = module.media.capture_media_manifest(self.source)
        with self.assertRaisesRegex(ValueError, "header"):
            module.verify_installer_readback(
                self.source, self.destination, manifest, "x64"
            )

    def test_malformed_pe_and_wrong_architecture_rejected(self):
        path = Path(self.temp.name) / "bad.efi"
        corruptions = [
            (60, "<I", 0xFFFFFFFF),
            (132, "<H", 0xAA64),
            (134, "<H", 0),
            (148, "<H", 4),
            (150, "<H", 0x2002),
            (152, "<H", 0x10B),
            (220, "<H", 3),
            (168, "<I", 0),
            (412, "<I", 1024),
            (428, "<I", 0),
        ]
        for offset, fmt, value in corruptions:
            with self.subTest(offset=offset):
                data = efi_image()
                struct.pack_into(fmt, data, offset, value)
                path.write_bytes(data)
                with self.assertRaises(ValueError):
                    module.inspect_efi_application(path, "x64")


if __name__ == "__main__":
    unittest.main()
