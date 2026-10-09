"""Live, read-only Windows installer target preparation; never authorizes a write."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import capture_windows_drive_evidence as drives
    from . import plan_fat32_windows_media as media
    from . import resolve_windows_source_disk as sources
else:
    import capture_windows_drive_evidence as drives
    import plan_fat32_windows_media as media
    import resolve_windows_source_disk as sources

# Conservative planning allowance, not a guarantee about an eventual filesystem.
LAYOUT_RESERVE_BYTES = 1024 * 1024 * 1024


def _sha(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdefABCDEF" for c in value)
    )


def plan_install_target(
    source_root: Path,
    manifest: dict[str, Any],
    target: str,
    expected_snapshot: str,
    expected_stable: str,
) -> dict[str, Any]:
    if sys.platform != "win32":
        raise RuntimeError(
            "Live Windows installer target preparation requires Windows."
        )
    number = drives.parse_raw_target(target)
    canonical = rf"\\.\PHYSICALDRIVE{number}"
    if target.upper() != canonical:
        raise ValueError(
            "Target must be an exact canonical Windows physical-drive path."
        )
    if not _sha(expected_snapshot) or not _sha(expected_stable):
        raise ValueError("Both expected target identities must be SHA-256 values.")
    verified = media.verify_media_manifest(source_root, manifest)
    layout = media.plan_media(source_root)
    raw = drives.query_windows_disk(number)
    disk = drives.normalize_disk_record(raw, canonical)
    source = sources.query_source_disk(str(source_root.resolve()))
    reasons = list(disk["write_block_reasons"])
    for flag in ("IsBoot", "IsSystem", "IsOffline", "IsReadOnly"):
        if type(raw.get(flag)) is not bool:
            reasons.append("target_" + flag.lower() + "_unknown")
        elif raw[flag]:
            reasons.append("target_" + flag.lower())
    partitions = raw.get("Partitions")
    if isinstance(partitions, dict):
        partitions = [partitions]
    if not isinstance(partitions, list):
        reasons.append("target_partition_inventory_unknown")
    else:
        # Collector now fails on Get-Partition errors. Empty inventory still
        # lacks independent blank-RAW-disk proof required by this workflow.
        if not partitions:
            reasons.append("target_empty_partition_inventory_not_independently_proven")
        for partition in partitions:
            if not isinstance(partition, dict):
                reasons.append("target_partition_record_invalid")
                continue
            for flag in ("IsBoot", "IsSystem"):
                if type(partition.get(flag)) is not bool or partition[flag]:
                    reasons.append(
                        "target_partition_" + flag.lower() + "_unsafe_or_unknown"
                    )
    if raw.get("HealthStatus") != "Healthy":
        reasons.append("target_health_not_proven_healthy")
    if disk["identity_sha256"].lower() != expected_snapshot.lower():
        reasons.append("target_snapshot_identity_mismatch")
    if (
        not _sha(disk.get("stable_identity_sha256"))
        or disk["stable_identity_sha256"].lower() != expected_stable.lower()
    ):
        reasons.append("target_stable_identity_mismatch")
    source_path = source.get("physical_target")
    source_stable = source.get("stable_identity_sha256")
    if not isinstance(source_path, str) or not _sha(source_stable):
        reasons.append("source_physical_identity_unknown")
    elif (
        source_path.upper() == canonical
        or source_stable.lower() == expected_stable.lower()
    ):
        reasons.append("source_target_physical_collision")
    if not layout.get("ready_for_fat32_copy_now"):
        reasons.append("source_not_ready_for_direct_fat32_copy")
    required = verified["total_bytes"] + LAYOUT_RESERVE_BYTES
    if disk["size_bytes"] < required:
        reasons.append("target_capacity_insufficient_with_layout_reserve")
    # Detect changes while the live device/source queries were running.
    media.verify_media_manifest(source_root, verified)
    binding = {
        "operation": "windows_install_media",
        "source_manifest_sha256": verified["manifest_sha256"],
        "target": canonical,
        "target_snapshot_identity_sha256": disk["identity_sha256"],
        "target_stable_identity_sha256": disk.get("stable_identity_sha256"),
        "source_physical_target": source_path,
        "source_stable_identity_sha256": source_stable,
        "target_size_bytes": disk["size_bytes"],
        "required_bytes": required,
        "layout_reserve_bytes": LAYOUT_RESERVE_BYTES,
        "filesystem": "FAT32",
    }
    encoded = json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema": "arcwyre.windows_install_target_plan.v1",
        "binding": binding,
        "plan_sha256": hashlib.sha256(encoded).hexdigest(),
        "block_reasons": sorted(set(reasons)),
        "eligible_for_preparation": not reasons,
        "write_authorized": False,
        "system_mutations_performed": False,
        "boot_proven": False,
        "fresh_revalidation_required_at_execution": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--target", required=True)
    parser.add_argument("--expected-snapshot-sha256", required=True)
    parser.add_argument("--expected-stable-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        with args.manifest.open(encoding="utf-8") as stream:
            manifest = json.load(stream)
        if not isinstance(manifest, dict):
            raise ValueError("Manifest must be a JSON object.")
        result = plan_install_target(
            args.source_root,
            manifest,
            args.target,
            args.expected_snapshot_sha256,
            args.expected_stable_sha256,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(
            json.dumps(
                {
                    "schema": "arcwyre.windows_install_target_plan.v1",
                    "eligible_for_preparation": False,
                    "error": str(exc),
                    "write_authorized": False,
                    "system_mutations_performed": False,
                }
            )
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["eligible_for_preparation"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
