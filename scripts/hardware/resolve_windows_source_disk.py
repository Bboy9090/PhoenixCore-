#!/usr/bin/env python3
"""Resolve a Windows recovery source path to its backing physical disk, read-only."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

DRIVE_RE = re.compile(r"^([A-Za-z]):[\\/]")


class SourceDiskResolutionError(RuntimeError):
    """Raised when the source physical disk cannot be proven safely."""


def canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def source_drive_letter(path: str) -> str:
    match = DRIVE_RE.match(path.strip())
    if not match:
        raise SourceDiskResolutionError(
            "Source path must resolve to a local Windows drive letter before physical-disk proof can proceed."
        )
    return match.group(1).upper()


def normalize_source_disk_record(
    *,
    source_path: str,
    drive_letter: str,
    disk_number: int,
    partition_number: int | None,
    friendly_name: str | None = None,
    serial_number: str | None = None,
    unique_id: str | None = None,
    bus_type: str | None = None,
    size_bytes: int | None = None,
) -> dict[str, Any]:
    if disk_number < 0:
        raise SourceDiskResolutionError("Source disk number is invalid.")
    physical_target = rf"\\.\PHYSICALDRIVE{disk_number}"
    size = int(size_bytes or 0)
    serial = _clean_text(serial_number)
    unique = _clean_text(unique_id)
    identity_material = {
        "target": physical_target.upper(),
        "disk_number": disk_number,
        "friendly_name": _clean_text(friendly_name),
        "serial_number": serial,
        "unique_id": unique,
        "bus_type": (_clean_text(bus_type) or "UNKNOWN").upper(),
        "size_bytes": size,
    }
    stable_identity_available = size > 0 and bool(serial or unique)
    return {
        "schema": "phoenix_key.windows_source_disk.v2",
        "source_path": source_path,
        "drive_letter": drive_letter.upper(),
        "disk_number": disk_number,
        "partition_number": partition_number,
        "physical_target": physical_target,
        "friendly_name": identity_material["friendly_name"],
        "serial_number": serial,
        "unique_id": unique,
        "bus_type": identity_material["bus_type"],
        "size_bytes": size,
        "identity_sha256": (
            sha256_payload(identity_material) if stable_identity_available else None
        ),
        "stable_identity_available": stable_identity_available,
        "resolved": True,
        "read_only": True,
    }


def query_source_disk(source_path: str) -> dict[str, Any]:
    if sys.platform != "win32":
        raise SourceDiskResolutionError("Live source-disk resolution requires Windows.")

    path = Path(source_path)
    if not path.exists():
        raise SourceDiskResolutionError("Source path does not exist.")

    drive_letter = source_drive_letter(str(path.resolve()))
    script = f"""
$ErrorActionPreference = 'Stop'
$partition = Get-Partition -DriveLetter '{drive_letter}'
$disk = Get-Disk -Number $partition.DiskNumber
[pscustomobject]@{{
  DiskNumber = [int]$partition.DiskNumber
  PartitionNumber = [int]$partition.PartitionNumber
  FriendlyName = [string]$disk.FriendlyName
  SerialNumber = [string]$disk.SerialNumber
  UniqueId = [string]$disk.UniqueId
  BusType = [string]$disk.BusType
  SizeBytes = [uint64]$disk.Size
}} | ConvertTo-Json -Compress
"""
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise SourceDiskResolutionError(f"Source disk resolution failed: {message}")
    try:
        raw = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise SourceDiskResolutionError(
            "PowerShell returned malformed source-disk JSON."
        ) from exc

    return normalize_source_disk_record(
        source_path=str(path.resolve()),
        drive_letter=drive_letter,
        disk_number=int(raw.get("DiskNumber", -1)),
        partition_number=(
            int(raw["PartitionNumber"])
            if raw.get("PartitionNumber") is not None
            else None
        ),
        friendly_name=raw.get("FriendlyName"),
        serial_number=raw.get("SerialNumber"),
        unique_id=raw.get("UniqueId"),
        bus_type=raw.get("BusType"),
        size_bytes=int(raw.get("SizeBytes") or 0),
    )


def compare_source_and_target(
    source_record: dict[str, Any], target: str
) -> dict[str, Any]:
    source_target = str(source_record.get("physical_target") or "")
    distinct = source_target.upper() != target.strip().upper()
    return {
        "schema": "phoenix_key.source_target_collision_check.v1",
        "source_physical_target": source_target,
        "target_physical_target": target.strip().upper(),
        "source_target_distinct": distinct,
        "blocked": not distinct,
        "block_reason": None if distinct else "source-and-target-same-physical-device",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--target")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = query_source_disk(args.source)
    payload: dict[str, Any] = {"source": source}
    if args.target:
        payload["collision_check"] = compare_source_and_target(source, args.target)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SourceDiskResolutionError, OSError, ValueError) as exc:
        print(f"SOURCE_DISK_RESOLUTION_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
