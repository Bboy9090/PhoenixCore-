"""Guarded deterministic GPT/FAT32 Windows installer-media provisioning.

This executor requires a live eligible target plan, an exact typed destruction
phrase, elevation, and an environment unlock. Existing mounted target volumes
are locked and dismounted before a final native identity-bound layout command.
It copies only a verified FAT32-ready manifest and performs full readback.
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Callable

from scripts.hardware import capture_windows_drive_evidence as drives
from scripts.hardware import plan_fat32_windows_media as media
from scripts.hardware import resolve_windows_source_disk as sources
from scripts.hardware import verify_windows_installer_target as target_verifier
from scripts.hardware import windows_volume_lock as volume_lock
from scripts.hardware import write_windows_sacrificial_drive as receipts


SCHEMA = "arcwyre.windows_installer_provisioning.v1"
UNLOCK_ENV = "ARCWYRE_ENABLE_WINDOWS_INSTALLER_PROVISIONING"
UNLOCK_VALUE = "I_ACCEPT_DESTRUCTION_OF_VERIFIED_INSTALLER_TARGET"
ALIGNMENT = 1024 * 1024
FAT32_MAX_PARTITION_BYTES = 32760 * ALIGNMENT
COPY_CHUNK = 1024 * 1024
ESP_GUID = "C12A7328-F81F-11D2-BA4B-00A0C93EC93B"


class ProvisioningError(RuntimeError):
    pass


def partition_size_bytes(plan: dict[str, Any]) -> int:
    binding = plan.get("binding") or {}
    target_size = binding.get("target_size_bytes")
    required = binding.get("required_bytes")
    if type(target_size) is not int or type(required) is not int:
        raise ProvisioningError("Target plan capacity facts are invalid")
    available = ((target_size - 2 * ALIGNMENT) // ALIGNMENT) * ALIGNMENT
    size = min(available, FAT32_MAX_PARTITION_BYTES)
    if size < required or size < 8 * 1024**3:
        raise ProvisioningError("FAT32 partition cannot satisfy installer capacity")
    return size


def expected_authorization(plan: dict[str, Any]) -> str:
    binding = plan.get("binding") or {}
    return (
        f"I AUTHORIZE GPT FAT32 DESTRUCTION OF {binding.get('target')} "
        f"SNAPSHOT {binding.get('target_snapshot_identity_sha256')} "
        f"STABLE {binding.get('target_stable_identity_sha256')} "
        f"SOURCE_MANIFEST {binding.get('source_manifest_sha256')}"
    )


def validate_execution(
    plan: dict[str, Any],
    authorization: str,
    *,
    execute: bool,
    admin: bool,
    environment: dict[str, str],
) -> int:
    if plan.get("schema") != "arcwyre.windows_install_target_plan.v1":
        raise ProvisioningError("Unsupported installer target plan")
    if plan.get("eligible_for_preparation") is not True or plan.get("block_reasons"):
        raise ProvisioningError("Installer target plan is blocked")
    if plan.get("write_authorized") is not False:
        raise ProvisioningError("Planning receipt has an invalid authorization state")
    binding = plan.get("binding")
    if not isinstance(binding, dict):
        raise ProvisioningError("Installer target binding is missing")
    encoded = json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()
    if hashlib.sha256(encoded).hexdigest() != plan.get("plan_sha256"):
        raise ProvisioningError("Installer target plan integrity check failed")
    number = drives.parse_raw_target(str(binding.get("target") or ""))
    if str(binding["target"]).upper() != rf"\\.\PHYSICALDRIVE{number}":
        raise ProvisioningError("Installer target is not canonical")
    for field in (
        "target_snapshot_identity_sha256",
        "target_stable_identity_sha256",
        "source_manifest_sha256",
    ):
        if not re.fullmatch(r"[0-9a-f]{64}", str(binding.get(field) or "")):
            raise ProvisioningError(f"Installer target binding {field} is invalid")
    if authorization != expected_authorization(plan):
        raise ProvisioningError("Typed destruction authorization does not match")
    if environment.get(UNLOCK_ENV) != UNLOCK_VALUE:
        raise ProvisioningError("Installer provisioning environment unlock is absent")
    if execute is not True:
        raise ProvisioningError("Installer provisioning requires --execute")
    if admin is not True:
        raise ProvisioningError("Installer provisioning requires elevation")
    return partition_size_bytes(plan)


def mounted_letters(raw: dict[str, Any]) -> list[str]:
    parts = raw.get("Partitions") or []
    if isinstance(parts, dict):
        parts = [parts]
    if not isinstance(parts, list):
        raise ProvisioningError("Target partition inventory is invalid")
    letters = []
    for part in parts:
        if not isinstance(part, dict):
            raise ProvisioningError("Target partition record is invalid")
        for flag in ("IsBoot", "IsSystem"):
            if type(part.get(flag)) is not bool or part[flag]:
                raise ProvisioningError("Target contains unsafe partition state")
        letter = part.get("DriveLetter")
        if letter not in (None, ""):
            text = str(letter).upper()
            if not re.fullmatch("[A-Z]", text) or text in letters:
                raise ProvisioningError("Target drive-letter inventory is ambiguous")
            letters.append(text)
    return sorted(letters)


def lock_and_dismount_existing(
    letters: list[str],
    cancelled: Callable[[], bool],
    lock_factory=volume_lock.LockedWindowsVolume,
) -> list[str]:
    if cancelled():
        raise ProvisioningError("Cancelled before existing-volume locks")
    with ExitStack() as stack:
        leases = [stack.enter_context(lock_factory(letter + ":", cancelled)) for letter in letters]
        for lease in leases:
            lease.dismount()
    return letters


def _quoted(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def provision_layout(
    plan: dict[str, Any],
    raw: dict[str, Any],
    size_bytes: int,
    cancelled: Callable[[], bool],
) -> dict[str, Any]:
    binding = plan["binding"]
    number = drives.parse_raw_target(binding["target"])
    unique = str(raw.get("UniqueId") or "").strip()
    bus = str(raw.get("BusType") or "").strip()
    if not str(raw.get("SerialNumber") or "").strip() or not unique or not bus:
        raise ProvisioningError("Fresh native target identity is incomplete")
    size_mib = size_bytes // ALIGNMENT
    script = f"""
$ErrorActionPreference = 'Stop'
$disk = Get-Disk -Number {number} -ErrorAction Stop
if ([bool]$disk.IsBoot -or [bool]$disk.IsSystem -or [bool]$disk.IsOffline -or [bool]$disk.IsReadOnly) {{ throw 'Target safety state changed' }}
if ([string]$disk.SerialNumber -ne {_quoted(str(raw.get('SerialNumber') or ''))}) {{ throw 'Target serial changed' }}
if ([string]$disk.UniqueId -ne {_quoted(str(raw.get('UniqueId') or ''))}) {{ throw 'Target unique ID changed' }}
if ([string]$disk.BusType -ne {_quoted(bus)} -or [uint64]$disk.Size -ne [uint64]{int(raw['SizeBytes'])}) {{ throw 'Target bus or size changed' }}
Clear-Disk -Number {number} -RemoveData -RemoveOEM -Confirm:$false -ErrorAction Stop
$disk = Get-Disk -Number {number} -ErrorAction Stop
if ([string]$disk.PartitionStyle -eq 'RAW') {{ Initialize-Disk -Number {number} -PartitionStyle GPT -ErrorAction Stop }}
elseif ([string]$disk.PartitionStyle -ne 'GPT') {{ throw 'Target did not enter RAW or GPT state after clear' }}
$partition = New-Partition -DiskNumber {number} -Offset 1048576 -Size {size_bytes} -AssignDriveLetter -GptType '{{{ESP_GUID}}}' -ErrorAction Stop
$volume = Format-Volume -Partition $partition -FileSystem FAT32 -NewFileSystemLabel 'ARCWYRE' -AllocationUnitSize 32768 -Force -Confirm:$false -ErrorAction Stop
[pscustomobject]@{{ DiskNumber=[int]$partition.DiskNumber; PartitionNumber=[int]$partition.PartitionNumber; DriveLetter=[string]$partition.DriveLetter; Offset=[uint64]$partition.Offset; Size=[uint64]$partition.Size; GptType=[string]$partition.GptType; FileSystem=[string]$volume.FileSystem; Label=[string]$volume.FileSystemLabel; AllocationUnitSize=[uint32]$volume.AllocationUnitSize; RequestedSizeMiB={size_mib} }} | ConvertTo-Json -Compress
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
            timeout_seconds=300,
            cancelled=cancelled,
        )
    except (sources.SystemToolCancelled, sources.SystemToolTimeout) as exc:
        raise ProvisioningError(str(exc)) from exc
    if result.returncode:
        raise ProvisioningError(
            "Native GPT/FAT32 provisioning failed: "
            + (result.stderr or result.stdout).strip()
        )
    try:
        layout = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ProvisioningError("Provisioning returned malformed layout JSON") from exc
    if (
        layout.get("DiskNumber") != number
        or layout.get("Offset") != ALIGNMENT
        or layout.get("Size") != size_bytes
        or str(layout.get("GptType", "")).strip("{}").upper() != ESP_GUID
        or layout.get("FileSystem") != "FAT32"
        or layout.get("Label") != "ARCWYRE"
        or not re.fullmatch("[A-Z]", str(layout.get("DriveLetter") or ""))
    ):
        raise ProvisioningError("Native layout does not match deterministic contract")
    return layout


def copy_and_verify(
    source: Path,
    destination: Path,
    manifest: dict[str, Any],
    cancelled: Callable[[], bool],
) -> dict[str, Any]:
    verified = media.verify_media_manifest(source, manifest, cancelled)
    if not media.plan_media(source).get("ready_for_fat32_copy_now"):
        raise ProvisioningError("Source is not FAT32-ready")
    destination.mkdir(exist_ok=True)
    if any(destination.iterdir()):
        raise ProvisioningError("Fresh installer volume is not empty")
    for record in verified["files"]:
        if cancelled():
            raise ProvisioningError("Cancelled during installer copy")
        relative = Path(record["path"])
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        with (source / relative).open("rb") as incoming, target.open("xb") as outgoing:
            while chunk := incoming.read(COPY_CHUNK):
                if cancelled():
                    raise ProvisioningError("Cancelled during installer copy")
                outgoing.write(chunk)
                digest.update(chunk)
            outgoing.flush()
            os.fsync(outgoing.fileno())
        if digest.hexdigest() != record["sha256"]:
            raise ProvisioningError("Copied installer file hash mismatch")
    actual = media.verify_media_manifest(destination, verified, cancelled)
    media.verify_media_manifest(source, verified, cancelled)
    return actual


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--architecture", choices=("x64", "arm64", "x86"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cancel-file", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    cancelled = lambda: args.cancel_file is not None and os.path.lexists(args.cancel_file)
    with args.manifest.open(encoding="utf-8") as stream:
        manifest = json.load(stream)
    with args.plan.open(encoding="utf-8") as stream:
        plan = json.load(stream)
    size = validate_execution(
        plan,
        args.authorization,
        execute=args.execute,
        admin=receipts.is_windows_admin(),
        environment=os.environ,
    )
    binding = plan["binding"]
    if manifest.get("manifest_sha256") != binding["source_manifest_sha256"]:
        raise ProvisioningError("Source manifest does not match the target plan")
    number = drives.parse_raw_target(binding["target"])
    receipt_plan = {
        "target": binding["target"],
        "target_stable_identity_sha256": binding[
            "target_stable_identity_sha256"
        ],
    }
    destination_binding = receipts.validate_receipt_destination(
        plan=receipt_plan, output_path=args.output
    )
    pending = {
        "schema": SCHEMA,
        "classification": "installer-provisioning-reserved-not-started",
        "plan_sha256": plan["plan_sha256"],
        "target": binding["target"],
        "physical_mutations_attempted": False,
        "boot_proven": False,
        "hardware_validated": False,
    }
    pending["receipt_sha256"] = drives.sha256_payload(pending)
    stage = "prewrite-revalidation"
    with receipts.ReceiptReservation(args.output, pending) as reservation:
        try:
            raw = drives.query_windows_disk(number, cancelled)
            fresh = drives.normalize_disk_record(raw, binding["target"])
            if (
                fresh["identity_sha256"]
                != binding["target_snapshot_identity_sha256"]
                or fresh["stable_identity_sha256"]
                != binding["target_stable_identity_sha256"]
                or fresh["write_block_reasons"]
            ):
                raise ProvisioningError("Fresh target identity or eligibility changed")
            letters = mounted_letters(raw)
            if not letters:
                raise ProvisioningError(
                    "At least one mounted target volume is required to prove the native lock lane"
                )
            lock_and_dismount_existing(letters, cancelled)
            raw = drives.query_windows_disk(number, cancelled)
            fresh = drives.normalize_disk_record(raw, binding["target"])
            if fresh["identity_sha256"] != binding[
                "target_snapshot_identity_sha256"
            ]:
                raise ProvisioningError("Target changed after volume dismount")
            receipts.validate_receipt_destination(
                plan=receipt_plan,
                output_path=args.output,
                expected_binding=destination_binding,
            )
            stage = "native-layout"
            layout = provision_layout(plan, raw, size, cancelled)
            root = Path(str(layout["DriveLetter"]) + ":\\")
            stage = "manifest-copy"
            copied = copy_and_verify(args.source_root, root, manifest, cancelled)
            stage = "bound-readback"
            bound = target_verifier.verify_target(
                args.source_root,
                str(root),
                manifest,
                args.architecture,
                binding["target"],
                binding["target_stable_identity_sha256"],
                int(layout["PartitionNumber"]),
                cancelled,
            )
            receipt = {
                "schema": SCHEMA,
                "plan_sha256": plan["plan_sha256"],
                "target": binding["target"],
                "prewrite_identity_sha256": fresh["identity_sha256"],
                "receipt_destination_binding": destination_binding,
                "layout": layout,
                "manifest_sha256": copied["manifest_sha256"],
                "verified_files": len(copied["files"]),
                "verified_bytes": copied["total_bytes"],
                "bound_readback": bound,
                "native_volume_locks_used": True,
                "native_volume_lock_count": len(letters),
                "continuous_disk_lease_proven": False,
                "boot_proven": False,
                "hardware_validated": False,
                "classification": "physical-layout-and-files-readback-verified-boot-unproven",
            }
            receipt["receipt_sha256"] = drives.sha256_payload(receipt)
            reservation.commit(receipt)
        except Exception as exc:
            failure = {
                "schema": SCHEMA,
                "classification": "installer-provisioning-failed",
                "failure_stage": stage,
                "error": str(exc),
                "plan_sha256": plan["plan_sha256"],
                "target": binding["target"],
                "physical_mutations_may_have_occurred": stage
                in {"native-layout", "manifest-copy", "bound-readback"},
                "resume_allowed": False,
                "boot_proven": False,
                "hardware_validated": False,
            }
            failure["receipt_sha256"] = drives.sha256_payload(failure)
            reservation.commit(failure)
            raise
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"INSTALLER_PROVISIONING_BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

