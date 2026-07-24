#!/usr/bin/env python3
"""Capture immutable, read-only evidence for one Windows physical drive.

This tool performs no writes, formatting, partition changes, volume dismounts,
or firmware operations. An optional exclusive read-handle probe opens and closes
an exact ``\\.\PHYSICALDRIVE<n>`` path with zero bytes read and zero bytes written.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "bws.physical-drive-evidence/v1"
RAW_DEVICE_PATTERN = re.compile(r"^\\\\\.\\PHYSICALDRIVE([0-9]+)$", re.IGNORECASE)
EXTERNAL_BUS_TYPES = {"USB", "SD", "MMC"}


class EvidenceError(RuntimeError):
    """Raised when trustworthy evidence cannot be collected."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def parse_raw_target(target: str) -> int:
    match = RAW_DEVICE_PATTERN.fullmatch(target.strip())
    if not match:
        raise EvidenceError(
            r"Target must be an exact Windows raw path such as \\.\PHYSICALDRIVE1."
        )
    return int(match.group(1))


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def normalize_disk_record(raw: dict[str, Any], target: str) -> dict[str, Any]:
    expected_number = parse_raw_target(target)
    number = int(raw.get("Number", -1))
    if number != expected_number:
        raise EvidenceError(
            f"PowerShell returned disk {number}, expected disk {expected_number}."
        )

    size_bytes = int(raw.get("SizeBytes") or raw.get("Size") or 0)
    if size_bytes <= 0:
        raise EvidenceError("Physical-drive size is missing or invalid.")

    operational_status = raw.get("OperationalStatus") or []
    if isinstance(operational_status, str):
        operational_status = [operational_status]

    partitions = raw.get("Partitions") or []
    if isinstance(partitions, dict):
        partitions = [partitions]

    normalized_partitions = []
    for partition in partitions:
        normalized_partitions.append(
            {
                "partition_number": int(partition.get("PartitionNumber") or 0),
                "drive_letter": _clean_text(partition.get("DriveLetter")),
                "offset_bytes": int(partition.get("Offset") or 0),
                "size_bytes": int(partition.get("Size") or 0),
                "type": _clean_text(partition.get("Type")),
                "is_boot": _coerce_bool(partition.get("IsBoot")),
                "is_system": _coerce_bool(partition.get("IsSystem")),
            }
        )

    record = {
        "target": target.upper(),
        "disk_number": number,
        "friendly_name": _clean_text(raw.get("FriendlyName")),
        "serial_number": _clean_text(raw.get("SerialNumber")),
        "unique_id": _clean_text(raw.get("UniqueId")),
        "bus_type": (_clean_text(raw.get("BusType")) or "UNKNOWN").upper(),
        "size_bytes": size_bytes,
        "partition_style": _clean_text(raw.get("PartitionStyle")),
        "is_boot": _coerce_bool(raw.get("IsBoot")),
        "is_system": _coerce_bool(raw.get("IsSystem")),
        "is_offline": _coerce_bool(raw.get("IsOffline")),
        "is_read_only": _coerce_bool(raw.get("IsReadOnly")),
        "health_status": _clean_text(raw.get("HealthStatus")),
        "operational_status": [str(item) for item in operational_status],
        "partitions": normalized_partitions,
    }

    identity_material = {
        "target": record["target"],
        "disk_number": record["disk_number"],
        "friendly_name": record["friendly_name"],
        "serial_number": record["serial_number"],
        "unique_id": record["unique_id"],
        "bus_type": record["bus_type"],
        "size_bytes": record["size_bytes"],
    }
    record["identity_sha256"] = sha256_payload(identity_material)

    block_reasons = []
    if record["is_boot"]:
        block_reasons.append("target-is-boot-disk")
    if record["is_system"]:
        block_reasons.append("target-is-system-disk")
    if record["bus_type"] not in EXTERNAL_BUS_TYPES:
        block_reasons.append("target-not-proven-external-removable")
    if not (record["serial_number"] or record["unique_id"]):
        block_reasons.append("stable-device-identity-missing")

    record["write_candidate"] = not block_reasons
    record["write_block_reasons"] = block_reasons
    return record


def query_windows_disk(disk_number: int) -> dict[str, Any]:
    if sys.platform != "win32":
        raise EvidenceError("Live physical-drive collection requires Windows.")

    script = f"""
$ErrorActionPreference = 'Stop'
$disk = Get-Disk -Number {disk_number}
$partitions = @(
  Get-Partition -DiskNumber {disk_number} -ErrorAction SilentlyContinue |
    Select-Object PartitionNumber, DriveLetter, Offset, Size, Type, IsBoot, IsSystem
)
[pscustomobject]@{{
  Number = [int]$disk.Number
  FriendlyName = [string]$disk.FriendlyName
  SerialNumber = [string]$disk.SerialNumber
  UniqueId = [string]$disk.UniqueId
  BusType = [string]$disk.BusType
  SizeBytes = [uint64]$disk.Size
  PartitionStyle = [string]$disk.PartitionStyle
  IsBoot = [bool]$disk.IsBoot
  IsSystem = [bool]$disk.IsSystem
  IsOffline = [bool]$disk.IsOffline
  IsReadOnly = [bool]$disk.IsReadOnly
  HealthStatus = [string]$disk.HealthStatus
  OperationalStatus = @($disk.OperationalStatus | ForEach-Object {{ [string]$_ }})
  Partitions = $partitions
}} | ConvertTo-Json -Depth 6 -Compress
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
        raise EvidenceError(f"Get-Disk evidence collection failed: {message}")
    try:
        return json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise EvidenceError(
            "PowerShell returned malformed disk evidence JSON."
        ) from exc


def probe_exclusive_read_handle(target: str) -> dict[str, Any]:
    """Open and close an exact raw drive with read-only access and no sharing."""

    parse_raw_target(target)
    if sys.platform != "win32":
        return {
            "requested": True,
            "status": "not-supported-on-current-platform",
            "raw_handle_opened": False,
            "bytes_read": 0,
            "bytes_written": 0,
            "winerror": None,
        }

    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE

    generic_read = 0x80000000
    open_existing = 3
    file_attribute_normal = 0x80
    invalid_handle = wintypes.HANDLE(-1).value

    handle = create_file(
        target,
        generic_read,
        0,
        None,
        open_existing,
        file_attribute_normal,
        None,
    )
    if handle == invalid_handle:
        error_code = ctypes.get_last_error()
        return {
            "requested": True,
            "status": "blocked-or-busy",
            "raw_handle_opened": False,
            "bytes_read": 0,
            "bytes_written": 0,
            "winerror": error_code,
        }

    try:
        return {
            "requested": True,
            "status": "opened-and-closed",
            "raw_handle_opened": True,
            "bytes_read": 0,
            "bytes_written": 0,
            "winerror": None,
        }
    finally:
        kernel32.CloseHandle(handle)


def build_receipt(
    *,
    target: str,
    raw_disk: dict[str, Any],
    evidence_source: str,
    source_commit: str,
    exclusive_probe: dict[str, Any] | None = None,
    captured_at: str | None = None,
) -> dict[str, Any]:
    disk = normalize_disk_record(raw_disk, target)
    probe = exclusive_probe or {
        "requested": False,
        "status": "not-run",
        "raw_handle_opened": False,
        "bytes_read": 0,
        "bytes_written": 0,
        "winerror": None,
    }
    if probe.get("bytes_written") != 0:
        raise EvidenceError("Read-only evidence probe reported nonzero bytes written.")

    receipt = {
        "schema_version": SCHEMA_VERSION,
        "captured_at": captured_at or utc_now_iso(),
        "evidence_source": evidence_source,
        "source_commit": source_commit,
        "platform": "windows" if evidence_source == "live" else "fixture",
        "operation": "read-only-physical-drive-evidence",
        "disk": disk,
        "exclusive_read_probe": probe,
        "bytes_written": 0,
        "physical_write_attempted": False,
        "hardware_observed": evidence_source == "live",
        "hardware_validated": False,
        "classification": (
            "hardware-evidence-captured"
            if evidence_source == "live"
            else "fixture-validated"
        ),
        "next_required_action": (
            "explicit-sacrificial-drive-authorization"
            if disk["write_candidate"]
            else "resolve-write-block-reasons"
        ),
    }
    receipt["receipt_sha256"] = sha256_payload(receipt)
    return receipt


def write_receipt_atomic(receipt: dict[str, Any], output_path: Path) -> None:
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=output_path.parent,
        delete=False,
    ) as temporary:
        temporary.write(data)
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--source-commit", default=os.environ.get("GITHUB_SHA", "unknown")
    )
    parser.add_argument("--fixture-json", type=Path)
    parser.add_argument("--probe-exclusive-read", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    disk_number = parse_raw_target(args.target)

    if args.fixture_json:
        raw_disk = json.loads(args.fixture_json.read_text(encoding="utf-8"))
        evidence_source = "fixture"
    else:
        raw_disk = query_windows_disk(disk_number)
        evidence_source = "live"

    probe = None
    if args.probe_exclusive_read:
        probe = probe_exclusive_read_handle(args.target)

    receipt = build_receipt(
        target=args.target,
        raw_disk=raw_disk,
        evidence_source=evidence_source,
        source_commit=args.source_commit,
        exclusive_probe=probe,
    )
    write_receipt_atomic(receipt, args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EvidenceError, OSError, json.JSONDecodeError) as exc:
        print(f"DRIVE_EVIDENCE_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
