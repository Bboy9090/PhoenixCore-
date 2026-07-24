#!/usr/bin/env python3
"""Checkpointed, evidence-backed regular-file repair coordinator.

The coordinator validates a replacement payload before any checkpoint or mutation,
creates a verified Continuity checkpoint, applies an atomic regular-file
replacement, verifies the final SHA-256, and automatically rolls back on repair
failure.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import uuid
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT_PATH = ROOT / "scripts" / "continuity" / "checkpoint_store.py"
LEDGER_PATH = ROOT / "scripts" / "evidence" / "evidence_ledger.py"
SHA256_ZERO = "0" * 64


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


checkpoint_module = load_module("checkpoint_store", CHECKPOINT_PATH)
ledger_module = load_module("evidence_ledger", LEDGER_PATH)


class RecoveryError(RuntimeError):
    """Raised when a repair cannot be completed safely."""


class RecoveryStatus(str, Enum):
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True, slots=True)
class PayloadManifest:
    path: str
    size_bytes: int
    sha256: str

    @classmethod
    def from_file(cls, path: Path) -> "PayloadManifest":
        payload = ensure_regular_file(path, label="replacement payload")
        return cls(
            path=str(payload),
            size_bytes=payload.stat().st_size,
            sha256=sha256_file(payload),
        )

    def verify_payload(self, path: Path) -> None:
        payload = ensure_regular_file(path, label="replacement payload")
        if self.size_bytes <= 0:
            raise RecoveryError("replacement manifest must declare a nonempty payload.")
        if len(self.sha256) != 64 or self.sha256 == SHA256_ZERO:
            raise RecoveryError("replacement manifest SHA-256 is invalid.")
        if payload.stat().st_size != self.size_bytes:
            raise RecoveryError("replacement payload size does not match manifest.")
        if sha256_file(payload) != self.sha256:
            raise RecoveryError("replacement payload SHA-256 does not match manifest.")


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    operation_id: str
    status: RecoveryStatus
    checkpoint_id: str
    final_sha256: str
    evidence_sequence: int


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
    expanded = path.expanduser()
    if expanded.is_symlink():
        raise RecoveryError(f"{label} must not be a symlink.")
    resolved = expanded.resolve(strict=True)
    if not resolved.is_file():
        raise RecoveryError(f"{label} must be an existing regular file.")
    return resolved


def result_to_json(result: RecoveryResult) -> dict[str, Any]:
    value = asdict(result)
    value["status"] = result.status.value
    return value


class RecoveryCoordinator:
    """Checkpointed regular-file repair with automatic verified rollback."""

    def __init__(self, checkpoint_store: Any, evidence_ledger: Any):
        self.checkpoint_store = checkpoint_store
        self.evidence_ledger = evidence_ledger

    def repair_file(
        self,
        target_path: Path,
        replacement_path: Path,
        payload_manifest: PayloadManifest,
        *,
        repair_id: int,
        after_replace: Callable[[Path], None] | None = None,
    ) -> RecoveryResult:
        target = ensure_regular_file(target_path, label="repair target")
        replacement = ensure_regular_file(replacement_path, label="replacement payload")
        if repair_id < 0:
            raise RecoveryError("repair ID cannot be negative.")

        payload_manifest.verify_payload(replacement)
        operation_id = str(uuid.uuid4())
        checkpoint = self.checkpoint_store.create_checkpoint(target, repair_id)
        checkpoint_event = self.evidence_ledger.append(
            "RECOVERY.CHECKPOINT_CREATED",
            {
                "operation_id": operation_id,
                "checkpoint_id": checkpoint.checkpoint_id,
                "repair_id": repair_id,
                "target": str(target),
                "backup_sha256": checkpoint.backup_sha256,
            },
        )

        try:
            temporary_target = self._write_temporary_replacement(
                target=target,
                replacement=replacement,
                operation_id=operation_id,
                payload_manifest=payload_manifest,
            )
            temporary_target.replace(target)
            fsync_directory(target.parent)

            if after_replace is not None:
                after_replace(target)

            final_hash = sha256_file(target)
            if final_hash != payload_manifest.sha256:
                raise RecoveryError("repair verification failed.")

            verified_event = self.evidence_ledger.append(
                "RECOVERY.REPAIR_VERIFIED",
                {
                    "operation_id": operation_id,
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "target_sha256": final_hash,
                    "checkpoint_evidence_sequence": checkpoint_event.sequence,
                },
            )
            self.checkpoint_store.mark_completed(checkpoint.checkpoint_id)
            return RecoveryResult(
                operation_id=operation_id,
                status=RecoveryStatus.COMPLETED,
                checkpoint_id=checkpoint.checkpoint_id,
                final_sha256=final_hash,
                evidence_sequence=verified_event.sequence,
            )
        except Exception as repair_error:
            return self._rollback_after_failure(
                operation_id=operation_id,
                checkpoint_id=checkpoint.checkpoint_id,
                target=target,
                repair_error=repair_error,
            )

    def _write_temporary_replacement(
        self,
        *,
        target: Path,
        replacement: Path,
        operation_id: str,
        payload_manifest: PayloadManifest,
    ) -> Path:
        target_dir = target.parent
        with tempfile.NamedTemporaryFile(
            "wb",
            dir=target_dir,
            prefix=f".{operation_id}.",
            suffix=".repair.tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            with replacement.open("rb") as source_stream:
                shutil.copyfileobj(source_stream, temporary, length=1024 * 1024)
            temporary.flush()
            os.fsync(temporary.fileno())

        try:
            payload_manifest.verify_payload(temporary_path)
            return temporary_path
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

    def _rollback_after_failure(
        self,
        *,
        operation_id: str,
        checkpoint_id: str,
        target: Path,
        repair_error: Exception,
    ) -> RecoveryResult:
        try:
            restored = self.checkpoint_store.restore(checkpoint_id, target)
            rollback_event = self.evidence_ledger.append(
                "RECOVERY.ROLLBACK_VERIFIED",
                {
                    "operation_id": operation_id,
                    "checkpoint_id": checkpoint_id,
                    "restored_sha256": restored.backup_sha256,
                    "repair_error": f"{type(repair_error).__name__}: {repair_error}",
                },
            )
            return RecoveryResult(
                operation_id=operation_id,
                status=RecoveryStatus.ROLLED_BACK,
                checkpoint_id=checkpoint_id,
                final_sha256=restored.backup_sha256,
                evidence_sequence=rollback_event.sequence,
            )
        except Exception as rollback_error:
            self.evidence_ledger.append(
                "RECOVERY.ROLLBACK_FAILED",
                {
                    "operation_id": operation_id,
                    "checkpoint_id": checkpoint_id,
                    "repair_error": f"{type(repair_error).__name__}: {repair_error}",
                    "rollback_error": f"{type(rollback_error).__name__}: {rollback_error}",
                },
            )
            raise RecoveryError(
                "repair failed and rollback also failed."
            ) from rollback_error


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-root", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--replacement", type=Path, required=True)
    parser.add_argument("--repair-id", type=int, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = PayloadManifest.from_file(args.replacement)
    coordinator = RecoveryCoordinator(
        checkpoint_module.CheckpointStore(args.checkpoint_root),
        ledger_module.EvidenceLedger(args.ledger),
    )
    result = coordinator.repair_file(
        args.target,
        args.replacement,
        manifest,
        repair_id=args.repair_id,
    )
    print(json.dumps(result_to_json(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RecoveryError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"CHECKPOINTED_REPAIR_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
