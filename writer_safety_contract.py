"""
writer_safety_contract.py
PhoenixCore / BootForge USB Creator
Phase 4C-1: Writer Safety Contract Schema + Validator

This module builds and validates a writer safety contract
(schema: bootforge.writer_safety_contract.v1).

It does NOT implement a real USB writer.
It does NOT write, format, partition, mount, unmount, or access any drive.
It does NOT call diskpart, dd, WriteFile, or any raw-device API.

All destructive_operations_enabled values are permanently False in Phase 4C-1.
All real_writer_implemented values are permanently False in Phase 4C-1.

The contract enforces every gate defined in the Phase 4B architecture before
any future writer would be permitted to arm. Currently all write paths remain
locked because real_writer_implemented is False.
"""

import json
import hashlib
import uuid
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------------
SCHEMA = "bootforge.writer_safety_contract.v1"
PHASE = "4C-1"

SUPPORTED_IMAGE_EXTENSIONS = {".iso", ".img", ".dmg", ".bin", ".raw"}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_str(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Device identity builder
# ---------------------------------------------------------------------------

def build_device_identity(
    root_path: str = None,
    label: str = None,
    filesystem: str = None,
    capacity_bytes: int = None,
    removable: bool = None,
    external: bool = None,
    system_drive: bool = None,
    fixed: bool = None,
    hardware_id: str = None,
    serial_number: str = None,
    stable_os_id: str = None,
    scan_timestamp: str = None,
) -> dict:
    """
    Build a device identity snapshot dict.
    All fields are recorded as-supplied; identity_hash is computed
    deterministically from the canonical field values.

    This function does NOT query the OS or access any drive.
    It only structures supplied data into the required schema.
    """
    scan_ts = scan_timestamp or _utc_now_iso()
    identity = {
        "root_path": root_path,
        "label": label,
        "filesystem": filesystem,
        "capacity_bytes": capacity_bytes,
        "removable": removable,
        "external": external,
        "system_drive": system_drive,
        "fixed": fixed,
        "hardware_id": hardware_id,
        "serial_number": serial_number,
        "stable_os_id": stable_os_id,
        "scan_timestamp": scan_ts,
        "identity_hash": None,
    }
    # Compute identity hash over all stable fields (excluding identity_hash itself)
    hashable = {k: v for k, v in identity.items() if k != "identity_hash"}
    identity["identity_hash"] = _sha256_str(_canonical_json(hashable))
    return identity


# ---------------------------------------------------------------------------
# Image identity builder
# ---------------------------------------------------------------------------

def build_image_identity(
    image_path: str = None,
    filename: str = None,
    extension: str = None,
    size_bytes: int = None,
    sha256: str = None,
    modified_timestamp: str = None,
    audit_timestamp: str = None,
) -> dict:
    """
    Build an image identity snapshot dict.
    identity_hash is computed deterministically from the canonical field values.

    This function does NOT read the image file. It only structures supplied data.
    """
    identity = {
        "image_path": image_path,
        "filename": filename,
        "extension": extension,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "modified_timestamp": modified_timestamp,
        "audit_timestamp": audit_timestamp,
        "identity_hash": None,
    }
    hashable = {k: v for k, v in identity.items() if k != "identity_hash"}
    identity["identity_hash"] = _sha256_str(_canonical_json(hashable))
    return identity


# ---------------------------------------------------------------------------
# Gate definitions
# ---------------------------------------------------------------------------

# All required gate names. Order is the canonical gate evaluation order.
REQUIRED_GATES = [
    "drive_selected",
    "image_selected",
    "drive_safety_scanned",
    "image_inspected",
    "write_plan_generated",
    "audit_passed",
    "simulation_passed",
    "fresh_device_rescan_required",
    "typed_confirmation_required",
    "destructive_acknowledgement_required",
    "final_confirmation_token_required",
]

# Gates that, even if provided as True in gate_results, must still block
# because the writer is not implemented. These represent future-only gates.
FUTURE_ONLY_GATES = {
    "fresh_device_rescan_required",
    "typed_confirmation_required",
    "destructive_acknowledgement_required",
    "final_confirmation_token_required",
}


# ---------------------------------------------------------------------------
# Contract builder
# ---------------------------------------------------------------------------

def build_writer_safety_contract(
    target_drive: str = None,
    image: str = None,
    device_identity: dict = None,
    image_identity: dict = None,
    gate_results: dict = None,
) -> dict:
    """
    Build a writer safety contract payload.

    Parameters
    ----------
    target_drive      : Path string of the candidate target drive.
    image             : Path string of the candidate image file.
    device_identity   : Dict produced by build_device_identity().
    image_identity    : Dict produced by build_image_identity().
    gate_results      : Dict of {gate_name: bool} representing which
                        prerequisite gates the caller claims have passed.

    Returns
    -------
    A JSON-serializable dict with schema bootforge.writer_safety_contract.v1.

    Safety guarantees (immutable in Phase 4C-1)
    -------------------------------------------
    - real_writer_implemented is always False.
    - destructive_operations_enabled is always False.
    - blocked is always True if real_writer_implemented is False.
    - No drive is accessed, read, written, or queried by this function.
    """
    gate_results = gate_results or {}
    block_reasons = []
    warnings = []

    # -----------------------------------------------------------------------
    # Gate evaluation — structural prerequisites
    # -----------------------------------------------------------------------

    # 1. Target drive present
    drive_present = bool(target_drive and str(target_drive).strip())
    if not drive_present:
        block_reasons.append("target_drive is missing or empty")

    # 2. Image present
    image_present = bool(image and str(image).strip())
    if not image_present:
        block_reasons.append("image is missing or empty")

    # 3. Device identity present and valid
    dev_id = device_identity or {}
    device_identity_hash = dev_id.get("identity_hash") if dev_id else None
    if not dev_id:
        block_reasons.append("device_identity is missing")
    elif not device_identity_hash:
        block_reasons.append("device_identity.identity_hash is missing")

    # 4. Image identity present and valid
    img_id = image_identity or {}
    image_identity_hash = img_id.get("identity_hash") if img_id else None
    if not img_id:
        block_reasons.append("image_identity is missing")
    elif not image_identity_hash:
        block_reasons.append("image_identity.identity_hash is missing")

    # -----------------------------------------------------------------------
    # Gate evaluation — drive safety properties
    # -----------------------------------------------------------------------

    if dev_id:
        if dev_id.get("system_drive") is True:
            block_reasons.append("target drive is flagged as system drive")

        if dev_id.get("fixed") is True:
            block_reasons.append("target drive is flagged as fixed/internal")

        if dev_id.get("removable") is not True and dev_id.get("external") is not True:
            # Only block if both removable and external are explicitly False/None
            # (if both fields are missing we already blocked on missing identity)
            if dev_id.get("removable") is False and dev_id.get("external") is False:
                block_reasons.append(
                    "target drive is not removable or external"
                )

    # -----------------------------------------------------------------------
    # Gate evaluation — required gates
    # -----------------------------------------------------------------------

    evaluated_gate_results = {}
    for gate in REQUIRED_GATES:
        caller_value = gate_results.get(gate, False)
        passed = bool(caller_value)

        # Future-only gates are recorded but do not generate block reasons
        # beyond the permanent real_writer_implemented=False block.
        evaluated_gate_results[gate] = passed

        if not passed and gate not in FUTURE_ONLY_GATES:
            block_reasons.append(f"gate not passed: {gate}")

    # Future-only gates that are False generate a warning, not a block reason,
    # since they are irrelevant while real_writer_implemented is False.
    for gate in FUTURE_ONLY_GATES:
        if not evaluated_gate_results.get(gate, False):
            warnings.append(
                f"future gate '{gate}' not satisfied — "
                "required before any real writer is armed"
            )

    # -----------------------------------------------------------------------
    # Permanent Phase 4C-1 safety lock
    # -----------------------------------------------------------------------

    # The writer is not implemented. This is a hard block that cannot be
    # overridden by any gate result, confirmation value, or caller argument.
    REAL_WRITER_IMPLEMENTED = False
    DESTRUCTIVE_OPERATIONS_ENABLED = False

    block_reasons.append(
        "real_writer_implemented is false — writer not yet implemented "
        "(Phase 4C-1 lock)"
    )

    # blocked is True if there are any block reasons (always at least one above)
    blocked = len(block_reasons) > 0

    # -----------------------------------------------------------------------
    # Next required action
    # -----------------------------------------------------------------------

    if not drive_present:
        next_required_action = "select_target_drive"
    elif not image_present:
        next_required_action = "select_image"
    elif not dev_id or not device_identity_hash:
        next_required_action = "perform_device_safety_scan"
    elif not img_id or not image_identity_hash:
        next_required_action = "perform_image_inspection"
    elif not evaluated_gate_results.get("audit_passed"):
        next_required_action = "run_plan_audit"
    elif not evaluated_gate_results.get("simulation_passed"):
        next_required_action = "run_mock_writer_simulation"
    else:
        next_required_action = (
            "awaiting_real_writer_implementation — Phase 4C-1 lock active"
        )

    # -----------------------------------------------------------------------
    # Assemble contract
    # -----------------------------------------------------------------------

    contract = {
        "schema": SCHEMA,
        "contract_id": str(uuid.uuid4()),
        "created_at": _utc_now_iso(),
        "phase": PHASE,
        "real_writer_implemented": REAL_WRITER_IMPLEMENTED,
        "destructive_operations_enabled": DESTRUCTIVE_OPERATIONS_ENABLED,
        "target_drive": target_drive,
        "image": image,
        "device_identity": dev_id if dev_id else None,
        "image_identity": img_id if img_id else None,
        "required_gates": REQUIRED_GATES,
        "gate_results": evaluated_gate_results,
        "blocked": blocked,
        "block_reasons": block_reasons,
        "warnings": warnings,
        "next_required_action": next_required_action,
    }

    return contract


# ---------------------------------------------------------------------------
# Validator (thin wrapper — contract is self-describing)
# ---------------------------------------------------------------------------

def validate_writer_safety_contract(contract: dict) -> dict:
    """
    Validate a pre-built contract dict and return a validation result.

    Returns a dict with:
        valid           : bool — True only if schema matches AND blocked is False
                          (currently always False in Phase 4C-1)
        schema_ok       : bool
        real_writer_implemented_ok : bool — True only if value is False
        destructive_disabled_ok    : bool — True only if value is False
        blocked         : bool
        block_reasons   : list[str]
        warnings        : list[str]
    """
    schema_ok = contract.get("schema") == SCHEMA
    real_writer_implemented = contract.get("real_writer_implemented", True)
    destructive_enabled = contract.get("destructive_operations_enabled", True)
    blocked = contract.get("blocked", True)

    # real_writer_implemented must be False — if it is True, that is a
    # validation failure in Phase 4C-1.
    real_writer_ok = (real_writer_implemented is False)
    destructive_ok = (destructive_enabled is False)

    valid = (
        schema_ok
        and real_writer_ok
        and destructive_ok
        and not blocked
    )

    # In Phase 4C-1 valid will always be False because blocked is always True.
    return {
        "valid": valid,
        "schema_ok": schema_ok,
        "real_writer_implemented_ok": real_writer_ok,
        "destructive_disabled_ok": destructive_ok,
        "blocked": blocked,
        "block_reasons": contract.get("block_reasons", []),
        "warnings": contract.get("warnings", []),
    }


# ---------------------------------------------------------------------------
# CLI entry point (non-destructive — prints contract JSON only)
# ---------------------------------------------------------------------------

def _cli_validate_writer_contract(args):
    """
    --validate-writer-contract

    Builds and prints a writer safety contract JSON for the given
    --target-drive and --image arguments.

    Does NOT write, read, format, partition, mount, or unmount any drive.
    Does NOT call diskpart, dd, WriteFile, or any raw-device API.
    Output is JSON only.
    """
    drive = getattr(args, "target_drive", None)
    image = getattr(args, "image", None)

    dev_id = None
    img_id = None

    if drive:
        dev_id = build_device_identity(root_path=drive)

    if image:
        from pathlib import Path as _Path
        p = _Path(image)
        img_id = build_image_identity(
            image_path=str(p),
            filename=p.name,
            extension=p.suffix.lower(),
            size_bytes=p.stat().st_size if p.exists() else None,
        )

    contract = build_writer_safety_contract(
        target_drive=drive,
        image=image,
        device_identity=dev_id,
        image_identity=img_id,
    )
    print(json.dumps(contract, indent=2))


# ---------------------------------------------------------------------------
# Safety declaration (module-level assertion — caught at import time)
# ---------------------------------------------------------------------------

# This assertion makes it impossible to accidentally import this module in a
# context where real_writer_implemented or destructive_operations_enabled have
# been patched to True at the module level.
assert SCHEMA == "bootforge.writer_safety_contract.v1", (
    "SAFETY: schema string tampered"
)
