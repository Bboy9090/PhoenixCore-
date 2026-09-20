#!/usr/bin/env python3
"""Locate a Windows physical disk by Phoenix Key stable hardware identity, read-only."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import capture_windows_drive_evidence as drive_evidence

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class StableIdentityLocatorError(RuntimeError):
    """Raised when stable-identity location cannot be proven safely."""


def normalize_candidates(
    raw_disks: list[dict[str, Any]], expected_stable_identity_sha256: str
) -> dict[str, Any]:
    expected = expected_stable_identity_sha256.strip().lower()
    if not SHA256_RE.fullmatch(expected):
        raise StableIdentityLocatorError(
            "Expected stable identity must be a 64-character SHA-256."
        )

    inspected = []
    matches = []
    for raw in raw_disks:
        number = int(raw.get("Number", -1))
        if number < 0:
            continue
        target = rf"\\.\PHYSICALDRIVE{number}"
        record = drive_evidence.normalize_disk_record(raw, target)
        summary = {
            "target": record["target"],
            "disk_number": record["disk_number"],
            "friendly_name": record["friendly_name"],
            "serial_number": record["serial_number"],
            "unique_id": record["unique_id"],
            "bus_type": record["bus_type"],
            "size_bytes": record["size_bytes"],
            "identity_sha256": record["identity_sha256"],
            "stable_identity_sha256": record["stable_identity_sha256"],
            "is_boot": record["is_boot"],
            "is_system": record["is_system"],
            "write_candidate": record["write_candidate"],
            "write_block_reasons": record["write_block_reasons"],
        }
        inspected.append(summary)
        if (
            isinstance(record["stable_identity_sha256"], str)
            and record["stable_identity_sha256"].lower() == expected
        ):
            matches.append(summary)

    classification = (
        "unique_match"
        if len(matches) == 1
        else "not_found"
        if not matches
        else "ambiguous_multiple_matches"
    )
    return {
        "schema": "phoenix_key.stable_target_locator.v1",
        "expected_stable_identity_sha256": expected,
        "classification": classification,
        "unique_match": len(matches) == 1,
        "ambiguous": len(matches) > 1,
        "match_count": len(matches),
        "match": matches[0] if len(matches) == 1 else None,
        "matches": matches,
        "inspected_disk_count": len(inspected),
        "inspected": inspected,
        "read_only": True,
        "system_mutations_performed": False,
    }


def query_all_windows_disks() -> list[dict[str, Any]]:
    if sys.platform != "win32":
        raise StableIdentityLocatorError("Live stable-identity location requires Windows.")

    script = r"""
$ErrorActionPreference = 'Stop'
$items = @()
foreach ($disk in @(Get-Disk)) {
  $partitions = @(
    Get-Partition -DiskNumber $disk.Number -ErrorAction SilentlyContinue |
      Select-Object PartitionNumber, DriveLetter, Offset, Size, Type, GptType, MbrType, IsBoot, IsSystem
  )
  $items += [pscustomobject]@{
    Number = [int]$disk.Number
    FriendlyName = [string]$disk.FriendlyName
    SerialNumber = [string]$disk.SerialNumber
    UniqueId = [string]$disk.UniqueId
    BusType = [string]$disk.BusType
    SizeBytes = [uint64]$disk.Size
    LogicalSectorSize = [uint32]$disk.LogicalSectorSize
    PhysicalSectorSize = [uint32]$disk.PhysicalSectorSize
    PartitionStyle = [string]$disk.PartitionStyle
    IsBoot = [bool]$disk.IsBoot
    IsSystem = [bool]$disk.IsSystem
    IsOffline = [bool]$disk.IsOffline
    IsReadOnly = [bool]$disk.IsReadOnly
    HealthStatus = [string]$disk.HealthStatus
    OperationalStatus = @($disk.OperationalStatus | ForEach-Object { [string]$_ })
    Partitions = $partitions
  }
}
$items | ConvertTo-Json -Depth 6 -Compress
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
        raise StableIdentityLocatorError(f"Windows disk enumeration failed: {message}")

    try:
        payload = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise StableIdentityLocatorError(
            "PowerShell returned malformed disk enumeration JSON."
        ) from exc

    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return payload
    raise StableIdentityLocatorError("PowerShell disk enumeration was not a list.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-stable-identity-sha256", required=True)
    parser.add_argument("--fixture-json", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.fixture_json:
        payload = json.loads(args.fixture_json.read_text(encoding="utf-8"))
        raw_disks = payload if isinstance(payload, list) else [payload]
    else:
        raw_disks = query_all_windows_disks()
    result = normalize_candidates(raw_disks, args.expected_stable_identity_sha256)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (StableIdentityLocatorError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"STABLE_TARGET_LOCATOR_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
