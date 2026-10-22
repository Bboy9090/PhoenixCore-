"""Read-only before/after native binding for GPT/FAT32 installer readback.

This does not establish a continuous volume lease or prove firmware boot.
"""

from __future__ import annotations

import importlib.util
import argparse
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).with_name(filename)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


readback = _load("_bound_readback", "verify_windows_installer_readback.py")
drives = _load("_bound_drives", "capture_windows_drive_evidence.py")
sources = _load("_bound_sources", "resolve_windows_source_disk.py")
ESP = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"
MSR = "E3C9E316-0B5C-4DB8-817D-F92DF00215AE"


def _volume(letter, cancelled=lambda: False):
    if not re.fullmatch("[A-Z]", letter):
        raise ValueError("Invalid volume letter")
    script = f"""
$ErrorActionPreference = 'Stop'
$v = Get-Volume -DriveLetter '{letter}' -ErrorAction Stop
if (@($v).Count -ne 1) {{ throw 'Ambiguous volume' }}
[pscustomobject]@{{ FileSystem = [string]$v.FileSystem; UniqueId = [string]$v.UniqueId;
HealthStatus = [string]$v.HealthStatus; Size = [uint64]$v.Size }} | ConvertTo-Json -Compress
"""
    try:
        result = sources.run_cancellable(
            [
                sources.system_tool_path("powershell"),
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
            ],
            timeout_seconds=30,
            cancelled=cancelled,
        )
    except sources.SystemToolCancelled as exc:
        raise ValueError("Volume evidence query cancelled") from exc
    except sources.SystemToolTimeout as exc:
        raise RuntimeError("Volume evidence query exceeded 30 seconds") from exc
    if result.returncode:
        raise RuntimeError(
            "Volume evidence query failed: " + (result.stderr or result.stdout).strip()
        )
    return json.loads(result.stdout)


def bind_target(
    root, target, stable_sha256, partition_number, cancelled=lambda: False
):
    """Fresh native queries only; supplied facts cannot substitute for queries."""
    if sys.platform != "win32":
        raise RuntimeError("Native target binding requires Windows")
    if not re.fullmatch(r"[A-Za-z]:[\\/]", str(root)):
        raise ValueError("Readback must use an exact local volume root")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", stable_sha256):
        raise ValueError("Reviewed stable target identity is required")
    if type(partition_number) is not int or partition_number <= 0:
        raise ValueError("Explicit positive partition number required")
    number = drives.parse_raw_target(target)
    canonical = rf"\\.\PHYSICALDRIVE{number}"
    if target.upper() != canonical:
        raise ValueError("Canonical physical target required")
    mount = sources.query_source_disk(str(root), cancelled)
    if (
        mount.get("physical_target", "").upper() != canonical
        or mount.get("partition_number") != partition_number
        or mount.get("stable_identity_sha256") != stable_sha256.lower()
    ):
        raise ValueError("Readback volume is not bound to the reviewed target")
    raw = drives.query_windows_disk(number, cancelled)
    disk = drives.normalize_disk_record(raw, canonical)
    if (
        disk["write_block_reasons"]
        or raw.get("HealthStatus") != "Healthy"
        or disk.get("stable_identity_sha256") != stable_sha256.lower()
        or not disk.get("serial_number")
        or not disk.get("unique_id")
        or raw.get("PartitionStyle") != "GPT"
    ):
        raise ValueError("Target identity, eligibility, health or GPT layout mismatch")
    parts = raw.get("Partitions")
    if isinstance(parts, dict):
        parts = [parts]
    if not isinstance(parts, list) or not 1 <= len(parts) <= 2:
        raise ValueError("Installer requires one ESP and at most one MSR")
    sector = raw.get("LogicalSectorSize")
    if type(sector) is not int or sector not in (512, 4096):
        raise ValueError("Unsupported or unknown logical sector size")
    selected = None
    ranges, numbers, kinds = [], set(), []
    for part in parts:
        index, offset, size = (
            part.get(k) for k in ("PartitionNumber", "Offset", "Size")
        )
        if (
            type(index) is not int
            or index <= 0
            or index in numbers
            or type(offset) is not int
            or type(size) is not int
            or offset < 1024 * 1024
            or size <= 0
            or offset % sector
            or size % sector
            or offset + size > disk["size_bytes"] - sector * 33
        ):
            raise ValueError("Partition geometry is invalid")
        numbers.add(index)
        ranges.append((offset, offset + size))
        kind = str(part.get("GptType", "")).strip("{}").upper()
        kinds.append(kind)
        if kind not in (ESP, MSR) or (kind == MSR and size != 16 * 1024 * 1024):
            raise ValueError("Unexpected installer partition type or MSR size")
        if index == partition_number:
            selected = part
    ranges.sort()
    if any(a[1] > b[0] for a, b in zip(ranges, ranges[1:])) or kinds.count(ESP) != 1:
        raise ValueError("Overlapping partitions or ambiguous ESP")
    letter = PureWindowsPath(str(root)).drive[0].upper()
    if (
        selected is None
        or str(selected.get("GptType", "")).strip("{}").upper() != ESP
        or selected.get("DriveLetter") != letter
    ):
        raise ValueError("Mounted partition is not the selected ESP")
    volume = _volume(letter, cancelled)
    if (
        volume.get("FileSystem") != "FAT32"
        or volume.get("HealthStatus") != "Healthy"
        or not isinstance(volume.get("UniqueId"), str)
        or not volume["UniqueId"].strip()
        or type(volume.get("Size")) is not int
        or not 0 < volume["Size"] <= selected["Size"]
    ):
        raise ValueError("Healthy FAT32 volume identity is not proven")
    return {
        "target": canonical,
        "stable_identity_sha256": stable_sha256.lower(),
        "partition_number": partition_number,
        "partitions": parts,
        "volume": volume,
        "logical_sector_size": sector,
    }


def verify_target(
    source,
    root,
    manifest,
    architecture,
    target,
    stable_sha256,
    partition_number,
    cancelled=lambda: False,
):
    if cancelled():
        raise ValueError("Cancelled before target binding")
    before = bind_target(root, target, stable_sha256, partition_number, cancelled)
    source_disk = sources.query_source_disk(str(source), cancelled)
    source_stable = source_disk.get("stable_identity_sha256")
    source_target = source_disk.get("physical_target")
    if (
        not isinstance(source_stable, str)
        or not re.fullmatch("[0-9a-f]{64}", source_stable)
        or source_stable == stable_sha256.lower()
        or not isinstance(source_target, str)
        or not drives.RAW_DEVICE_PATTERN.fullmatch(source_target)
        or source_target.upper()
        != rf"\\.\PHYSICALDRIVE{drives.parse_raw_target(source_target)}"
        or source_target.upper() == before["target"]
    ):
        raise ValueError("Source disk identity is unknown or collides with target")
    result = readback.verify_installer_readback(
        Path(source), Path(root), manifest, architecture, cancelled
    )
    after = bind_target(root, target, stable_sha256, partition_number, cancelled)
    if (
        before != after
        or sources.query_source_disk(str(source), cancelled) != source_disk
    ):
        raise ValueError("Disk, partition or source binding changed during readback")
    if cancelled():
        raise ValueError("Cancelled before bound readback receipt")
    return {
        **result,
        "schema": "arcwyre.windows_installer_bound_readback.v1",
        "native_binding": after,
        "disk_identity_observations_match": True,
        "gpt_fat32_layout_observations_match": True,
        "continuous_volume_lease_proven": False,
        "physical_media_certified": False,
        "boot_proven": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--readback-root", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--architecture", choices=tuple(readback.EFI_TARGETS), required=True
    )
    parser.add_argument("--target", required=True)
    parser.add_argument("--stable-sha256", required=True)
    parser.add_argument("--partition", type=int, required=True)
    parser.add_argument("--cancel-file", type=Path)
    args = parser.parse_args(argv)
    cancelled = lambda: args.cancel_file is not None and os.path.lexists(
        args.cancel_file
    )
    try:
        with args.manifest.open(encoding="utf-8") as stream:
            manifest = json.load(stream)
        if not isinstance(manifest, dict):
            raise ValueError("Manifest must be a JSON object")
        result = verify_target(
            args.source_root,
            args.readback_root,
            manifest,
            args.architecture,
            args.target,
            args.stable_sha256,
            args.partition,
            cancelled,
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(
            json.dumps(
                {
                    "schema": "arcwyre.windows_installer_bound_readback.v1",
                    "status": "cancelled" if cancelled() else "failed",
                    "error": str(exc),
                    "physical_media_certified": False,
                    "boot_proven": False,
                    "system_mutations_performed": False,
                },
                sort_keys=True,
            )
        )
        return 130 if cancelled() else 2


if __name__ == "__main__":
    raise SystemExit(main())
