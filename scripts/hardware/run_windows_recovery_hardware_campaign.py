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
import compare_windows_drive_reenumeration as drive_compare
import resolve_windows_source_disk as source_disk

SCHEMA = "phoenix_key.windows_recovery_hardware_campaign.v1"
NEXT_STEP_SCHEMA = "phoenix_key.windows_recovery_hardware_next_step.v1"
PREFLIGHT_SCHEMA = "phoenix_key.windows_recovery_hardware_preflight.v1"
ROLLBACK_SCHEMA = "phoenix_key.restore_target_rollback_capture.v1"
BOOT_METADATA_SCHEMA = "phoenix_key.restore_target_boot_metadata.v1"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
SOURCE_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{40}$")


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


def preflight_sha256(report: dict[str, Any]) -> str:
    unsigned = dict(report)
    unsigned.pop("preflight_sha256", None)
    return sha256_payload(unsigned)


def verify_preflight_report(
    report: dict[str, Any],
    *,
    campaign_dir: Path,
    target_receipt: dict[str, Any],
) -> None:
    if report.get("schema") != PREFLIGHT_SCHEMA:
        raise HardwareCampaignError("Unsupported hardware campaign preflight schema.")
    expected = str(report.get("preflight_sha256") or "").lower()
    if not SHA256_RE.fullmatch(expected):
        raise HardwareCampaignError("Hardware campaign preflight SHA-256 is invalid.")
    if preflight_sha256(report) != expected:
        raise HardwareCampaignError("Hardware campaign preflight checksum is invalid.")
    if report.get("ready_for_hardware_campaign") is not True:
        raise HardwareCampaignError("Hardware campaign preflight is not ready.")
    if report.get("block_reasons") not in ([], None):
        raise HardwareCampaignError(
            "Hardware campaign preflight still has block reasons."
        )
    if (
        report.get("restore_executor_authorized") is not False
        or report.get("target_write_attempted") is not False
        or report.get("system_mutations_performed") is not False
    ):
        raise HardwareCampaignError(
            "Hardware campaign preflight does not preserve read-only safety locks."
        )

    expected_dir = os.path.normcase(os.path.normpath(str(campaign_dir.resolve())))
    reported_dir = os.path.normcase(
        os.path.normpath(str(report.get("campaign_dir") or ""))
    )
    if reported_dir != expected_dir:
        raise HardwareCampaignError(
            "Hardware campaign preflight belongs to a different campaign directory."
        )

    disk = verify_drive_receipt(target_receipt)
    current_target = str(disk.get("target") or "").upper()
    current_snapshot = str(disk.get("identity_sha256") or "").lower()
    current_stable = str(disk.get("stable_identity_sha256") or "").lower()
    if current_target != str(report.get("target") or "").upper():
        raise HardwareCampaignError(
            "Baseline target path does not match the hardware campaign preflight."
        )
    if (
        current_snapshot
        != str(report.get("target_snapshot_identity_sha256") or "").lower()
    ):
        raise HardwareCampaignError(
            "Baseline target snapshot changed after hardware campaign preflight."
        )
    if current_stable != str(report.get("target_stable_identity_sha256") or "").lower():
        raise HardwareCampaignError(
            "Baseline stable hardware identity does not match preflight."
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

    gates = {
        "baseline_live_hardware": bool(
            baseline.get("hardware_observed")
            and baseline.get("evidence_source") == "live"
        ),
        "rollback_live_zero_write": bool(
            rollback
            and rollback.get("source_commit") == manifest.get("source_commit")
            and rollback.get("hardware_observed")
            and rollback.get("evidence_source") == "live"
            and rollback.get("target_bytes_written") == 0
            and rollback.get("target_write_attempted") is False
        ),
        "reconnect_same_hardware": bool(
            reconnect
            and reconnect.get("operator_confirmed_physical_reconnect")
            and reconnect.get("hardware_observed")
            and reconnect.get("evidence_source") == "live"
            and reconnect.get("same_stable_hardware")
            and reconnect.get("comparison_trusted")
        ),
        "reenumeration_observed": bool(
            reconnect
            and reconnect.get("operator_confirmed_physical_reconnect")
            and reconnect.get("hardware_observed")
            and reconnect.get("same_stable_hardware")
            and reconnect.get("comparison_trusted")
            and reconnect.get("stale_authorization_rejected")
            and (
                reconnect.get("snapshot_changed")
                or reconnect.get("target_path_changed")
            )
        ),
        "substitution_rejection_proven": bool(
            substitution
            and substitution.get("operator_confirmed_physical_substitution")
            and substitution.get("hardware_observed")
            and substitution.get("evidence_source") == "live"
            and substitution.get("stable_identity_differs")
            and substitution.get("comparison_trusted")
            and substitution.get("classification")
            == "hardware-substitution-or-mismatch"
            and substitution.get("stale_authorization_reusable") is False
        ),
        "boot_metadata_live_read_only": bool(
            boot
            and boot.get("source_commit") == manifest.get("source_commit")
            and boot.get("hardware_observed")
            and boot.get("evidence_source") == "live"
            and boot.get("target_bytes_written") == 0
            and boot.get("target_write_attempted") is False
            and boot.get("partition_mount_or_assignment_attempted") is False
        ),
    }

    manifest["gates"] = gates
    manifest["hardware_campaign_complete"] = all(gates.values())
    manifest["restore_executor_authorized"] = False
    manifest["system_mutations_performed"] = False
    manifest["outstanding_requirements"] = [
        name for name, satisfied in gates.items() if not satisfied
    ]
    if manifest["hardware_campaign_complete"]:
        manifest["next_required_action"] = (
            "resolve_data_preservation_then_run_final_non_executable_preflight"
        )
    else:
        manifest["next_required_action"] = "collect_remaining_physical_evidence"
    manifest["manifest_sha256"] = manifest_sha256(manifest)
    return manifest


def build_campaign_manifest(baseline_receipt: dict[str, Any]) -> dict[str, Any]:
    disk = verify_drive_receipt(baseline_receipt)
    source_commit = str(baseline_receipt.get("source_commit") or "").lower()
    if not SOURCE_COMMIT_RE.fullmatch(source_commit):
        raise HardwareCampaignError(
            "Baseline drive receipt requires a valid source commit."
        )
    stable = str(disk.get("stable_identity_sha256") or "").lower()
    snapshot = str(disk.get("identity_sha256") or "").lower()
    if not SHA256_RE.fullmatch(stable) or not SHA256_RE.fullmatch(snapshot):
        raise HardwareCampaignError(
            "Baseline target requires valid snapshot and stable identities."
        )

    manifest = {
        "schema": SCHEMA,
        "campaign_id": baseline_receipt["receipt_sha256"][:24],
        "source_commit": source_commit,
        "baseline": {
            "target": str(disk.get("target") or ""),
            "snapshot_identity_sha256": snapshot,
            "stable_identity_sha256": stable,
            "receipt_sha256": baseline_receipt["receipt_sha256"],
            "source_commit": source_commit,
            "evidence_source": baseline_receipt.get("evidence_source"),
            "hardware_observed": baseline_receipt.get("hardware_observed") is True,
        },
        "rollback_capture": None,
        "reconnect": None,
        "substitution": None,
        "boot_metadata": None,
        "operator_actions_are_not_software_inferred": True,
        "restore_executor_authorized": False,
        "system_mutations_performed": False,
    }
    return refresh_manifest(manifest)


def record_rollback_capture(
    manifest: dict[str, Any], receipt: dict[str, Any]
) -> dict[str, Any]:
    verify_rollback_receipt(receipt)
    expected_source_commit = str(manifest.get("source_commit") or "").lower()
    receipt_source_commit = str(receipt.get("source_commit") or "").lower()
    if (
        not SOURCE_COMMIT_RE.fullmatch(expected_source_commit)
        or receipt_source_commit != expected_source_commit
    ):
        raise HardwareCampaignError(
            "Rollback capture receipt was produced by a different source commit."
        )
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
        "source_commit": receipt_source_commit,
        "rollback_contract_sha256": str(
            receipt.get("rollback_contract_sha256") or ""
        ).lower(),
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
    comparison: dict[str, Any],
    *,
    operator_confirmed: bool,
) -> dict[str, Any]:
    disk = verify_drive_receipt(current_receipt)
    if not operator_confirmed:
        raise HardwareCampaignError(
            "Physical reconnect must be explicitly confirmed by the operator."
        )
    baseline = manifest["baseline"]
    expected_source_commit = str(manifest.get("source_commit") or "").lower()
    current_source_commit = str(current_receipt.get("source_commit") or "").lower()
    if (
        not SOURCE_COMMIT_RE.fullmatch(expected_source_commit)
        or current_source_commit != expected_source_commit
    ):
        raise HardwareCampaignError(
            "Reconnect drive receipt was captured by a different source commit."
        )
    current_stable = str(disk.get("stable_identity_sha256") or "").lower()
    current_snapshot = str(disk.get("identity_sha256") or "").lower()
    same_stable = current_stable == baseline["stable_identity_sha256"]
    if not same_stable:
        raise HardwareCampaignError(
            "Reconnect observation did not return the baseline stable hardware."
        )

    if comparison.get("schema") != drive_compare.COMPARISON_SCHEMA:
        raise HardwareCampaignError("Reconnect comparison uses an unsupported schema.")
    if comparison.get("comparison_trusted") is not True:
        raise HardwareCampaignError("Reconnect comparison is not trusted.")
    if comparison.get("real_hardware_evidence") is not True:
        raise HardwareCampaignError(
            "Reconnect comparison is not live hardware evidence."
        )
    if comparison.get("same_hardware") is not True:
        raise HardwareCampaignError(
            "Reconnect comparison did not prove the same hardware."
        )
    if comparison.get("stale_authorization_reusable") is not False:
        raise HardwareCampaignError(
            "Reconnect comparison did not reject stale authorization."
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
        "source_commit": current_source_commit,
        "comparison_sha256": comparison["comparison_sha256"],
        "comparison_trusted": comparison.get("comparison_trusted") is True,
        "stale_authorization_rejected": comparison.get("stale_authorization_reusable")
        is False,
        "classification": comparison.get("classification"),
    }
    return refresh_manifest(manifest)


def record_substitution(
    manifest: dict[str, Any],
    candidate_receipt: dict[str, Any],
    comparison: dict[str, Any],
    *,
    operator_confirmed: bool,
) -> dict[str, Any]:
    disk = verify_drive_receipt(candidate_receipt)
    if not operator_confirmed:
        raise HardwareCampaignError(
            "Physical substitution must be explicitly confirmed by the operator."
        )
    baseline = manifest["baseline"]
    expected_source_commit = str(manifest.get("source_commit") or "").lower()
    candidate_source_commit = str(candidate_receipt.get("source_commit") or "").lower()
    if (
        not SOURCE_COMMIT_RE.fullmatch(expected_source_commit)
        or candidate_source_commit != expected_source_commit
    ):
        raise HardwareCampaignError(
            "Substitution drive receipt was captured by a different source commit."
        )
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

    if comparison.get("schema") != drive_compare.COMPARISON_SCHEMA:
        raise HardwareCampaignError(
            "Substitution comparison uses an unsupported schema."
        )
    if comparison.get("comparison_trusted") is not True:
        raise HardwareCampaignError("Substitution comparison is not trusted.")
    if comparison.get("real_hardware_evidence") is not True:
        raise HardwareCampaignError(
            "Substitution comparison is not live hardware evidence."
        )
    if comparison.get("classification") != "hardware-substitution-or-mismatch":
        raise HardwareCampaignError(
            "Substitution comparison did not classify different hardware."
        )
    if comparison.get("stale_authorization_reusable") is not False:
        raise HardwareCampaignError(
            "Substitution comparison did not reject stale authorization."
        )

    manifest["substitution"] = {
        "operator_confirmed_physical_substitution": True,
        "candidate_target": str(disk.get("target") or ""),
        "candidate_stable_identity_sha256": candidate_stable,
        "stable_identity_differs": True,
        "evidence_source": candidate_receipt.get("evidence_source"),
        "hardware_observed": candidate_receipt.get("hardware_observed") is True,
        "receipt_sha256": candidate_receipt["receipt_sha256"],
        "source_commit": candidate_source_commit,
        "comparison_sha256": comparison["comparison_sha256"],
        "comparison_trusted": comparison.get("comparison_trusted") is True,
        "classification": comparison.get("classification"),
        "stale_authorization_reusable": comparison.get("stale_authorization_reusable"),
    }
    return refresh_manifest(manifest)


def record_boot_metadata(
    manifest: dict[str, Any], receipt: dict[str, Any]
) -> dict[str, Any]:
    verify_boot_metadata_receipt(receipt)
    expected_source_commit = str(manifest.get("source_commit") or "").lower()
    receipt_source_commit = str(receipt.get("source_commit") or "").lower()
    if (
        not SOURCE_COMMIT_RE.fullmatch(expected_source_commit)
        or receipt_source_commit != expected_source_commit
    ):
        raise HardwareCampaignError(
            "Boot-metadata receipt was produced by a different source commit."
        )
    baseline = manifest["baseline"]
    rollback = manifest.get("rollback_capture")
    if not rollback:
        raise HardwareCampaignError(
            "Boot-metadata receipt requires a recorded rollback capture first."
        )
    if (
        str(receipt.get("target_snapshot_identity_sha256") or "").lower()
        != baseline["snapshot_identity_sha256"]
        or str(receipt.get("target_stable_identity_sha256") or "").lower()
        != baseline["stable_identity_sha256"]
    ):
        raise HardwareCampaignError(
            "Boot-metadata receipt is not bound to the campaign baseline target."
        )
    if (
        str(receipt.get("rollback_capture_receipt_sha256") or "").lower()
        != str(rollback.get("receipt_sha256") or "").lower()
    ):
        raise HardwareCampaignError(
            "Boot-metadata receipt is not bound to the recorded rollback capture."
        )
    if (
        str(receipt.get("rollback_contract_sha256") or "").lower()
        != str(rollback.get("rollback_contract_sha256") or "").lower()
    ):
        raise HardwareCampaignError(
            "Boot-metadata receipt rollback contract does not match the recorded rollback capture."
        )

    manifest["boot_metadata"] = {
        "receipt_sha256": receipt["receipt_sha256"],
        "source_commit": receipt_source_commit,
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


def next_step_sha256(plan: dict[str, Any]) -> str:
    unsigned = dict(plan)
    unsigned.pop("next_step_sha256", None)
    return sha256_payload(unsigned)


def build_next_step_plan(
    manifest: dict[str, Any],
    *,
    campaign_dir: Path,
) -> dict[str, Any]:
    gates = manifest.get("gates") or {}
    baseline = manifest.get("baseline") or {}
    campaign = str(campaign_dir.resolve())
    target = str(baseline.get("target") or "")

    if not gates.get("baseline_live_hardware"):
        action = "start_new_live_campaign"
        gate = "baseline_live_hardware"
        instruction = (
            "Start a new campaign with a live external GPT target; fixture or "
            "non-live baseline evidence cannot be promoted."
        )
        command = None
        operator_confirmation_required = False
    elif not gates.get("rollback_live_zero_write"):
        action = "record_live_rollback_capture"
        gate = "rollback_live_zero_write"
        instruction = (
            "Create a fresh live read-only GPT rollback capture for the baseline "
            "target, then record its receipt."
        )
        command = (
            "python scripts/hardware/run_windows_recovery_hardware_campaign.py "
            f'record-rollback --campaign-dir "{campaign}" '
            '--receipt "<restore-rollback-capture.json>"'
        )
        operator_confirmation_required = False
    elif not gates.get("boot_metadata_live_read_only"):
        action = "record_live_boot_metadata"
        gate = "boot_metadata_live_read_only"
        instruction = (
            "Capture live boot metadata while the baseline snapshot and rollback "
            "capture are still current, then record its receipt."
        )
        command = (
            "python scripts/hardware/run_windows_recovery_hardware_campaign.py "
            f'record-boot-metadata --campaign-dir "{campaign}" '
            '--receipt "<restore-target-boot-metadata.json>"'
        )
        operator_confirmation_required = False
    elif not gates.get("reconnect_same_hardware") or not gates.get(
        "reenumeration_observed"
    ):
        action = "physically_reconnect_baseline_target"
        gate = (
            "reconnect_same_hardware"
            if not gates.get("reconnect_same_hardware")
            else "reenumeration_observed"
        )
        instruction = (
            "Physically disconnect and reconnect the baseline target, confirm the "
            "physical event, then capture the newly enumerated raw target path. "
            "If Windows returns the exact same path and snapshot, repeat later "
            "under conditions that cause real re-enumeration."
        )
        command = (
            "python scripts/hardware/run_windows_recovery_hardware_campaign.py "
            f'reconnect --campaign-dir "{campaign}" '
            '--current-target "<CURRENT_PHYSICALDRIVE>" '
            "--operator-confirmed-physical-reconnect"
        )
        operator_confirmation_required = True
    elif not gates.get("substitution_rejection_proven"):
        action = "physically_substitute_different_target"
        gate = "substitution_rejection_proven"
        instruction = (
            "Disconnect the baseline target, connect a different external disk, "
            "confirm the physical substitution, and capture that candidate path."
        )
        command = (
            "python scripts/hardware/run_windows_recovery_hardware_campaign.py "
            f'substitution --campaign-dir "{campaign}" '
            '--candidate-target "<DIFFERENT_PHYSICALDRIVE>" '
            "--operator-confirmed-physical-substitution"
        )
        operator_confirmation_required = True
    else:
        action = "resolve_data_preservation_then_final_preflight"
        gate = None
        instruction = (
            "The physical evidence campaign is complete. Resolve target-data "
            "preservation, build a fresh Recovery Evidence Bundle v2, and run the "
            "final non-executable preflight."
        )
        command = (
            "python scripts/hardware/run_windows_recovery_hardware_campaign.py "
            f'status --campaign-dir "{campaign}"'
        )
        operator_confirmation_required = False

    plan = {
        "schema": NEXT_STEP_SCHEMA,
        "campaign_dir": campaign,
        "campaign_id": manifest.get("campaign_id"),
        "baseline_target": target or None,
        "hardware_campaign_complete": manifest.get("hardware_campaign_complete")
        is True,
        "next_gate": gate,
        "action": action,
        "instruction": instruction,
        "command": command,
        "operator_confirmation_required": operator_confirmation_required,
        "restore_executor_authorized": False,
        "system_mutations_performed": False,
        "manifest_sha256": manifest.get("manifest_sha256"),
    }
    plan["next_step_sha256"] = next_step_sha256(plan)
    return plan


def command_next_step(args: argparse.Namespace) -> dict[str, Any]:
    _, _, manifest = load_manifest(args.campaign_dir)
    return build_next_step_plan(manifest, campaign_dir=args.campaign_dir)


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


def build_preflight_report(
    target_receipt: dict[str, Any],
    evidence_disk: dict[str, Any],
    *,
    campaign_dir: str,
) -> dict[str, Any]:
    disk = verify_drive_receipt(target_receipt)
    target_stable = str(disk.get("stable_identity_sha256") or "").lower()
    evidence_stable = str(evidence_disk.get("stable_identity_sha256") or "").lower()

    checks = {
        "target_live_hardware": live_drive_receipt(target_receipt),
        "target_stable_identity_available": bool(SHA256_RE.fullmatch(target_stable)),
        "target_external_bus": str(disk.get("bus_type") or "").upper()
        in drive_evidence.EXTERNAL_BUS_TYPES,
        "target_not_boot_disk": disk.get("is_boot") is False,
        "target_not_system_disk": disk.get("is_system") is False,
        "target_partition_style_gpt": str(disk.get("partition_style") or "").upper()
        == "GPT",
        "target_future_write_safety_clear": disk.get("write_candidate") is True,
        "target_zero_write_probe": target_receipt.get("bytes_written") == 0
        and target_receipt.get("physical_write_attempted") is False,
        "evidence_disk_resolved": evidence_disk.get("resolved") is True,
        "evidence_disk_stable_identity_available": bool(
            evidence_disk.get("stable_identity_available")
            and SHA256_RE.fullmatch(evidence_stable)
        ),
        "evidence_disk_distinct_from_target": bool(
            SHA256_RE.fullmatch(target_stable)
            and SHA256_RE.fullmatch(evidence_stable)
            and target_stable != evidence_stable
        ),
    }
    ready = all(checks.values())
    report = {
        "schema": PREFLIGHT_SCHEMA,
        "campaign_dir": campaign_dir,
        "target": str(disk.get("target") or ""),
        "target_snapshot_identity_sha256": disk.get("identity_sha256"),
        "target_stable_identity_sha256": target_stable or None,
        "target_bus_type": disk.get("bus_type"),
        "target_partition_style": disk.get("partition_style"),
        "evidence_physical_target": evidence_disk.get("physical_target"),
        "evidence_stable_identity_sha256": evidence_stable or None,
        "checks": checks,
        "ready_for_hardware_campaign": ready,
        "block_reasons": [name for name, passed in checks.items() if not passed],
        "restore_executor_authorized": False,
        "target_write_attempted": False,
        "system_mutations_performed": False,
    }
    report["preflight_sha256"] = preflight_sha256(report)
    return report


def command_preflight(args: argparse.Namespace) -> dict[str, Any]:
    if sys.platform != "win32":
        raise HardwareCampaignError("Hardware campaign preflight requires Windows.")
    root = args.campaign_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    target_receipt = capture_live_drive(args.target, args.source_commit)
    evidence_disk = source_disk.query_source_disk(str(root))
    report = build_preflight_report(
        target_receipt,
        evidence_disk,
        campaign_dir=str(root),
    )
    write_json_atomic(target_receipt, root / "preflight-target-drive-evidence.json")
    write_json_atomic(report, root / "hardware-campaign-preflight.json")
    if not report["ready_for_hardware_campaign"]:
        raise HardwareCampaignError(
            "Hardware campaign preflight blocked: " + ", ".join(report["block_reasons"])
        )
    return report


def command_baseline(args: argparse.Namespace) -> dict[str, Any]:
    root, manifest_path = campaign_paths(args.campaign_dir)
    if manifest_path.exists():
        raise HardwareCampaignError(
            "Campaign manifest already exists; refusing to overwrite evidence."
        )
    root.mkdir(parents=True, exist_ok=True)
    preflight_path = root / "hardware-campaign-preflight.json"
    if not preflight_path.is_file():
        raise HardwareCampaignError(
            "Hardware campaign preflight is required before baseline capture."
        )
    preflight = load_json(preflight_path)
    receipt = capture_live_drive(args.target, args.source_commit)
    verify_preflight_report(
        preflight,
        campaign_dir=root,
        target_receipt=receipt,
    )
    write_json_atomic(receipt, root / "baseline-drive-evidence.json")
    manifest = build_campaign_manifest(receipt)
    manifest["preflight_sha256"] = preflight["preflight_sha256"]
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
    baseline_receipt = load_json(root / "baseline-drive-evidence.json")
    receipt = capture_live_drive(args.current_target, args.source_commit)
    comparison = drive_compare.compare_receipts(baseline_receipt, receipt)
    write_json_atomic(receipt, root / "reconnect-drive-evidence.json")
    write_json_atomic(comparison, root / "reconnect-comparison.json")
    manifest = record_reconnect(
        manifest,
        receipt,
        comparison,
        operator_confirmed=args.operator_confirmed_physical_reconnect,
    )
    save_manifest(manifest, manifest_path)
    return manifest


def command_substitution(args: argparse.Namespace) -> dict[str, Any]:
    root, manifest_path, manifest = load_manifest(args.campaign_dir)
    baseline_receipt = load_json(root / "baseline-drive-evidence.json")
    receipt = capture_live_drive(args.candidate_target, args.source_commit)
    comparison = drive_compare.compare_receipts(baseline_receipt, receipt)
    write_json_atomic(receipt, root / "substitution-drive-evidence.json")
    write_json_atomic(comparison, root / "substitution-comparison.json")
    manifest = record_substitution(
        manifest,
        receipt,
        comparison,
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


def command_status(args: argparse.Namespace) -> dict[str, Any]:
    _, _, manifest = load_manifest(args.campaign_dir)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser("preflight")
    preflight.add_argument("--target", required=True)
    preflight.add_argument("--campaign-dir", type=Path, required=True)
    preflight.add_argument(
        "--source-commit", default=os.environ.get("GITHUB_SHA", "unknown")
    )
    preflight.set_defaults(handler=command_preflight)

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

    status = subparsers.add_parser("status")
    status.add_argument("--campaign-dir", type=Path, required=True)
    status.set_defaults(handler=command_status)

    next_step = subparsers.add_parser("next-step")
    next_step.add_argument("--campaign-dir", type=Path, required=True)
    next_step.set_defaults(handler=command_next_step)

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
        source_disk.SourceDiskResolutionError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"RECOVERY_HARDWARE_CAMPAIGN_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
