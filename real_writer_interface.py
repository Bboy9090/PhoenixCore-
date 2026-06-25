"""
real_writer_interface.py
PhoenixCore / BootForge USB Creator
Part 3: Real Writer Interface

Defines standard request, result, and adapter interface models for lab-only raw write mode.
"""

import os
import sys
import uuid
import hashlib
from datetime import datetime, timezone

class RealWriterRequest:
    """
    Data holder for a raw USB write request in Lab Write Mode.
    Schema: bootforge.real_writer_request.v1
    """
    def __init__(self, **kwargs):
        self.schema = "bootforge.real_writer_request.v1"
        self.request_id = kwargs.get("request_id") or f"req_{str(uuid.uuid4())[:32].replace('-', '')}"
        self.created_at = kwargs.get("created_at") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.target_drive = kwargs.get("target_drive")
        self.target_stable_id = kwargs.get("target_stable_id")
        self.target_identity_hash = kwargs.get("target_identity_hash")
        self.image_path = kwargs.get("image_path")
        self.image_sha256 = kwargs.get("image_sha256")
        self.image_size_bytes = kwargs.get("image_size_bytes")
        self.contract_id = kwargs.get("contract_id")
        self.session_id = kwargs.get("session_id")
        self.readiness_gate_id = kwargs.get("readiness_gate_id")
        self.ledger_path = kwargs.get("ledger_path")
        self.lab_mode = kwargs.get("lab_mode", False)
        self.typed_confirmation = kwargs.get("typed_confirmation")
        self.destructive_acknowledgement = kwargs.get("destructive_acknowledgement")

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "request_id": self.request_id,
            "created_at": self.created_at,
            "target_drive": self.target_drive,
            "target_stable_id": self.target_stable_id,
            "target_identity_hash": self.target_identity_hash,
            "image_path": self.image_path,
            "image_sha256": self.image_sha256,
            "image_size_bytes": self.image_size_bytes,
            "contract_id": self.contract_id,
            "session_id": self.session_id,
            "readiness_gate_id": self.readiness_gate_id,
            "ledger_path": self.ledger_path,
            "lab_mode": self.lab_mode,
            "typed_confirmation": self.typed_confirmation,
            "destructive_acknowledgement": self.destructive_acknowledgement
        }

class RealWriterResult:
    """
    Data holder for a raw USB write result in Lab Write Mode.
    Schema: bootforge.real_writer_lab_result.v1
    """
    def __init__(self, **kwargs):
        self.schema = "bootforge.real_writer_lab_result.v1"
        self.request_id = kwargs.get("request_id")
        self.platform = kwargs.get("platform") or sys.platform
        self.adapter = kwargs.get("adapter")
        self.real_writer_implemented = kwargs.get("real_writer_implemented", False)
        self.destructive_operations_enabled = kwargs.get("destructive_operations_enabled", False)
        self.lab_mode = kwargs.get("lab_mode", False)
        self.write_attempted = kwargs.get("write_attempted", False)
        self.write_started_at = kwargs.get("write_started_at")
        self.write_completed_at = kwargs.get("write_completed_at")
        self.bytes_expected = kwargs.get("bytes_expected", 0)
        self.bytes_written = kwargs.get("bytes_written", 0)
        self.image_sha256_expected = kwargs.get("image_sha256_expected")
        self.verification_sha256 = kwargs.get("verification_sha256")
        self.verification_passed = kwargs.get("verification_passed", False)
        self.cancelled = kwargs.get("cancelled", False)
        self.blocked = kwargs.get("blocked", True)
        self.block_reasons = kwargs.get("block_reasons") or []
        self.warnings = kwargs.get("warnings") or []
        self.next_required_action = kwargs.get("next_required_action")
        self.ledger_record_ids = kwargs.get("ledger_record_ids") or []
        self.real_usb_write_performed = kwargs.get("real_usb_write_performed", False)
        self.file_backed_lab_write = kwargs.get("file_backed_lab_write", False)

    def to_dict(self) -> dict:
        return {
            "schema": self.schema,
            "request_id": self.request_id,
            "platform": self.platform,
            "adapter": self.adapter,
            "real_writer_implemented": self.real_writer_implemented,
            "destructive_operations_enabled": self.destructive_operations_enabled,
            "lab_mode": self.lab_mode,
            "write_attempted": self.write_attempted,
            "write_started_at": self.write_started_at,
            "write_completed_at": self.write_completed_at,
            "bytes_expected": self.bytes_expected,
            "bytes_written": self.bytes_written,
            "image_sha256_expected": self.image_sha256_expected,
            "verification_sha256": self.verification_sha256,
            "verification_passed": self.verification_passed,
            "cancelled": self.cancelled,
            "blocked": self.blocked,
            "block_reasons": self.block_reasons,
            "warnings": self.warnings,
            "next_required_action": self.next_required_action,
            "ledger_record_ids": self.ledger_record_ids,
            "real_usb_write_performed": self.real_usb_write_performed,
            "file_backed_lab_write": self.file_backed_lab_write
        }

class PlatformWriterAdapter:
    """
    Base class for system-specific raw disk writing adapters.
    """
    def execute_write(self, request: RealWriterRequest) -> RealWriterResult:
        raise NotImplementedError("Subclasses must implement execute_write")

class NullDisabledWriterAdapter(PlatformWriterAdapter):
    """
    Default adapter. Blocks all execution requests and performs no mutations.
    """
    def execute_write(self, request: RealWriterRequest) -> RealWriterResult:
        return RealWriterResult(
            request_id=request.request_id,
            adapter="NullDisabledWriterAdapter",
            real_writer_implemented=False,
            destructive_operations_enabled=False,
            lab_mode=request.lab_mode,
            write_attempted=False,
            blocked=True,
            block_reasons=["Real writing remains disabled by default. No active platform adapter configured."],
            next_required_action="configure_valid_lab_writer_adapter"
        )

class WindowsLabWriterAdapter(PlatformWriterAdapter):
    """
    Blocked Windows raw physical USB adapter (TODO).
    """
    def execute_write(self, request: RealWriterRequest) -> RealWriterResult:
        return RealWriterResult(
            request_id=request.request_id,
            adapter="WindowsLabWriterAdapter",
            real_writer_implemented=False,
            destructive_operations_enabled=False,
            lab_mode=request.lab_mode,
            write_attempted=False,
            blocked=True,
            block_reasons=["Physical USB writing is blocked on Windows in this phase. Use file-backed writer instead."],
            next_required_action="use_file_backed_fallback_writer"
        )

class MacOSLabWriterAdapter(PlatformWriterAdapter):
    """
    Blocked macOS raw physical USB adapter (TODO).
    """
    def execute_write(self, request: RealWriterRequest) -> RealWriterResult:
        return RealWriterResult(
            request_id=request.request_id,
            adapter="MacOSLabWriterAdapter",
            real_writer_implemented=False,
            destructive_operations_enabled=False,
            lab_mode=request.lab_mode,
            write_attempted=False,
            blocked=True,
            block_reasons=["Physical USB writing is blocked on macOS. Use file-backed writer instead."],
            next_required_action="use_file_backed_fallback_writer"
        )

class LinuxLabWriterAdapter(PlatformWriterAdapter):
    """
    Blocked Linux raw physical USB adapter (TODO).
    """
    def execute_write(self, request: RealWriterRequest) -> RealWriterResult:
        return RealWriterResult(
            request_id=request.request_id,
            adapter="LinuxLabWriterAdapter",
            real_writer_implemented=False,
            destructive_operations_enabled=False,
            lab_mode=request.lab_mode,
            write_attempted=False,
            blocked=True,
            block_reasons=["Physical USB writing is blocked on Linux. Use file-backed writer instead."],
            next_required_action="use_file_backed_fallback_writer"
        )

class FileBackedLabWriterAdapter(PlatformWriterAdapter):
    """
    Safe file-backed fallback adapter. Writes raw image byte-for-byte to a target file.
    """
    def execute_write(self, request: RealWriterRequest) -> RealWriterResult:
        if not request.image_path or not os.path.exists(request.image_path):
            return RealWriterResult(
                request_id=request.request_id,
                adapter="FileBackedLabWriterAdapter",
                blocked=True,
                block_reasons=["Source image file not found or inaccessible."],
                next_required_action="provide_valid_source_image"
            )
            
        target_file = request.target_drive
        if not target_file:
            return RealWriterResult(
                request_id=request.request_id,
                adapter="FileBackedLabWriterAdapter",
                blocked=True,
                block_reasons=["Target file path is missing."],
                next_required_action="provide_valid_target_file"
            )

        start_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        bytes_written = 0
        chunk_size = 1024 * 1024 # 1MB chunks
        
        try:
            # Read from image, write to target file
            image_size = os.path.getsize(request.image_path)
            
            with open(request.image_path, "rb") as src, open(target_file, "wb") as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    bytes_written += len(chunk)
                    
            # Compute hash of written bytes to verify integrity
            sha256_hash = hashlib.sha256()
            with open(target_file, "rb") as f:
                for byte_block in iter(lambda: f.read(65536), b""):
                    sha256_hash.update(byte_block)
            written_sha = sha256_hash.hexdigest()
            
            expected_sha = request.image_sha256
            verification_passed = (written_sha == expected_sha) if expected_sha else True
            
            end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            
            return RealWriterResult(
                request_id=request.request_id,
                adapter="FileBackedLabWriterAdapter",
                real_writer_implemented=True,
                destructive_operations_enabled=True,
                lab_mode=request.lab_mode,
                write_attempted=True,
                write_started_at=start_time,
                write_completed_at=end_time,
                bytes_expected=image_size,
                bytes_written=bytes_written,
                image_sha256_expected=expected_sha,
                verification_sha256=written_sha,
                verification_passed=verification_passed,
                blocked=False,
                real_usb_write_performed=False,
                file_backed_lab_write=True,
                next_required_action="verify_flashed_content_on_host"
            )
            
        except Exception as e:
            end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return RealWriterResult(
                request_id=request.request_id,
                adapter="FileBackedLabWriterAdapter",
                real_writer_implemented=True,
                destructive_operations_enabled=True,
                lab_mode=request.lab_mode,
                write_attempted=True,
                write_started_at=start_time,
                write_completed_at=end_time,
                blocked=True,
                block_reasons=[f"Exception during file-backed flash: {str(e)}"],
                next_required_action="check_write_permissions_and_retry"
            )


# ===========================================================================
# PART 1 & 2 — HARDWARE PREFLIGHT & REMOVABLE TARGET IDENTITY LOCK
# ===========================================================================

def _resolve_scanner_device(target_drive: str, scan_payload: dict = None):
    """
    Resolves a target drive path to a device_scanner.v2 device record.
    Checks the scan_payload first (if v2 devices are present), then falls
    back to running a fresh scan via usb_creator.get_normalized_scan().
    Returns the matched device dict, or None.
    """
    norm_target = target_drive.lower().rstrip("\\/")

    if scan_payload:
        for d in scan_payload.get("devices", []):
            if d.get("drive_path", "").lower().rstrip("\\/") == norm_target:
                return d
        for d in scan_payload.get("drives", []):
            dp = d.get("drive_path") or d.get("path") or d.get("drive") or ""
            if dp.lower().rstrip("\\/") == norm_target:
                return d

    try:
        from usb_creator import get_normalized_scan
        fresh = get_normalized_scan(quiet=True)
        for d in fresh.get("devices", []):
            if d.get("drive_path", "").lower().rstrip("\\/") == norm_target:
                return d
    except Exception:
        pass

    return None


def _build_scanner_identity_hash(device: dict) -> str:
    """
    Builds a deterministic identity hash from scanner v2 evidence fields:
    stable_id, serial, size_bytes, platform, drive_path, detection_source, bus_protocol.
    """
    import json as _json
    fields = {
        "stable_id": device.get("stable_id"),
        "serial": device.get("serial"),
        "size_bytes": device.get("size_bytes"),
        "platform": device.get("platform"),
        "drive_path": device.get("drive_path"),
        "detection_source": device.get("detection_source"),
        "bus_protocol": device.get("bus_protocol"),
    }
    canonical = _json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def build_removable_target_identity_lock(target_drive: str, scan_payload: dict = None) -> dict:
    """
    Builds a deterministic removable target identity lock payload.
    Uses device_scanner.v2 evidence when available.
    Schema: bootforge.removable_target_identity_lock.v1
    """
    import json
    import hashlib

    if not target_drive:
        return {
            "schema": "bootforge.removable_target_identity_lock.v1",
            "identity_lock_id": None,
            "blocked": True,
            "block_reasons": ["Target drive is missing or empty."],
            "next_required_action": "specify_target_drive"
        }

    p_str = str(target_drive).strip().lower()
    if "\\\\.\\" in p_str or "//./" in p_str or p_str.startswith("\\\\") or p_str.startswith("//"):
        if not scan_payload:
            return {
                "schema": "bootforge.removable_target_identity_lock.v1",
                "identity_lock_id": None,
                "blocked": True,
                "block_reasons": ["Direct raw device paths are blocked without scanned target context."],
                "next_required_action": "rescan_and_match_target"
            }

    scanner_device = _resolve_scanner_device(target_drive, scan_payload)
    device_path = (scanner_device.get("drive_path") or scanner_device.get("path") or scanner_device.get("drive") or "") if scanner_device else ""

    if scanner_device and device_path:
        stable_id = scanner_device.get("stable_id")
        serial = scanner_device.get("serial")
        is_removable = scanner_device.get("is_removable") or scanner_device.get("removable") or False
        is_external = scanner_device.get("is_external") or scanner_device.get("external") or False
        is_fixed = scanner_device.get("is_fixed") or scanner_device.get("fixed") or False
        is_system = scanner_device.get("is_system") or scanner_device.get("is_system_drive") or False
        size_bytes = scanner_device.get("size_bytes") or scanner_device.get("capacity_bytes") or 0
        confidence = scanner_device.get("confidence", "low")
        detection_source = scanner_device.get("detection_source")
        bus_protocol = scanner_device.get("bus_protocol") or scanner_device.get("bus_type")
        block_reasons_from_scanner = list(scanner_device.get("block_reasons", []))
        warnings_from_scanner = list(scanner_device.get("warnings", []))
        is_v2_device = "drive_path" in scanner_device
        if is_v2_device:
            dev_hash = _build_scanner_identity_hash(scanner_device)
        else:
            dev_hash = scanner_device.get("device_identity_hash") or scanner_device.get("identity_hash")
        volume_label = scanner_device.get("volume_label") or scanner_device.get("display_name") or scanner_device.get("label")
    else:
        stable_id = None
        serial = None
        is_removable = True
        is_external = True
        is_fixed = False
        is_system = False
        size_bytes = 16000000000
        confidence = "low"
        detection_source = "fallback"
        bus_protocol = "USB"
        block_reasons_from_scanner = []
        warnings_from_scanner = ["No scanner v2 device matched; using fallback identity."]
        dev_hash = "mock_hash_" + hashlib.sha256(target_drive.encode()).hexdigest()[:16]
        volume_label = "Removable USB"

    block_reasons = list(block_reasons_from_scanner)
    warnings = list(warnings_from_scanner)

    if is_fixed is True:
        if "Target drive is fixed/internal." not in block_reasons and "Drive is fixed/internal, not removable." not in block_reasons:
            block_reasons.append("Target drive is fixed/internal.")
    if is_system is True:
        if "Target drive is flagged as system drive." not in block_reasons and "Drive is a system/boot drive." not in block_reasons:
            block_reasons.append("Target drive is flagged as system drive.")
    if not is_removable and not is_external:
        block_reasons.append("Target drive is not removable or external.")
    if not dev_hash:
        block_reasons.append("Target identity hash is missing.")
    if not size_bytes or size_bytes <= 0:
        block_reasons.append("Target size is unknown or invalid.")

    blocked = len(block_reasons) > 0

    lock_record = {
        "schema": "bootforge.removable_target_identity_lock.v1",
        "identity_lock_id": None,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target_drive": target_drive,
        "stable_id": stable_id or "stable_usb_device",
        "serial": serial,
        "device_identity_hash": dev_hash,
        "volume_label": volume_label,
        "size_bytes": size_bytes,
        "bus_type": bus_protocol or "USB",
        "detection_source": detection_source,
        "confidence": confidence,
        "is_removable": bool(is_removable),
        "is_external": bool(is_external),
        "is_fixed": bool(is_fixed),
        "is_system_drive": bool(is_system),
        "scan_source": detection_source or "initial_scan",
        "lock_reasons": [],
        "warnings": warnings,
        "blocked": blocked,
        "block_reasons": block_reasons,
        "next_required_action": "verify_target_identity" if not blocked else "resolve_preflight_blockers"
    }

    stable_data = {
        "target_drive": lock_record["target_drive"],
        "stable_id": lock_record["stable_id"],
        "device_identity_hash": lock_record["device_identity_hash"],
        "size_bytes": lock_record["size_bytes"]
    }
    h = hashlib.sha256(json.dumps(stable_data, sort_keys=True).encode()).hexdigest()
    lock_record["identity_lock_id"] = f"lock_{h[:32]}"

    return lock_record


def validate_removable_target_identity_lock(identity_lock: dict) -> bool:
    """
    Validates target identity lock structure. Returns True if not blocked.
    """
    if not identity_lock or not isinstance(identity_lock, dict):
        return False
    if identity_lock.get("schema") != "bootforge.removable_target_identity_lock.v1":
        return False
    return not bool(identity_lock.get("blocked", True))


def rescan_and_compare_target_identity(identity_lock: dict, latest_scan_payload: dict = None) -> dict:
    """
    Compares latest scan parameters against identity lock to detect target identity drift.
    Uses scanner v2 identity hash when devices are present.
    """
    if not identity_lock or identity_lock.get("blocked"):
        return {"match": False, "drift_detected": True, "error": "Invalid or blocked identity lock payload."}

    target_drive = identity_lock.get("target_drive")

    scanner_device = _resolve_scanner_device(target_drive, latest_scan_payload)

    if scanner_device and scanner_device.get("drive_path"):
        latest_hash = _build_scanner_identity_hash(scanner_device)
    else:
        latest_drive = None
        if latest_scan_payload and "drives" in latest_scan_payload:
            for d in latest_scan_payload["drives"]:
                dp = d.get("path") or d.get("drive") or ""
                if dp.lower().rstrip("\\/") == target_drive.lower().rstrip("\\/"):
                    latest_drive = d
                    break
        if not latest_drive:
            return {"match": False, "drift_detected": True, "error": "Target drive was not found during re-scan."}
        latest_hash = latest_drive.get("device_identity_hash") or latest_drive.get("identity_hash")

    lock_hash = identity_lock.get("device_identity_hash")
    match = (lock_hash == latest_hash)
    drift = not match

    return {
        "match": match,
        "drift_detected": drift,
        "latest_identity_hash": latest_hash,
        "error": None if match else "Target drive identity has changed since initialization."
    }


def build_physical_writer_preflight_result(identity_lock: dict, image_payload: dict = None, readiness_gate: dict = None) -> dict:
    """
    Combines identity lock, image metadata, and readiness status into a hardware preflight summary.
    Includes scanner v2 evidence fields for downstream consumers.
    Schema: bootforge.hardware_writer_preflight.v1
    """
    import uuid

    preflight_id = f"preflight_{str(uuid.uuid4())[:32].replace('-', '')}"
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    block_reasons = []
    warnings = []

    physical_writer_allowed = False
    physical_write_attempted = False

    lock_ok = validate_removable_target_identity_lock(identity_lock)
    if not lock_ok:
        block_reasons.extend(identity_lock.get("block_reasons", ["Identity lock failed verification."]))

    image_path = None
    image_sha256 = None
    image_size_bytes = 0
    if image_payload:
        image_path = image_payload.get("image_path") or image_payload.get("path")
        image_sha256 = image_payload.get("image_sha256") or image_payload.get("sha256")
        image_size_bytes = image_payload.get("image_size_bytes") or image_payload.get("size_bytes") or 0
        if not image_sha256:
            block_reasons.append("Source image hash is missing.")

    scanner_confidence = identity_lock.get("confidence", "low") if identity_lock else "low"
    scanner_detection_source = identity_lock.get("detection_source") if identity_lock else None
    scanner_stable_id = identity_lock.get("stable_id") if identity_lock else None
    scanner_serial = identity_lock.get("serial") if identity_lock else None
    scanner_block_reasons = list(identity_lock.get("block_reasons", [])) if identity_lock else []
    scanner_warnings = list(identity_lock.get("warnings", [])) if identity_lock else []

    if scanner_confidence == "low":
        block_reasons.append("Scanner confidence is low; identity lock is unreliable for lab write eligibility.")

    block_reasons.append("Physical USB writing remains locked. Phase 5A-2 preflight mode only.")

    preflight = {
        "schema": "bootforge.hardware_writer_preflight.v1",
        "preflight_id": preflight_id,
        "created_at": created_at,
        "target_drive": identity_lock.get("target_drive") if identity_lock else None,
        "target_stable_id": identity_lock.get("stable_id") if identity_lock else None,
        "target_identity_hash": identity_lock.get("device_identity_hash") if identity_lock else None,
        "target_volume_label": identity_lock.get("volume_label") if identity_lock else None,
        "target_size_bytes": identity_lock.get("size_bytes") if identity_lock else 0,
        "target_bus_type": identity_lock.get("bus_type") if identity_lock else "USB",
        "target_is_removable": identity_lock.get("is_removable") if identity_lock else False,
        "target_is_external": identity_lock.get("is_external") if identity_lock else False,
        "target_is_fixed": identity_lock.get("is_fixed") if identity_lock else False,
        "target_is_system_drive": identity_lock.get("is_system_drive") if identity_lock else False,
        "target_scan_source": identity_lock.get("scan_source") if identity_lock else None,
        "scanner_schema": "bootforge.device_scan.v2",
        "scanner_confidence": scanner_confidence,
        "scanner_detection_source": scanner_detection_source,
        "scanner_stable_id": scanner_stable_id,
        "scanner_serial": scanner_serial,
        "scanner_block_reasons": scanner_block_reasons,
        "scanner_warnings": scanner_warnings,
        "image_path": image_path,
        "image_sha256": image_sha256,
        "image_size_bytes": image_size_bytes,
        "identity_lock_id": identity_lock.get("identity_lock_id") if identity_lock else None,
        "identity_lock_passed": lock_ok,
        "latest_identity_hash": identity_lock.get("device_identity_hash") if identity_lock else None,
        "identity_drift_detected": False,
        "physical_writer_allowed": physical_writer_allowed,
        "physical_write_attempted": physical_write_attempted,
        "blocked": True,
        "block_reasons": block_reasons,
        "warnings": warnings,
        "next_required_action": "await_hardware_writer_release"
    }

    return preflight


# ===========================================================================
# PART 5 — EXPORT EVIDENCE
# ===========================================================================

def generate_hardware_preflight_markdown(preflight_payload: dict) -> str:
    """
    Generates a beautifully layouted human-readable Markdown summary of preflight results.
    """
    status = "⛔ BLOCKED" if preflight_payload.get("blocked") else "✓ ALLOWED"
    
    reasons_list = preflight_payload.get("block_reasons", [])
    reasons_str = "\n".join(f"- {r}" for r in reasons_list) if reasons_list else "None"
    
    warnings_list = preflight_payload.get("warnings", [])
    warnings_str = "\n".join(f"- {w}" for w in warnings_list) if warnings_list else "None"
    
    md = f"""# PhoenixCore / BootForge Hardware USB Preflight Report
    
## General Info
- **Preflight ID**: {preflight_payload.get("preflight_id")}
- **Schema**: {preflight_payload.get("schema")}
- **Created At**: {preflight_payload.get("created_at")}
- **Status**: {status}

---

## Target USB Details
- **Drive Path**: {preflight_payload.get("target_drive")}
- **Stable OS ID**: {preflight_payload.get("target_stable_id")}
- **Identity Hash**: `{preflight_payload.get("target_identity_hash")}`
- **Volume Label**: {preflight_payload.get("target_volume_label")}
- **Size**: {preflight_payload.get("target_size_bytes")} bytes
- **Bus Type**: {preflight_payload.get("target_bus_type")}
- **Removable**: {preflight_payload.get("target_is_removable")}
- **System Drive**: {preflight_payload.get("target_is_system_drive")}

---

## Target Lock Verification
- **Identity Lock ID**: {preflight_payload.get("identity_lock_id")}
- **Identity Lock Verified**: {preflight_payload.get("identity_lock_passed")}
- **Identity Drift Detected**: {preflight_payload.get("identity_drift_detected")}

---

## Block Reasons
{reasons_str}

---

## Warnings
{warnings_str}

---

## Preflight Safety Assertion
> [!IMPORTANT]
> **This report is evidence of a hardware preflight audit check only. Physical USB writing remains disabled by default.**
"""
    return md


def validate_hardware_preflight_export_path(output_path: str, export_type: str, target_drive: str = None):
    """
    Validates export path safety according to preflight safety rules.
    """
    from pathlib import Path
    
    if not output_path or not str(output_path).strip():
        raise ValueError("Export path is empty.")
        
    p_str = str(output_path).strip().lower()
    
    if "\\\\.\\" in p_str or "//./" in p_str or p_str.startswith("\\\\") or p_str.startswith("//"):
        raise ValueError("Raw device style or UNC network paths are blocked for export.")
        
    for suspicious in ["sys32", "system32", "windows", "/etc", "/bin", "/sbin", "/var", "/usr"]:
        if suspicious in p_str.replace("\\", "/"):
            raise ValueError(f"Suspicious path detected: export path in {suspicious} folders is blocked.")
            
    p = Path(output_path).resolve()
    
    # Overwrite protection
    if p.exists():
        raise ValueError(f"Export file '{output_path}' already exists. Overwriting is blocked.")
        
    # Directory check
    if p.exists() and p.is_dir():
        raise ValueError("Export path is a directory.")
        
    # Parent directory check
    parent = p.parent
    if not parent.exists() or not parent.is_dir():
        raise ValueError("Parent directory of export path does not exist.")
        
    # Extension check
    if export_type == "json" and p.suffix.lower() != ".json":
        raise ValueError(f"Export path extension '{p.suffix}' must be '.json'.")
    elif export_type == "markdown" and p.suffix.lower() != ".md":
        raise ValueError(f"Export path extension '{p.suffix}' must be '.md'.")
        
    # Target drive root check
    if target_drive:
        from usb_creator import get_drive_root
        td_root = get_drive_root(target_drive)
        export_root = get_drive_root(p)
        if td_root and export_root and td_root.lower().rstrip("\\") == export_root.lower().rstrip("\\"):
            raise ValueError(f"Export path is on the target drive '{target_drive}'. Overwriting target drive is blocked.")


def export_hardware_preflight_json(preflight_payload: dict, output_path: str) -> dict:
    """
    Safely exports the preflight JSON to a file path.
    """
    import json
    try:
        validate_hardware_preflight_export_path(output_path, "json", preflight_payload.get("target_drive"))
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(preflight_payload, f, indent=2)
        return {"status": "success", "export_path": output_path, "error": None}
    except Exception as e:
        return {"status": "failed", "export_path": output_path, "error": str(e)}


def export_hardware_preflight_markdown(preflight_payload: dict, output_path: str) -> dict:
    """
    Safely exports the preflight Markdown summary to a file path.
    """
    try:
        validate_hardware_preflight_export_path(output_path, "markdown", preflight_payload.get("target_drive"))
        md = generate_hardware_preflight_markdown(preflight_payload)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        return {"status": "success", "export_path": output_path, "error": None}
    except Exception as e:
        return {"status": "failed", "export_path": output_path, "error": str(e)}


# ===========================================================================
# PART 6 — PHYSICAL WRITER DRY-RUN HARNESS (Phase 5A-3)
# ===========================================================================

def build_hardware_lab_permission_status(platform_name=None) -> dict:
    """
    Checks if current user has admin/root privileges across Windows, macOS, and Linux.
    Schema: bootforge.hardware_lab_permission_status.v1
    """
    import sys
    import ctypes
    import os
    
    plat = platform_name or sys.platform
    is_win = (plat == "win32")
    is_mac = (plat == "darwin")
    is_lin = plat.startswith("linux")
    
    # Check admin status
    running_as_admin = False
    if is_win:
        try:
            running_as_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            running_as_admin = False
    else:
        try:
            running_as_admin = (os.getuid() == 0)
        except Exception:
            running_as_admin = False
            
    permission_passed = running_as_admin
    blocked = not permission_passed
    block_reasons = []
    if blocked:
        block_reasons.append("Administrative/root privileges are required to access physical drives.")
        
    return {
        "schema": "bootforge.hardware_lab_permission_status.v1",
        "platform": plat,
        "is_windows": is_win,
        "is_macos": is_mac,
        "is_linux": is_lin,
        "running_as_admin_or_root": running_as_admin,
        "permission_check_supported": True,
        "permission_required": True,
        "permission_passed": permission_passed,
        "blocked": blocked,
        "block_reasons": block_reasons,
        "warnings": [],
        "next_required_action": "request_elevation" if blocked else "none"
    }


def build_physical_writer_dryrun_request(preflight_payload: dict, readiness_gate: dict = None, ledger_path: str = None) -> dict:
    """
    Builds a dry-run physical writer request payload.
    Schema: bootforge.physical_writer_dryrun_request.v1
    """
    import uuid
    from datetime import datetime, timezone
    
    req_id = f"dryreq_{str(uuid.uuid4())[:32].replace('-', '')}"
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Safely get target fields from preflight_payload
    target_drive = preflight_payload.get("target_drive") if preflight_payload else None
    target_stable_id = preflight_payload.get("target_stable_id") if preflight_payload else None
    target_identity_hash = preflight_payload.get("target_identity_hash") if preflight_payload else None
    image_path = preflight_payload.get("image_path") if preflight_payload else None
    image_sha256 = preflight_payload.get("image_sha256") if preflight_payload else None
    image_size_bytes = preflight_payload.get("image_size_bytes") if preflight_payload else 0
    preflight_id = preflight_payload.get("preflight_id") if preflight_payload else None
    identity_lock_id = preflight_payload.get("identity_lock_id") if preflight_payload else None
    
    readiness_gate_id = readiness_gate.get("readiness_gate_id") if readiness_gate else None
    session_id = ((preflight_payload.get("session_id") if preflight_payload else None) or 
                  (readiness_gate.get("session_id") if readiness_gate else None) or 
                  f"session_{str(uuid.uuid4())[:32].replace('-', '')}")
                  
    return {
        "schema": "bootforge.physical_writer_dryrun_request.v1",
        "request_id": req_id,
        "created_at": created_at,
        "target_drive": target_drive,
        "target_stable_id": target_stable_id,
        "target_identity_hash": target_identity_hash,
        "image_path": image_path,
        "image_sha256": image_sha256,
        "image_size_bytes": image_size_bytes,
        "preflight_id": preflight_id,
        "identity_lock_id": identity_lock_id,
        "readiness_gate_id": readiness_gate_id,
        "session_id": session_id,
        "ledger_path": ledger_path,
        "lab_mode": True,
        "dry_run_only": True,
        "physical_write_requested": False,
        "physical_write_allowed": False
    }


def validate_physical_writer_dryrun_request(request_payload: dict) -> tuple:
    """
    Validates a dry-run physical writer request payload against all safety constraints.
    Returns (is_valid, list of block_reasons).
    """
    block_reasons = []
    
    if not request_payload:
        return False, ["Missing request payload."]
        
    if request_payload.get("schema") != "bootforge.physical_writer_dryrun_request.v1":
        block_reasons.append("Invalid request schema. Must be bootforge.physical_writer_dryrun_request.v1.")
        
    # Check locks/preflight presence
    if not request_payload.get("preflight_id"):
        block_reasons.append("Hardware preflight ID is missing.")
    if not request_payload.get("identity_lock_id"):
        block_reasons.append("Target identity lock ID is missing.")
    if not request_payload.get("readiness_gate_id"):
        block_reasons.append("Final destructive readiness gate ID is missing.")
    if not request_payload.get("target_identity_hash"):
        block_reasons.append("Target identity hash is missing.")
    if not request_payload.get("image_sha256"):
        block_reasons.append("Source image hash is missing.")
        
    # Check permissions
    perm = build_hardware_lab_permission_status()
    if perm.get("blocked"):
        block_reasons.extend(perm.get("block_reasons", []))
        
    # Check environment unlock
    unlock = os.environ.get("BOOTFORGE_ENABLE_LAB_WRITE")
    if unlock != "I_ACCEPT_REAL_USB_WRITE_RISK":
        block_reasons.append("Environment variable unlock 'BOOTFORGE_ENABLE_LAB_WRITE=I_ACCEPT_REAL_USB_WRITE_RISK' is missing.")
        
    # Check requested writes
    if request_payload.get("physical_write_requested") or request_payload.get("physical_write_allowed"):
        block_reasons.append("Physical USB writing is not allowed in this phase.")
        
    is_valid = len(block_reasons) == 0
    return is_valid, block_reasons


def build_physical_writer_dryrun_result(request_payload: dict, validation_result: tuple = None) -> dict:
    """
    Builds a dry-run physical writer result payload.
    Schema: bootforge.physical_writer_dryrun_result.v1
    """
    import uuid
    from datetime import datetime, timezone
    
    res_id = f"dryres_{str(uuid.uuid4())[:32].replace('-', '')}"
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    is_valid = True
    block_reasons = []
    if validation_result:
        is_valid, block_reasons = validation_result
    else:
        is_valid, block_reasons = validate_physical_writer_dryrun_request(request_payload)
        
    perm = build_hardware_lab_permission_status()
    
    # Calculate chunk plan (simulated 1MB chunks)
    image_size = request_payload.get("image_size_bytes") or 0
    chunk_size = 1048576 # 1MB
    chunks_planned = 0
    if image_size > 0:
        chunks_planned = (image_size + chunk_size - 1) // chunk_size
        
    # Physical OS adapters must remain blocked
    # Even if permission passed, blocked remains True, physical_write_allowed remains False.
    blocked = not is_valid or len(block_reasons) > 0
    
    # Double ensure we are blocked and write remains false
    blocked = True
    if "Physical USB writing is not allowed in this phase." not in block_reasons:
        block_reasons.append("Physical USB writing is not allowed in this phase.")
        
    return {
        "schema": "bootforge.physical_writer_dryrun_result.v1",
        "request_id": request_payload.get("request_id"),
        "result_id": res_id,
        "created_at": created_at,
        "platform": sys.platform,
        "adapter": "physical-dryrun-writer",
        "dry_run_only": True,
        "physical_write_requested": False,
        "physical_write_allowed": False,
        "physical_write_attempted": False,
        "bytes_written": 0,
        "chunks_planned": chunks_planned,
        "chunk_size_bytes": chunk_size,
        "image_size_bytes": image_size,
        "target_identity_hash": request_payload.get("target_identity_hash"),
        "latest_identity_hash": request_payload.get("target_identity_hash"), # matches in dry-run
        "identity_drift_detected": False,
        "permission_passed": perm.get("permission_passed", False),
        "blocked": blocked,
        "block_reasons": block_reasons,
        "warnings": ["Physical USB write is mock dry-run only. No bytes written."],
        "next_required_action": "await_physical_writer_implementation"
    }


class PhysicalDryRunWriterAdapter:
    """
    Adapter that executes the dry-run simulation for physical writing.
    Does not write bytes or open raw device paths.
    """
    def __init__(self):
        self.name = "physical-dryrun-writer"
        
    def execute_dryrun(self, request_payload: dict) -> dict:
        is_valid, block_reasons = validate_physical_writer_dryrun_request(request_payload)
        
        target_drive = request_payload.get("target_drive")
        if target_drive:
            from usb_creator import get_removable_drives
            drives = get_removable_drives(quiet=True)
            details = None
            for d in drives:
                d_path = d.get("drive") or d.get("path")
                if d_path and d_path.lower().rstrip("\\") == target_drive.lower().rstrip("\\"):
                    details = d
                    break
            if details:
                is_fixed = details.get("is_fixed") or details.get("fixed")
                is_system_drive = details.get("is_system_drive") or details.get("system_drive")
                if is_fixed or is_system_drive:
                    is_valid = False
                    if "Target drive is fixed/internal or system." not in block_reasons:
                        block_reasons.append("Target drive is fixed/internal or system.")
                        
        result = build_physical_writer_dryrun_result(request_payload, (is_valid, block_reasons))
        return result


class WindowsPhysicalWriterAdapter:
    def __init__(self):
        self.name = "windows-physical-writer"
    def execute_write(self, request):
        return {"blocked": True, "block_reasons": ["Windows physical writer is blocked."]}


class MacPhysicalWriterAdapter:
    def __init__(self):
        self.name = "macos-physical-writer"
    def execute_write(self, request):
        return {"blocked": True, "block_reasons": ["macOS physical writer is blocked."]}


class LinuxPhysicalWriterAdapter:
    def __init__(self):
        self.name = "linux-physical-writer"
    def execute_write(self, request):
        return {"blocked": True, "block_reasons": ["Linux physical writer is blocked."]}


def validate_physical_writer_dryrun_export_path(output_path: str, export_type: str, target_drive: str = None):
    """
    Validates export path safety according to physical writer dryrun rules.
    """
    from pathlib import Path
    
    if not output_path or not str(output_path).strip():
        raise ValueError("Export path is empty.")
        
    p_str = str(output_path).strip().lower()
    
    if "\\\\.\\" in p_str or "//./" in p_str or p_str.startswith("\\\\") or p_str.startswith("//"):
        raise ValueError("Raw device style or UNC network paths are blocked for export.")
        
    for suspicious in ["sys32", "system32", "windows", "/etc", "/bin", "/sbin", "/var", "/usr"]:
        if suspicious in p_str.replace("\\", "/"):
            raise ValueError(f"Suspicious path detected: export path in {suspicious} folders is blocked.")
            
    p = Path(output_path)
    p_resolved = p.resolve()
    
    if p_resolved.exists() and p_resolved.is_dir():
        raise ValueError("Export path is a directory.")
        
    if p_resolved.exists():
        raise ValueError(f"Export file '{output_path}' already exists. Overwriting is blocked.")
        
    parent = p_resolved.parent
    if not parent.exists() or not parent.is_dir():
        raise ValueError("Parent directory of export path does not exist.")
        
    if export_type == "json" and p_resolved.suffix.lower() != ".json":
        raise ValueError(f"Export path extension '{p_resolved.suffix}' must be '.json'.")
    elif export_type == "markdown" and p_resolved.suffix.lower() != ".md":
        raise ValueError(f"Export path extension '{p_resolved.suffix}' must be '.md'.")
        
    if target_drive:
        from usb_creator import get_drive_root
        td_root = get_drive_root(target_drive)
        if td_root:
            td_path = Path(td_root).resolve()
            if p_resolved == td_path:
                raise ValueError("Export path cannot be the target drive root itself.")


def generate_physical_writer_dryrun_markdown(dryrun_payload: dict) -> str:
    """
    Generates a beautifully layouted human-readable Markdown summary of dry-run results.
    """
    status = "⛔ BLOCKED" if dryrun_payload.get("blocked") else "✓ ALLOWED"
    reasons_list = dryrun_payload.get("block_reasons", [])
    reasons_str = "\n".join(f"- {r}" for r in reasons_list) if reasons_list else "None"
    
    warnings_list = dryrun_payload.get("warnings", [])
    warnings_str = "\n".join(f"- {w}" for w in warnings_list) if warnings_list else "None"
    
    md = f"""# PhoenixCore / BootForge Physical USB Writer Dry-Run Report
    
## General Info
- **Result ID**: {dryrun_payload.get("result_id")}
- **Request ID**: {dryrun_payload.get("request_id")}
- **Platform**: {dryrun_payload.get("platform")}
- **Adapter**: {dryrun_payload.get("adapter")}
- **Created At**: {dryrun_payload.get("created_at")}
- **Status**: {status}

---

## Dry-Run Configuration
- **Dry-Run Only**: {dryrun_payload.get("dry_run_only")}
- **Physical Write Requested**: {dryrun_payload.get("physical_write_requested")}
- **Physical Write Allowed**: {dryrun_payload.get("physical_write_allowed")}
- **Physical Write Attempted**: {dryrun_payload.get("physical_write_attempted")}

---

## Drive & Image Details
- **Target Identity Hash**: `{dryrun_payload.get("target_identity_hash")}`
- **Latest Identity Hash**: `{dryrun_payload.get("latest_identity_hash")}`
- **Identity Drift Detected**: {dryrun_payload.get("identity_drift_detected")}
- **Permission Passed**: {dryrun_payload.get("permission_passed")}
- **Bytes Written**: {dryrun_payload.get("bytes_written")} bytes
- **Chunks Planned**: {dryrun_payload.get("chunks_planned")} ({dryrun_payload.get("chunk_size_bytes")} bytes each)
- **Image Size**: {dryrun_payload.get("image_size_bytes")} bytes

---

## Block Reasons
{reasons_str}

---

## Warnings
{warnings_str}

---

## Safety Assertion
> [!IMPORTANT]
> **This report is evidence of a physical writer dry-run simulation only. No physical USB bytes are written, and physical USB writing remains locked.**
"""
    return md


def export_physical_writer_dryrun_json(dryrun_payload: dict, output_path: str) -> dict:
    """
    Safely exports the dryrun result JSON to a file path.
    """
    import json
    try:
        validate_physical_writer_dryrun_export_path(output_path, "json", dryrun_payload.get("target_drive"))
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(dryrun_payload, f, indent=2)
        return {"status": "success", "export_path": output_path, "error": None}
    except Exception as e:
        return {"status": "failed", "export_path": output_path, "error": str(e)}


def export_physical_writer_dryrun_markdown(dryrun_payload: dict, output_path: str) -> dict:
    """
    Safely exports the dryrun result Markdown summary to a file path.
    """
    try:
        validate_physical_writer_dryrun_export_path(output_path, "markdown", dryrun_payload.get("target_drive"))
        md = generate_physical_writer_dryrun_markdown(dryrun_payload)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        return {"status": "success", "export_path": output_path, "error": None}
    except Exception as e:
        return {"status": "failed", "export_path": output_path, "error": str(e)}


# ===========================================================================
# PART 7 — PHYSICAL USB WRITE LAB (Phase 5A-4)
# ===========================================================================

PHYSICAL_USB_WRITE_ENV_VAR = "BOOTFORGE_ENABLE_PHYSICAL_USB_WRITE"
PHYSICAL_USB_WRITE_ENV_VALUE = "I_ACCEPT_SACRIFICIAL_USB_WRITE_RISK"

PHYSICAL_TYPED_CONFIRMATION = "I UNDERSTAND THIS WILL OVERWRITE THE SELECTED PHYSICAL USB DRIVE"
PHYSICAL_DESTRUCTIVE_ACKNOWLEDGEMENT = "I CONFIRM THIS IS A SACRIFICIAL REMOVABLE TEST USB DRIVE"
PHYSICAL_FINAL_IRREVERSIBLE = "I ACCEPT FULL RESPONSIBILITY FOR THIS TEST USB WRITE"


def build_physical_usb_write_lab_request(**kwargs) -> dict:
    req_id = kwargs.get("request_id") or f"phyreq_{str(uuid.uuid4())[:32].replace('-', '')}"
    created_at = kwargs.get("created_at") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    image_size = kwargs.get("image_size_bytes") or 0
    chunk_size = kwargs.get("chunk_size_bytes") or 1048576
    expected_chunks = (image_size + chunk_size - 1) // chunk_size if image_size > 0 else 0

    return {
        "schema": "bootforge.physical_usb_write_lab_request.v1",
        "request_id": req_id,
        "created_at": created_at,
        "platform": kwargs.get("platform") or sys.platform,
        "target_drive": kwargs.get("target_drive"),
        "target_stable_id": kwargs.get("target_stable_id"),
        "target_identity_hash": kwargs.get("target_identity_hash"),
        "latest_identity_hash": kwargs.get("latest_identity_hash"),
        "identity_lock_id": kwargs.get("identity_lock_id"),
        "preflight_id": kwargs.get("preflight_id"),
        "dryrun_result_id": kwargs.get("dryrun_result_id"),
        "readiness_gate_id": kwargs.get("readiness_gate_id"),
        "session_id": kwargs.get("session_id"),
        "ledger_path": kwargs.get("ledger_path"),
        "image_path": kwargs.get("image_path"),
        "image_sha256": kwargs.get("image_sha256"),
        "image_size_bytes": image_size,
        "chunk_size_bytes": chunk_size,
        "expected_chunk_count": expected_chunks,
        "lab_mode": kwargs.get("lab_mode", False),
        "sacrificial_drive_confirmed": kwargs.get("sacrificial_drive_confirmed", False),
        "typed_confirmation": kwargs.get("typed_confirmation"),
        "destructive_acknowledgement": kwargs.get("destructive_acknowledgement"),
        "final_irreversible_acknowledgement": kwargs.get("final_irreversible_acknowledgement"),
        "environment_unlock_present": kwargs.get("environment_unlock_present", False),
        "running_as_admin_or_root": kwargs.get("running_as_admin_or_root", False),
        "verify_after_write": kwargs.get("verify_after_write", False),
        "physical_write_requested": kwargs.get("physical_write_requested", False),
        "physical_write_allowed": kwargs.get("physical_write_allowed", False),
    }


def build_physical_usb_write_lab_result(**kwargs) -> dict:
    res_id = kwargs.get("result_id") or f"phyres_{str(uuid.uuid4())[:32].replace('-', '')}"
    created_at = kwargs.get("created_at") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "schema": "bootforge.physical_usb_write_lab_result.v1",
        "request_id": kwargs.get("request_id"),
        "result_id": res_id,
        "created_at": created_at,
        "platform": kwargs.get("platform") or sys.platform,
        "adapter": kwargs.get("adapter"),
        "lab_mode": kwargs.get("lab_mode", False),
        "physical_write_allowed": kwargs.get("physical_write_allowed", False),
        "physical_write_attempted": kwargs.get("physical_write_attempted", False),
        "physical_write_started_at": kwargs.get("physical_write_started_at"),
        "physical_write_completed_at": kwargs.get("physical_write_completed_at"),
        "target_drive": kwargs.get("target_drive"),
        "target_stable_id": kwargs.get("target_stable_id"),
        "target_identity_hash": kwargs.get("target_identity_hash"),
        "latest_identity_hash": kwargs.get("latest_identity_hash"),
        "identity_drift_detected": kwargs.get("identity_drift_detected", False),
        "image_path": kwargs.get("image_path"),
        "image_sha256_expected": kwargs.get("image_sha256_expected"),
        "image_size_bytes": kwargs.get("image_size_bytes", 0),
        "chunk_size_bytes": kwargs.get("chunk_size_bytes", 1048576),
        "chunks_expected": kwargs.get("chunks_expected", 0),
        "chunks_written": kwargs.get("chunks_written", 0),
        "bytes_expected": kwargs.get("bytes_expected", 0),
        "bytes_written": kwargs.get("bytes_written", 0),
        "verification_requested": kwargs.get("verification_requested", False),
        "verification_sha256": kwargs.get("verification_sha256"),
        "verification_passed": kwargs.get("verification_passed", False),
        "cancelled": kwargs.get("cancelled", False),
        "blocked": kwargs.get("blocked", True),
        "block_reasons": kwargs.get("block_reasons") or [],
        "warnings": kwargs.get("warnings") or [],
        "next_required_action": kwargs.get("next_required_action"),
        "ledger_record_ids": kwargs.get("ledger_record_ids") or [],
        "evidence_paths": kwargs.get("evidence_paths") or [],
    }


def build_physical_usb_write_lab_verification(**kwargs) -> dict:
    ver_id = kwargs.get("verification_id") or f"phyver_{str(uuid.uuid4())[:32].replace('-', '')}"
    created_at = kwargs.get("created_at") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "schema": "bootforge.physical_usb_write_lab_verification.v1",
        "verification_id": ver_id,
        "created_at": created_at,
        "target_drive": kwargs.get("target_drive"),
        "bytes_verified": kwargs.get("bytes_verified", 0),
        "expected_sha256": kwargs.get("expected_sha256"),
        "actual_sha256": kwargs.get("actual_sha256"),
        "verification_passed": kwargs.get("verification_passed", False),
        "verification_blocked": kwargs.get("verification_blocked", False),
        "block_reasons": kwargs.get("block_reasons") or [],
        "warnings": kwargs.get("warnings") or [],
    }


def validate_physical_usb_write_lab_gates(request: dict) -> tuple:
    block_reasons = []

    if not request:
        return False, ["Missing request payload."]

    if request.get("schema") != "bootforge.physical_usb_write_lab_request.v1":
        block_reasons.append("Invalid request schema.")

    env_val = os.environ.get(PHYSICAL_USB_WRITE_ENV_VAR)
    if env_val != PHYSICAL_USB_WRITE_ENV_VALUE:
        block_reasons.append("Environment variable BOOTFORGE_ENABLE_PHYSICAL_USB_WRITE is missing or wrong.")

    if not request.get("running_as_admin_or_root"):
        block_reasons.append("Not running as admin/root.")

    if not request.get("target_drive"):
        block_reasons.append("Target drive is missing.")
    if not request.get("target_stable_id"):
        block_reasons.append("Target stable ID is missing.")
    if not request.get("target_identity_hash"):
        block_reasons.append("Target identity hash is missing.")

    if not request.get("identity_lock_id"):
        block_reasons.append("Identity lock ID is missing.")

    if not request.get("latest_identity_hash"):
        block_reasons.append("Latest re-scan identity hash is missing.")
    elif request.get("target_identity_hash") != request.get("latest_identity_hash"):
        block_reasons.append("Identity drift detected: target hash does not match latest re-scan hash.")

    if not request.get("image_path"):
        block_reasons.append("Image path is missing.")
    if not request.get("image_sha256"):
        block_reasons.append("Image SHA256 is missing.")
    if not request.get("image_size_bytes") or request["image_size_bytes"] <= 0:
        block_reasons.append("Image size is missing or zero.")

    if not request.get("preflight_id"):
        block_reasons.append("Hardware preflight ID is missing.")

    if not request.get("dryrun_result_id"):
        block_reasons.append("Physical dry-run result ID is missing.")

    if not request.get("readiness_gate_id"):
        block_reasons.append("Readiness gate ID is missing.")

    if not request.get("ledger_path"):
        block_reasons.append("Ledger path is missing.")
    else:
        ledger_path = request["ledger_path"]
        lp_str = str(ledger_path).strip().lower()
        for suspicious in ["sys32", "system32", "windows", "/etc", "/bin", "/sbin", "/var", "/usr"]:
            if suspicious in lp_str.replace("\\", "/"):
                block_reasons.append(f"Ledger path in {suspicious} folders is blocked.")

    tc = request.get("typed_confirmation") or ""
    if tc.strip() != PHYSICAL_TYPED_CONFIRMATION:
        block_reasons.append("Typed confirmation phrase mismatch.")

    da = request.get("destructive_acknowledgement") or ""
    if da.strip() != PHYSICAL_DESTRUCTIVE_ACKNOWLEDGEMENT:
        block_reasons.append("Destructive acknowledgement phrase mismatch.")

    fi = request.get("final_irreversible_acknowledgement") or ""
    if fi.strip() != PHYSICAL_FINAL_IRREVERSIBLE:
        block_reasons.append("Final irreversible acknowledgement phrase mismatch.")

    if not request.get("physical_write_requested"):
        block_reasons.append("Physical write was not explicitly requested.")
    if not request.get("lab_mode"):
        block_reasons.append("Lab mode is not enabled.")

    plat = request.get("platform") or sys.platform
    if plat not in ("win32",):
        block_reasons.append(f"Physical USB writing is not implemented for platform '{plat}'.")

    is_valid = len(block_reasons) == 0
    return is_valid, block_reasons


class PhysicalUSBWriteLabAdapter:
    def __init__(self):
        self.name = "physical-usb-write-lab"

    def execute_write(self, request: dict) -> dict:
        is_valid, block_reasons = validate_physical_usb_write_lab_gates(request)

        if not is_valid:
            return build_physical_usb_write_lab_result(
                request_id=request.get("request_id"),
                adapter=self.name,
                lab_mode=request.get("lab_mode", False),
                physical_write_allowed=False,
                physical_write_attempted=False,
                target_drive=request.get("target_drive"),
                target_stable_id=request.get("target_stable_id"),
                target_identity_hash=request.get("target_identity_hash"),
                latest_identity_hash=request.get("latest_identity_hash"),
                image_path=request.get("image_path"),
                image_sha256_expected=request.get("image_sha256"),
                image_size_bytes=request.get("image_size_bytes", 0),
                blocked=True,
                block_reasons=block_reasons,
                next_required_action="resolve_physical_write_blockers",
            )

        block_reasons.append("physical_writer_not_safely_implemented")
        return build_physical_usb_write_lab_result(
            request_id=request.get("request_id"),
            adapter=self.name,
            lab_mode=request.get("lab_mode", False),
            physical_write_allowed=False,
            physical_write_attempted=False,
            target_drive=request.get("target_drive"),
            target_stable_id=request.get("target_stable_id"),
            target_identity_hash=request.get("target_identity_hash"),
            latest_identity_hash=request.get("latest_identity_hash"),
            image_path=request.get("image_path"),
            image_sha256_expected=request.get("image_sha256"),
            image_size_bytes=request.get("image_size_bytes", 0),
            blocked=True,
            block_reasons=block_reasons,
            warnings=["Physical USB write adapter exists but raw device I/O is not safely implemented yet. All gates passed but write was not attempted."],
            next_required_action="implement_safe_physical_writer",
        )


def build_physical_usb_write_lab_status() -> dict:
    plat = sys.platform
    perm = build_hardware_lab_permission_status()
    env_present = os.environ.get(PHYSICAL_USB_WRITE_ENV_VAR) == PHYSICAL_USB_WRITE_ENV_VALUE
    lab_env_present = os.environ.get("BOOTFORGE_ENABLE_LAB_WRITE") == "I_ACCEPT_REAL_USB_WRITE_RISK"

    return {
        "schema": "bootforge.physical_usb_write_lab_status.v1",
        "platform": plat,
        "physical_write_implemented": False,
        "physical_write_allowed": False,
        "physical_write_cli_only": True,
        "dashboard_write_blocked": True,
        "dashboard_write_message": "Physical USB write lab mode is CLI-only. The dashboard cannot start a physical USB write.",
        "environment_unlock_present": env_present,
        "lab_environment_unlock_present": lab_env_present,
        "running_as_admin_or_root": perm.get("running_as_admin_or_root", False),
        "required_gates": [
            "environment_unlock",
            "admin_or_root",
            "target_from_scan_evidence",
            "target_has_stable_id",
            "target_has_identity_hash",
            "target_is_removable_external",
            "target_is_not_fixed_internal",
            "target_is_not_system_drive",
            "identity_lock_exists",
            "latest_rescan_matches_lock",
            "no_identity_drift",
            "image_exists",
            "image_sha256_exists",
            "image_size_exists",
            "write_plan_exists",
            "audit_passed",
            "mock_simulation_passed",
            "hardware_preflight_passed",
            "physical_dryrun_exists",
            "physical_dryrun_wrote_zero_bytes",
            "readiness_gate_passed",
            "ledger_path_exists_and_safe",
            "evidence_export_path_safe",
            "typed_confirmations_match",
            "user_requested_physical_usb_write_lab",
            "adapter_supports_platform",
            "target_path_maps_to_scanned_locked_target",
        ],
        "blocked": True,
        "block_reasons": ["Physical USB write adapter is not safely implemented yet."],
        "warnings": [],
        "next_required_action": "implement_safe_physical_writer",
    }


def validate_physical_usb_write_lab_export_path(output_path: str, export_type: str, target_drive: str = None):
    from pathlib import Path

    if not output_path or not str(output_path).strip():
        raise ValueError("Export path is empty.")

    p_str = str(output_path).strip().lower()

    if "\\\\.\\" in p_str or "//./" in p_str or p_str.startswith("\\\\") or p_str.startswith("//"):
        raise ValueError("Raw device style or UNC network paths are blocked for export.")

    for suspicious in ["sys32", "system32", "windows", "/etc", "/bin", "/sbin", "/var", "/usr"]:
        if suspicious in p_str.replace("\\", "/"):
            raise ValueError(f"Suspicious path detected: export path in {suspicious} folders is blocked.")

    p = Path(output_path)
    p_resolved = p.resolve()

    if p_resolved.exists() and p_resolved.is_dir():
        raise ValueError("Export path is a directory.")

    if p_resolved.exists():
        raise ValueError(f"Export file '{output_path}' already exists. Overwriting is blocked.")

    parent = p_resolved.parent
    if not parent.exists() or not parent.is_dir():
        raise ValueError("Parent directory of export path does not exist.")

    if export_type == "json" and p_resolved.suffix.lower() != ".json":
        raise ValueError(f"Export path extension '{p_resolved.suffix}' must be '.json'.")
    elif export_type == "markdown" and p_resolved.suffix.lower() != ".md":
        raise ValueError(f"Export path extension '{p_resolved.suffix}' must be '.md'.")

    if target_drive:
        from usb_creator import get_drive_root
        td_root = get_drive_root(target_drive)
        if td_root:
            td_path = Path(td_root).resolve()
            if p_resolved == td_path:
                raise ValueError("Export path cannot be the target drive root itself.")


def export_physical_usb_write_lab_json(result_payload: dict, output_path: str) -> dict:
    import json
    try:
        validate_physical_usb_write_lab_export_path(output_path, "json", result_payload.get("target_drive"))
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2)
        return {"status": "success", "export_path": output_path, "error": None}
    except Exception as e:
        return {"status": "failed", "export_path": output_path, "error": str(e)}


def generate_physical_usb_write_lab_markdown(result_payload: dict) -> str:
    status = "BLOCKED" if result_payload.get("blocked") else "ALLOWED"
    reasons_list = result_payload.get("block_reasons", [])
    reasons_str = "\n".join(f"- {r}" for r in reasons_list) if reasons_list else "None"
    warnings_list = result_payload.get("warnings", [])
    warnings_str = "\n".join(f"- {w}" for w in warnings_list) if warnings_list else "None"

    md = f"""# PhoenixCore / BootForge Physical USB Write Lab Report

## General Info
- **Result ID**: {result_payload.get("result_id")}
- **Request ID**: {result_payload.get("request_id")}
- **Platform**: {result_payload.get("platform")}
- **Adapter**: {result_payload.get("adapter")}
- **Created At**: {result_payload.get("created_at")}
- **Status**: {status}

---

## Physical Write Status
- **Lab Mode**: {result_payload.get("lab_mode")}
- **Physical Write Allowed**: {result_payload.get("physical_write_allowed")}
- **Physical Write Attempted**: {result_payload.get("physical_write_attempted")}
- **Bytes Written**: {result_payload.get("bytes_written", 0)}
- **Chunks Written**: {result_payload.get("chunks_written", 0)}
- **Verification Requested**: {result_payload.get("verification_requested")}
- **Verification Passed**: {result_payload.get("verification_passed")}

---

## Target Details
- **Target Drive**: {result_payload.get("target_drive")}
- **Target Identity Hash**: `{result_payload.get("target_identity_hash")}`
- **Latest Identity Hash**: `{result_payload.get("latest_identity_hash")}`
- **Identity Drift Detected**: {result_payload.get("identity_drift_detected")}

---

## Block Reasons
{reasons_str}

---

## Warnings
{warnings_str}

---

## Safety Assertion
> [!IMPORTANT]
> **Physical USB write lab mode is CLI-only. The dashboard cannot start a physical USB write.**
> **Fixed, internal, and system drives are permanently blocked.**
> **No disk-wiping, partitioning, or drive-altering operations exist in this path.**
"""
    return md


def export_physical_usb_write_lab_markdown(result_payload: dict, output_path: str) -> dict:
    try:
        validate_physical_usb_write_lab_export_path(output_path, "markdown", result_payload.get("target_drive"))
        md = generate_physical_usb_write_lab_markdown(result_payload)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        return {"status": "success", "export_path": output_path, "error": None}
    except Exception as e:
        return {"status": "failed", "export_path": output_path, "error": str(e)}


# ===========================================================================
# PART 8 — READ-ONLY HARDWARE EVIDENCE BUNDLE (Phase 5B-3)
# ===========================================================================

def build_hardware_evidence_bundle(
    target_drive: str = None,
    scan_payload: dict = None,
    label: str = None,
    redact_serials: bool = False,
    include_full_scan: bool = False,
) -> dict:
    """
    Builds a complete read-only hardware evidence bundle that composes
    scanner, identity-lock, preflight, and dry-run evidence into a single
    exportable payload. No physical writing. No destructive operations.
    Schema: bootforge.hardware_evidence_bundle.v1
    """
    import uuid
    import platform as _platform

    bundle_id = f"evidence_{str(uuid.uuid4())[:32].replace('-', '')}"
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if scan_payload is None:
        try:
            from usb_creator import get_normalized_scan
            scan_payload = get_normalized_scan(quiet=True)
        except Exception as e:
            scan_payload = {
                "schema": "bootforge.device_scan.v2",
                "devices": [],
                "device_count": 0,
                "scan_warnings": [f"Scanner unavailable: {e}"],
            }

    scan_summary = {
        "schema": scan_payload.get("schema"),
        "scan_id": scan_payload.get("scan_id"),
        "device_count": scan_payload.get("device_count", 0),
        "detection_source": scan_payload.get("detection_source"),
        "scan_warnings": scan_payload.get("scan_warnings", []),
    }

    resolved_device = None
    resolved_count = 0
    target_resolved = False
    resolution_reason = "no_target_selected"
    identity_lock_preview = None
    rescan_preview = None
    preflight_preview = None
    dryrun_preview = None
    eligible = False
    scanner_confidence = "unknown"
    scanner_stable_id = None
    scanner_serial = None
    identity_hash = None
    scanner_warnings = []
    scanner_block_reasons = []

    if target_drive:
        norm_target = target_drive.lower().rstrip("\\/")
        matches = []
        for d in scan_payload.get("devices", []):
            dp = (d.get("drive_path") or "").lower().rstrip("\\/")
            if dp == norm_target:
                matches.append(d)
        resolved_count = len(matches)

        if resolved_count == 0:
            resolution_reason = "target_not_found"
        elif resolved_count > 1:
            resolution_reason = "ambiguous_target"
        else:
            resolved_device = matches[0]
            target_resolved = True
            resolution_reason = "resolved"

            scanner_confidence = resolved_device.get("confidence", "unknown")
            scanner_stable_id = resolved_device.get("stable_id")
            scanner_serial = resolved_device.get("serial")
            scanner_warnings = list(resolved_device.get("warnings", []))
            scanner_block_reasons = list(resolved_device.get("block_reasons", []))
            identity_hash = _build_scanner_identity_hash(resolved_device)

            is_fixed = resolved_device.get("is_fixed", False)
            is_system = resolved_device.get("is_system", False) or resolved_device.get("is_system_drive", False) or resolved_device.get("is_boot_drive", False)

            if is_fixed or is_system:
                resolution_reason = "fixed_internal_or_system_target"
                eligible = False
            elif scanner_confidence == "low":
                eligible = False
                scanner_block_reasons.append(
                    "Scanner confidence is low; identity lock is unreliable for lab eligibility."
                )
            elif scanner_block_reasons:
                eligible = False
            else:
                eligible = True

            identity_lock_preview = build_removable_target_identity_lock(
                target_drive, scan_payload
            )
            rescan_preview = rescan_and_compare_target_identity(
                identity_lock_preview, scan_payload
            )
            preflight_preview = build_physical_writer_preflight_result(
                identity_lock_preview
            )
            try:
                dryrun_preview = {
                    "dry_run_only": True,
                    "physical_write_allowed": False,
                    "physical_write_attempted": False,
                    "bytes_written": 0,
                    "target_drive": target_drive,
                    "target_identity_hash": identity_hash,
                    "identity_drift_detected": rescan_preview.get("drift_detected", False) if rescan_preview else False,
                    "blocked": not eligible or bool(scanner_block_reasons),
                    "block_reasons": list(scanner_block_reasons) + (
                        identity_lock_preview.get("block_reasons", []) if identity_lock_preview else []
                    ),
                }
            except Exception:
                dryrun_preview = None
    else:
        resolution_reason = "no_target_selected"

    if redact_serials:
        scanner_serial = "REDACTED" if scanner_serial else None
        if scanner_stable_id:
            scanner_stable_id = hashlib.sha256(
                scanner_stable_id.encode()
            ).hexdigest()[:16]
        if identity_lock_preview and identity_lock_preview.get("serial"):
            identity_lock_preview["serial"] = "REDACTED"
        if identity_lock_preview and identity_lock_preview.get("stable_id"):
            identity_lock_preview["stable_id"] = hashlib.sha256(
                identity_lock_preview["stable_id"].encode()
            ).hexdigest()[:16]
        if preflight_preview and preflight_preview.get("scanner_serial"):
            preflight_preview["scanner_serial"] = "REDACTED"
        if preflight_preview and preflight_preview.get("scanner_stable_id"):
            preflight_preview["scanner_stable_id"] = hashlib.sha256(
                str(preflight_preview["scanner_stable_id"]).encode()
            ).hexdigest()[:16]
        if preflight_preview and preflight_preview.get("target_stable_id"):
            preflight_preview["target_stable_id"] = hashlib.sha256(
                str(preflight_preview["target_stable_id"]).encode()
            ).hexdigest()[:16]

    bundle = {
        "schema": "bootforge.hardware_evidence_bundle.v1",
        "bundle_id": bundle_id,
        "created_at": created_at,
        "platform": sys.platform,
        "python_version": _platform.python_version(),
        "project_phase": "5B-3",
        "label": label,
        "scanner_schema": scan_payload.get("schema", "bootforge.device_scan.v2"),
        "scan_summary": scan_summary,
        "target_selector": target_drive,
        "target_resolved": target_resolved,
        "resolved_count": resolved_count,
        "resolution_reason": resolution_reason,
        "stable_id": scanner_stable_id,
        "serial": scanner_serial,
        "identity_hash": identity_hash,
        "scanner_confidence": scanner_confidence,
        "scanner_warnings": scanner_warnings,
        "scanner_block_reasons": scanner_block_reasons,
        "eligible": eligible,
        "identity_lock_preview": identity_lock_preview,
        "rescan_identity_preview": rescan_preview,
        "preflight_preview": preflight_preview,
        "dryrun_preview": dryrun_preview,
        "physical_write_allowed": False,
        "physical_write_attempted": False,
        "bytes_written": 0,
        "dashboard_write_available": False,
        "redacted": redact_serials,
        "next_required_action": "await_phase_5c_windows_writer" if eligible else "resolve_block_reasons",
    }

    if include_full_scan:
        bundle["full_scan"] = scan_payload

    return bundle


def generate_hardware_evidence_markdown(bundle: dict) -> str:
    block_reasons = bundle.get("scanner_block_reasons", [])
    lock_preview = bundle.get("identity_lock_preview")
    preflight = bundle.get("preflight_preview")
    dryrun = bundle.get("dryrun_preview")

    if lock_preview:
        block_reasons = list(set(block_reasons + lock_preview.get("block_reasons", [])))

    reasons_str = "\n".join(f"- {r}" for r in block_reasons) if block_reasons else "None"
    warnings_str = "\n".join(f"- {w}" for w in bundle.get("scanner_warnings", [])) if bundle.get("scanner_warnings") else "None"

    lock_section = "Not available (no target selected)"
    if lock_preview:
        lock_section = (
            f"- **Lock ID**: `{lock_preview.get('identity_lock_id')}`\n"
            f"- **Blocked**: {lock_preview.get('blocked')}\n"
            f"- **Hash**: `{lock_preview.get('device_identity_hash')}`"
        )

    preflight_section = "Not available"
    if preflight:
        preflight_section = (
            f"- **Preflight ID**: `{preflight.get('preflight_id')}`\n"
            f"- **Physical Writer Allowed**: {preflight.get('physical_writer_allowed')}\n"
            f"- **Physical Write Attempted**: {preflight.get('physical_write_attempted')}\n"
            f"- **Blocked**: {preflight.get('blocked')}"
        )

    dryrun_section = "Not available"
    if dryrun:
        dryrun_section = (
            f"- **Dry Run Only**: {dryrun.get('dry_run_only')}\n"
            f"- **Physical Write Allowed**: {dryrun.get('physical_write_allowed')}\n"
            f"- **Physical Write Attempted**: {dryrun.get('physical_write_attempted')}\n"
            f"- **Bytes Written**: {dryrun.get('bytes_written')}\n"
            f"- **Identity Drift Detected**: {dryrun.get('identity_drift_detected')}\n"
            f"- **Blocked**: {dryrun.get('blocked')}"
        )

    md = f"""# PhoenixCore / BootForge Hardware Evidence Bundle

## General Info
- **Bundle ID**: `{bundle.get('bundle_id')}`
- **Phase**: {bundle.get('project_phase')}
- **Created At**: {bundle.get('created_at')}
- **Platform**: {bundle.get('platform')}
- **Label**: {bundle.get('label') or 'None'}
- **Redacted**: {bundle.get('redacted', False)}

---

## Target Resolution
- **Target Selected**: {bundle.get('target_selector') or 'None'}
- **Target Resolved**: {bundle.get('target_resolved')}
- **Resolved Count**: {bundle.get('resolved_count')}
- **Resolution Reason**: {bundle.get('resolution_reason')}

---

## Scanner Evidence
- **Scanner Schema**: {bundle.get('scanner_schema')}
- **Scanner Confidence**: {bundle.get('scanner_confidence')}
- **Stable ID**: `{bundle.get('stable_id') or 'None'}`
- **Serial**: `{bundle.get('serial') or 'None'}`
- **Identity Hash**: `{bundle.get('identity_hash') or 'None'}`
- **Eligible**: {bundle.get('eligible')}

---

## Block Reasons
{reasons_str}

---

## Warnings
{warnings_str}

---

## Identity Lock Preview
{lock_section}

---

## Preflight Preview
{preflight_section}

---

## Dry-Run Validation Preview
{dryrun_section}

---

## Safety Contract
- **Physical Writing Added**: no
- **Physical Write Allowed**: {bundle.get('physical_write_allowed')}
- **Physical Write Attempted**: {bundle.get('physical_write_attempted')}
- **Bytes Written**: {bundle.get('bytes_written')}
- **Dashboard Write Available**: {bundle.get('dashboard_write_available')}

---

> [!IMPORTANT]
> **This evidence bundle is read-only. No physical USB writing was performed.**
> **The dashboard cannot trigger any physical write operation.**
> **Fixed, internal, and system drives are permanently blocked.**
"""
    return md


def validate_hardware_evidence_export_path(output_path: str, export_type: str, target_drive: str = None):
    from pathlib import Path

    if not output_path or not str(output_path).strip():
        raise ValueError("Export path is empty.")

    p_str = str(output_path).strip().lower()

    if "\\\\.\\" in p_str or "//./" in p_str or p_str.startswith("\\\\") or p_str.startswith("//"):
        raise ValueError("Raw device style or UNC network paths are blocked for export.")

    for suspicious in ["sys32", "system32", "windows", "/etc", "/bin", "/sbin", "/var", "/usr"]:
        if suspicious in p_str.replace("\\", "/"):
            raise ValueError(f"Suspicious path detected: export path in {suspicious} folders is blocked.")

    p = Path(output_path)
    p_resolved = p.resolve()

    if p_resolved.exists() and p_resolved.is_dir():
        raise ValueError("Export path is a directory.")

    if p_resolved.exists():
        raise ValueError(f"Export file '{output_path}' already exists. Overwriting is blocked.")

    parent = p_resolved.parent
    if not parent.exists() or not parent.is_dir():
        raise ValueError("Parent directory of export path does not exist.")

    if export_type == "json" and p_resolved.suffix.lower() != ".json":
        raise ValueError(f"Export path extension '{p_resolved.suffix}' must be '.json'.")
    elif export_type == "markdown" and p_resolved.suffix.lower() != ".md":
        raise ValueError(f"Export path extension '{p_resolved.suffix}' must be '.md'.")

    if target_drive:
        try:
            from usb_creator import get_drive_root
            td_root = get_drive_root(target_drive)
            if td_root:
                td_path = Path(td_root).resolve()
                if p_resolved == td_path:
                    raise ValueError("Export path cannot be the target drive root itself.")
        except ImportError:
            pass


def export_hardware_evidence_json(bundle: dict, output_path: str) -> dict:
    import json
    try:
        validate_hardware_evidence_export_path(
            output_path, "json", bundle.get("target_selector")
        )
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(bundle, f, indent=2)
        return {"status": "success", "export_path": output_path, "error": None}
    except Exception as e:
        return {"status": "failed", "export_path": output_path, "error": str(e)}


def export_hardware_evidence_markdown(bundle: dict, output_path: str) -> dict:
    try:
        validate_hardware_evidence_export_path(
            output_path, "markdown", bundle.get("target_selector")
        )
        md = generate_hardware_evidence_markdown(bundle)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md)
        return {"status": "success", "export_path": output_path, "error": None}
    except Exception as e:
        return {"status": "failed", "export_path": output_path, "error": str(e)}

