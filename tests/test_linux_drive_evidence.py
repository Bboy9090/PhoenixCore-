import importlib.util
from pathlib import Path

MODULE_PATH = (
    Path(__file__).parents[1]
    / "scripts"
    / "hardware"
    / "capture_linux_drive_evidence.py"
)
SPEC = importlib.util.spec_from_file_location(
    "capture_linux_drive_evidence", MODULE_PATH
)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)


def payload(
    *, rm=1, ro=0, tran="usb", serial="USB123", wwn=None, mounts=None, target="/dev/sdb"
):
    return {
        "blockdevices": [
            {
                "name": Path(target).name,
                "kname": Path(target).name,
                "path": target,
                "type": "disk",
                "size": 16 * 1024**3,
                "rm": rm,
                "ro": ro,
                "tran": tran,
                "serial": serial,
                "wwn": wwn,
                "model": "Sacrificial USB",
                "mountpoint": None,
                "mountpoints": [],
                "children": [
                    {
                        "name": Path(target).name + "1",
                        "type": "part",
                        "mountpoint": mounts[0] if mounts else None,
                        "mountpoints": mounts or [],
                    }
                ],
            }
        ]
    }


def test_accepts_unmounted_external_whole_disk_with_stable_identity():
    receipt = MOD.build_receipt(
        target="/dev/sdb",
        lsblk_payload=payload(),
        source_commit="a" * 40,
        evidence_source="fixture",
    )
    assert receipt["disk"]["write_candidate"] is True
    assert receipt["physical_write_attempted"] is False
    assert receipt["bytes_written"] == 0
    assert (
        receipt["next_required_action"]
        == "linux-writer-remains-locked-pending-separate-executor-qualification"
    )


def test_rejects_partition_target():
    try:
        MOD.parse_target("/dev/sdb1")
    except MOD.EvidenceError:
        pass
    else:
        raise AssertionError("partition path must be rejected")


def test_blocks_mounted_child_partition():
    receipt = MOD.build_receipt(
        target="/dev/sdb",
        lsblk_payload=payload(mounts=["/media/user/USB"]),
        source_commit="b" * 40,
        evidence_source="fixture",
    )
    assert receipt["disk"]["write_candidate"] is False
    assert (
        "target-or-child-partition-is-mounted" in receipt["disk"]["write_block_reasons"]
    )


def test_blocks_internal_disk_and_missing_identity():
    receipt = MOD.build_receipt(
        target="/dev/nvme0n1",
        lsblk_payload=payload(
            rm=0, tran="nvme", serial="", wwn=None, target="/dev/nvme0n1"
        ),
        source_commit="c" * 40,
        evidence_source="fixture",
    )
    reasons = receipt["disk"]["write_block_reasons"]
    assert "target-not-proven-external-removable" in reasons
    assert "stable-device-identity-missing" in reasons


def test_blocks_root_system_mount():
    receipt = MOD.build_receipt(
        target="/dev/sda",
        lsblk_payload=payload(mounts=["/"], target="/dev/sda"),
        source_commit="d" * 40,
        evidence_source="fixture",
    )
    reasons = receipt["disk"]["write_block_reasons"]
    assert "target-contains-system-mount" in reasons
