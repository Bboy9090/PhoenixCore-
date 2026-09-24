#!/usr/bin/env python3
"""Capture read-only Windows EFI/BCD/WinRE state and persist a rollback manifest.

This module never edits firmware variables, BCD, partitions, WinRE, or the EFI
System Partition. It records evidence that must exist before a future repair
executor can be authorized.
"""

from __future__ import annotations

import argparse
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

BOOT_STATE_SCHEMA = "phoenix_key.windows_boot_state.v1"
ROLLBACK_SCHEMA = "phoenix_key.rollback_manifest.v1"
DRIVE_EVIDENCE_SCHEMA = "bws.physical-drive-evidence/v1"
EFI_SYSTEM_PARTITION_GUID = "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class BootStateError(RuntimeError):
    """Raised when trustworthy boot-state evidence cannot be produced."""


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


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def normalize_efi_partitions(partitions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for partition in partitions:
        gpt_type = str(partition.get("GptType") or "").lower()
        if gpt_type != EFI_SYSTEM_PARTITION_GUID:
            continue
        normalized.append(
            {
                "disk_number": int(partition.get("DiskNumber", -1)),
                "partition_number": int(partition.get("PartitionNumber", -1)),
                "drive_letter": (
                    str(partition.get("DriveLetter")).strip() or None
                    if partition.get("DriveLetter") is not None
                    else None
                ),
                "offset_bytes": int(partition.get("Offset") or 0),
                "size_bytes": int(partition.get("Size") or 0),
                "gpt_type": gpt_type,
            }
        )
    normalized.sort(key=lambda item: (item["disk_number"], item["partition_number"]))
    return normalized


def command_record(
    command: list[str],
    *,
    runner=subprocess.run,
) -> dict[str, Any]:
    completed = runner(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    return {
        "command": command[0],
        "arguments": command[1:],
        "returncode": int(completed.returncode),
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": sha256_text(stdout),
        "stderr_sha256": sha256_text(stderr),
    }


def query_windows_partition_and_secure_boot() -> dict[str, Any]:
    script = rf"""
$ErrorActionPreference = 'Stop'
$secure = $null
try {{ $secure = [bool](Confirm-SecureBootUEFI) }} catch {{ $secure = $null }}
$parts = @(
  Get-Partition |
    Select-Object DiskNumber, PartitionNumber, DriveLetter, Offset, Size, GptType
)
[pscustomobject]@{{
  SecureBootEnabled = $secure
  Partitions = $parts
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
        raise BootStateError(f"Windows partition/firmware query failed: {message}")
    try:
        payload = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise BootStateError("PowerShell returned malformed boot-state JSON.") from exc
    if not isinstance(payload, dict):
        raise BootStateError("PowerShell boot-state payload is not an object.")
    return payload


def build_boot_state_snapshot(
    *,
    partition_payload: dict[str, Any],
    bcd_record: dict[str, Any],
    winre_record: dict[str, Any],
    captured_at: str | None = None,
) -> dict[str, Any]:
    raw_partitions = partition_payload.get("Partitions") or []
    if isinstance(raw_partitions, dict):
        raw_partitions = [raw_partitions]
    if not isinstance(raw_partitions, list):
        raise BootStateError("Partition inventory is malformed.")

    snapshot = {
        "schema": BOOT_STATE_SCHEMA,
        "captured_at": captured_at or utc_now_iso(),
        "operation": "read-only-windows-boot-state-capture",
        "efi_system_partitions": normalize_efi_partitions(raw_partitions),
        "secure_boot_enabled": partition_payload.get("SecureBootEnabled"),
        "bcd": bcd_record,
        "winre": winre_record,
        "efi_write_attempted": False,
        "bcd_write_attempted": False,
        "winre_write_attempted": False,
        "partition_write_attempted": False,
        "bytes_written_to_system": 0,
    }
    snapshot["complete"] = (
        bool(snapshot["efi_system_partitions"])
        and bcd_record.get("returncode") == 0
        and winre_record.get("returncode") == 0
    )
    snapshot["snapshot_sha256"] = sha256_payload(snapshot)
    return snapshot


def capture_windows_boot_state() -> dict[str, Any]:
    if sys.platform != "win32":
        raise BootStateError("Live EFI/BCD/WinRE capture requires Windows.")
    partition_payload = query_windows_partition_and_secure_boot()
    bcd_record = command_record(["bcdedit.exe", "/enum", "all"])
    winre_record = command_record(["reagentc.exe", "/info"])
    return build_boot_state_snapshot(
        partition_payload=partition_payload,
        bcd_record=bcd_record,
        winre_record=winre_record,
    )


def load_drive_evidence(path: Path) -> dict[str, Any]:
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BootStateError(f"Target evidence could not be read: {exc}") from exc
    if evidence.get("schema_version") != DRIVE_EVIDENCE_SCHEMA:
        raise BootStateError("Unsupported target-evidence schema.")
    disk = evidence.get("disk")
    if not isinstance(disk, dict):
        raise BootStateError("Target evidence is missing its disk record.")
    identity = str(disk.get("identity_sha256") or "")
    if not SHA256_RE.fullmatch(identity):
        raise BootStateError("Target evidence is missing a valid identity SHA-256.")
    stable_identity = str(disk.get("stable_identity_sha256") or "")
    if not SHA256_RE.fullmatch(stable_identity):
        raise BootStateError(
            "Target evidence is missing a valid stable identity SHA-256."
        )
    return evidence


def build_rollback_manifest(
    *,
    source_identity_sha256: str,
    target_evidence: dict[str, Any],
    boot_state: dict[str, Any],
    source_path: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    source_identity_sha256 = source_identity_sha256.strip().lower()
    if not SHA256_RE.fullmatch(source_identity_sha256):
        raise BootStateError("Source identity must be a 64-character SHA-256.")
    if boot_state.get("schema") != BOOT_STATE_SCHEMA:
        raise BootStateError("Unsupported boot-state schema.")
    snapshot_sha = str(boot_state.get("snapshot_sha256") or "")
    if not SHA256_RE.fullmatch(snapshot_sha):
        raise BootStateError("Boot-state snapshot is missing its SHA-256.")

    disk = target_evidence.get("disk")
    if not isinstance(disk, dict):
        raise BootStateError("Target evidence is missing its disk record.")
    target_identity = str(disk.get("identity_sha256") or "")
    if not SHA256_RE.fullmatch(target_identity):
        raise BootStateError("Target evidence is missing a valid identity SHA-256.")
    target_stable_identity = str(disk.get("stable_identity_sha256") or "")
    if not SHA256_RE.fullmatch(target_stable_identity):
        raise BootStateError(
            "Target evidence is missing a valid stable identity SHA-256."
        )
    if disk.get("is_boot") is not True and disk.get("is_system") is not True:
        raise BootStateError(
            "Online BCD/WinRE evidence can only bind to the current Windows boot/system disk."
        )

    manifest = {
        "schema": ROLLBACK_SCHEMA,
        "created_at": created_at or utc_now_iso(),
        "source": {
            "path": source_path,
            "identity_sha256": source_identity_sha256,
        },
        "target": {
            "scope": "online_current_windows_boot_repair",
            "physical_target": disk.get("target"),
            "is_boot": disk.get("is_boot"),
            "is_system": disk.get("is_system"),
            "identity_sha256": disk.get("identity_sha256"),
            "stable_identity_sha256": disk.get("stable_identity_sha256"),
            "size_bytes": disk.get("size_bytes"),
            "partition_style": disk.get("partition_style"),
            "partitions": disk.get("partitions") or [],
        },
        "boot_state_snapshot_sha256": snapshot_sha,
        "boot_state_complete": bool(boot_state.get("complete")),
        "required_backup_artifacts_before_repair": [
            "partition_table_backup",
            "efi_system_partition_file_backup",
            "bcd_store_export",
            "winre_configuration_and_image_identity",
        ],
        "repair_unlock_ready": False,
        "repair_unlock_block_reasons": [
            "rollback artifacts have not yet been persisted and independently verified",
            "source identity must be rechecked immediately before mutation",
            "target snapshot identity must be rechecked immediately before mutation",
            "target stable hardware identity must be rechecked immediately before mutation",
        ],
        "system_mutations_performed": False,
    }
    manifest["manifest_sha256"] = sha256_payload(manifest)
    return manifest


def write_json_atomic(payload: dict[str, Any], destination: Path) -> None:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=destination.parent,
        delete=False,
    ) as temporary:
        temporary.write(text)
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-identity-sha256", required=True)
    parser.add_argument("--source-path")
    parser.add_argument("--drive-receipt", type=Path, required=True)
    parser.add_argument("--boot-state-output", type=Path, required=True)
    parser.add_argument("--rollback-output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target_evidence = load_drive_evidence(args.drive_receipt)
    boot_state = capture_windows_boot_state()
    write_json_atomic(boot_state, args.boot_state_output)
    rollback = build_rollback_manifest(
        source_identity_sha256=args.source_identity_sha256,
        source_path=args.source_path,
        target_evidence=target_evidence,
        boot_state=boot_state,
    )
    write_json_atomic(rollback, args.rollback_output)
    print(json.dumps(rollback, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BootStateError, OSError, ValueError) as exc:
        print(f"BOOT_STATE_CAPTURE_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
