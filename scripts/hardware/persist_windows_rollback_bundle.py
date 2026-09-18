#!/usr/bin/env python3
"""Persist a non-destructive Windows rollback bundle before any boot repair.

The bundle is local evidence only. It never assigns an EFI mount point, changes
BCD entries, changes WinRE configuration, writes partition tables, or modifies
firmware variables.
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BUNDLE_SCHEMA = "phoenix_key.rollback_bundle.v1"
BOOT_STATE_SCHEMA = "phoenix_key.windows_boot_state.v1"
ROLLBACK_SCHEMA = "phoenix_key.rollback_manifest.v1"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class RollbackBundleError(RuntimeError):
    """Raised when required rollback evidence cannot be persisted safely."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RollbackBundleError(f"Could not read JSON evidence {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RollbackBundleError(f"Evidence {path} must contain a JSON object.")
    return value


def verify_embedded_digest(
    payload: dict[str, Any],
    *,
    schema: str,
    digest_field: str,
) -> None:
    if payload.get("schema") != schema:
        raise RollbackBundleError(f"Unsupported evidence schema: {payload.get('schema')}")
    expected = str(payload.get(digest_field) or "")
    if not SHA256_RE.fullmatch(expected):
        raise RollbackBundleError(f"{digest_field} is missing or invalid.")
    body = dict(payload)
    body.pop(digest_field, None)
    if sha256_payload(body) != expected.lower():
        raise RollbackBundleError(f"{digest_field} does not match its contents.")


def verify_boot_state(snapshot: dict[str, Any]) -> None:
    verify_embedded_digest(
        snapshot,
        schema=BOOT_STATE_SCHEMA,
        digest_field="snapshot_sha256",
    )
    if snapshot.get("complete") is not True:
        raise RollbackBundleError("Boot-state snapshot is incomplete; repair must remain locked.")


def verify_rollback_manifest(
    manifest: dict[str, Any],
    boot_state: dict[str, Any],
) -> None:
    verify_embedded_digest(
        manifest,
        schema=ROLLBACK_SCHEMA,
        digest_field="manifest_sha256",
    )
    if manifest.get("boot_state_snapshot_sha256") != boot_state.get("snapshot_sha256"):
        raise RollbackBundleError(
            "Rollback manifest is not bound to this boot-state snapshot."
        )
    if manifest.get("system_mutations_performed") is not False:
        raise RollbackBundleError("Rollback manifest must precede all system mutations.")
    target = manifest.get("target")
    if not isinstance(target, dict) or target.get("scope") != "online_current_windows_boot_repair":
        raise RollbackBundleError(
            "Rollback manifest is not scoped to online Windows boot repair."
        )


def parse_winre_location(reagent_stdout: str) -> str | None:
    for line in reagent_stdout.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip().lower() == "windows re location":
            value = value.strip()
            return value or None
    return None


def windows_path_from_winre_location(location: str | None) -> Path | None:
    if not location:
        return None
    match = re.match(r"^([A-Za-z]:[\\/].+)$", location)
    if not match:
        return None
    return Path(match.group(1)) / "Winre.wim"


def run_bcd_export(destination: Path) -> dict[str, Any]:
    if sys.platform != "win32":
        return {
            "status": "not-run-non-windows",
            "path": None,
            "sha256": None,
            "size_bytes": None,
        }
    destination.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        ["bcdedit.exe", "/export", str(destination)],
        check=False,
        capture_output=True,
        text=True,
        errors="replace",
    )
    if completed.returncode != 0:
        return {
            "status": "failed",
            "path": str(destination),
            "sha256": None,
            "size_bytes": None,
            "stderr": completed.stderr.strip(),
        }
    if not destination.is_file():
        return {
            "status": "failed-missing-output",
            "path": str(destination),
            "sha256": None,
            "size_bytes": None,
        }
    return {
        "status": "persisted",
        "path": str(destination),
        "sha256": file_sha256(destination),
        "size_bytes": destination.stat().st_size,
    }


def copy_file_if_accessible(source: Path, destination: Path) -> dict[str, Any]:
    if not source.is_file():
        return {
            "status": "source-not-found",
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
        "path": str(destination),
        "sha256": file_sha256(destination),
        "size_bytes": destination.stat().st_size,
    }


def copy_tree_with_hashes(source: Path, destination: Path) -> dict[str, Any]:
    if not source.is_dir():
        return {
            "status": "source-not-found",
            "source": str(source),
            "path": None,
            "manifest_sha256": None,
            "file_count": 0,
        }
    files: list[dict[str, Any]] = []
    for root, directories, filenames in os.walk(source):
        root_path = Path(root)
        directories[:] = [
            name for name in directories if not (root_path / name).is_symlink()
        ]
        for name in filenames:
            source_file = root_path / name
            if source_file.is_symlink():
                raise RollbackBundleError(
                    f"Symbolic-link EFI backup source is not accepted: {source_file}"
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
        "path": str(destination),
        "manifest_sha256": sha256_payload(files),
        "file_count": len(files),
        "files": files,
    }


def efi_path_if_already_accessible(boot_state: dict[str, Any]) -> Path | None:
    for partition in boot_state.get("efi_system_partitions") or []:
        if not isinstance(partition, dict):
            continue
        drive_letter = str(partition.get("drive_letter") or "").strip()
        if not drive_letter:
            continue
        candidate = Path(f"{drive_letter}:\\EFI")
        if candidate.is_dir():
            return candidate
    return None


def copy_efi_if_accessible(
    *,
    boot_state: dict[str, Any],
    destination: Path,
) -> dict[str, Any]:
    source = efi_path_if_already_accessible(boot_state)
    if source is None:
        return {
            "status": "not-directly-accessible",
            "source": None,
            "path": None,
            "manifest_sha256": None,
            "file_count": 0,
        }
    return copy_tree_with_hashes(source, destination)


def copy_winre_if_accessible(
    *,
    reagent_stdout: str,
    destination: Path,
) -> dict[str, Any]:
    source = windows_path_from_winre_location(parse_winre_location(reagent_stdout))
    if source is None:
        return {
            "status": "location-not-directly-accessible",
            "source": None,
            "path": None,
            "sha256": None,
            "size_bytes": None,
        }
    return copy_file_if_accessible(source, destination)


def copy_reagent_config(destination: Path) -> dict[str, Any]:
    source = (
        Path(os.environ.get("WINDIR", r"C:\Windows"))
        / "System32"
        / "Recovery"
        / "ReAgent.xml"
    )
    return copy_file_if_accessible(source, destination)


def write_json_atomic(payload: dict[str, Any], destination: Path) -> None:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=destination.parent, delete=False
    ) as temporary:
        json.dump(payload, temporary, indent=2, sort_keys=True)
        temporary.write("\n")
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, destination)


def build_fixture_bundle(
    *,
    boot_state: dict[str, Any],
    rollback_manifest: dict[str, Any],
    output_dir: Path,
    bcd_export_status: dict[str, Any],
    efi_backup_status: dict[str, Any],
    winre_config_status: dict[str, Any],
    winre_status: dict[str, Any],
    created_at: str | None = None,
) -> dict[str, Any]:
    verify_boot_state(boot_state)
    verify_rollback_manifest(rollback_manifest, boot_state)
    output_dir = output_dir.resolve()
    efi_inventory_path = output_dir / "efi_partition_inventory.json"
    partition_layout_path = output_dir / "partition_layout.json"

    efi_inventory = {
        "schema": "phoenix_key.efi_partition_inventory.v1",
        "efi_system_partitions": boot_state.get("efi_system_partitions") or [],
        "secure_boot_enabled": boot_state.get("secure_boot_enabled"),
        "boot_state_snapshot_sha256": boot_state["snapshot_sha256"],
    }
    partition_layout = {
        "schema": "phoenix_key.partition_layout_snapshot.v1",
        "efi_system_partitions": boot_state.get("efi_system_partitions") or [],
        "boot_state_snapshot_sha256": boot_state["snapshot_sha256"],
    }
    write_json_atomic(efi_inventory, efi_inventory_path)
    write_json_atomic(partition_layout, partition_layout_path)

    required = {
        "partition_layout": {
            "status": "persisted",
            "path": str(partition_layout_path),
            "sha256": file_sha256(partition_layout_path),
        },
        "efi_inventory": {
            "status": "persisted",
            "path": str(efi_inventory_path),
            "sha256": file_sha256(efi_inventory_path),
        },
        "efi_file_backup": efi_backup_status,
        "bcd_store_export": bcd_export_status,
        "winre_configuration": winre_config_status,
        "winre_image": winre_status,
    }
    missing = [
        name
        for name, record in required.items()
        if record.get("status") != "persisted"
    ]
    complete = not missing
    bundle = {
        "schema": BUNDLE_SCHEMA,
        "created_at": created_at or utc_now_iso(),
        "boot_state_snapshot_sha256": boot_state["snapshot_sha256"],
        "rollback_manifest_sha256": rollback_manifest["manifest_sha256"],
        "source_identity_sha256": rollback_manifest["source"]["identity_sha256"],
        "target_identity_sha256": rollback_manifest["target"]["identity_sha256"],
        "output_directory": str(output_dir),
        "artifacts": required,
        "complete": complete,
        "missing_or_unverified_artifacts": missing,
        "system_configuration_mutated": False,
        "efi_mounted_by_bundle_tool": False,
        "repair_unlock_ready": complete,
        "repair_unlock_scope": (
            ["bcd_repair", "winre_repair", "efi_file_repair"] if complete else []
        ),
        "always_blocked_by_this_bundle": [
            "repartition_disk",
            "apply_system_image",
            "modify_secure_boot_keys",
        ],
    }
    bundle["bundle_sha256"] = sha256_payload(bundle)
    return bundle


def persist_rollback_bundle(
    *,
    boot_state: dict[str, Any],
    rollback_manifest: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    verify_boot_state(boot_state)
    verify_rollback_manifest(rollback_manifest, boot_state)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    bcd_export = run_bcd_export(output_dir / "bcd_store.bak")
    efi_backup = copy_efi_if_accessible(
        boot_state=boot_state,
        destination=output_dir / "efi",
    )
    winre_config = copy_reagent_config(output_dir / "ReAgent.xml")
    reagent_stdout = str((boot_state.get("winre") or {}).get("stdout") or "")
    winre = copy_winre_if_accessible(
        reagent_stdout=reagent_stdout,
        destination=output_dir / "Winre.wim",
    )
    bundle = build_fixture_bundle(
        boot_state=boot_state,
        rollback_manifest=rollback_manifest,
        output_dir=output_dir,
        bcd_export_status=bcd_export,
        efi_backup_status=efi_backup,
        winre_config_status=winre_config,
        winre_status=winre,
    )
    write_json_atomic(bundle, output_dir / "rollback_bundle.json")
    return bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boot-state", type=Path, required=True)
    parser.add_argument("--rollback-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    boot_state = load_json(args.boot_state)
    rollback_manifest = load_json(args.rollback_manifest)
    bundle = persist_rollback_bundle(
        boot_state=boot_state,
        rollback_manifest=rollback_manifest,
        output_dir=args.output_dir,
    )
    print(json.dumps(bundle, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RollbackBundleError, OSError, ValueError) as exc:
        print(f"ROLLBACK_BUNDLE_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
