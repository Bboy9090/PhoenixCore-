#!/usr/bin/env python3
"""Verified regular-file checkpoint store for PhoenixCore Continuity.

This module creates atomic, SHA-256 verified backups for regular files only. It
is intentionally not a partition, firmware, NVRAM, block-device, or cloud restore
system. Those things require their own gates, because apparently people keep
asking software to juggle chainsaws in production.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import uuid
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any

SCHEMA_VERSION = "bws.continuity-checkpoint/v1"
ZERO_UUID = "00000000-0000-0000-0000-000000000000"


class CheckpointError(RuntimeError):
    """Raised when checkpoint evidence cannot be trusted."""


class CheckpointState(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    RESTORED = "restored"


@dataclass(frozen=True, slots=True)
class CheckpointRecord:
    schema_version: str
    checkpoint_id: str
    repair_id: int
    state: CheckpointState
    source_path: str
    backup_path: str
    backup_size: int
    backup_sha256: str
    created_at: str
    updated_at: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def ensure_regular_file(path: Path, *, label: str) -> Path:
    resolved = path.expanduser().resolve(strict=True)
    if not resolved.is_file():
        raise CheckpointError(f"{label} must be an existing regular file.")
    if resolved.is_symlink():
        raise CheckpointError(f"{label} must not be a symlink.")
    return resolved


def parse_checkpoint_id(value: str) -> str:
    normalized = str(uuid.UUID(value))
    if normalized == ZERO_UUID:
        raise CheckpointError("checkpoint ID must be nonzero.")
    return normalized


def record_to_json(record: CheckpointRecord) -> dict[str, Any]:
    value = asdict(record)
    value["state"] = record.state.value
    return value


def record_from_json(value: dict[str, Any]) -> CheckpointRecord:
    record = CheckpointRecord(
        schema_version=str(value["schema_version"]),
        checkpoint_id=parse_checkpoint_id(str(value["checkpoint_id"])),
        repair_id=int(value["repair_id"]),
        state=CheckpointState(str(value["state"])),
        source_path=str(value["source_path"]),
        backup_path=str(value["backup_path"]),
        backup_size=int(value["backup_size"]),
        backup_sha256=str(value["backup_sha256"]),
        created_at=str(value["created_at"]),
        updated_at=str(value["updated_at"]),
    )
    validate_record(record)
    return record


def validate_record(record: CheckpointRecord) -> None:
    if record.schema_version != SCHEMA_VERSION:
        raise CheckpointError("unsupported checkpoint schema.")
    parse_checkpoint_id(record.checkpoint_id)
    if record.repair_id < 0:
        raise CheckpointError("repair ID cannot be negative.")
    if record.backup_size <= 0:
        raise CheckpointError("checkpoint backup must be nonempty.")
    if len(record.backup_sha256) != 64 or set(record.backup_sha256) == {"0"}:
        raise CheckpointError("checkpoint backup SHA-256 is invalid.")


class CheckpointStore:
    """Atomic regular-file checkpoint store with verified restore."""

    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.backup_dir = self.root / "backups"
        self.metadata_dir = self.root / "metadata"
        self._lock = Lock()

    def create_checkpoint(self, source_path: Path, repair_id: int) -> CheckpointRecord:
        source = ensure_regular_file(source_path, label="checkpoint source")
        if repair_id < 0:
            raise CheckpointError("repair ID cannot be negative.")

        with self._lock:
            checkpoint_id = str(uuid.uuid4())
            now = utc_now_iso()
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.metadata_dir.mkdir(parents=True, exist_ok=True)

            final_backup = self.backup_dir / f"{checkpoint_id}.bin"
            temporary_backup = final_backup.with_suffix(".bin.tmp")
            with source.open("rb") as source_stream, temporary_backup.open(
                "wb"
            ) as backup_stream:
                shutil.copyfileobj(source_stream, backup_stream, length=1024 * 1024)
                backup_stream.flush()
                os.fsync(backup_stream.fileno())
            temporary_backup.replace(final_backup)
            fsync_directory(self.backup_dir)

            record = CheckpointRecord(
                schema_version=SCHEMA_VERSION,
                checkpoint_id=checkpoint_id,
                repair_id=repair_id,
                state=CheckpointState.PENDING,
                source_path=str(source),
                backup_path=str(final_backup.resolve()),
                backup_size=final_backup.stat().st_size,
                backup_sha256=sha256_file(final_backup),
                created_at=now,
                updated_at=now,
            )
            validate_record(record)
            self._write_metadata(record)
            return record

    def load(self, checkpoint_id: str) -> CheckpointRecord:
        normalized = parse_checkpoint_id(checkpoint_id)
        metadata_path = self.metadata_dir / f"{normalized}.json"
        try:
            value = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CheckpointError(
                f"checkpoint metadata could not be read: {exc}"
            ) from exc
        if not isinstance(value, dict):
            raise CheckpointError("checkpoint metadata must be a JSON object.")
        return record_from_json(value)

    def verify(self, checkpoint_id: str) -> CheckpointRecord:
        record = self.load(checkpoint_id)
        backup = Path(record.backup_path)
        if not backup.is_file():
            raise CheckpointError("checkpoint backup is missing.")
        if backup.is_symlink():
            raise CheckpointError("checkpoint backup must not be a symlink.")
        if backup.stat().st_size != record.backup_size:
            raise CheckpointError("checkpoint backup size changed.")
        if sha256_file(backup) != record.backup_sha256:
            raise CheckpointError("checkpoint backup hash changed.")
        return record

    def restore(self, checkpoint_id: str, target_path: Path) -> CheckpointRecord:
        with self._lock:
            record = self.verify(checkpoint_id)
            backup = ensure_regular_file(
                Path(record.backup_path), label="checkpoint backup"
            )
            target = target_path.expanduser().resolve()
            if target.exists() and not target.is_file():
                raise CheckpointError(
                    "restore target must be a regular file if it exists."
                )
            if target.exists() and target.is_symlink():
                raise CheckpointError("restore target must not be a symlink.")
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                "wb", dir=target.parent, delete=False
            ) as temporary:
                temporary_path = Path(temporary.name)
                with backup.open("rb") as source_stream:
                    shutil.copyfileobj(source_stream, temporary, length=1024 * 1024)
                temporary.flush()
                os.fsync(temporary.fileno())

            if sha256_file(temporary_path) != record.backup_sha256:
                temporary_path.unlink(missing_ok=True)
                raise CheckpointError("restored file hash does not match checkpoint.")
            temporary_path.replace(target)
            fsync_directory(target.parent)
            restored = replace(
                record,
                state=CheckpointState.RESTORED,
                updated_at=utc_now_iso(),
            )
            self._write_metadata(restored)
            return restored

    def mark_completed(self, checkpoint_id: str) -> CheckpointRecord:
        with self._lock:
            record = self.verify(checkpoint_id)
            completed = replace(
                record,
                state=CheckpointState.COMPLETED,
                updated_at=utc_now_iso(),
            )
            self._write_metadata(completed)
            return completed

    def list_pending(self) -> list[CheckpointRecord]:
        if not self.metadata_dir.exists():
            return []
        records = [
            self.load(path.stem) for path in sorted(self.metadata_dir.glob("*.json"))
        ]
        return [record for record in records if record.state is CheckpointState.PENDING]

    def _write_metadata(self, record: CheckpointRecord) -> None:
        validate_record(record)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        final_path = self.metadata_dir / f"{record.checkpoint_id}.json"
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=self.metadata_dir, delete=False
        ) as temporary:
            json.dump(record_to_json(record), temporary, indent=2, sort_keys=True)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        temporary_path.replace(final_path)
        fsync_directory(self.metadata_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("--root", type=Path, required=True)
    create.add_argument("--source", type=Path, required=True)
    create.add_argument("--repair-id", type=int, required=True)

    verify = subparsers.add_parser("verify")
    verify.add_argument("--root", type=Path, required=True)
    verify.add_argument("--checkpoint-id", required=True)

    restore = subparsers.add_parser("restore")
    restore.add_argument("--root", type=Path, required=True)
    restore.add_argument("--checkpoint-id", required=True)
    restore.add_argument("--target", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    store = CheckpointStore(args.root)
    if args.command == "create":
        record = store.create_checkpoint(args.source, repair_id=args.repair_id)
    elif args.command == "verify":
        record = store.verify(args.checkpoint_id)
    elif args.command == "restore":
        record = store.restore(args.checkpoint_id, args.target)
    else:
        raise CheckpointError("unsupported command.")
    print(json.dumps(record_to_json(record), sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CheckpointError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CONTINUITY_CHECKPOINT_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
