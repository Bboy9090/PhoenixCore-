#!/usr/bin/env python3
"""Write one verified image to one explicitly authorized Windows sacrificial drive.

This tool is CLI-only and fail-closed. It consumes a live read-only drive-evidence
receipt, immediately rescans the target, requires an exact identity match, writes
no more than the verified image size, and validates every written byte by SHA-256.
It never formats, partitions, silently dismounts, or selects a target automatically.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO, Callable

try:
    from scripts.hardware.capture_windows_drive_evidence import (
        EvidenceError,
        canonical_json,
        normalize_disk_record,
        parse_raw_target,
        query_windows_disk,
        sha256_payload,
    )
except ModuleNotFoundError:
    from capture_windows_drive_evidence import (  # type: ignore
        EvidenceError,
        canonical_json,
        normalize_disk_record,
        parse_raw_target,
        query_windows_disk,
        sha256_payload,
    )

SCHEMA_VERSION = "bws.sacrificial-drive-write/v1"
DRIVE_EVIDENCE_SCHEMA = "bws.physical-drive-evidence/v1"
UNLOCK_ENV = "BWS_ENABLE_SACRIFICIAL_DRIVE_WRITE"
UNLOCK_VALUE = "I_ACCEPT_COMPLETE_DESTRUCTION_OF_NAMED_TEST_DRIVE"
SOURCE_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
DEFAULT_CHUNK_SIZE = 1024 * 1024


class WriteGateError(RuntimeError):
    """Raised when a destructive-operation gate is not satisfied."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def file_sha256(path: Path, *, byte_limit: int | None = None) -> str:
    digest = hashlib.sha256()
    remaining = byte_limit
    with path.open("rb") as stream:
        while remaining is None or remaining > 0:
            read_size = DEFAULT_CHUNK_SIZE
            if remaining is not None:
                read_size = min(read_size, remaining)
            chunk = stream.read(read_size)
            if not chunk:
                break
            digest.update(chunk)
            if remaining is not None:
                remaining -= len(chunk)
    if remaining not in (None, 0):
        raise WriteGateError("Source image ended before the declared byte count.")
    return digest.hexdigest()


def verify_embedded_digest(payload: dict[str, Any], digest_field: str) -> str:
    expected = payload.get(digest_field)
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise WriteGateError(f"{digest_field} is missing or invalid.")
    body = dict(payload)
    body.pop(digest_field, None)
    actual = hashlib.sha256(canonical_json(body)).hexdigest()
    if actual != expected:
        raise WriteGateError(f"{digest_field} does not match the receipt contents.")
    return actual


def load_drive_evidence(path: Path) -> dict[str, Any]:
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WriteGateError(f"Drive evidence could not be read: {exc}") from exc

    if receipt.get("schema_version") != DRIVE_EVIDENCE_SCHEMA:
        raise WriteGateError("Unsupported physical-drive evidence schema.")
    verify_embedded_digest(receipt, "receipt_sha256")
    if receipt.get("evidence_source") != "live":
        raise WriteGateError("Fixture evidence cannot authorize a physical write.")
    if receipt.get("hardware_observed") is not True:
        raise WriteGateError(
            "Drive evidence does not contain a live hardware observation."
        )
    if receipt.get("hardware_validated") is not False:
        raise WriteGateError("Pre-write evidence must not claim hardware validation.")
    if receipt.get("physical_write_attempted") is not False:
        raise WriteGateError("Drive evidence is not a clean pre-write receipt.")
    if receipt.get("bytes_written") != 0:
        raise WriteGateError("Drive evidence reports nonzero prior writes.")

    disk = receipt.get("disk")
    if not isinstance(disk, dict):
        raise WriteGateError("Drive evidence is missing the disk record.")
    if disk.get("write_candidate") is not True:
        reasons = disk.get("write_block_reasons") or ["unspecified"]
        raise WriteGateError(f"Drive evidence blocks writing: {reasons}")
    if disk.get("is_boot") or disk.get("is_system"):
        raise WriteGateError(
            "Boot and system disks are never valid sacrificial targets."
        )
    if not disk.get("identity_sha256"):
        raise WriteGateError("Drive evidence is missing its identity SHA-256.")
    return receipt


def expected_authorization(target: str, identity_sha256: str, size_bytes: int) -> str:
    return (
        f"I AUTHORIZE COMPLETE DESTRUCTION OF {target.upper()} "
        f"IDENTITY {identity_sha256} SIZE {size_bytes}"
    )


def is_windows_admin() -> bool:
    if sys.platform != "win32":
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def verify_live_identity(
    *,
    evidence: dict[str, Any],
    query_disk: Callable[[int], dict[str, Any]] = query_windows_disk,
) -> dict[str, Any]:
    disk = evidence["disk"]
    target = str(disk["target"])
    disk_number = parse_raw_target(target)
    fresh = normalize_disk_record(query_disk(disk_number), target)

    if fresh["identity_sha256"] != disk["identity_sha256"]:
        raise WriteGateError("Fresh target identity does not match the evidence lock.")
    if fresh["size_bytes"] != disk["size_bytes"]:
        raise WriteGateError("Fresh target capacity does not match the evidence lock.")
    if fresh["is_boot"] or fresh["is_system"]:
        raise WriteGateError("Fresh scan identifies a boot or system disk.")
    if fresh["write_candidate"] is not True:
        raise WriteGateError(
            f"Fresh scan blocks writing: {fresh['write_block_reasons']}"
        )
    return fresh


def validate_write_request(
    *,
    evidence: dict[str, Any],
    image_path: Path,
    target: str,
    authorization: str,
    source_commit: str,
    execute: bool,
    environment: dict[str, str] | None = None,
    admin: bool | None = None,
    query_disk: Callable[[int], dict[str, Any]] = query_windows_disk,
) -> dict[str, Any]:
    environment = environment if environment is not None else os.environ
    disk = evidence["disk"]
    locked_target = str(disk["target"]).upper()
    target = target.upper()

    parse_raw_target(target)
    if target != locked_target:
        raise WriteGateError("Requested target does not match the evidence receipt.")
    if environment.get(UNLOCK_ENV) != UNLOCK_VALUE:
        raise WriteGateError(f"Required environment unlock {UNLOCK_ENV} is absent.")
    if not SOURCE_COMMIT_RE.fullmatch(source_commit):
        raise WriteGateError("Writer source commit must be a 40-character SHA.")
    if not image_path.is_file():
        raise WriteGateError("Source image does not exist or is not a regular file.")

    image_size = image_path.stat().st_size
    if image_size <= 0:
        raise WriteGateError("Source image is empty.")
    if image_size > int(disk["size_bytes"]):
        raise WriteGateError("Source image is larger than the target drive.")

    required_authorization = expected_authorization(
        target,
        str(disk["identity_sha256"]),
        int(disk["size_bytes"]),
    )
    if authorization != required_authorization:
        raise WriteGateError("Sacrificial-drive authorization phrase does not match.")
    if execute is not True:
        raise WriteGateError("Physical write requires the explicit --execute flag.")

    if admin is None:
        admin = is_windows_admin()
    if not admin:
        raise WriteGateError("Physical write requires an elevated Windows process.")

    fresh = verify_live_identity(evidence=evidence, query_disk=query_disk)
    image_hash = file_sha256(image_path)
    return {
        "target": target,
        "identity_sha256": fresh["identity_sha256"],
        "target_size_bytes": fresh["size_bytes"],
        "image_path": str(image_path.resolve()),
        "image_size_bytes": image_size,
        "image_sha256": image_hash,
        "byte_cap": image_size,
        "source_commit": source_commit,
        "authorization": required_authorization,
        "fresh_scan": fresh,
    }


def open_windows_raw_device(target: str) -> BinaryIO:
    if sys.platform != "win32":
        raise WriteGateError("Physical writing is implemented only for Windows.")
    parse_raw_target(target)

    import msvcrt
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE

    generic_read = 0x80000000
    generic_write = 0x40000000
    open_existing = 3
    file_attribute_normal = 0x80
    file_flag_write_through = 0x80000000
    invalid_handle = wintypes.HANDLE(-1).value

    handle = create_file(
        target,
        generic_read | generic_write,
        0,
        None,
        open_existing,
        file_attribute_normal | file_flag_write_through,
        None,
    )
    if handle == invalid_handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        descriptor = msvcrt.open_osfhandle(handle, os.O_RDWR | os.O_BINARY)
    except Exception:
        kernel32.CloseHandle(handle)
        raise
    return os.fdopen(descriptor, "r+b", buffering=0)


def write_and_verify(
    *,
    image_path: Path,
    target_stream: BinaryIO,
    byte_cap: int,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> dict[str, Any]:
    if byte_cap != image_path.stat().st_size or byte_cap <= 0:
        raise WriteGateError("Byte cap must exactly equal the positive image size.")
    if chunk_size <= 0:
        raise WriteGateError("Chunk size must be positive.")

    source_digest = hashlib.sha256()
    bytes_written = 0
    target_stream.seek(0)
    with image_path.open("rb") as source:
        while bytes_written < byte_cap:
            chunk = source.read(min(chunk_size, byte_cap - bytes_written))
            if not chunk:
                raise WriteGateError("Source image ended before the byte cap.")
            source_digest.update(chunk)
            written = target_stream.write(chunk)
            if written != len(chunk):
                raise WriteGateError(
                    f"Short write after {bytes_written} bytes: expected "
                    f"{len(chunk)}, wrote {written}."
                )
            bytes_written += written

        if source.read(1):
            raise WriteGateError("Source image contains data beyond the byte cap.")

    target_stream.flush()
    try:
        os.fsync(target_stream.fileno())
    except (AttributeError, OSError):
        pass

    target_stream.seek(0)
    readback_digest = hashlib.sha256()
    bytes_read = 0
    while bytes_read < byte_cap:
        chunk = target_stream.read(min(chunk_size, byte_cap - bytes_read))
        if not chunk:
            raise WriteGateError("Read-back ended before the written byte count.")
        readback_digest.update(chunk)
        bytes_read += len(chunk)

    source_hash = source_digest.hexdigest()
    readback_hash = readback_digest.hexdigest()
    if bytes_written != byte_cap or bytes_read != byte_cap:
        raise WriteGateError(
            "Write or read-back byte count does not match the byte cap."
        )
    if source_hash != readback_hash:
        raise WriteGateError("Full read-back SHA-256 does not match the source image.")

    return {
        "bytes_expected": byte_cap,
        "bytes_written": bytes_written,
        "bytes_read_back": bytes_read,
        "source_sha256": source_hash,
        "readback_sha256": readback_hash,
        "verification_passed": True,
    }


def build_result(
    *,
    plan: dict[str, Any],
    write_result: dict[str, Any],
    started_at: str,
    completed_at: str,
) -> dict[str, Any]:
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "started_at": started_at,
        "completed_at": completed_at,
        "source_commit": plan["source_commit"],
        "target": plan["target"],
        "target_identity_sha256": plan["identity_sha256"],
        "target_size_bytes": plan["target_size_bytes"],
        "image_path": plan["image_path"],
        "image_size_bytes": plan["image_size_bytes"],
        "image_sha256": plan["image_sha256"],
        "byte_cap": plan["byte_cap"],
        "physical_write_attempted": True,
        "physical_write_completed": True,
        "readback_completed": True,
        "verification_passed": True,
        "hardware_validated": False,
        "classification": "hardware-write-readback-verified",
        "next_required_action": "named-machine-boot-test",
        **write_result,
    }
    receipt["receipt_sha256"] = sha256_payload(receipt)
    return receipt


def write_json_atomic(payload: dict[str, Any], destination: Path) -> None:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=destination.parent,
        delete=False,
    ) as temporary:
        json.dump(payload, temporary, indent=2, sort_keys=True)
        temporary.write("\n")
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drive-receipt", type=Path, required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence = load_drive_evidence(args.drive_receipt)
    plan = validate_write_request(
        evidence=evidence,
        image_path=args.image,
        target=args.target,
        authorization=args.authorization,
        source_commit=args.source_commit,
        execute=args.execute,
    )

    started_at = utc_now_iso()
    with open_windows_raw_device(plan["target"]) as target_stream:
        write_result = write_and_verify(
            image_path=args.image,
            target_stream=target_stream,
            byte_cap=plan["byte_cap"],
        )
    completed_at = utc_now_iso()

    receipt = build_result(
        plan=plan,
        write_result=write_result,
        started_at=started_at,
        completed_at=completed_at,
    )
    write_json_atomic(receipt, args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EvidenceError, WriteGateError, OSError, json.JSONDecodeError) as exc:
        print(f"SACRIFICIAL_WRITE_BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
