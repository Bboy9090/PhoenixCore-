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
    stable_identity_material = {
        "serial_number": serial,
        "unique_id": unique,
        "bus_type": identity_material["bus_type"],
        "size_bytes": size,
    }
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
        "stable_identity_sha256": (
            sha256_payload(stable_identity_material)
            if stable_identity_available
            else None
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
    source_record: dict[str, Any],
    target: str,
    target_stable_identity_sha256: str | None = None,
) -> dict[str, Any]:
    source_target = str(source_record.get("physical_target") or "")
    target_normalized = target.strip().upper()
    path_distinct = source_target.upper() != target_normalized

    source_stable = str(source_record.get("stable_identity_sha256") or "").lower()
    target_stable = str(target_stable_identity_sha256 or "").strip().lower()
    stable_proof_requested = bool(target_stable)
    source_stable_valid = bool(re.fullmatch(r"[0-9a-f]{64}", source_stable))
    target_stable_valid = bool(re.fullmatch(r"[0-9a-f]{64}", target_stable))
    stable_identity_proven = (
        stable_proof_requested and source_stable_valid and target_stable_valid
    )
    stable_identity_distinct = (
        source_stable != target_stable if stable_identity_proven else None
    )

    if stable_proof_requested:
        distinct = path_distinct and stable_identity_distinct is True
    else:
        distinct = path_distinct

    if not path_distinct:
        block_reason = "source-and-target-same-physical-device"
    elif stable_proof_requested and not stable_identity_proven:
        block_reason = "stable-source-target-identity-not-proven"
    elif stable_identity_distinct is False:
        block_reason = "source-and-target-same-physical-device"
    else:
        block_reason = None

    return {
        "schema": "phoenix_key.source_target_collision_check.v2",
        "source_physical_target": source_target,
        "target_physical_target": target_normalized,
        "source_stable_identity_sha256": source_stable or None,
        "target_stable_identity_sha256": target_stable or None,
        "path_distinct": path_distinct,
        "stable_identity_proven": stable_identity_proven,
        "stable_identity_distinct": stable_identity_distinct,
        "source_target_distinct": distinct,
        "blocked": not distinct,
        "block_reason": block_reason,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--target")
    parser.add_argument("--target-stable-identity-sha256")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = query_source_disk(args.source)
    payload: dict[str, Any] = {"source": source}
    if args.target:
        payload["collision_check"] = compare_source_and_target(
            source,
            args.target,
            args.target_stable_identity_sha256,
        )
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (SourceDiskResolutionError, OSError, ValueError) as exc:
        print(f"SOURCE_DISK_RESOLUTION_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
