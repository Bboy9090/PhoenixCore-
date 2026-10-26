import importlib.util
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location(
    "installer_provisioning",
    Path(__file__).resolve().parents[1]
    / "scripts/hardware/provision_windows_installer_disk.py",
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class InstallerProvisioningTests(unittest.TestCase):
    def setUp(self):
        self.plan = {
            "schema": "arcwyre.windows_install_target_plan.v1",
            "eligible_for_preparation": True,
            "block_reasons": [],
            "write_authorized": False,
            "binding": {
                "target": r"\\.\PHYSICALDRIVE7",
                "target_snapshot_identity_sha256": "a" * 64,
                "target_stable_identity_sha256": "b" * 64,
                "source_manifest_sha256": "c" * 64,
                "target_size_bytes": 64 * 1024**3,
                "required_bytes": 10 * 1024**3,
            },
        }
        encoded = json.dumps(
            self.plan["binding"], sort_keys=True, separators=(",", ":")
        ).encode()
        self.plan["plan_sha256"] = hashlib.sha256(encoded).hexdigest()

    def test_execution_requires_all_destructive_gates(self):
        authorization = module.expected_authorization(self.plan)
        size = module.validate_execution(
            self.plan,
            authorization,
            execute=True,
            admin=True,
            environment={module.UNLOCK_ENV: module.UNLOCK_VALUE},
        )
        self.assertEqual(module.FAT32_MAX_PARTITION_BYTES, size)
        for field, value in (("execute", False), ("admin", False)):
            args = {"execute": True, "admin": True}
            args[field] = value
            with self.assertRaises(module.ProvisioningError):
                module.validate_execution(
                    self.plan,
                    authorization,
                    environment={module.UNLOCK_ENV: module.UNLOCK_VALUE},
                    **args,
                )
        with self.assertRaises(module.ProvisioningError):
            module.validate_execution(
                self.plan,
                "wrong",
                execute=True,
                admin=True,
                environment={module.UNLOCK_ENV: module.UNLOCK_VALUE},
            )
        tampered = json.loads(json.dumps(self.plan))
        tampered["binding"]["target_size_bytes"] += 1
        with self.assertRaisesRegex(module.ProvisioningError, "integrity"):
            module.validate_execution(
                tampered,
                module.expected_authorization(tampered),
                execute=True,
                admin=True,
                environment={module.UNLOCK_ENV: module.UNLOCK_VALUE},
            )

    def test_existing_volumes_are_locked_and_dismounted_in_order(self):
        events = []

        class Lease:
            def __init__(self, volume, cancelled):
                self.volume = volume

            def __enter__(self):
                events.append(("lock", self.volume))
                return self

            def dismount(self):
                events.append(("dismount", self.volume))

            def __exit__(self, *_):
                events.append(("unlock", self.volume))

        result = module.lock_and_dismount_existing(
            ["E", "F"], lambda: False, Lease
        )
        self.assertEqual(["E", "F"], result)
        self.assertEqual(
            [
                ("lock", "E:"),
                ("lock", "F:"),
                ("dismount", "E:"),
                ("dismount", "F:"),
                ("unlock", "F:"),
                ("unlock", "E:"),
            ],
            events,
        )

    def test_layout_contract_rejects_native_drift(self):
        raw = {
            "Number": 7,
            "SerialNumber": "serial",
            "UniqueId": "unique",
            "BusType": "USB",
            "SizeBytes": 64 * 1024**3,
        }
        good = {
            "DiskNumber": 7,
            "PartitionNumber": 1,
            "DriveLetter": "G",
            "Offset": module.ALIGNMENT,
            "Size": module.FAT32_MAX_PARTITION_BYTES,
            "GptType": module.ESP_GUID,
            "FileSystem": "FAT32",
            "Label": "ARCWYRE",
        }
        completed = subprocess.CompletedProcess([], 0, json.dumps(good), "")
        with patch.object(
            module.sources, "system_tool_path", return_value="powershell"
        ), patch.object(module.sources, "run_cancellable", return_value=completed):
            self.assertEqual(
                good,
                module.provision_layout(
                    self.plan,
                    raw,
                    module.FAT32_MAX_PARTITION_BYTES,
                    lambda: False,
                ),
            )
            bad = dict(good, Offset=2 * module.ALIGNMENT)
            completed.stdout = json.dumps(bad)
            with self.assertRaises(module.ProvisioningError):
                module.provision_layout(
                    self.plan,
                    raw,
                    module.FAT32_MAX_PARTITION_BYTES,
                    lambda: False,
                )

    def test_file_copy_is_manifest_bound_and_read_back(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source, destination = root / "source", root / "target"
            loader = source / "EFI/Boot/bootx64.efi"
            loader.parent.mkdir(parents=True)
            loader.write_bytes(b"efi")
            sources = source / "sources"
            sources.mkdir()
            wim = b"MSWIM\0\0\0" + (208).to_bytes(4, "little") + bytes(196)
            (sources / "boot.wim").write_bytes(wim)
            (sources / "install.wim").write_bytes(wim)
            (source / "setup.exe").write_bytes(b"setup")
            destination.mkdir()
            manifest = module.media.capture_media_manifest(source)
            with patch.object(
                module.media,
                "plan_media",
                return_value={"ready_for_fat32_copy_now": True},
            ):
                result = module.copy_and_verify(
                    source, destination, manifest, lambda: False
                )
            self.assertEqual(manifest, result)


if __name__ == "__main__":
    unittest.main()
