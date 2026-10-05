#!/usr/bin/env python3
"""Read-only prerequisite assessment; never executes a restore or proves a boot."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Any

_spec = importlib.util.spec_from_file_location(
    "_rehearsal_media", Path(__file__).with_name("plan_fat32_windows_media.py"))
_media = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_media)


def assess_restore_rehearsal(
    *,
    source: Path,
    expected_sha256: str,
    sandbox: Path,
    destination: Path,
    image_architecture: str,
    executor_architectures: tuple[str, ...],
    executor: Path,
    boot_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assess a new disposable VM image destination, without creating it.

    The sandbox/executor are operator-controlled configuration, not evidence of
    successful restoration. An imported boot receipt is explicitly untrusted.
    """
    blockers: list[str] = []
    actual_sha = None
    source_path = source.resolve()
    if source.is_symlink() or not source.is_file():
        blockers.append("source-not-regular-file")
    else:
        with source.open("rb") as stream:
            before = os.fstat(stream.fileno())
            digest = hashlib.sha256()
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
            after = os.fstat(stream.fileno())
        actual_sha = digest.hexdigest()
        current = source.stat()
        try:
            identity = _media.file_stat_identity
            if (identity(before) != identity(after)
                    or before.st_ctime_ns != after.st_ctime_ns
                    or identity(after) != identity(current)):
                blockers.append("source-changed-during-inspection")
        except _media.MediaPlanError:
            blockers.append("source-identity-unavailable")
        if actual_sha != expected_sha256.lower():
            blockers.append("source-integrity-mismatch")

    sandbox_path = sandbox.resolve()
    destination_path = destination.resolve()
    if sandbox.is_symlink() or not sandbox.is_dir() or sandbox_path == Path("/"):
        blockers.append("sandbox-invalid")
    if destination.exists() or destination.is_symlink():
        blockers.append("destination-must-be-new")
    if destination_path.parent != sandbox_path:
        blockers.append("destination-not-direct-sandbox-child")
    if destination_path == source_path:
        blockers.append("source-destination-collision")
    if destination.suffix.lower() not in {".qcow2", ".vhdx"}:
        blockers.append("destination-not-disposable-image")
    if image_architecture not in {"x86_64", "aarch64"}:
        blockers.append("image-architecture-unverified")
    elif image_architecture not in executor_architectures:
        blockers.append("executor-architecture-unsupported")
    if (
        executor.is_symlink()
        or not executor.is_file()
        or not os.access(executor, os.X_OK)
    ):
        blockers.append("executor-unavailable")

    binding = {
        "source_sha256": actual_sha,
        "destination": str(destination_path),
        "image_architecture": image_architecture,
        "executor": str(executor.resolve()),
    }
    binding_sha = hashlib.sha256(
        json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    receipt_bound = (
        isinstance(boot_receipt, dict)
        and boot_receipt.get("assessment_binding_sha256") == binding_sha
    )
    return {
        "schema": "arcwyre.restore_rehearsal_assessment.v1",
        **binding,
        "assessment_binding_sha256": binding_sha,
        "prerequisites_ready": not blockers,
        "block_reasons": blockers,
        "source_provenance_verified": False,
        "restore_executor_authorized": False,
        "physical_writes_authorized": False,
        "system_mutations_performed": False,
        "boot_receipt_binding_matches": receipt_bound,
        "boot_receipt_trusted": False,
        "boot_proven": False,
        "allowed_next_stage": (
            "review-virtual-restore-plan" if not blockers else "resolve-prerequisites"
        ),
    }
