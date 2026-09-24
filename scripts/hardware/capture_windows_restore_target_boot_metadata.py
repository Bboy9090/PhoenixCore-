#!/usr/bin/env python3
"""Capture read-only boot metadata from an external Windows restore target.

The target disk is never mounted, assigned a drive letter, or written. Metadata
is copied only from partitions that Windows already exposes with drive letters.
Artifacts are written only beneath the caller-provided rollback output folder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

SCHEMA = "phoenix_key.restore_target_boot_metadata.v1"
DRIVE_EVIDENCE_SCHEMA = "bws.physical-drive-evidence/v1"
ROLLBACK_CAPTURE_SCHEMA = "phoenix_key.restore_target_rollback_capture.v1"
EFI_GUID = "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"
RECOVERY_GUID = "{de94bba4-06d1-4d40-a16a-bfd50179d6ac}"
RAW_DEVICE_PATTERN = re.compile(r"^\\\\\.\\PHYSICALDRIVE([0-9]+)$", re.IGNORECASE)
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class RestoreTargetBootMetadataError(RuntimeError):
    """Raised when trustworthy target boot-metadata capture cannot proceed."""


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
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(payload: dict[str, Any], destination: Path) -> None:
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


def verify_embedded_sha256(
    payload: dict[str, Any],
    *,
    schema_key: str,
    schema: str,
    digest_field: str,
) -> None:
    if payload.get(schema_key) != schema:
        raise RestoreTargetBootMetadataError(
            f"Unsupported evidence schema: {payload.get(schema_key)}"
        )
    expected = str(payload.get(digest_field) or "")
    if not SHA256_RE.fullmatch(expected):
        raise RestoreTargetBootMetadataError(f"{digest_field} is missing or invalid.")
    body = dict(payload)
    body.pop(digest_field, None)
    if sha256_payload(body) != expected.lower():
        raise RestoreTargetBootMetadataError(
            f"{digest_field} does not match its contents."
        )


def verify_drive_evidence(receipt: dict[str, Any]) -> dict[str, Any]:
    if receipt.get("schema_version") != DRIVE_EVIDENCE_SCHEMA:
        raise RestoreTargetBootMetadataError("Unsupported drive-evidence schema.")
    expected = str(receipt.get("receipt_sha256") or "")
    if not SHA256_RE.fullmatch(expected):
        raise RestoreTargetBootMetadataError(
            "Drive-evidence receipt SHA-256 is missing or invalid."
        )
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    if sha256_payload(unsigned) != expected.lower():
        raise RestoreTargetBootMetadataError(
            "Drive-evidence receipt checksum is invalid."
        )
    if (
        receipt.get("bytes_written") != 0
        or receipt.get("physical_write_attempted") is not False
    ):
        raise RestoreTargetBootMetadataError(
            "Drive evidence does not prove read-only target inspection."
        )
    disk = receipt.get("disk")
    if not isinstance(disk, dict):
        raise RestoreTargetBootMetadataError(
            "Drive evidence is missing its disk record."
        )
    return disk


def require_live_boot_metadata_inputs(
    drive_receipt: dict[str, Any],
    rollback_receipt: dict[str, Any],
) -> None:
    if (
        drive_receipt.get("evidence_source") != "live"
        or drive_receipt.get("hardware_observed") is not True
    ):
        raise RestoreTargetBootMetadataError(
            "Live boot-metadata capture requires live target drive evidence."
        )
    if (
        rollback_receipt.get("evidence_source") != "live"
        or rollback_receipt.get("hardware_observed") is not True
    ):
        raise RestoreTargetBootMetadataError(
            "Live boot-metadata capture requires a live rollback-capture receipt."
        )


def verify_rollback_capture(receipt: dict[str, Any]) -> None:
    verify_embedded_sha256(
        receipt,
        schema_key="schema",
        schema=ROLLBACK_CAPTURE_SCHEMA,
        digest_field="receipt_sha256",
    )
    if (
        receipt.get("target_bytes_written") != 0
        or receipt.get("target_write_attempted") is not False
        or receipt.get("restore_unlock_ready") is not False
        or receipt.get("system_mutations_performed") is not False
    ):
        raise RestoreTargetBootMetadataError(
            "Rollback capture receipt does not preserve the required safety locks."
        )


def parse_raw_target(target: str) -> int:
    match = RAW_DEVICE_PATTERN.fullmatch(target.strip())
    if not match:
        raise RestoreTargetBootMetadataError(
            r"Target must be an exact Windows raw path such as \\.\PHYSICALDRIVE7."
        )
    return int(match.group(1))


def query_target_partitions(disk_number: int) -> list[dict[str, Any]]:
    if sys.platform != "win32":
        raise RestoreTargetBootMetadataError(
            "Live restore-target boot metadata capture requires Windows."
        )
    script = rf"""
$ErrorActionPreference = 'Stop'
$items = @(
  Get-Partition -DiskNumber {disk_number} |
    Select-Object DiskNumber, PartitionNumber, DriveLetter, Offset, Size, Type, GptType, MbrType
)
$items | ConvertTo-Json -Depth 5 -Compress
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
        raise RestoreTargetBootMetadataError(
            f"Windows target partition query failed: {message}"
        )
    try:
        payload = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise RestoreTargetBootMetadataError(
            "PowerShell returned malformed target partition JSON."
        ) from exc
    if isinstance(payload, dict):
        return [payload]
    if isinstance(payload, list):
        return payload
    raise RestoreTargetBootMetadataError(
        "PowerShell target partition inventory was not a list."
    )


def copy_file_artifact(source: Path, destination: Path) -> dict[str, Any]:
    if source.is_symlink():
        raise RestoreTargetBootMetadataError(
            f"Symbolic-link boot metadata source is not accepted: {source}"
        )
    if not source.is_file():
        return {
            "status": "not-present",
            "source": str(source),
            "path": None,
            "sha256": None,
            "size_bytes": None,
        }
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "status": "persisted",
        "source": str(source),
        "path": str(destination.resolve()),
        "sha256": file_sha256(destination),
        "size_bytes": destination.stat().st_size,
    }


def copy_tree_artifact(source: Path, destination: Path) -> dict[str, Any]:
    if source.is_symlink():
        raise RestoreTargetBootMetadataError(
            f"Symbolic-link boot metadata root is not accepted: {source}"
        )
    if not source.is_dir():
        return {
            "status": "not-present",
            "source": str(source),
            "path": None,
            "manifest_sha256": None,
            "file_count": 0,
            "files": [],
        }

    files: list[dict[str, Any]] = []
    for root, directories, filenames in os.walk(source):
        root_path = Path(root)
        for directory in list(directories):
            if (root_path / directory).is_symlink():
                raise RestoreTargetBootMetadataError(
                    f"Symbolic-link boot metadata directory is not accepted: "
                    f"{root_path / directory}"
                )
        for filename in filenames:
            source_file = root_path / filename
            if source_file.is_symlink():
                raise RestoreTargetBootMetadataError(
                    f"Symbolic-link boot metadata file is not accepted: {source_file}"
                )
            relative = source_file.relative_to(source)
            destination_file = destination / relative
            destination_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, destination_file)
            files.append(
                {
                    "relative_path": relative.as_posix(),
                    "size_bytes": destination_file.stat().st_size,
                    "sha256": file_sha256(destination_file),
                }
            )
    files.sort(key=lambda item: item["relative_path"])
    return {
        "status": "persisted",
        "source": str(source),
        "path": str(destination.resolve()),
        "manifest_sha256": sha256_payload(files),
        "file_count": len(files),
        "files": files,
    }


def default_partition_root(partition: dict[str, Any]) -> Path | None:
    drive_letter = str(partition.get("DriveLetter") or "").strip()
    if not drive_letter:
        return None
    return Path(f"{drive_letter}:\\")


def capture_partition_metadata(
    *,
    partitions: list[dict[str, Any]],
    output_dir: Path,
    root_resolver: Callable[[dict[str, Any]], Path | None] = default_partition_root,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    inventory: list[dict[str, Any]] = []
    artifacts: dict[str, Any] = {}
    missing_or_unverified: list[str] = []

    for raw in partitions:
        number = int(raw.get("PartitionNumber") or -1)
        gpt_type = str(raw.get("GptType") or "").lower()
        root = root_resolver(raw)
        role = (
            "efi_system"
            if gpt_type == EFI_GUID
            else "windows_recovery" if gpt_type == RECOVERY_GUID else "other"
        )
        record = {
            "partition_number": number,
            "gpt_type": gpt_type or None,
            "role": role,
            "drive_letter": str(raw.get("DriveLetter") or "").strip() or None,
            "offset_bytes": int(raw.get("Offset") or 0),
            "size_bytes": int(raw.get("Size") or 0),
            "already_accessible": root is not None and root.exists(),
        }
        inventory.append(record)

        if role in {"efi_system", "windows_recovery"} and (
            root is None or not root.exists()
        ):
            missing_or_unverified.append(
                f"{role}_partition_{number}_not_already_accessible"
            )
            continue
        if root is None or not root.exists():
            continue

        if role == "efi_system":
            artifacts[f"efi_partition_{number}"] = copy_tree_artifact(
                root / "EFI",
                output_dir / f"efi-partition-{number}" / "EFI",
            )

        if role == "windows_recovery":
            recovery_root = root / "Recovery" / "WindowsRE"
            artifacts[f"winre_wim_partition_{number}"] = copy_file_artifact(
                recovery_root / "Winre.wim",
                output_dir
                / f"recovery-partition-{number}"
                / "Recovery"
                / "WindowsRE"
                / "Winre.wim",
            )
            artifacts[f"winre_config_partition_{number}"] = copy_file_artifact(
                recovery_root / "ReAgent.xml",
                output_dir
                / f"recovery-partition-{number}"
                / "Recovery"
                / "WindowsRE"
                / "ReAgent.xml",
            )

        known_files = {
            "boot_bcd": root / "Boot" / "BCD",
            "efi_bcd": root / "EFI" / "Microsoft" / "Boot" / "BCD",
            "windows_reagent": root
            / "Windows"
            / "System32"
            / "Recovery"
            / "ReAgent.xml",
        }
        for label, source in known_files.items():
            artifact = copy_file_artifact(
                source,
                output_dir / f"partition-{number}" / label / source.name,
            )
            if artifact["status"] == "persisted":
                artifacts[f"{label}_partition_{number}"] = artifact

    inventory.sort(key=lambda item: item["partition_number"])
    return inventory, artifacts, missing_or_unverified


def build_receipt(
    *,
    target: str,
    target_disk: dict[str, Any],
    rollback_capture: dict[str, Any],
    rollback_contract_sha256: str,
    output_dir: Path,
    inventory: list[dict[str, Any]],
    artifacts: dict[str, Any],
    missing_or_unverified: list[str],
    evidence_source: str = "fixture",
) -> dict[str, Any]:
    if evidence_source not in {"live", "fixture"}:
        raise RestoreTargetBootMetadataError(
            "Boot-metadata evidence source is invalid."
        )

    target_snapshot = str(target_disk.get("identity_sha256") or "").lower()
    target_stable = str(target_disk.get("stable_identity_sha256") or "").lower()
    if not SHA256_RE.fullmatch(target_snapshot) or not SHA256_RE.fullmatch(
        target_stable
    ):
        raise RestoreTargetBootMetadataError(
            "Target drive evidence is missing valid SHA-256 identities."
        )

    contract_sha = rollback_contract_sha256.strip().lower()
    if not SHA256_RE.fullmatch(contract_sha):
        raise RestoreTargetBootMetadataError(
            "Rollback contract SHA-256 is missing or invalid."
        )

    if str(rollback_capture.get("target") or "").upper() != target.upper():
        raise RestoreTargetBootMetadataError(
            "Rollback capture target does not match the current target."
        )
    if (
        str(rollback_capture.get("target_snapshot_identity_sha256") or "").lower()
        != target_snapshot
        or str(rollback_capture.get("target_stable_identity_sha256") or "").lower()
        != target_stable
    ):
        raise RestoreTargetBootMetadataError(
            "Target identity changed after GPT rollback capture."
        )
    if (
        str(rollback_capture.get("rollback_contract_sha256") or "").lower()
        != contract_sha
    ):
        raise RestoreTargetBootMetadataError(
            "Rollback capture is not bound to this rollback contract."
        )

    receipt = {
        "schema": SCHEMA,
        "evidence_source": evidence_source,
        "hardware_observed": evidence_source == "live",
        "target": target,
        "target_snapshot_identity_sha256": target_snapshot,
        "target_stable_identity_sha256": target_stable,
        "rollback_contract_sha256": contract_sha,
        "rollback_capture_receipt_sha256": rollback_capture["receipt_sha256"],
        "output_directory": str(output_dir.resolve()),
        "partition_inventory": inventory,
        "artifacts": artifacts,
        "resolved": not missing_or_unverified,
        "missing_or_unverified": missing_or_unverified,
        "restore_unlock_ready": False,
        "target_bytes_written": 0,
        "target_write_attempted": False,
        "partition_mount_or_assignment_attempted": False,
        "system_mutations_performed": False,
    }
    receipt["receipt_sha256"] = sha256_payload(receipt)
    return receipt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--drive-evidence", type=Path, required=True)
    parser.add_argument("--rollback-capture-receipt", type=Path, required=True)
    parser.add_argument("--rollback-contract-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    disk_number = parse_raw_target(args.target)
    drive_evidence = json.loads(args.drive_evidence.read_text(encoding="utf-8"))
    target_disk = verify_drive_evidence(drive_evidence)
    rollback_capture = json.loads(
        args.rollback_capture_receipt.read_text(encoding="utf-8")
    )
    verify_rollback_capture(rollback_capture)
    require_live_boot_metadata_inputs(drive_evidence, rollback_capture)

    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RestoreTargetBootMetadataError(
            "Boot-metadata output directory already contains files."
        )
    output_dir.mkdir(parents=True, exist_ok=True)

    partitions = query_target_partitions(disk_number)
    inventory, artifacts, missing = capture_partition_metadata(
        partitions=partitions,
        output_dir=output_dir,
    )
    receipt = build_receipt(
        target=args.target,
        target_disk=target_disk,
        rollback_capture=rollback_capture,
        rollback_contract_sha256=args.rollback_contract_sha256,
        output_dir=output_dir,
        inventory=inventory,
        artifacts=artifacts,
        missing_or_unverified=missing,
        evidence_source="live",
    )
    write_json_atomic(receipt, output_dir / "restore-target-boot-metadata.json")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        RestoreTargetBootMetadataError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"RESTORE_TARGET_BOOT_METADATA_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
