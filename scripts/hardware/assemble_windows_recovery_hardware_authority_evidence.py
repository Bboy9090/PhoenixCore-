#!/usr/bin/env python3
"""Assemble real Windows Recovery Forge hardware evidence for Rust authority review.

This tool only reads JSON receipts and writes one combined JSON package. It does
not inspect, mount, dismount, format, repartition, or write any physical disk.
Fixture-tagged hardware receipts are rejected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

SCHEMA = "phoenix_key.recovery_hardware_campaign_evidence_package.v1"
DRIVE_SCHEMA = "bws.physical-drive-evidence/v1"
ROLLBACK_CAPTURE_SCHEMA = "phoenix_key.restore_target_rollback_capture.v1"
REENUMERATION_SCHEMA = "phoenix_key.recovery_target_reenumeration_receipt.v1"
BOOT_METADATA_SCHEMA = "phoenix_key.restore_target_boot_metadata.v1"
DATA_PRESERVATION_SCHEMA = "phoenix_key.target_data_preservation_receipt.v1"


class AuthorityEvidenceError(RuntimeError):
    """Raised when a hardware authority package is incomplete or unsafe."""


def canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuthorityEvidenceError(f"{label} is not readable JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise AuthorityEvidenceError(f"{label} must be a JSON object.")
    return payload


def require_schema(
    payload: dict[str, Any],
    *,
    label: str,
    expected: str,
    field: str = "schema",
) -> None:
    if payload.get(field) != expected:
        raise AuthorityEvidenceError(
            f"{label} has unsupported schema: {payload.get(field)!r}"
        )


def require_live_hardware(payload: dict[str, Any], label: str) -> None:
    if (
        payload.get("evidence_source") != "live"
        or payload.get("hardware_observed") is not True
    ):
        raise AuthorityEvidenceError(
            f"{label} is not live observed hardware evidence."
        )
    if payload.get("platform") == "fixture":
        raise AuthorityEvidenceError(f"{label} is fixture evidence.")


def require_read_only_drive(payload: dict[str, Any], label: str) -> None:
    require_schema(
        payload,
        label=label,
        expected=DRIVE_SCHEMA,
        field="schema_version",
    )
    require_live_hardware(payload, label)
    if (
        payload.get("bytes_written") != 0
        or payload.get("physical_write_attempted") is not False
    ):
        raise AuthorityEvidenceError(f"{label} does not prove read-only inspection.")


def require_reenumeration_receipt(payload: dict[str, Any], label: str) -> None:
    require_schema(payload, label=label, expected=REENUMERATION_SCHEMA)
    if payload.get("system_mutations_performed") is not False:
        raise AuthorityEvidenceError(f"{label} reports system mutation.")


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


def build_package(args: argparse.Namespace) -> dict[str, Any]:
    baseline = load_object(args.baseline_target_drive, "baseline target drive evidence")
    rollback_destination = load_object(
        args.rollback_destination, "rollback destination verification"
    )
    rollback_capture = load_object(args.rollback_capture, "rollback capture receipt")
    reconnect_drive = load_object(
        args.reconnect_target_drive, "reconnect target drive evidence"
    )
    reconnect_receipt = load_object(
        args.reconnect_receipt, "reconnect re-enumeration receipt"
    )
    post_safety = load_object(
        args.post_reanalysis_target_safety, "post-reanalysis target safety"
    )
    post_verification = load_object(
        args.post_reanalysis_target_verification,
        "post-reanalysis target verification",
    )
    substitution_drive = load_object(
        args.substitution_target_drive, "substitution target drive evidence"
    )
    substitution_receipt = load_object(
        args.substitution_receipt, "substitution re-enumeration receipt"
    )
    boot_metadata = load_object(args.boot_metadata, "boot metadata receipt")
    data_preservation = load_object(
        args.data_preservation, "data preservation receipt"
    )

    for payload, label in [
        (baseline, "baseline target drive evidence"),
        (reconnect_drive, "reconnect target drive evidence"),
        (substitution_drive, "substitution target drive evidence"),
    ]:
        require_read_only_drive(payload, label)

    require_schema(
        rollback_capture,
        label="rollback capture receipt",
        expected=ROLLBACK_CAPTURE_SCHEMA,
    )
    require_live_hardware(rollback_capture, "rollback capture receipt")
    if (
        rollback_capture.get("target_bytes_written") != 0
        or rollback_capture.get("target_write_attempted") is not False
        or rollback_capture.get("system_mutations_performed") is not False
        or rollback_capture.get("restore_unlock_ready") is not False
    ):
        raise AuthorityEvidenceError(
            "rollback capture receipt does not preserve the zero-write safety boundary."
        )

    require_reenumeration_receipt(
        reconnect_receipt, "reconnect re-enumeration receipt"
    )
    require_reenumeration_receipt(
        substitution_receipt, "substitution re-enumeration receipt"
    )

    require_schema(
        boot_metadata,
        label="boot metadata receipt",
        expected=BOOT_METADATA_SCHEMA,
    )
    require_live_hardware(boot_metadata, "boot metadata receipt")
    if (
        boot_metadata.get("target_bytes_written") != 0
        or boot_metadata.get("target_write_attempted") is not False
        or boot_metadata.get("partition_mount_or_assignment_attempted") is not False
        or boot_metadata.get("system_mutations_performed") is not False
        or boot_metadata.get("restore_unlock_ready") is not False
    ):
        raise AuthorityEvidenceError(
            "boot metadata receipt does not preserve the read-only safety boundary."
        )

    require_schema(
        data_preservation,
        label="data preservation receipt",
        expected=DATA_PRESERVATION_SCHEMA,
    )
    if (
        data_preservation.get("restore_unlock_ready") is not False
        or data_preservation.get("system_mutations_performed") is not False
    ):
        raise AuthorityEvidenceError(
            "data preservation receipt violates the non-executable boundary."
        )

    if rollback_destination.get("system_mutations_performed") is not False:
        raise AuthorityEvidenceError(
            "rollback destination verification reports system mutation."
        )
    if post_verification.get("system_mutations_performed") is not False:
        raise AuthorityEvidenceError(
            "post-reanalysis target verification reports system mutation."
        )

    package = {
        "schema": SCHEMA,
        "baseline_target_drive_evidence": baseline,
        "rollback_destination_verification": rollback_destination,
        "rollback_capture_receipt": rollback_capture,
        "reconnect_target_drive_evidence": reconnect_drive,
        "reconnect_reenumeration_receipt": reconnect_receipt,
        "post_reanalysis_target_safety": post_safety,
        "post_reanalysis_target_verification": post_verification,
        "substitution_target_drive_evidence": substitution_drive,
        "substitution_reenumeration_receipt": substitution_receipt,
        "boot_metadata_receipt": boot_metadata,
        "data_preservation_receipt": data_preservation,
        "fixture_evidence_allowed": False,
        "restore_executable": False,
        "destructive_authorization_granted": False,
        "system_mutations_performed": False,
    }
    package["package_sha256"] = sha256_payload(package)
    return package


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-target-drive", type=Path, required=True)
    parser.add_argument("--rollback-destination", type=Path, required=True)
    parser.add_argument("--rollback-capture", type=Path, required=True)
    parser.add_argument("--reconnect-target-drive", type=Path, required=True)
    parser.add_argument("--reconnect-receipt", type=Path, required=True)
    parser.add_argument("--post-reanalysis-target-safety", type=Path, required=True)
    parser.add_argument(
        "--post-reanalysis-target-verification", type=Path, required=True
    )
    parser.add_argument("--substitution-target-drive", type=Path, required=True)
    parser.add_argument("--substitution-receipt", type=Path, required=True)
    parser.add_argument("--boot-metadata", type=Path, required=True)
    parser.add_argument("--data-preservation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    package = build_package(args)
    if args.output.exists():
        raise AuthorityEvidenceError(
            "authority evidence output already exists; refusing to overwrite it."
        )
    write_json_atomic(package, args.output)
    print(json.dumps(package, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AuthorityEvidenceError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"HARDWARE_AUTHORITY_EVIDENCE_FAILED: {exc}", file=os.sys.stderr)
        raise SystemExit(2) from exc
