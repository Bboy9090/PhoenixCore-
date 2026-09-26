#!/usr/bin/env python3
r"""Orchestrate Phoenix Key's read-only Windows Recovery Forge hardware campaign.

This harness never formats, repartitions, mounts, dismounts, writes to, or restores
the target. It records evidence around operator-performed physical reconnect and
substitution events and refuses to promote fixture receipts into hardware proof.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

HARDWARE_DIR = Path(__file__).resolve().parent
if str(HARDWARE_DIR) not in sys.path:
    sys.path.insert(0, str(HARDWARE_DIR))

import capture_windows_drive_evidence as drive_evidence
import capture_windows_restore_rollback as rollback_capture

SCHEMA = "phoenix_key.windows_recovery_hardware_campaign.v1"
ROLLBACK_SCHEMA = "phoenix_key.restore_target_rollback_capture.v1"
BOOT_METADATA_SCHEMA = "phoenix_key.restore_target_boot_metadata.v1"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class HardwareCampaignError(RuntimeError):
    """Raised when the hardware campaign cannot advance safely."""


def canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


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


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise HardwareCampaignError(f"{path} is not a JSON object.")
    return payload


def verify_embedded_sha256(
    payload: dict[str, Any],
    *,
    schema_key: str,
    schema: str,
    digest_field: str,
) -> None:
    if payload.get(schema_key) != schema:
        raise HardwareCampaignError(
            f"Unsupported evidence schema: {payload.get(schema_key)}"
        )
    expected = str(payload.get(digest_field) or "").lower()
    if not SHA256_RE.fullmatch(expected):
        raise HardwareCampaignError(f"{digest_field} is missing or invalid.")
    unsigned = dict(payload)
    unsigned.pop(digest_field, None)
    if sha256_payload(unsigned) != expected:
        raise HardwareCampaignError(f"{digest_field} does not match its contents.")


def verify_drive_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    try:
        disk = rollback_capture.verify_drive_evidence(receipt)
    except rollback_capture.RollbackCaptureError as exc:
        raise HardwareCampaignError(str(exc)) from exc
    if (
        receipt.get("bytes_written") != 0
        or receipt.get("physical_write_attempted") is not False
    ):
        raise HardwareCampaignError(
            "Drive receipt does not prove read-only inspection."
        )
    return disk


def live_drive_receipt(receipt: dict[str, Any]) -> bool:
    verify_drive_receipt(receipt)
    return (
        receipt.get("evidence_source") == "live"
        and receipt.get("hardware_observed") is True
    )


def verify_rollback_receipt(receipt: dict[str, Any]) -> None:
    verify_embedded_sha256(
        receipt,
        schema_key="schema",
        schema=ROLLBACK_SCHEMA,
        digest_field="receipt_sha256",
    )
    if (
        receipt.get("target_bytes_written") != 0
        or receipt.get("target_write_attempted") is not False
        or receipt.get("system_mutations_performed") is not False
        or receipt.get("restore_unlock_ready") is not False
    ):
        raise HardwareCampaignError(
            "Rollback receipt does not preserve the required read-only locks."
        )


def verify_boot_metadata_receipt(receipt: dict[str, Any]) -> None:
    verify_embedded_sha256(
        receipt,
        schema_key="schema",
        schema=BOOT_METADATA_SCHEMA,
        digest_field="receipt_sha256",
    )
    if (
        receipt.get("target_bytes_written") != 0
        or receipt.get("target_write_attempted") is not False
        or receipt.get("partition_mount_or_assignment_attempted") is not False
        or receipt.get("system_mutations_performed") is not False
        or receipt.get("restore_unlock_ready") is not False
    ):
        raise HardwareCampaignError(
            "Boot-metadata receipt does not preserve the required read-only locks."
        )


def manifest_sha256(manifest: dict[str, Any]) -> str:
    unsigned = dict(manifest)
    unsigned.pop("manifest_sha256", None)
    return sha256_payload(unsigned)


def refresh_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    baseline = manifest["baseline"]
    rollback = manifest.get("rollback_capture")
    reconnect = manifest.get("reconnect")
    substitution = manifest.get("substitution")
    boot = manifest.get("boot_metadata")
    authority = manifest.get("authority_report")

    collection_gates = {
        "baseline_live_hardware": bool(
            baseline.get("hardware_observed")
            and baseline.get("evidence_source") == "live"
        ),
        "rollback_live_zero_write": bool(
            rollback
            and rollback.get("hardware_observed")
            and rollback.get("evidence_source") == "live"
            and rollback.get("target_bytes_written") == 0
            and rollback.get("target_write_attempted") is False
        ),
        "reconnect_same_hardware": bool(
            reconnect
            and reconnect.get("operator_confirmed_physical_reconnect")
            and reconnect.get("hardware_observed")
            and reconnect.get("same_stable_hardware")
        ),
        "reenumeration_observed": bool(
            reconnect
            and reconnect.get("operator_confirmed_physical_reconnect")
            and reconnect.get("hardware_observed")
            and reconnect.get("same_stable_hardware")
            and (
                reconnect.get("snapshot_changed")
                or reconnect.get("target_path_changed")
            )
        ),
        "substitution_rejection_proven": bool(
            substitution
            and substitution.get("operator_confirmed_physical_substitution")
            and substitution.get("hardware_observed")
            and substitution.get("stable_identity_differs")
        ),
        "boot_metadata_live_read_only": bool(
            boot
            and boot.get("hardware_observed")
            and boot.get("evidence_source") == "live"
            and boot.get("target_bytes_written") == 0
            and boot.get("target_write_attempted") is False
            and boot.get("partition_mount_or_assignment_attempted") is False
        ),
    }

    collection_complete = all(collection_gates.values())
    authority_complete = bool(
        authority
        and authority.get("campaign_complete") is True
        and authority.get("fixture_evidence_rejected") is True
        and authority.get("restore_executable") is False
        and authority.get("destructive_authorization_granted") is False
        and authority.get("system_mutations_performed") is False
    )

    manifest["gates"] = collection_gates
    manifest["collection_complete"] = collection_complete
    manifest["hardware_campaign_complete"] = collection_complete and authority_complete
    manifest["restore_executor_authorized"] = False
    manifest["system_mutations_performed"] = False
    manifest["outstanding_requirements"] = [
        name for name, satisfied in collection_gates.items() if not satisfied
    ]
    if collection_complete and not authority_complete:
        manifest["outstanding_requirements"].append(
            "hardware_campaign_authority_report"
        )
    if manifest["hardware_campaign_complete"]:
        manifest["next_required_action"] = "run_final_non_executable_preflight"
    elif collection_complete:
        manifest["next_required_action"] = "generate_hardware_campaign_authority_report"
    else:
        manifest["next_required_action"] = "collect_remaining_physical_evidence"
    manifest["manifest_sha256"] = manifest_sha256(manifest)
    return manifest


def build_campaign_manifest(baseline_receipt: dict[str, Any]) -> dict[str, Any]:
    disk = verify_drive_receipt(baseline_receipt)
    stable = str(disk.get("stable_identity_sha256") or "").lower()
    snapshot = str(disk.get("identity_sha256") or "").lower()
    if not SHA256_RE.fullmatch(stable) or not SHA256_RE.fullmatch(snapshot):
        raise HardwareCampaignError(
            "Baseline target requires valid snapshot and stable identities."
        )

    manifest = {
        "schema": SCHEMA,
        "campaign_id": baseline_receipt["receipt_sha256"][:24],
        "baseline": {
            "target": str(disk.get("target") or ""),
            "snapshot_identity_sha256": snapshot,
            "stable_identity_sha256": stable,
            "receipt_sha256": baseline_receipt["receipt_sha256"],
            "evidence_source": baseline_receipt.get("evidence_source"),
            "hardware_observed": baseline_receipt.get("hardware_observed") is True,
        },
        "rollback_capture": None,
        "reconnect": None,
        "substitution": None,
        "boot_metadata": None,
        "authority_report": None,
        "operator_actions_are_not_software_inferred": True,
        "restore_executor_authorized": False,
        "system_mutations_performed": False,
    }
    return refresh_manifest(manifest)


def record_rollback_capture(
    manifest: dict[str, Any], receipt: dict[str, Any]
) -> dict[str, Any]:
    verify_rollback_receipt(receipt)
    baseline = manifest["baseline"]
    if (
        str(receipt.get("target_snapshot_identity_sha256") or "").lower()
        != baseline["snapshot_identity_sha256"]
        or str(receipt.get("target_stable_identity_sha256") or "").lower()
        != baseline["stable_identity_sha256"]
    ):
        raise HardwareCampaignError(
            "Rollback capture is not bound to the campaign baseline target."
        )
    destination = str(
        receipt.get("rollback_destination_stable_identity_sha256") or ""
    ).lower()
    if destination == baseline["stable_identity_sha256"]:
        raise HardwareCampaignError(
            "Rollback destination stable identity equals the restore target."
        )

    manifest["rollback_capture"] = {
        "receipt_sha256": receipt["receipt_sha256"],
        "evidence_source": receipt.get("evidence_source"),
        "hardware_observed": receipt.get("hardware_observed") is True,
        "target_bytes_written": receipt.get("target_bytes_written"),
        "target_write_attempted": receipt.get("target_write_attempted"),
        "rollback_destination_stable_identity_sha256": destination,
    }
    return refresh_manifest(manifest)


def record_reconnect(
    manifest: dict[str, Any],
    current_receipt: dict[str, Any],
    *,
    operator_confirmed: bool,
) -> dict[str, Any]:
    disk = verify_drive_receipt(current_receipt)
    if not operator_confirmed:
        raise HardwareCampaignError(
            "Physical reconnect must be explicitly confirmed by the operator."
        )
    baseline = manifest["baseline"]
    current_stable = str(disk.get("stable_identity_sha256") or "").lower()
    current_snapshot = str(disk.get("identity_sha256") or "").lower()
    same_stable = current_stable == baseline["stable_identity_sha256"]
    if not same_stable:
        raise HardwareCampaignError(
            "Reconnect observation did not return the baseline stable hardware."
        )

    manifest["reconnect"] = {
        "operator_confirmed_physical_reconnect": True,
        "target": str(disk.get("target") or ""),
        "snapshot_identity_sha256": current_snapshot,
        "stable_identity_sha256": current_stable,
        "same_stable_hardware": True,
        "snapshot_changed": current_snapshot != baseline["snapshot_identity_sha256"],
        "target_path_changed": str(disk.get("target") or "").upper()
        != str(baseline["target"]).upper(),
        "evidence_source": current_receipt.get("evidence_source"),
        "hardware_observed": current_receipt.get("hardware_observed") is True,
        "receipt_sha256": current_receipt["receipt_sha256"],
    }
    return refresh_manifest(manifest)


def record_substitution(
    manifest: dict[str, Any],
    candidate_receipt: dict[str, Any],
    *,
    operator_confirmed: bool,
) -> dict[str, Any]:
    disk = verify_drive_receipt(candidate_receipt)
    if not operator_confirmed:
        raise HardwareCampaignError(
            "Physical substitution must be explicitly confirmed by the operator."
        )
    baseline = manifest["baseline"]
    candidate_stable = str(disk.get("stable_identity_sha256") or "").lower()
    if not SHA256_RE.fullmatch(candidate_stable):
        raise HardwareCampaignError(
            "Substitution candidate lacks a valid stable hardware identity."
        )
    differs = candidate_stable != baseline["stable_identity_sha256"]
    if not differs:
        raise HardwareCampaignError(
            "Substitution candidate is the baseline target, not different hardware."
        )

    manifest["substitution"] = {
        "operator_confirmed_physical_substitution": True,
        "candidate_target": str(disk.get("target") or ""),
        "candidate_stable_identity_sha256": candidate_stable,
        "stable_identity_differs": True,
        "evidence_source": candidate_receipt.get("evidence_source"),
        "hardware_observed": candidate_receipt.get("hardware_observed") is True,
        "receipt_sha256": candidate_receipt["receipt_sha256"],
    }
    return refresh_manifest(manifest)


def record_boot_metadata(
    manifest: dict[str, Any], receipt: dict[str, Any]
) -> dict[str, Any]:
    verify_boot_metadata_receipt(receipt)
    baseline = manifest["baseline"]
    if (
        str(receipt.get("target_stable_identity_sha256") or "").lower()
        != baseline["stable_identity_sha256"]
    ):
        raise HardwareCampaignError(
            "Boot-metadata receipt is not bound to the campaign target."
        )

    manifest["boot_metadata"] = {
        "receipt_sha256": receipt["receipt_sha256"],
        "evidence_source": receipt.get("evidence_source"),
        "hardware_observed": receipt.get("hardware_observed") is True,
        "resolved": receipt.get("resolved") is True,
        "missing_or_unverified": receipt.get("missing_or_unverified") or [],
        "target_bytes_written": receipt.get("target_bytes_written"),
        "target_write_attempted": receipt.get("target_write_attempted"),
        "partition_mount_or_assignment_attempted": receipt.get(
            "partition_mount_or_assignment_attempted"
        ),
    }
    return refresh_manifest(manifest)


def record_authority_report(
    manifest: dict[str, Any], report: dict[str, Any]
) -> dict[str, Any]:
    verify_embedded_sha256(
        report,
        schema_key="schema",
        schema="phoenix_key.recovery_hardware_campaign_report.v1",
        digest_field="report_sha256",
    )
    if (
        report.get("restore_executable") is not False
        or report.get("destructive_authorization_granted") is not False
        or report.get("system_mutations_performed") is not False
    ):
        raise HardwareCampaignError(
            "Hardware authority report violated the non-executable safety boundary."
        )

    manifest["authority_report"] = {
        "report_sha256": report["report_sha256"],
        "campaign_complete": report.get("campaign_complete") is True,
        "fixture_evidence_rejected": report.get("fixture_evidence_rejected") is True,
        "restore_executable": report.get("restore_executable") is True,
        "destructive_authorization_granted": (
            report.get("destructive_authorization_granted") is True
        ),
        "system_mutations_performed": (
            report.get("system_mutations_performed") is True
        ),
        "blockers": report.get("blockers") or [],
    }
    return refresh_manifest(manifest)


def campaign_paths(campaign_dir: Path) -> tuple[Path, Path]:
    root = campaign_dir.resolve()
    return root, root / "hardware-campaign-manifest.json"


def load_manifest(campaign_dir: Path) -> tuple[Path, Path, dict[str, Any]]:
    root, manifest_path = campaign_paths(campaign_dir)
    if not manifest_path.is_file():
        raise HardwareCampaignError(
            f"Campaign manifest does not exist: {manifest_path}"
        )
    manifest = load_json(manifest_path)
    if manifest.get("schema") != SCHEMA:
        raise HardwareCampaignError("Unsupported hardware campaign schema.")
    expected = str(manifest.get("manifest_sha256") or "")
    if not SHA256_RE.fullmatch(expected):
        raise HardwareCampaignError("Campaign manifest SHA-256 is invalid.")
    if manifest_sha256(manifest) != expected.lower():
        raise HardwareCampaignError("Campaign manifest checksum is invalid.")
    return root, manifest_path, manifest


def capture_live_drive(target: str, source_commit: str) -> dict[str, Any]:
    number = drive_evidence.parse_raw_target(target)
    raw = drive_evidence.query_windows_disk(number)
    probe = drive_evidence.probe_exclusive_read_handle(target)
    return drive_evidence.build_receipt(
        target=target,
        raw_disk=raw,
        evidence_source="live",
        source_commit=source_commit,
        exclusive_probe=probe,
    )


def save_manifest(manifest: dict[str, Any], manifest_path: Path) -> None:
    write_json_atomic(refresh_manifest(manifest), manifest_path)


def command_baseline(args: argparse.Namespace) -> dict[str, Any]:
    root, manifest_path = campaign_paths(args.campaign_dir)
    if manifest_path.exists():
        raise HardwareCampaignError(
            "Campaign manifest already exists; refusing to overwrite evidence."
        )
    root.mkdir(parents=True, exist_ok=True)
    receipt = capture_live_drive(args.target, args.source_commit)
    write_json_atomic(receipt, root / "baseline-drive-evidence.json")
    manifest = build_campaign_manifest(receipt)
    save_manifest(manifest, manifest_path)
    return manifest


def command_record_rollback(args: argparse.Namespace) -> dict[str, Any]:
    _, manifest_path, manifest = load_manifest(args.campaign_dir)
    receipt = load_json(args.receipt)
    manifest = record_rollback_capture(manifest, receipt)
    save_manifest(manifest, manifest_path)
    return manifest


def command_reconnect(args: argparse.Namespace) -> dict[str, Any]:
    root, manifest_path, manifest = load_manifest(args.campaign_dir)
    receipt = capture_live_drive(args.current_target, args.source_commit)
    write_json_atomic(receipt, root / "reconnect-drive-evidence.json")
    manifest = record_reconnect(
        manifest,
        receipt,
        operator_confirmed=args.operator_confirmed_physical_reconnect,
    )
    save_manifest(manifest, manifest_path)
    return manifest


def command_substitution(args: argparse.Namespace) -> dict[str, Any]:
    root, manifest_path, manifest = load_manifest(args.campaign_dir)
    receipt = capture_live_drive(args.candidate_target, args.source_commit)
    write_json_atomic(receipt, root / "substitution-drive-evidence.json")
    manifest = record_substitution(
        manifest,
        receipt,
        operator_confirmed=args.operator_confirmed_physical_substitution,
    )
    save_manifest(manifest, manifest_path)
    return manifest


def command_record_boot(args: argparse.Namespace) -> dict[str, Any]:
    _, manifest_path, manifest = load_manifest(args.campaign_dir)
    receipt = load_json(args.receipt)
    manifest = record_boot_metadata(manifest, receipt)
    save_manifest(manifest, manifest_path)
    return manifest


def command_record_authority(args: argparse.Namespace) -> dict[str, Any]:
    _, manifest_path, manifest = load_manifest(args.campaign_dir)
    report = load_json(args.report)
    manifest = record_authority_report(manifest, report)
    save_manifest(manifest, manifest_path)
    return manifest


def command_status(args: argparse.Namespace) -> dict[str, Any]:
    _, _, manifest = load_manifest(args.campaign_dir)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    baseline = subparsers.add_parser("baseline")
    baseline.add_argument("--target", required=True)
    baseline.add_argument("--campaign-dir", type=Path, required=True)
    baseline.add_argument(
        "--source-commit", default=os.environ.get("GITHUB_SHA", "unknown")
    )
    baseline.set_defaults(handler=command_baseline)

    rollback = subparsers.add_parser("record-rollback")
    rollback.add_argument("--campaign-dir", type=Path, required=True)
    rollback.add_argument("--receipt", type=Path, required=True)
    rollback.set_defaults(handler=command_record_rollback)

    reconnect = subparsers.add_parser("reconnect")
    reconnect.add_argument("--campaign-dir", type=Path, required=True)
    reconnect.add_argument("--current-target", required=True)
    reconnect.add_argument(
        "--operator-confirmed-physical-reconnect", action="store_true"
    )
    reconnect.add_argument(
        "--source-commit", default=os.environ.get("GITHUB_SHA", "unknown")
    )
    reconnect.set_defaults(handler=command_reconnect)

    substitution = subparsers.add_parser("substitution")
    substitution.add_argument("--campaign-dir", type=Path, required=True)
    substitution.add_argument("--candidate-target", required=True)
    substitution.add_argument(
        "--operator-confirmed-physical-substitution", action="store_true"
    )
    substitution.add_argument(
        "--source-commit", default=os.environ.get("GITHUB_SHA", "unknown")
    )
    substitution.set_defaults(handler=command_substitution)

    boot = subparsers.add_parser("record-boot-metadata")
    boot.add_argument("--campaign-dir", type=Path, required=True)
    boot.add_argument("--receipt", type=Path, required=True)
    boot.set_defaults(handler=command_record_boot)

    authority = subparsers.add_parser("record-authority-report")
    authority.add_argument("--campaign-dir", type=Path, required=True)
    authority.add_argument("--report", type=Path, required=True)
    authority.set_defaults(handler=command_record_authority)

    status = subparsers.add_parser("status")
    status.add_argument("--campaign-dir", type=Path, required=True)
    status.set_defaults(handler=command_status)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = args.handler(args)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        HardwareCampaignError,
        rollback_capture.RollbackCaptureError,
        drive_evidence.EvidenceError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"RECOVERY_HARDWARE_CAMPAIGN_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
