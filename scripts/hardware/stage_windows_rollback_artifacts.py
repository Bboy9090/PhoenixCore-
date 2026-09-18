#!/usr/bin/env python3
"""Stage rollback artifacts for Windows boot repair without mutating boot state.

This helper may write only into the caller-selected rollback destination. It
exports the BCD system store to a backup file and copies already-accessible EFI
and WinRE artifacts. It never mounts an EFI partition, imports BCD, changes
WinRE configuration, or edits firmware/partition state.
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
from typing import Any

BOOT_STATE_SCHEMA = "phoenix_key.windows_boot_state.v1"
ROLLBACK_SCHEMA = "phoenix_key.rollback_manifest.v1"
ARTIFACT_SCHEMA = "phoenix_key.rollback_artifacts.v1"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
WINRE_LOCATION_RE = re.compile(
    r"(?im)^\s*Windows\s+RE\s+location\s*:\s*(\\\\\?\\GLOBALROOT\\[^\r\n]+?)\s*$"
)


class RollbackArtifactError(RuntimeError):
    """Raised when rollback artifacts cannot be staged or verified safely."""


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
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def verify_embedded_digest(
    payload: dict[str, Any],
    digest_field: str,
    *,
    expected_schema: str,
    schema_field: str = "schema",
) -> str:
    if payload.get(schema_field) != expected_schema:
        raise RollbackArtifactError(f"Unsupported {expected_schema} payload.")
    expected = str(payload.get(digest_field) or "")
    if not SHA256_RE.fullmatch(expected):
        raise RollbackArtifactError(f"{digest_field} is missing or invalid.")
    body = dict(payload)
    body.pop(digest_field, None)
    actual = sha256_payload(body)
    if actual != expected.lower():
        raise RollbackArtifactError(f"{digest_field} does not match payload contents.")
    return actual


def load_verified_json(
    path: Path,
    *,
    expected_schema: str,
    digest_field: str,
) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RollbackArtifactError(f"Evidence file could not be read: {exc}") from exc
    if not isinstance(payload, dict):
        raise RollbackArtifactError("Evidence payload is not an object.")
    verify_embedded_digest(
        payload,
        digest_field,
        expected_schema=expected_schema,
    )
    return payload


def extract_winre_location(reagentc_stdout: str) -> str | None:
    match = WINRE_LOCATION_RE.search(reagentc_stdout)
    return match.group(1).strip() if match else None


def copy_file_with_hash(source: Path, destination: Path) -> dict[str, Any]:
    if not source.is_file():
        raise RollbackArtifactError(f"Rollback source file does not exist: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "source": str(source),
        "destination": str(destination),
        "size_bytes": destination.stat().st_size,
        "sha256": file_sha256(destination),
    }


def copy_tree_with_hashes(source: Path, destination: Path) -> dict[str, Any]:
    if not source.is_dir():
        raise RollbackArtifactError(f"Rollback source directory does not exist: {source}")
    files: list[dict[str, Any]] = []
    for root, directories, filenames in os.walk(source):
        root_path = Path(root)
        directories[:] = [
            name for name in directories if not (root_path / name).is_symlink()
        ]
        for name in filenames:
            source_file = root_path / name
            if source_file.is_symlink():
                raise RollbackArtifactError(
                    f"Symbolic-link rollback source is not accepted: {source_file}"
                )
            relative = source_file.relative_to(source)
            destination_file = destination / relative
            files.append(copy_file_with_hash(source_file, destination_file))
    files.sort(key=lambda item: item["destination"])
    manifest_sha256 = sha256_payload(files)
    return {
        "source": str(source),
        "destination": str(destination),
        "file_count": len(files),
        "files": files,
        "manifest_sha256": manifest_sha256,
    }


def run_bcd_export(destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        ["bcdedit.exe", "/export", str(destination)],
        check=False,
        capture_output=True,
        text=True,
    )
    record: dict[str, Any] = {
        "returncode": int(completed.returncode),
        "stdout": completed.stdout or "",
        "stderr": completed.stderr or "",
        "destination": str(destination),
        "captured": False,
    }
    if completed.returncode == 0 and destination.is_file():
        record.update(
            {
                "captured": True,
                "size_bytes": destination.stat().st_size,
                "sha256": file_sha256(destination),
            }
        )
    return record


def accessible_efi_root(boot_state: dict[str, Any]) -> Path | None:
    partitions = boot_state.get("efi_system_partitions") or []
    for partition in partitions:
        if not isinstance(partition, dict):
            continue
        letter = str(partition.get("drive_letter") or "").strip()
        if not letter:
            continue
        candidate = Path(f"{letter}:\\EFI")
        if candidate.is_dir():
            return candidate
    return None


def stage_rollback_artifacts(
    *,
    boot_state: dict[str, Any],
    rollback_manifest: dict[str, Any],
    destination: Path,
) -> dict[str, Any]:
    if sys.platform != "win32":
        raise RollbackArtifactError("Live rollback artifact staging requires Windows.")

    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)

    bcd = run_bcd_export(destination / "bcd" / "BCD.export")

    efi_root = accessible_efi_root(boot_state)
    efi: dict[str, Any]
    if efi_root is None:
        efi = {
            "captured": False,
            "reason": "EFI System Partition is not already exposed by a drive letter; Phoenix Key will not mount it during read-only staging.",
        }
    else:
        efi = {
            "captured": True,
            **copy_tree_with_hashes(efi_root, destination / "efi"),
        }

    reagent_xml_source = (
        Path(os.environ.get("WINDIR", r"C:\Windows"))
        / "System32"
        / "Recovery"
        / "ReAgent.xml"
    )
    if reagent_xml_source.is_file():
        winre_config = {
            "captured": True,
            **copy_file_with_hash(
                reagent_xml_source,
                destination / "winre" / "ReAgent.xml",
            ),
        }
    else:
        winre_config = {
            "captured": False,
            "reason": "ReAgent.xml was not accessible at the standard online Windows location.",
        }

    winre_stdout = str(
        (boot_state.get("winre") or {}).get("stdout")
        if isinstance(boot_state.get("winre"), dict)
        else ""
    )
    winre_location = extract_winre_location(winre_stdout)
    winre_image: dict[str, Any]
    if winre_location:
        source = Path(winre_location) / "winre.wim"
        if source.is_file():
            winre_image = {
                "captured": True,
                **copy_file_with_hash(
                    source,
                    destination / "winre" / "winre.wim",
                ),
            }
        else:
            winre_image = {
                "captured": False,
                "source": str(source),
                "reason": "WinRE location was reported but winre.wim was not readable.",
            }
    else:
        winre_image = {
            "captured": False,
            "reason": "WinRE location could not be parsed from REAgentC /info output.",
        }

    receipt = {
        "schema": ARTIFACT_SCHEMA,
        "boot_state_snapshot_sha256": boot_state["snapshot_sha256"],
        "rollback_manifest_sha256": rollback_manifest["manifest_sha256"],
        "bcd_export": bcd,
        "efi_backup": efi,
        "winre_configuration": winre_config,
        "winre_image": winre_image,
        "system_mutations_performed": False,
        "efi_mount_performed": False,
        "rollback_artifacts_complete": all(
            [
                bool(bcd.get("captured")),
                bool(efi.get("captured")),
                bool(winre_config.get("captured")),
                bool(winre_image.get("captured")),
            ]
        ),
    }
    receipt["artifact_receipt_sha256"] = sha256_payload(receipt)
    return receipt


def write_json_atomic(payload: dict[str, Any], destination: Path) -> None:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=destination.parent,
        delete=False,
    ) as temporary:
        temporary.write(data)
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boot-state", type=Path, required=True)
    parser.add_argument("--rollback-manifest", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    boot_state = load_verified_json(
        args.boot_state,
        expected_schema=BOOT_STATE_SCHEMA,
        digest_field="snapshot_sha256",
    )
    rollback = load_verified_json(
        args.rollback_manifest,
        expected_schema=ROLLBACK_SCHEMA,
        digest_field="manifest_sha256",
    )
    if rollback.get("boot_state_snapshot_sha256") != boot_state.get("snapshot_sha256"):
        raise RollbackArtifactError(
            "Rollback manifest is not bound to this boot-state snapshot."
        )
    receipt = stage_rollback_artifacts(
        boot_state=boot_state,
        rollback_manifest=rollback,
        destination=args.destination,
    )
    write_json_atomic(
        receipt,
        args.destination / "rollback-artifacts.json",
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RollbackArtifactError, OSError, ValueError) as exc:
        print(f"ROLLBACK_ARTIFACT_STAGE_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
