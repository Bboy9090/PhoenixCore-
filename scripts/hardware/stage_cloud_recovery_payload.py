#!/usr/bin/env python3
"""Stage a cloud recovery payload locally with resumable, read-only source handling."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, BinaryIO

SCHEMA = "phoenix_key.cloud_recovery_stage.v1"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
MD5_RE = re.compile(r"^[0-9a-fA-F]{32}$")
CHUNK_SIZE = 4 * 1024 * 1024


class CloudStageError(RuntimeError):
    """Raised when a cloud payload cannot be staged safely."""


def file_digest(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(CHUNK_SIZE)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def prefix_digest(path: Path, byte_count: int, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    remaining = byte_count
    with path.open("rb") as stream:
        while remaining:
            chunk = stream.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                raise CloudStageError("Source ended before the staged partial prefix.")
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def verify_partial_prefix(source: Path, partial: Path) -> int:
    if not partial.exists():
        return 0
    if not partial.is_file():
        raise CloudStageError("Partial staging path is not a regular file.")
    partial_size = partial.stat().st_size
    source_size = source.stat().st_size
    if partial_size > source_size:
        raise CloudStageError("Partial staging file is larger than the cloud payload.")
    if partial_size == 0:
        return 0
    if file_digest(partial, "sha256") != prefix_digest(source, partial_size):
        raise CloudStageError(
            "Partial staging file does not match the cloud payload prefix; resume is unsafe."
        )
    return partial_size


def copy_remaining(
    source_stream: BinaryIO,
    partial_stream: BinaryIO,
    *,
    start_offset: int,
    stop_after_bytes: int | None = None,
) -> tuple[int, bool]:
    source_stream.seek(start_offset)
    partial_stream.seek(start_offset)
    copied = 0
    interrupted = False
    while True:
        if stop_after_bytes is not None and copied >= stop_after_bytes:
            interrupted = True
            break
        limit = CHUNK_SIZE
        if stop_after_bytes is not None:
            limit = min(limit, stop_after_bytes - copied)
            if limit <= 0:
                interrupted = True
                break
        chunk = source_stream.read(limit)
        if not chunk:
            break
        written = partial_stream.write(chunk)
        if written != len(chunk):
            raise CloudStageError(
                f"Short local staging write: expected {len(chunk)}, wrote {written}."
            )
        copied += written
    partial_stream.flush()
    os.fsync(partial_stream.fileno())
    return copied, interrupted


def stage_cloud_payload(
    *,
    source_file: Path,
    destination: Path,
    provider: str,
    provider_file_id: str,
    provider_name: str,
    provider_size_bytes: int,
    provider_md5: str | None = None,
    expected_sha256: str | None = None,
    stop_after_bytes: int | None = None,
) -> dict[str, Any]:
    if not source_file.is_file():
        raise CloudStageError("Materialized cloud payload is not a regular file.")
    if not provider.strip() or not provider_file_id.strip():
        raise CloudStageError("Cloud provider and provider file ID are required.")
    if provider_size_bytes <= 0:
        raise CloudStageError("Cloud provider size must be positive.")

    actual_source_size = source_file.stat().st_size
    if actual_source_size != provider_size_bytes:
        raise CloudStageError(
            "Materialized payload size does not match cloud metadata."
        )

    provider_md5_normalized = (provider_md5 or "").strip().lower()
    if provider_md5_normalized and not MD5_RE.fullmatch(provider_md5_normalized):
        raise CloudStageError("Cloud MD5 metadata is malformed.")
    expected_sha256_normalized = (expected_sha256 or "").strip().lower()
    if expected_sha256_normalized and not SHA256_RE.fullmatch(
        expected_sha256_normalized
    ):
        raise CloudStageError("Expected SHA-256 is malformed.")

    source_resolved = source_file.resolve()
    destination = destination.resolve()
    partial = destination.with_name(destination.name + ".partial")
    if destination == source_resolved or partial == source_resolved:
        raise CloudStageError(
            "Cloud staging destination must be distinct from the materialized source."
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    resume_offset = verify_partial_prefix(source_file, partial)

    with source_file.open("rb") as source_stream:
        mode = "r+b" if partial.exists() else "w+b"
        with partial.open(mode) as partial_stream:
            copied, interrupted = copy_remaining(
                source_stream,
                partial_stream,
                start_offset=resume_offset,
                stop_after_bytes=stop_after_bytes,
            )

    staged_size = partial.stat().st_size
    complete = not interrupted and staged_size == provider_size_bytes
    observed_md5 = file_digest(partial, "md5") if complete else None
    observed_sha256 = file_digest(partial, "sha256") if complete else None
    md5_matches = (
        bool(provider_md5_normalized)
        and observed_md5 == provider_md5_normalized
        if complete
        else False
    )
    sha256_matches = (
        bool(expected_sha256_normalized)
        and observed_sha256 == expected_sha256_normalized
        if complete
        else False
    )

    transfer_integrity_verified = complete and (
        md5_matches or sha256_matches
    )
    recovery_trust_verified = complete and sha256_matches

    final_path: str | None = None
    if complete and transfer_integrity_verified:
        os.replace(partial, destination)
        final_path = str(destination)

    return {
        "schema": SCHEMA,
        "provider": provider.strip(),
        "provider_file_id": provider_file_id.strip(),
        "provider_name": provider_name,
        "provider_size_bytes": provider_size_bytes,
        "provider_md5": provider_md5_normalized or None,
        "expected_sha256": expected_sha256_normalized or None,
        "resume_offset_bytes": resume_offset,
        "bytes_copied_this_attempt": copied,
        "staged_size_bytes": staged_size,
        "complete": complete,
        "interrupted": interrupted,
        "observed_md5": observed_md5,
        "observed_sha256": observed_sha256,
        "provider_md5_matches": md5_matches,
        "expected_sha256_matches": sha256_matches,
        "transfer_integrity_verified": transfer_integrity_verified,
        "recovery_trust_verified": recovery_trust_verified,
        "staged_path": final_path,
        "partial_path": None if final_path else str(partial),
        "cloud_original_modified": False,
        "recovery_eligible": recovery_trust_verified and final_path is not None,
        "block_reasons": [
            reason
            for condition, reason in [
                (not complete, "cloud_stage_incomplete"),
                (
                    complete and not transfer_integrity_verified,
                    "cloud_transfer_integrity_not_verified",
                ),
                (
                    complete and not recovery_trust_verified,
                    "trusted_sha256_not_verified",
                ),
            ]
            if condition
        ],
    }


def write_receipt(payload: dict[str, Any], destination: Path) -> None:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=destination.parent, delete=False
    ) as temporary:
        json.dump(payload, temporary, indent=2, sort_keys=True)
        temporary.write("\n")
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-file", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--provider", required=True)
    parser.add_argument("--provider-file-id", required=True)
    parser.add_argument("--provider-name", required=True)
    parser.add_argument("--provider-size-bytes", type=int, required=True)
    parser.add_argument("--provider-md5")
    parser.add_argument("--expected-sha256")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = stage_cloud_payload(
        source_file=args.source_file,
        destination=args.destination,
        provider=args.provider,
        provider_file_id=args.provider_file_id,
        provider_name=args.provider_name,
        provider_size_bytes=args.provider_size_bytes,
        provider_md5=args.provider_md5,
        expected_sha256=args.expected_sha256,
    )
    write_receipt(receipt, args.receipt)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CloudStageError, OSError, ValueError) as exc:
        print(f"CLOUD_RECOVERY_STAGE_FAILED: {exc}", file=os.sys.stderr)
        raise SystemExit(2) from exc
