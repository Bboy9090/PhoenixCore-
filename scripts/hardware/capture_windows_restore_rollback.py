#!/usr/bin/env python3
r"""Capture read-only GPT rollback artifacts for one Windows physical drive.

The restore target is opened read-only. This tool writes only rollback artifacts
to the caller-provided output directory. It does not format, repartition,
dismount, mount, or write to the target disk.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import os
import re
import struct
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO

SCHEMA = "phoenix_key.restore_target_rollback_capture.v1"
DRIVE_EVIDENCE_SCHEMA = "bws.physical-drive-evidence/v1"
RAW_DEVICE_PATTERN = re.compile(r"^\\\\\.\\PHYSICALDRIVE([0-9]+)$", re.IGNORECASE)
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
MAX_GPT_TABLE_BYTES = 16 * 1024 * 1024


class RollbackCaptureError(RuntimeError):
    """Raised when trustworthy read-only rollback capture cannot proceed."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_raw_target(target: str) -> int:
    match = RAW_DEVICE_PATTERN.fullmatch(target.strip())
    if not match:
        raise RollbackCaptureError(
            r"Target must be an exact Windows raw path such as \\.\PHYSICALDRIVE7."
        )
    return int(match.group(1))


def require_sha256(value: str, label: str) -> str:
    value = value.strip().lower()
    if not SHA256_RE.fullmatch(value):
        raise RollbackCaptureError(f"{label} must be a 64-character SHA-256.")
    return value


def verify_drive_evidence(receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt.get("schema_version") != DRIVE_EVIDENCE_SCHEMA:
        raise RollbackCaptureError("Drive evidence schema is unsupported.")
    expected = receipt.get("receipt_sha256")
    if not isinstance(expected, str) or not SHA256_RE.fullmatch(expected):
        raise RollbackCaptureError("Drive evidence receipt hash is missing or invalid.")
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    if sha256_payload(unsigned).lower() != expected.lower():
        raise RollbackCaptureError("Drive evidence receipt checksum is invalid.")
    if (
        receipt.get("bytes_written") != 0
        or receipt.get("physical_write_attempted") is not False
    ):
        raise RollbackCaptureError(
            "Drive evidence does not prove a read-only target inspection."
        )
    disk = receipt.get("disk")
    if not isinstance(disk, dict):
        raise RollbackCaptureError("Drive evidence is missing the disk record.")
    return disk


def read_exact(handle: BinaryIO, offset: int, length: int) -> bytes:
    handle.seek(offset)
    data = handle.read(length)
    if len(data) != length:
        raise RollbackCaptureError(
            f"Short raw read at offset {offset}: expected {length} bytes, got {len(data)}."
        )
    return data


def parse_gpt_header(
    sector: bytes, logical_sector_size: int, label: str
) -> dict[str, Any]:
    if len(sector) != logical_sector_size:
        raise RollbackCaptureError(f"{label} GPT header sector has the wrong size.")
    if sector[:8] != b"EFI PART":
        raise RollbackCaptureError(f"{label} GPT header signature is missing.")

    revision, header_size, stored_crc = struct.unpack_from("<III", sector, 8)
    if header_size < 92 or header_size > logical_sector_size:
        raise RollbackCaptureError(f"{label} GPT header size is invalid.")

    header = bytearray(sector[:header_size])
    struct.pack_into("<I", header, 16, 0)
    calculated_crc = binascii.crc32(header) & 0xFFFFFFFF
    if calculated_crc != stored_crc:
        raise RollbackCaptureError(
            f"{label} GPT header CRC mismatch: expected {stored_crc:#x}, got {calculated_crc:#x}."
        )

    current_lba, backup_lba, first_usable_lba, last_usable_lba = struct.unpack_from(
        "<QQQQ", sector, 24
    )
    partition_entry_lba = struct.unpack_from("<Q", sector, 72)[0]
    number_of_entries, entry_size, entries_crc = struct.unpack_from("<III", sector, 80)

    if number_of_entries <= 0 or entry_size < 128 or entry_size % 8:
        raise RollbackCaptureError(f"{label} GPT entry geometry is invalid.")
    table_bytes = number_of_entries * entry_size
    if table_bytes <= 0 or table_bytes > MAX_GPT_TABLE_BYTES:
        raise RollbackCaptureError(
            f"{label} GPT entry array exceeds the bounded capture limit."
        )

    return {
        "revision": revision,
        "header_size": header_size,
        "header_crc32": stored_crc,
        "current_lba": current_lba,
        "backup_lba": backup_lba,
        "first_usable_lba": first_usable_lba,
        "last_usable_lba": last_usable_lba,
        "disk_guid_hex": sector[56:72].hex(),
        "partition_entry_lba": partition_entry_lba,
        "number_of_entries": number_of_entries,
        "entry_size": entry_size,
        "partition_entries_crc32": entries_crc,
        "partition_table_bytes": table_bytes,
    }


def verify_partition_array(data: bytes, expected_crc: int, label: str) -> None:
    calculated = binascii.crc32(data) & 0xFFFFFFFF
    if calculated != expected_crc:
        raise RollbackCaptureError(
            f"{label} GPT partition-array CRC mismatch: expected {expected_crc:#x}, got {calculated:#x}."
        )


def write_binary_atomic(path: Path, data: bytes) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as temporary:
        temporary.write(data)
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)
    return {
        "path": str(path.resolve()),
        "size_bytes": path.stat().st_size,
        "sha256": file_sha256(path),
    }


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as temporary:
        temporary.write(data)
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, path)


def capture_gpt_artifacts(
    *,
    handle: BinaryIO,
    disk_size_bytes: int,
    logical_sector_size: int,
    output_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if logical_sector_size < 512 or logical_sector_size > 4096:
        raise RollbackCaptureError(
            "Logical sector size is outside the supported 512-4096 range."
        )
    if disk_size_bytes < logical_sector_size * 34:
        raise RollbackCaptureError("Target disk is too small to contain a valid GPT.")

    protective_mbr = read_exact(handle, 0, logical_sector_size)
    primary_header_sector = read_exact(handle, logical_sector_size, logical_sector_size)
    primary = parse_gpt_header(primary_header_sector, logical_sector_size, "primary")

    disk_lbas = disk_size_bytes // logical_sector_size
    if primary["current_lba"] != 1:
        raise RollbackCaptureError("Primary GPT header is not located at LBA 1.")
    if primary["backup_lba"] >= disk_lbas:
        raise RollbackCaptureError("Primary GPT backup LBA is outside the target disk.")

    primary_entries_offset = primary["partition_entry_lba"] * logical_sector_size
    primary_entries = read_exact(
        handle,
        primary_entries_offset,
        primary["partition_table_bytes"],
    )
    verify_partition_array(
        primary_entries,
        primary["partition_entries_crc32"],
        "primary",
    )

    backup_header_offset = primary["backup_lba"] * logical_sector_size
    backup_header_sector = read_exact(handle, backup_header_offset, logical_sector_size)
    backup = parse_gpt_header(backup_header_sector, logical_sector_size, "backup")

    if backup["current_lba"] != primary["backup_lba"] or backup["backup_lba"] != 1:
        raise RollbackCaptureError(
            "Primary and backup GPT headers do not cross-reference correctly."
        )
    for key in ("disk_guid_hex", "number_of_entries", "entry_size"):
        if backup[key] != primary[key]:
            raise RollbackCaptureError(
                f"Primary and backup GPT {key} values do not match."
            )

    backup_entries_offset = backup["partition_entry_lba"] * logical_sector_size
    backup_entries = read_exact(
        handle,
        backup_entries_offset,
        backup["partition_table_bytes"],
    )
    verify_partition_array(
        backup_entries,
        backup["partition_entries_crc32"],
        "backup",
    )
    if backup_entries != primary_entries:
        raise RollbackCaptureError("Primary and backup GPT partition arrays differ.")

    artifacts = {
        "protective_mbr": write_binary_atomic(
            output_dir / "protective-mbr.bin",
            protective_mbr,
        ),
        "gpt_primary_header": write_binary_atomic(
            output_dir / "gpt-primary-header.bin",
            primary_header_sector,
        ),
        "gpt_primary_entries": write_binary_atomic(
            output_dir / "gpt-primary-entries.bin",
            primary_entries,
        ),
        "gpt_backup_entries": write_binary_atomic(
            output_dir / "gpt-backup-entries.bin",
            backup_entries,
        ),
        "gpt_backup_header": write_binary_atomic(
            output_dir / "gpt-backup-header.bin",
            backup_header_sector,
        ),
    }
    geometry = {
        "logical_sector_size": logical_sector_size,
        "disk_size_bytes": disk_size_bytes,
        "primary": primary,
        "backup": backup,
    }
    return artifacts, geometry


def open_target_read_only(target: str) -> BinaryIO:
    if sys.platform != "win32":
        raise RollbackCaptureError(
            "Live physical-drive rollback capture requires Windows."
        )
    parse_raw_target(target)
    try:
        return open(target, "rb", buffering=0)
    except OSError as exc:
        raise RollbackCaptureError(
            f"Could not open restore target read-only: {exc}"
        ) from exc


def build_capture_receipt(
    *,
    target: str,
    drive_evidence: dict[str, Any],
    output_dir: Path,
    expected_target_snapshot_identity_sha256: str,
    expected_target_stable_identity_sha256: str,
    expected_destination_stable_identity_sha256: str,
    destination_stable_identity_sha256: str,
    logical_sector_size: int,
    rollback_contract_sha256: str,
    artifacts: dict[str, Any],
    gpt_geometry: dict[str, Any],
    captured_at: str | None = None,
) -> dict[str, Any]:
    disk = verify_drive_evidence(drive_evidence)
    observed_target = str(disk.get("target") or "")
    if observed_target.upper() != target.strip().upper():
        raise RollbackCaptureError(
            "Drive evidence target does not match the requested target."
        )

    expected_snapshot = require_sha256(
        expected_target_snapshot_identity_sha256,
        "Expected target snapshot identity",
    )
    expected_stable = require_sha256(
        expected_target_stable_identity_sha256,
        "Expected target stable identity",
    )
    expected_destination = require_sha256(
        expected_destination_stable_identity_sha256,
        "Expected rollback destination stable identity",
    )
    observed_destination = require_sha256(
        destination_stable_identity_sha256,
        "Observed rollback destination stable identity",
    )
    observed_snapshot = require_sha256(
        str(disk.get("identity_sha256") or ""),
        "Observed target snapshot identity",
    )
    observed_stable = require_sha256(
        str(disk.get("stable_identity_sha256") or ""),
        "Observed target stable identity",
    )

    contract_sha256 = require_sha256(
        rollback_contract_sha256,
        "Rollback contract SHA-256",
    )

    if observed_snapshot != expected_snapshot:
        raise RollbackCaptureError(
            "Restore target snapshot identity changed before capture."
        )
    if observed_stable != expected_stable:
        raise RollbackCaptureError(
            "Restore target stable identity changed before capture."
        )
    if observed_destination != expected_destination:
        raise RollbackCaptureError(
            "Rollback destination stable identity changed before capture."
        )
    if observed_destination == observed_stable:
        raise RollbackCaptureError(
            "Rollback destination is the restore target physical device."
        )

    partition_style = str(disk.get("partition_style") or "").upper()
    if partition_style != "GPT":
        raise RollbackCaptureError(
            "Full partition-table rollback capture currently requires a GPT target."
        )

    partition_manifest = {
        "schema": "phoenix_key.restore_target_partition_manifest.v1",
        "target": observed_target,
        "target_snapshot_identity_sha256": observed_snapshot,
        "target_stable_identity_sha256": observed_stable,
        "destination_stable_identity_sha256": observed_destination,
        "size_bytes": int(disk.get("size_bytes") or 0),
        "partition_style": partition_style,
        "logical_sector_size": logical_sector_size,
        "partitions": disk.get("partitions") or [],
        "gpt_geometry": gpt_geometry,
        "system_mutations_performed": False,
    }
    partition_manifest["manifest_sha256"] = sha256_payload(partition_manifest)
    manifest_path = output_dir / "target-partition-manifest.json"
    write_json_atomic(manifest_path, partition_manifest)

    artifact_checksums = {
        name: {
            "path": artifact["path"],
            "size_bytes": artifact["size_bytes"],
            "sha256": artifact["sha256"],
        }
        for name, artifact in artifacts.items()
    }
    artifact_checksums["target_partition_manifest"] = {
        "path": str(manifest_path.resolve()),
        "size_bytes": manifest_path.stat().st_size,
        "sha256": file_sha256(manifest_path),
    }

    receipt = {
        "schema": SCHEMA,
        "captured_at": captured_at or utc_now_iso(),
        "target": observed_target,
        "target_snapshot_identity_sha256": observed_snapshot,
        "target_stable_identity_sha256": observed_stable,
        "rollback_destination_stable_identity_sha256": observed_destination,
        "rollback_contract_sha256": contract_sha256,
        "output_directory": str(output_dir.resolve()),
        "captured_requirements": [
            "target_partition_table_backup",
            "target_partition_manifest",
            "artifact_checksums",
        ],
        "remaining_requirements": [
            "target_boot_metadata_backup_if_present",
            "target_data_preservation_receipt_or_explicit_discard_decision",
        ],
        "artifacts": artifact_checksums,
        "partition_manifest_sha256": partition_manifest["manifest_sha256"],
        "restore_unlock_ready": False,
        "restore_unlock_scope": [],
        "always_blocked_by_this_capture": ["apply_system_image"],
        "target_bytes_written": 0,
        "target_write_attempted": False,
        "rollback_destination_files_written": True,
        "system_mutations_performed": False,
    }
    receipt["receipt_sha256"] = sha256_payload(receipt)
    write_json_atomic(output_dir / "restore-rollback-capture.json", receipt)
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--drive-evidence", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--logical-sector-size", type=int, required=True)
    parser.add_argument("--expected-target-snapshot-identity-sha256", required=True)
    parser.add_argument("--expected-target-stable-identity-sha256", required=True)
    parser.add_argument("--expected-destination-stable-identity-sha256", required=True)
    parser.add_argument("--destination-stable-identity-sha256", required=True)
    parser.add_argument("--rollback-contract-sha256", required=True)
    parser.add_argument("--fixture-disk-image", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    parse_raw_target(args.target)
    drive_evidence = json.loads(args.drive_evidence.read_text(encoding="utf-8"))
    disk = verify_drive_evidence(drive_evidence)
    disk_size = int(disk.get("size_bytes") or 0)
    if disk_size <= 0:
        raise RollbackCaptureError("Drive evidence target size is missing or invalid.")

    expected_snapshot = require_sha256(
        args.expected_target_snapshot_identity_sha256,
        "Expected target snapshot identity",
    )
    expected_stable = require_sha256(
        args.expected_target_stable_identity_sha256,
        "Expected target stable identity",
    )
    expected_destination = require_sha256(
        args.expected_destination_stable_identity_sha256,
        "Expected rollback destination stable identity",
    )
    observed_destination = require_sha256(
        args.destination_stable_identity_sha256,
        "Observed rollback destination stable identity",
    )
    observed_snapshot = require_sha256(
        str(disk.get("identity_sha256") or ""),
        "Observed target snapshot identity",
    )
    observed_stable = require_sha256(
        str(disk.get("stable_identity_sha256") or ""),
        "Observed target stable identity",
    )
    require_sha256(args.rollback_contract_sha256, "Rollback contract SHA-256")

    if observed_snapshot != expected_snapshot:
        raise RollbackCaptureError(
            "Restore target snapshot identity changed before capture."
        )
    if observed_stable != expected_stable:
        raise RollbackCaptureError(
            "Restore target stable identity changed before capture."
        )
    if observed_destination != expected_destination:
        raise RollbackCaptureError(
            "Rollback destination stable identity changed before capture."
        )
    if observed_destination == observed_stable:
        raise RollbackCaptureError(
            "Rollback destination is the restore target physical device."
        )
    if str(disk.get("partition_style") or "").upper() != "GPT":
        raise RollbackCaptureError(
            "Full partition-table rollback capture currently requires a GPT target."
        )

    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RollbackCaptureError(
            "Rollback capture output directory already contains files; "
            "refusing to overwrite evidence."
        )
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.fixture_disk_image:
        handle = args.fixture_disk_image.open("rb")
    else:
        handle = open_target_read_only(args.target)

    with handle:
        artifacts, geometry = capture_gpt_artifacts(
            handle=handle,
            disk_size_bytes=disk_size,
            logical_sector_size=args.logical_sector_size,
            output_dir=output_dir,
        )

    receipt = build_capture_receipt(
        target=args.target,
        drive_evidence=drive_evidence,
        output_dir=output_dir,
        expected_target_snapshot_identity_sha256=(
            args.expected_target_snapshot_identity_sha256
        ),
        expected_target_stable_identity_sha256=(
            args.expected_target_stable_identity_sha256
        ),
        expected_destination_stable_identity_sha256=(
            args.expected_destination_stable_identity_sha256
        ),
        destination_stable_identity_sha256=args.destination_stable_identity_sha256,
        logical_sector_size=args.logical_sector_size,
        rollback_contract_sha256=args.rollback_contract_sha256,
        artifacts=artifacts,
        gpt_geometry=geometry,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RollbackCaptureError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"RESTORE_ROLLBACK_CAPTURE_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
