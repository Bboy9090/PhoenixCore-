#!/usr/bin/env python3
"""Persist a non-destructive Windows rollback bundle before any boot repair.

The bundle is local evidence only. It never mounts the EFI System Partition,
changes BCD entries, changes WinRE configuration, writes partition tables, or
modifies firmware variables.
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


def verify_boot_state(snapshot: dict[str, Any]) -> None:
    if snapshot.get("schema") != BOOT_STATE_SCHEMA:
        raise RollbackBundleError("Unsupported boot-state snapshot schema.")
    expected = str(snapshot.get("snapshot_sha256") or "")
    if not SHA256_RE.fullmatch(expected):
        raise RollbackBundleError("Boot-state snapshot is missing its SHA-256.")
    body = dict(snapshot)
    body.pop("snapshot_sha256", None)
    if sha256_payload(body) != expected.lower():
        raise RollbackBundleError("Boot-state snapshot SHA-256 does not match its contents.")
    if snapshot.get("complete") is not True:
        raise RollbackBundleError("Boot-state snapshot is incomplete; repair must remain locked.")


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
    # reagentc often returns a device path such as
    # \\?\GLOBALROOT\device\harddisk0\partition4\Recovery\WindowsRE.
    # That is not a normal filesystem path we can safely traverse without
    # additional privileged mapping, so only accept ordinary drive-letter paths.
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
    output_dir: Path,
    bcd_export_status: dict[str, Any],
    winre_status: dict[str, Any],
    created_at: str | None = None,
) -> dict[str, Any]:
    verify_boot_state(boot_state)
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
        "bcd_store_export": bcd_export_status,
        "winre_image": winre_status,
    }
    missing = [
        name
        for name, record in required.items()
        if record.get("status") != "persisted"
    ]
    bundle = {
        "schema": BUNDLE_SCHEMA,
        "created_at": created_at or utc_now_iso(),
        "boot_state_snapshot_sha256": boot_state["snapshot_sha256"],
        "output_directory": str(output_dir),
        "artifacts": required,
        "complete": not missing,
        "missing_or_unverified_artifacts": missing,
        "system_configuration_mutated": False,
        "efi_mounted_by_bundle_tool": False,
        "repair_unlock_ready": not missing,
    }
    bundle["bundle_sha256"] = sha256_payload(bundle)
    return bundle


def persist_rollback_bundle(
    *,
    boot_state: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    verify_boot_state(boot_state)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    bcd_export = run_bcd_export(output_dir / "bcd_store.bak")
    reagent_stdout = str((boot_state.get("winre") or {}).get("stdout") or "")
    winre = copy_winre_if_accessible(
        reagent_stdout=reagent_stdout,
        destination=output_dir / "Winre.wim",
    )
    bundle = build_fixture_bundle(
        boot_state=boot_state,
        output_dir=output_dir,
        bcd_export_status=bcd_export,
        winre_status=winre,
    )
    write_json_atomic(bundle, output_dir / "rollback_bundle.json")
    return bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boot-state", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    boot_state = load_json(args.boot_state)
    bundle = persist_rollback_bundle(boot_state=boot_state, output_dir=args.output_dir)
    print(json.dumps(bundle, sort_keys=True))
    return 0 if bundle["complete"] else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RollbackBundleError, OSError, ValueError) as exc:
        print(f"ROLLBACK_BUNDLE_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
