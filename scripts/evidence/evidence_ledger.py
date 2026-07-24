#!/usr/bin/env python3
"""Append-only SHA-256 hash-chained evidence ledger for PhoenixCore.

The ledger records host-side evidence events as JSON Lines. Every record includes
its previous record hash and its own canonical SHA-256 hash, making deletion,
reordering, and payload edits detectable during verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Mapping

SCHEMA_VERSION = "bws.evidence-ledger/v1"
ZERO_HASH = "0" * 64
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EVENT_RE = re.compile(r"^[A-Z][A-Z0-9_.-]{2,63}$")


class EvidenceLedgerError(RuntimeError):
    """Raised when a ledger cannot be trusted."""


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    schema_version: str
    sequence: int
    timestamp: str
    event_type: str
    payload: dict[str, Any]
    previous_hash: str
    record_hash: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def record_body(record: EvidenceRecord | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(record, EvidenceRecord):
        value = asdict(record)
    else:
        value = dict(record)
    value.pop("record_hash", None)
    return value


def hash_record_body(body: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(body)).hexdigest()


def validate_event_type(event_type: str) -> str:
    normalized = event_type.strip()
    if not EVENT_RE.fullmatch(normalized):
        raise EvidenceLedgerError(
            "event type must be an uppercase identifier, 3-64 chars."
        )
    return normalized


def validate_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise EvidenceLedgerError("payload must be a JSON object.")
    normalized = dict(payload)
    canonical_json(normalized)
    return normalized


def validate_record_shape(value: Mapping[str, Any], *, line_number: int) -> EvidenceRecord:
    try:
        record = EvidenceRecord(
            schema_version=str(value["schema_version"]),
            sequence=int(value["sequence"]),
            timestamp=str(value["timestamp"]),
            event_type=str(value["event_type"]),
            payload=dict(value["payload"]),
            previous_hash=str(value["previous_hash"]),
            record_hash=str(value["record_hash"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EvidenceLedgerError(
            f"invalid evidence record at line {line_number}"
        ) from exc

    if record.schema_version != SCHEMA_VERSION:
        raise EvidenceLedgerError(f"unsupported schema at line {line_number}")
    validate_event_type(record.event_type)
    validate_payload(record.payload)
    if not SHA256_RE.fullmatch(record.previous_hash):
        raise EvidenceLedgerError(f"invalid previous hash at line {line_number}")
    if not SHA256_RE.fullmatch(record.record_hash):
        raise EvidenceLedgerError(f"invalid record hash at line {line_number}")
    return record


class EvidenceLedger:
    """Append-only JSONL evidence ledger with SHA-256 hash chaining."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = Lock()

    def append(
        self,
        event_type: str,
        payload: Mapping[str, Any],
        *,
        timestamp: str | None = None,
    ) -> EvidenceRecord:
        normalized_event = validate_event_type(event_type)
        normalized_payload = validate_payload(payload)
        with self._lock:
            existing = self.read_all()
            verify_records(existing)
            sequence = len(existing) + 1
            previous_hash = existing[-1].record_hash if existing else ZERO_HASH
            body = {
                "schema_version": SCHEMA_VERSION,
                "sequence": sequence,
                "timestamp": timestamp or utc_now_iso(),
                "event_type": normalized_event,
                "payload": normalized_payload,
                "previous_hash": previous_hash,
            }
            record = EvidenceRecord(
                record_hash=hash_record_body(body),
                **body,
            )
            self._append_json_line(asdict(record))
            return record

    def read_all(self) -> list[EvidenceRecord]:
        if not self.path.exists():
            return []
        records: list[EvidenceRecord] = []
        for line_number, line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise EvidenceLedgerError(
                    f"invalid JSON at line {line_number}"
                ) from exc
            if not isinstance(value, dict):
                raise EvidenceLedgerError(
                    f"ledger line {line_number} must be a JSON object"
                )
            records.append(validate_record_shape(value, line_number=line_number))
        return records

    def verify(self) -> list[EvidenceRecord]:
        records = self.read_all()
        verify_records(records)
        return records

    def _append_json_line(self, payload: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())


def verify_records(records: list[EvidenceRecord]) -> None:
    previous_hash = ZERO_HASH
    for expected_sequence, record in enumerate(records, start=1):
        if record.sequence != expected_sequence:
            raise EvidenceLedgerError("evidence sequence is not contiguous")
        if record.previous_hash != previous_hash:
            raise EvidenceLedgerError("evidence previous-hash link is invalid")
        actual_hash = hash_record_body(record_body(record))
        if record.record_hash != actual_hash:
            raise EvidenceLedgerError("evidence record hash is invalid")
        previous_hash = record.record_hash


def write_summary_atomic(records: list[EvidenceRecord], destination: Path) -> None:
    payload = {
        "schema_version": "bws.evidence-ledger-summary/v1",
        "record_count": len(records),
        "head_hash": records[-1].record_hash if records else ZERO_HASH,
        "verified": True,
    }
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=destination.parent, delete=False
    ) as temporary:
        json.dump(payload, temporary, indent=2, sort_keys=True)
        temporary.write("\n")
        temporary.flush()
        os.fsync(temporary.fileno())
        temp_path = Path(temporary.name)
    os.replace(temp_path, destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    append = subparsers.add_parser("append", help="Append one evidence event.")
    append.add_argument("--ledger", type=Path, required=True)
    append.add_argument("--event-type", required=True)
    append.add_argument("--payload-json", required=True)
    append.add_argument("--timestamp")

    verify = subparsers.add_parser("verify", help="Verify a ledger chain.")
    verify.add_argument("--ledger", type=Path, required=True)
    verify.add_argument("--summary", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ledger = EvidenceLedger(args.ledger)
    if args.command == "append":
        payload = json.loads(args.payload_json)
        record = ledger.append(args.event_type, payload, timestamp=args.timestamp)
        print(json.dumps(asdict(record), sort_keys=True))
        return 0
    if args.command == "verify":
        records = ledger.verify()
        if args.summary:
            write_summary_atomic(records, args.summary)
        print(
            json.dumps(
                {
                    "schema_version": "bws.evidence-ledger-summary/v1",
                    "record_count": len(records),
                    "head_hash": records[-1].record_hash if records else ZERO_HASH,
                    "verified": True,
                },
                sort_keys=True,
            )
        )
        return 0
    raise EvidenceLedgerError("unsupported command")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EvidenceLedgerError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"EVIDENCE_LEDGER_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
