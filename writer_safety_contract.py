"""
writer_safety_contract.py
PhoenixCore / BootForge USB Creator
Phase 4C-1/4C-2: Writer Safety Contract Schema + Validator + Preview Bridge

This module builds and validates a writer safety contract
(schema: bootforge.writer_safety_contract.v1).

It does NOT implement a real USB writer.
It does NOT write, format, partition, mount, unmount, or access any drive.
It does NOT call diskpart, dd, WriteFile, or any raw-device API.

All destructive_operations_enabled values are permanently False.
All real_writer_implemented values are permanently False.

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
# Preview bridge — used by CLI and dashboard API route
# ---------------------------------------------------------------------------

def build_contract_preview_payload(
    target_drive: str = None,
    image: str = None,
    audit_passed: bool = False,
    simulation_passed: bool = False,
    typed_confirmation: str = None,
    destructive_acknowledgement: str = None,
) -> dict:
    """
    Build a read-only writer safety contract preview payload.

    This is the single entry-point used by both the CLI
    (--validate-writer-contract) and the dashboard API route
    (GET /api/write/contract).

    It builds minimal device/image identity from path metadata only.
    It does NOT open, read, query, mount, or write to any drive.
    It does NOT call diskpart, dd, WriteFile, or any raw-device API.
    Output is always blocked in Phase 4C-2 (real_writer_implemented=False).

    Parameters
    ----------
    target_drive             : Path string of candidate target drive.
    image                    : Path string of candidate image file.
    audit_passed             : Whether the caller reports audit gate as passed.
    simulation_passed        : Whether the caller reports simulation gate as passed.
    typed_confirmation       : Typed confirmation phrase (future gate — not checked here).
    destructive_acknowledgement : Typed acknowledgement (future gate — not checked here).

    Returns
    -------
    JSON-serializable dict with schema bootforge.writer_safety_contract.v1.
    Always blocked. Never enables real writing.
    """
    from pathlib import Path as _Path

    dev_id = None
    img_id = None

    if target_drive and str(target_drive).strip():
        dev_id = build_device_identity(root_path=str(target_drive).strip())

    if image and str(image).strip():
        p = _Path(str(image).strip())
        img_id = build_image_identity(
            image_path=str(p),
            filename=p.name,
            extension=p.suffix.lower() if p.suffix else None,
            size_bytes=p.stat().st_size if p.exists() else None,
        )

    # Build gate_results from the caller-supplied context.
    # Future-only gates (typed confirmation / destructive acknowledgement)
    # are recorded but do not unlock any writer.
    gate_results = {
        "drive_selected": bool(target_drive and str(target_drive).strip()),
        "image_selected": bool(image and str(image).strip()),
        "drive_safety_scanned": bool(dev_id),
        "image_inspected": bool(img_id),
        "write_plan_generated": bool(audit_passed),  # plan must precede audit
        "audit_passed": bool(audit_passed),
        "simulation_passed": bool(simulation_passed),
        # Future confirmation gates — present but do not affect Phase 4C-2 blocking
        "fresh_device_rescan_required": False,
        "typed_confirmation_required": bool(typed_confirmation and str(typed_confirmation).strip()),
        "destructive_acknowledgement_required": bool(
            destructive_acknowledgement and str(destructive_acknowledgement).strip()
        ),
        "final_confirmation_token_required": False,
    }

    contract = build_writer_safety_contract(
        target_drive=target_drive,
        image=image,
        device_identity=dev_id,
        image_identity=img_id,
        gate_results=gate_results,
    )
    contract["session_id"] = build_writer_contract_session_id(contract)
    return contract


# ---------------------------------------------------------------------------
# CLI entry point (non-destructive — prints contract JSON only)
# ---------------------------------------------------------------------------

def _cli_validate_writer_contract(args):
    """
    --validate-writer-contract

    Builds and prints a writer safety contract JSON preview.
    Accepts optional gate flags: --audit-passed, --simulation-passed,
    --typed-confirmation, --destructive-acknowledgement.

    Does NOT write, read, format, partition, mount, or unmount any drive.
    Does NOT call diskpart, dd, WriteFile, or any raw-device API.
    Output is JSON only.
    """
    contract = build_contract_preview_payload(
        target_drive=getattr(args, "target_drive", None),
        image=getattr(args, "image", None),
        audit_passed=bool(getattr(args, "audit_passed", False)),
        simulation_passed=bool(getattr(args, "simulation_passed", False)),
        typed_confirmation=getattr(args, "typed_confirmation", None),
        destructive_acknowledgement=getattr(args, "destructive_acknowledgement", None),
    )
    
    # Check if CLI requested contract export or ledger append
    export_json_path = getattr(args, "export_writer_contract_json", None)
    export_md_path = getattr(args, "export_writer_contract_markdown", None)
    ledger_path = getattr(args, "append_writer_contract_ledger", None)
    
    export_res = None
    if export_json_path:
        export_res = export_writer_contract_json(contract, export_json_path)
    elif export_md_path:
        export_res = export_writer_contract_markdown(contract, export_md_path)
        
    if ledger_path:
        # Build ledger record with optional export_res if it occurred
        record = build_writer_contract_ledger_record(contract, "cli_preview_action", export_result=export_res)
        res = append_writer_contract_ledger_record(record, ledger_path)
        print(json.dumps(res, indent=2))
    else:
        if export_res:
            print(json.dumps(export_res, indent=2))
        else:
            print(json.dumps(contract, indent=2))


# ---------------------------------------------------------------------------
# Contract Evidence Export Helpers
# ---------------------------------------------------------------------------

def generate_writer_contract_markdown(contract_payload: dict) -> str:
    """
    Generate a human-readable Markdown summary of the writer safety contract.
    """
    status_emoji = "⛔ BLOCKED" if contract_payload.get("blocked") else "✓ UNBLOCKED"
    
    # Format gate results
    gate_results = contract_payload.get("gate_results", {})
    gates_list = []
    for g in contract_payload.get("required_gates", []):
        val = gate_results.get(g, False)
        mark = "✓ PASS" if val else "— PENDING"
        gates_list.append(f"- **{g}**: {mark}")
    gates_str = "\n".join(gates_list)
    
    # Format block reasons
    reasons_list = contract_payload.get("block_reasons", [])
    reasons_str = "\n".join(f"- {r}" for r in reasons_list) if reasons_list else "None"
    
    # Format warnings
    warnings_list = contract_payload.get("warnings", [])
    warnings_str = "\n".join(f"- {w}" for w in warnings_list) if warnings_list else "None"
    
    # Format device/image details
    dev = contract_payload.get("device_identity") or {}
    img = contract_payload.get("image_identity") or {}
    
    device_str = (
        f"- **Root Path**: {dev.get('root_path') or 'N/A'}\n"
        f"- **Label**: {dev.get('label') or 'N/A'}\n"
        f"- **Filesystem**: {dev.get('filesystem') or 'N/A'}\n"
        f"- **Capacity**: {dev.get('capacity_bytes') or 0} bytes\n"
        f"- **System Drive**: {dev.get('system_drive') or False}\n"
        f"- **Stable OS ID**: {dev.get('stable_os_id') or 'N/A'}\n"
        f"- **Identity Hash**: `{dev.get('identity_hash') or 'N/A'}`"
    ) if dev else "N/A"
    
    image_str = (
        f"- **Image Path**: {img.get('image_path') or 'N/A'}\n"
        f"- **Filename**: {img.get('filename') or 'N/A'}\n"
        f"- **Extension**: {img.get('extension') or 'N/A'}\n"
        f"- **Size**: {img.get('size_bytes') or 0} bytes\n"
        f"- **SHA256**: {img.get('sha256') or 'N/A'}\n"
        f"- **Identity Hash**: `{img.get('identity_hash') or 'N/A'}`"
    ) if img else "N/A"

    md = f"""# PhoenixCore / BootForge Writer Safety Contract Report

## General Info
- **Contract ID**: {contract_payload.get("contract_id")}
- **Schema**: {contract_payload.get("schema")}
- **Phase**: {contract_payload.get("phase")}
- **Created At**: {contract_payload.get("created_at")}
- **Blocked State**: {status_emoji}
- **Target Drive**: {contract_payload.get("target_drive") or "N/A"}
- **Image File**: {contract_payload.get("image") or "N/A"}

---

## Immutable Safety Parameters
- **real_writer_implemented**: {contract_payload.get("real_writer_implemented")}
- **destructive_operations_enabled**: {contract_payload.get("destructive_operations_enabled")}

---

## Gate Results Checklist
{gates_str}

---

## Device Identity
{device_str}

---

## Image Identity
{image_str}

---

## Block Reasons
{reasons_str}

---

## Warnings
{warnings_str}

---

## Read-Only Safety Statement
> [!IMPORTANT]
> **This report is evidence of a read-only safety contract preview only. It does not indicate that a write, format, partition, or mount operation was performed.**
> All actual destructive writing engines remain completely locked and dry-run safe.

---
*Prepared by PhoenixCore BootForge Supply-Chain Safety Engine.*
"""
    return md


def validate_writer_contract_export_path(output_path: str, export_type: str, target_drive: str = None):
    """
    Validate the export path according to strict safety rules.
    1. Export path must not be empty.
    2. Parent folder must already exist.
    3. Export path must not be a directory.
    4. Export file must not already exist (overwrite is blocked).
    5. JSON exports must end with .json.
    6. Markdown exports must end with .md.
    7. Export path must not be on the target drive root.
    8. Export path must not be a raw device path or suspicious system path.
    """
    from pathlib import Path
    
    if not output_path or not str(output_path).strip():
        raise ValueError("Export path is empty.")
        
    p_str = str(output_path).strip().lower()
    
    # Raw device or suspicious paths checks (e.g. \\.\PhysicalDrive, NUL, CON, etc.)
    # We check raw patterns FIRST to prevent resolve() raising permission errors on devices
    if "\\\\.\\" in p_str or "//./" in p_str or p_str.startswith("\\\\") or p_str.startswith("//"):
        raise ValueError("Raw device style or UNC network paths are blocked for export.")
        
    for suspicious in ["sys32", "system32", "windows", "/etc", "/bin", "/sbin", "/var", "/usr"]:
        if suspicious in p_str.replace("\\", "/"):
            raise ValueError(f"Suspicious path detected: exporting to {suspicious} folders is blocked.")

    p = Path(output_path).resolve()
    
    # Directory check
    if p.exists() and p.is_dir():
        raise ValueError("Export path is a directory.")
        
    # Overwrite protection
    if p.exists():
        raise ValueError(f"Export file '{output_path}' already exists. Overwriting is blocked.")
        
    # Parent directory check
    parent = p.parent
    if not parent.exists() or not parent.is_dir():
        raise ValueError("Parent directory of export path does not exist.")
        
    # Extension checks
    ext = p.suffix.lower()
    if export_type == "json" and ext != ".json":
        raise ValueError(f"Export path extension '{ext}' does not match format 'json' (expected '.json').")
    elif export_type == "markdown" and ext != ".md":
        raise ValueError(f"Export path extension '{ext}' does not match format 'markdown' (expected '.md').")
    elif export_type not in ("json", "markdown"):
        raise ValueError(f"Unsupported export type '{export_type}'.")
        
    # Target drive root check
    if target_drive:
        from usb_creator import get_drive_root
        td_root = get_drive_root(target_drive)
        exp_root = get_drive_root(p)
        if td_root and exp_root and td_root.lower().rstrip("\\") == exp_root.lower().rstrip("\\"):
            raise ValueError(f"Export path is on the target drive '{target_drive}'. Overwriting target drive is blocked.")


def export_writer_contract_json(contract_payload: dict, output_path: str) -> dict:
    """
    Safely writes the contract JSON to the specified path after safety validations.
    """
    try:
        validate_writer_contract_export_path(output_path, "json", contract_payload.get("target_drive"))
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(contract_payload, f, indent=2)
            
        return {
            "schema": "bootforge.writer_safety_contract_export.v1",
            "status": "success",
            "format": "json",
            "export_path": output_path,
            "contract_id": contract_payload.get("contract_id"),
            "error": None
        }
    except Exception as e:
        return {
            "schema": "bootforge.writer_safety_contract_export.v1",
            "status": "failed",
            "format": "json",
            "export_path": output_path,
            "contract_id": contract_payload.get("contract_id"),
            "error": str(e)
        }


def export_writer_contract_markdown(contract_payload: dict, output_path: str) -> dict:
    """
    Safely writes the contract Markdown summary to the specified path after safety validations.
    """
    try:
        validate_writer_contract_export_path(output_path, "markdown", contract_payload.get("target_drive"))
        
        md_content = generate_writer_contract_markdown(contract_payload)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        return {
            "schema": "bootforge.writer_safety_contract_export.v1",
            "status": "success",
            "format": "markdown",
            "export_path": output_path,
            "contract_id": contract_payload.get("contract_id"),
            "error": None
        }
    except Exception as e:
        return {
            "schema": "bootforge.writer_safety_contract_export.v1",
            "status": "failed",
            "format": "markdown",
            "export_path": output_path,
            "contract_id": contract_payload.get("contract_id"),
            "error": str(e)
        }


# ---------------------------------------------------------------------------
# Safety declaration (module-level assertion — caught at import time)
# ---------------------------------------------------------------------------

# This assertion makes it impossible to accidentally import this module in a
# context where real_writer_implemented or destructive_operations_enabled have
# been patched to True at the module level.


# ---------------------------------------------------------------------------
# Contract History Ledger & Session ID Helpers (Phase 4C-4)
# ---------------------------------------------------------------------------

def build_writer_contract_session_id(contract_payload: dict) -> str:
    """
    Builds a deterministic, JSON-safe session ID based on stable fields of
    the writer safety contract payload. Does not include volatile timestamps.
    """
    import hashlib
    import json
    
    # Extract stable trace details
    schema = contract_payload.get("schema", "")
    contract_id = contract_payload.get("contract_id", "")
    target_drive = contract_payload.get("target_drive") or "placeholder_drive"
    image = contract_payload.get("image") or "placeholder_image"
    
    dev_id = contract_payload.get("device_identity") or {}
    device_identity_hash = dev_id.get("identity_hash") or "no_device_hash"
    
    img_id = contract_payload.get("image_identity") or {}
    image_identity_hash = img_id.get("identity_hash") or "no_image_hash"
    
    real_writer = contract_payload.get("real_writer_implemented", False)
    destructive = contract_payload.get("destructive_operations_enabled", False)
    blocked = contract_payload.get("blocked", True)
    
    reasons = sorted(contract_payload.get("block_reasons") or [])
    reasons_str = "|".join(reasons)
    
    trace_data = {
        "schema": schema,
        "contract_id": contract_id,
        "target_drive": target_drive,
        "image": image,
        "device_identity_hash": device_identity_hash,
        "image_identity_hash": image_identity_hash,
        "real_writer_implemented": real_writer,
        "destructive_operations_enabled": destructive,
        "blocked": blocked,
        "block_reasons": reasons_str
    }
    
    canonical = json.dumps(trace_data, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"session_{h[:32]}"


def build_writer_contract_ledger_record(contract_payload: dict, event_type: str, export_result: dict = None) -> dict:
    """
    Builds a structured ledger record for the writer safety contract.
    Schema: bootforge.writer_safety_contract_ledger.v1
    """
    import hashlib
    import json
    
    session_id = build_writer_contract_session_id(contract_payload)
    
    dev_id = contract_payload.get("device_identity") or {}
    img_id = contract_payload.get("image_identity") or {}
    
    record = {
        "schema": "bootforge.writer_safety_contract_ledger.v1",
        "session_id": session_id,
        "ledger_record_id": None,
        "event_type": event_type,
        "created_at": contract_payload.get("created_at") or _utc_now_iso(),
        "contract_schema": contract_payload.get("schema"),
        "contract_id": contract_payload.get("contract_id"),
        "blocked": contract_payload.get("blocked", True),
        "real_writer_implemented": contract_payload.get("real_writer_implemented", False),
        "destructive_operations_enabled": contract_payload.get("destructive_operations_enabled", False),
        "target_drive": contract_payload.get("target_drive"),
        "image_path": contract_payload.get("image"),
        "device_identity_hash": dev_id.get("identity_hash"),
        "image_identity_hash": img_id.get("identity_hash"),
        "block_reasons": contract_payload.get("block_reasons", []),
        "warnings": contract_payload.get("warnings", []),
        "next_required_action": contract_payload.get("next_required_action"),
    }
    
    if export_result is not None:
        record["export_result"] = export_result
        
    # Generate ledger_record_id deterministically based on record content (excluding itself)
    hashable = {k: v for k, v in record.items() if k != "ledger_record_id"}
    canonical = json.dumps(hashable, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    record["ledger_record_id"] = f"ledger_{h[:32]}"
    
    return record


def validate_writer_contract_ledger_path(ledger_path: str):
    """
    Validates a ledger append path according to strict safety rules.
    """
    from pathlib import Path
    
    if not ledger_path or not str(ledger_path).strip():
        raise ValueError("Ledger path is empty.")
        
    p_str = str(ledger_path).strip().lower()
    
    # UNC and raw device prefix checks (must be first to avoid resolve errors)
    if "\\\\.\\" in p_str or "//./" in p_str or p_str.startswith("\\\\") or p_str.startswith("//"):
        raise ValueError("Raw device style or UNC network paths are blocked for ledger.")
        
    for suspicious in ["sys32", "system32", "windows", "/etc", "/bin", "/sbin", "/var", "/usr"]:
        if suspicious in p_str.replace("\\", "/"):
            raise ValueError(f"Suspicious path detected: ledger path in {suspicious} folders is blocked.")
            
    p = Path(ledger_path).resolve()
    
    # Directory check
    if p.exists() and p.is_dir():
        raise ValueError("Ledger path is a directory.")
        
    # Parent directory check
    parent = p.parent
    if not parent.exists() or not parent.is_dir():
        raise ValueError("Parent directory of ledger path does not exist.")
        
    # Extension check
    if p.suffix.lower() != ".jsonl":
        raise ValueError(f"Ledger path extension '{p.suffix}' must be '.jsonl'.")


def append_writer_contract_ledger_record(record: dict, ledger_path: str) -> dict:
    """
    Safely appends a ledger record to the validated ledger path (JSONL format).
    """
    import json
    try:
        validate_writer_contract_ledger_path(ledger_path)
        
        # Verify target drive root check
        target_drive = record.get("target_drive")
        if target_drive:
            from usb_creator import get_drive_root
            from pathlib import Path
            td_root = get_drive_root(target_drive)
            ledger_root = get_drive_root(Path(ledger_path).resolve())
            if td_root and ledger_root and td_root.lower().rstrip("\\") == ledger_root.lower().rstrip("\\"):
                raise ValueError(f"Ledger path is on the target drive '{target_drive}'. Overwriting target drive is blocked.")
                
        # Append record
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
        with open(ledger_path, "a", encoding="utf-8") as f:
            f.write(canonical + "\n")
            
        return {
            "schema": "bootforge.writer_safety_contract_ledger_append.v1",
            "status": "success",
            "ledger_path": ledger_path,
            "ledger_record_id": record.get("ledger_record_id"),
            "error": None
        }
    except Exception as e:
        return {
            "schema": "bootforge.writer_safety_contract_ledger_append.v1",
            "status": "failed",
            "ledger_path": ledger_path,
            "ledger_record_id": record.get("ledger_record_id"),
            "error": str(e)
        }

assert SCHEMA == "bootforge.writer_safety_contract.v1", (
    "SAFETY: schema string tampered"
)
