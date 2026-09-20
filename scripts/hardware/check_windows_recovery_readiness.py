#!/usr/bin/env python3
"""Evaluate whether Windows recovery may advance from evidence to repair planning.

This gate authorizes only the next repair-planning stage. It never authorizes a
destructive restore and performs no system mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
SOURCE_SCHEMA = "phoenix_key.recovery_source_identity.v1"
TARGET_SCHEMA = "bws.physical-drive-evidence/v1"
BOOT_SCHEMA = "phoenix_key.windows_boot_state.v1"
BUNDLE_SCHEMA = "phoenix_key.rollback_bundle.v1"
COLLISION_SCHEMA = "phoenix_key.source_target_collision_check.v1"
READINESS_SCHEMA = "phoenix_key.windows_recovery_readiness.v1"


class RecoveryReadinessError(RuntimeError):
    """Raised when evidence files are malformed rather than merely incomplete."""


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
        raise RecoveryReadinessError(f"Could not read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RecoveryReadinessError(f"{path} must contain a JSON object.")
    return value


def verify_embedded_hash(
    payload: dict[str, Any],
    field: str,
    *,
    required: bool = True,
) -> bool:
    expected = str(payload.get(field) or "")
    if not SHA256_RE.fullmatch(expected):
        if required:
            raise RecoveryReadinessError(f"{field} is missing or invalid.")
        return False
    body = dict(payload)
    body.pop(field, None)
    return sha256_payload(body) == expected.lower()


def build_recovery_readiness(
    *,
    source_identity: dict[str, Any],
    target_evidence: dict[str, Any],
    boot_state: dict[str, Any],
    rollback_bundle: dict[str, Any],
    collision_check: dict[str, Any],
) -> dict[str, Any]:
    block_reasons: list[str] = []

    if source_identity.get("schema") != SOURCE_SCHEMA:
        block_reasons.append("source-identity-schema-invalid")
    if source_identity.get("complete") is not True:
        block_reasons.append("source-identity-incomplete")
    source_sha = str(source_identity.get("sha256") or "")
    if not SHA256_RE.fullmatch(source_sha):
        block_reasons.append("source-identity-sha256-invalid")

    if target_evidence.get("schema_version") != TARGET_SCHEMA:
        block_reasons.append("target-evidence-schema-invalid")
    target_disk = target_evidence.get("disk")
    if not isinstance(target_disk, dict):
        block_reasons.append("target-disk-evidence-missing")
        target_disk = {}
    if target_disk.get("write_candidate") is not True:
        block_reasons.append("target-not-safe-write-candidate")
    target_sha = str(target_disk.get("identity_sha256") or "")
    if not SHA256_RE.fullmatch(target_sha):
        block_reasons.append("target-identity-sha256-invalid")
    target_stable_sha = str(target_disk.get("stable_identity_sha256") or "")
    if not SHA256_RE.fullmatch(target_stable_sha):
        block_reasons.append("target-stable-identity-sha256-invalid")

    if boot_state.get("schema") != BOOT_SCHEMA:
        block_reasons.append("boot-state-schema-invalid")
    if boot_state.get("complete") is not True:
        block_reasons.append("boot-state-incomplete")
    boot_sha = str(boot_state.get("snapshot_sha256") or "")
    if not SHA256_RE.fullmatch(boot_sha):
        block_reasons.append("boot-state-sha256-invalid")
    elif not verify_embedded_hash(boot_state, "snapshot_sha256", required=False):
        block_reasons.append("boot-state-sha256-mismatch")

    if rollback_bundle.get("schema") != BUNDLE_SCHEMA:
        block_reasons.append("rollback-bundle-schema-invalid")
    if rollback_bundle.get("complete") is not True:
        block_reasons.append("rollback-bundle-incomplete")
    if rollback_bundle.get("repair_unlock_ready") is not True:
        block_reasons.append("rollback-bundle-not-ready")
    bundle_sha = str(rollback_bundle.get("bundle_sha256") or "")
    if not SHA256_RE.fullmatch(bundle_sha):
        block_reasons.append("rollback-bundle-sha256-invalid")
    elif not verify_embedded_hash(rollback_bundle, "bundle_sha256", required=False):
        block_reasons.append("rollback-bundle-sha256-mismatch")
    if rollback_bundle.get("boot_state_snapshot_sha256") != boot_sha:
        block_reasons.append("rollback-bundle-boot-state-mismatch")
    if rollback_bundle.get("source_identity_sha256") != source_sha:
        block_reasons.append("rollback-bundle-source-identity-mismatch")
    if rollback_bundle.get("target_identity_sha256") != target_sha:
        block_reasons.append("rollback-bundle-target-identity-mismatch")
    if rollback_bundle.get("target_stable_identity_sha256") != target_stable_sha:
        block_reasons.append("rollback-bundle-target-stable-identity-mismatch")

    if collision_check.get("schema") != COLLISION_SCHEMA:
        block_reasons.append("source-target-collision-schema-invalid")
    if collision_check.get("source_target_distinct") is not True:
        block_reasons.append("source-target-not-proven-distinct")
    if collision_check.get("blocked") is not False:
        block_reasons.append("source-target-collision-blocked")
    if (
        collision_check.get("target_physical_target")
        and target_disk.get("target")
        and str(collision_check["target_physical_target"]).upper()
        != str(target_disk["target"]).upper()
    ):
        block_reasons.append("collision-proof-target-mismatch")

    source_size = int(source_identity.get("size_bytes") or 0)
    target_size = int(target_disk.get("size_bytes") or 0)
    if source_size <= 0:
        block_reasons.append("source-size-invalid")
    if target_size < source_size:
        block_reasons.append("target-capacity-smaller-than-source")

    ready = not block_reasons
    result = {
        "schema": READINESS_SCHEMA,
        "repair_planning_ready": ready,
        "destructive_restore_unlocked": False,
        "allowed_next_stage": (
            "build-checkpointed-repair-plan" if ready else "resolve-evidence-blocks"
        ),
        "source_identity_sha256": source_sha or None,
        "target_identity_sha256": target_sha or None,
        "target_stable_identity_sha256": target_stable_sha or None,
        "boot_state_snapshot_sha256": boot_sha or None,
        "rollback_bundle_sha256": bundle_sha or None,
        "block_reasons": block_reasons,
        "system_mutations_performed": False,
    }
    result["readiness_sha256"] = sha256_payload(result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-identity", type=Path, required=True)
    parser.add_argument("--target-evidence", type=Path, required=True)
    parser.add_argument("--boot-state", type=Path, required=True)
    parser.add_argument("--rollback-bundle", type=Path, required=True)
    parser.add_argument("--collision-check", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_recovery_readiness(
        source_identity=load_json(args.source_identity),
        target_evidence=load_json(args.target_evidence),
        boot_state=load_json(args.boot_state),
        rollback_bundle=load_json(args.rollback_bundle),
        collision_check=load_json(args.collision_check),
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["repair_planning_ready"] else 3


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RecoveryReadinessError, OSError, ValueError) as exc:
        print(f"RECOVERY_READINESS_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
