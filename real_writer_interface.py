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
