"""Mocked native binding tests; these do not certify real Windows disks."""

import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "target_readback",
    Path(__file__).resolve().parents[1]
    / "scripts/hardware/verify_windows_installer_target.py",
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class TargetReadbackTests(unittest.TestCase):
    def setUp(self):
        self.target = r"\\.\PHYSICALDRIVE2"
        self.raw = {
            "Number": 2,
            "FriendlyName": "Fixture USB",
            "SerialNumber": "serial",
            "UniqueId": "unique",
            "BusType": "USB",
            "SizeBytes": 2 * 1024**3,
            "LogicalSectorSize": 512,
            "PhysicalSectorSize": 512,
            "PartitionStyle": "GPT",
            "IsBoot": False,
            "IsSystem": False,
            "IsOffline": False,
            "IsReadOnly": False,
            "HealthStatus": "Healthy",
            "OperationalStatus": ["Online"],
            "Partitions": [
                {
                    "PartitionNumber": 1,
                    "DriveLetter": "G",
                    "Offset": 1024**2,
                    "Size": 512 * 1024**2,
                    "GptType": module.ESP,
                    "IsBoot": False,
                    "IsSystem": False,
                }
            ],
        }
        self.sha = module.drives.normalize_disk_record(self.raw, self.target)[
            "stable_identity_sha256"
        ]
        self.mount = {
            "physical_target": self.target,
            "partition_number": 1,
            "stable_identity_sha256": self.sha,
        }
        self.volume = {
            "FileSystem": "FAT32",
            "UniqueId": "volume-guid",
            "HealthStatus": "Healthy",
            "Size": 500 * 1024**2,
        }
        self.source = {
            "stable_identity_sha256": "a" * 64,
            "physical_target": r"\\.\PHYSICALDRIVE0",
        }
        self.enterContext(patch.object(module.sys, "platform", "win32"))
        self.disk_query = self.enterContext(
            patch.object(
                module.drives,
                "query_windows_disk",
                side_effect=lambda n, *_: copy.deepcopy(self.raw),
            )
        )
        self.enterContext(
            patch.object(
                module.sources,
                "query_source_disk",
                side_effect=lambda p, *_: copy.deepcopy(
                    self.mount if p == "G:\\" else self.source
                ),
            )
        )
        self.enterContext(
            patch.object(
                module,
                "_volume",
                side_effect=lambda letter, *_: copy.deepcopy(self.volume),
            )
        )

    def bind(self):
        return module.bind_target("G:\\", self.target, self.sha, 1)

    def test_fresh_binding_matches_expected_disk_and_esp(self):
        self.assertEqual(self.sha, self.bind()["stable_identity_sha256"])
        self.assertEqual(2, self.disk_query.call_args.args[0])
        self.assertTrue(callable(self.disk_query.call_args.args[1]))

    def test_unsafe_or_unknown_disk_facts_rejected(self):
        for field, value in (
            ("IsSystem", True),
            ("IsBoot", "false"),
            ("BusType", "SATA"),
            ("HealthStatus", "Unknown"),
            ("PartitionStyle", "MBR"),
            ("SerialNumber", "changed"),
            ("LogicalSectorSize", True),
        ):
            with self.subTest(field=field):
                old = self.raw[field]
                self.raw[field] = value
                with self.assertRaises((ValueError, RuntimeError)):
                    self.bind()
                self.raw[field] = old

    def test_wrong_mount_or_volume_rejected(self):
        for field, value in (
            ("physical_target", r"\\.\PHYSICALDRIVE3"),
            ("partition_number", 2),
            ("stable_identity_sha256", "b" * 64),
        ):
            old = self.mount[field]
            self.mount[field] = value
            with self.assertRaises(ValueError):
                self.bind()
            self.mount[field] = old
        self.volume["FileSystem"] = "NTFS"
        with self.assertRaises(ValueError):
            self.bind()

    def test_geometry_and_partition_guid_fail_closed(self):
        part = self.raw["Partitions"][0]
        for field, value in (
            ("Offset", 1),
            ("Size", self.raw["SizeBytes"]),
            ("GptType", "unknown"),
            ("DriveLetter", "H"),
            ("IsSystem", "false"),
        ):
            with self.subTest(field=field):
                old = part[field]
                part[field] = value
                with self.assertRaises((ValueError, RuntimeError)):
                    self.bind()
                part[field] = old

    def test_overlapping_or_extra_partition_rejected(self):
        extra = copy.deepcopy(self.raw["Partitions"][0])
        extra.update(PartitionNumber=2, GptType=module.MSR, Size=16 * 1024**2)
        self.raw["Partitions"].append(extra)
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            self.bind()

    def test_nonoverlapping_standard_msr_is_accepted(self):
        self.raw["Partitions"][0]["Offset"] = 32 * 1024**2
        self.raw["Partitions"].append(
            {
                "PartitionNumber": 2,
                "Offset": 1024**2,
                "Size": 16 * 1024**2,
                "GptType": module.MSR,
                "IsBoot": False,
                "IsSystem": False,
            }
        )
        self.assertEqual(2, len(self.bind()["partitions"]))

    def test_valid_observations_do_not_certify_physical_media_or_boot(self):
        with patch.object(
            module.readback,
            "verify_installer_readback",
            return_value={"boot_proven": False},
        ):
            result = module.verify_target(
                Path("source"), "G:\\", {}, "x64", self.target, self.sha, 1
            )
        self.assertTrue(result["disk_identity_observations_match"])
        self.assertFalse(result["continuous_volume_lease_proven"])
        self.assertFalse(result["physical_media_certified"])
        self.assertFalse(result["boot_proven"])

    def test_volume_swap_after_file_readback_cannot_succeed(self):
        def read(*args):
            self.volume["UniqueId"] = "replacement"
            return {}

        with patch.object(
            module.readback, "verify_installer_readback", side_effect=read
        ):
            with self.assertRaisesRegex(ValueError, "binding changed"):
                module.verify_target(
                    Path("source"), "G:\\", {}, "x64", self.target, self.sha, 1
                )

    def test_source_collision_or_cancel_prevents_file_readback(self):
        with patch.object(module.readback, "verify_installer_readback") as read:
            self.source["stable_identity_sha256"] = self.sha
            with self.assertRaisesRegex(ValueError, "collides"):
                module.verify_target(
                    Path("source"), "G:\\", {}, "x64", self.target, self.sha, 1
                )
            read.assert_not_called()
            self.disk_query.reset_mock()
            with self.assertRaisesRegex(ValueError, "Cancelled"):
                module.verify_target(
                    Path("source"),
                    "G:\\",
                    {},
                    "x64",
                    self.target,
                    self.sha,
                    1,
                    lambda: True,
                )
            self.disk_query.assert_not_called()

    def test_source_disk_swap_cannot_publish_success(self):
        def read(*args):
            self.source["stable_identity_sha256"] = "b" * 64
            return {}

        with patch.object(
            module.readback, "verify_installer_readback", side_effect=read
        ):
            with self.assertRaisesRegex(ValueError, "binding changed"):
                module.verify_target(
                    Path("source"), "G:\\", {}, "x64", self.target, self.sha, 1
                )

    def test_source_physical_target_required_and_cannot_collide_with_different_hash(
        self,
    ):
        for target in (None, self.target, "invalid"):
            with self.subTest(target=target):
                self.source["physical_target"] = target
                with patch.object(module.readback, "verify_installer_readback") as read:
                    with self.assertRaisesRegex(ValueError, "collides"):
                        module.verify_target(
                            Path("source"), "G:\\", {}, "x64", self.target, self.sha, 1
                        )
                    read.assert_not_called()


if __name__ == "__main__":
    unittest.main()
