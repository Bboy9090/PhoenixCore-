#!/usr/bin/env python3
"""Build a checkpointed Windows boot-repair plan from proven recovery evidence.

This module plans only. It never executes BCDBoot, BCDEdit mutations, REAgentC
mutations, firmware writes, partition changes, or a destructive restore.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

READINESS_SCHEMA = "phoenix_key.windows_recovery_readiness.v1"
PLAN_SCHEMA = "phoenix_key.windows_boot_repair_plan.v1"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")

SUPPORTED_REPAIRS = {
    "bcd_repair": {
        "summary": "Repair the Windows BCD/boot configuration using the detected Windows installation and preserved rollback evidence.",
        "actions": [
            "identify_target_windows_installation",
            "identify_existing_efi_system_partition",
            "rebuild_or_repair_bcd_store_from_detected_windows",
            "verify_boot_entries_after_repair",
        ],
        "required_artifacts": ["bcd_store_export", "efi_inventory", "partition_layout"],
    },
    "winre_relink": {
        "summary": "Repair Windows Recovery Environment registration without replacing the operating system.",
        "actions": [
            "identify_existing_winre_image",
            "verify_winre_image_identity",
            "relink_winre_configuration",
            "verify_winre_enabled_and_location",
        ],
        "required_artifacts": ["winre_image", "partition_layout"],
    },
    "efi_boot_files_repair": {
        "summary": "Repair signed Windows EFI boot files on the existing EFI System Partition.",
        "actions": [
            "identify_existing_efi_system_partition",
            "verify_windows_source_and_architecture",
            "verify_signed_windows_boot_files",
            "stage_signed_boot_files_to_existing_efi_partition",
            "verify_secure_boot_compatibility",
        ],
        "required_artifacts": ["efi_inventory", "partition_layout", "bcd_store_export"],
    },
}


class RepairPlanError(RuntimeError):
    """Raised when a repair plan cannot be safely built."""


def canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RepairPlanError(f"Could not read readiness evidence: {exc}") from exc
    if not isinstance(value, dict):
        raise RepairPlanError("Readiness evidence must be a JSON object.")
    return value


def verify_readiness(readiness: dict[str, Any]) -> None:
    if readiness.get("schema") != READINESS_SCHEMA:
        raise RepairPlanError("Unsupported recovery-readiness schema.")
    expected = str(readiness.get("readiness_sha256") or "")
    if not SHA256_RE.fullmatch(expected):
        raise RepairPlanError("Recovery-readiness SHA-256 is missing or invalid.")
    body = dict(readiness)
    body.pop("readiness_sha256", None)
    if sha256_payload(body) != expected.lower():
        raise RepairPlanError("Recovery-readiness SHA-256 does not match its contents.")
    if readiness.get("repair_planning_ready") is not True:
        raise RepairPlanError("Recovery evidence is not ready for repair planning.")
    if readiness.get("destructive_restore_unlocked") is not False:
        raise RepairPlanError("Destructive restore must remain locked during repair planning.")


def build_repair_plan(
    *,
    readiness: dict[str, Any],
    repair_kind: str,
) -> dict[str, Any]:
    verify_readiness(readiness)
    definition = SUPPORTED_REPAIRS.get(repair_kind)
    if definition is None:
        raise RepairPlanError(
            f"Unsupported repair kind. Choose one of: {', '.join(sorted(SUPPORTED_REPAIRS))}"
        )

    plan = {
        "schema": PLAN_SCHEMA,
        "repair_kind": repair_kind,
        "summary": definition["summary"],
        "source_identity_sha256": readiness.get("source_identity_sha256"),
        "target_identity_sha256": readiness.get("target_identity_sha256"),
        "boot_state_snapshot_sha256": readiness.get("boot_state_snapshot_sha256"),
        "rollback_bundle_sha256": readiness.get("rollback_bundle_sha256"),
        "required_rollback_artifacts": definition["required_artifacts"],
        "planned_actions": definition["actions"],
        "checkpoints": [
            "recheck_source_identity_immediately_before_repair",
            "recheck_target_identity_immediately_before_repair",
            "recapture_boot_state_and_compare_snapshot",
            "revalidate_rollback_bundle_and_artifact_hashes",
            "verify_repair_specific_source_and_boot_mode_compatibility",
            "require_explicit_repair_authorization",
        ],
        "execution_enabled": False,
        "destructive_restore_unlocked": False,
        "system_mutations_performed": False,
        "next_stage": "repair-specific-preflight-evidence",
    }
    plan["plan_sha256"] = sha256_payload(plan)
    return plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness", type=Path, required=True)
    parser.add_argument("--repair-kind", choices=sorted(SUPPORTED_REPAIRS), required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = build_repair_plan(
        readiness=load_json(args.readiness),
        repair_kind=args.repair_kind,
    )
    print(json.dumps(plan, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RepairPlanError, OSError, ValueError) as exc:
        print(f"BOOT_REPAIR_PLAN_BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
