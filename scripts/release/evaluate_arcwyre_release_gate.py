#!/usr/bin/env python3
"""Evaluate ARCWYRE release evidence without manufacturing missing proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

SCHEMA = "arcwyre.release-evidence.v1"
REPORT_SCHEMA = "arcwyre.release-gate-report.v1"

GATES = (
    "windows_native_suite",
    "aws_windows_build",
    "google_independent_build",
    "vm_rehearsal",
    "artifact_signing",
    "usb_provisioning",
    "physical_readback",
    "physical_boot",
    "cancellation_recovery",
    "partner_center_private_flight",
)

LEVELS = {
    "integrated": GATES[:4],
    "hardware_validated": GATES[:9],
    "release_candidate": GATES,
}


class EvidenceError(RuntimeError):
    pass


def canonical_sha256(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("receipt_sha256", None)
    encoded = json.dumps(
        unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_receipt(path: Path, source_commit: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise EvidenceError("receipt must be a non-symlink regular file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise EvidenceError(f"receipt is unreadable: {error}") from error
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        raise EvidenceError("unsupported receipt schema")
    if payload.get("source_commit") != source_commit:
        raise EvidenceError("receipt source commit does not match candidate")
    if payload.get("gate") not in GATES:
        raise EvidenceError("receipt names an unknown gate")
    if payload.get("status") not in {"passed", "blocked", "failed"}:
        raise EvidenceError("receipt status is invalid")
    for field in ("executor", "observed_at", "evidence_uri"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EvidenceError(f"receipt field {field} is missing")
    if payload.get("receipt_sha256") != canonical_sha256(payload):
        raise EvidenceError("receipt integrity hash does not match")
    return payload


def evaluate(
    *, evidence_dir: Path, source_commit: str, target_level: str
) -> dict[str, Any]:
    if not evidence_dir.is_dir() or evidence_dir.is_symlink():
        raise EvidenceError("evidence directory must be a real directory")
    if target_level not in LEVELS:
        raise EvidenceError("unsupported target level")
    if not isinstance(source_commit, str) or len(source_commit) != 40 or any(
        character not in "0123456789abcdef" for character in source_commit
    ):
        raise EvidenceError("source commit must be a lowercase 40-character Git SHA")

    observations: dict[str, dict[str, Any]] = {}
    observation_files: dict[str, str] = {}
    duplicate_gates: set[str] = set()
    rejected: list[dict[str, str]] = []
    for path in sorted(evidence_dir.glob("*.json")):
        try:
            receipt = load_receipt(path, source_commit)
        except EvidenceError as error:
            rejected.append({"file": path.name, "reason": str(error)})
            continue
        gate = receipt["gate"]
        if gate in duplicate_gates:
            rejected.append({"file": path.name, "reason": f"duplicate gate: {gate}"})
            continue
        if gate in observations:
            rejected.append(
                {
                    "file": observation_files.pop(gate),
                    "reason": f"duplicate gate: {gate}",
                }
            )
            rejected.append({"file": path.name, "reason": f"duplicate gate: {gate}"})
            observations.pop(gate, None)
            duplicate_gates.add(gate)
            continue
        observations[gate] = receipt
        observation_files[gate] = path.name

    required = LEVELS[target_level]
    missing = [gate for gate in required if gate not in observations]
    not_passed = [
        gate
        for gate in required
        if gate in observations and observations[gate]["status"] != "passed"
    ]
    passed = [
        gate
        for gate in required
        if gate in observations and observations[gate]["status"] == "passed"
    ]
    promoted = not missing and not not_passed and not rejected
    report = {
        "schema": REPORT_SCHEMA,
        "source_commit": source_commit,
        "target_level": target_level,
        "promoted": promoted,
        "classification": target_level if promoted else "blocked",
        "required_gates": list(required),
        "passed_gates": passed,
        "missing_gates": missing,
        "not_passed_gates": not_passed,
        "rejected_receipts": rejected,
        "receipt_files": sorted(path.name for path in evidence_dir.glob("*.json")),
    }
    report["report_sha256"] = canonical_sha256(report)
    return report


def write_json_atomic(destination: Path, payload: dict[str, Any]) -> None:
    destination = destination.absolute()
    if destination.exists() or destination.is_symlink():
        raise EvidenceError("output already exists")
    if not destination.parent.is_dir() or destination.parent.is_symlink():
        raise EvidenceError("output parent must be an existing real directory")
    with tempfile.NamedTemporaryFile(
        "x", encoding="utf-8", dir=destination.parent, delete=False
    ) as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
        temporary = Path(stream.name)
    try:
        os.link(temporary, destination)
        if os.name != "nt":
            directory = os.open(
                destination.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            )
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--target-level", choices=tuple(LEVELS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report = evaluate(
            evidence_dir=args.evidence_dir,
            source_commit=args.source_commit,
            target_level=args.target_level,
        )
        write_json_atomic(args.output, report)
    except EvidenceError as error:
        print(f"ARCWYRE_RELEASE_GATE_INVALID: {error}")
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["promoted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
