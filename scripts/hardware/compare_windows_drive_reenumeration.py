#!/usr/bin/env python3
"""Compare two immutable Windows physical-drive evidence receipts.

This tool is read-only. It proves whether two captures refer to the same stable
hardware, whether the snapshot identity changed because Windows re-enumerated
the device, and whether stale destructive authorization must be discarded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

DRIVE_SCHEMA = "bws.physical-drive-evidence/v1"
COMPARISON_SCHEMA = "phoenix_key.windows_drive_reenumeration.v1"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class ComparisonError(RuntimeError):
    """Raised when either evidence receipt cannot be trusted."""


def canonical_json(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_payload(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def verify_receipt(receipt: dict[str, Any], label: str) -> dict[str, Any]:
    if receipt.get("schema_version") != DRIVE_SCHEMA:
        raise ComparisonError(f"{label} receipt uses an unsupported schema.")

    expected = str(receipt.get("receipt_sha256") or "")
    if not SHA256_RE.fullmatch(expected):
        raise ComparisonError(f"{label} receipt is missing a valid receipt SHA-256.")

    canonical = dict(receipt)
    canonical.pop("receipt_sha256", None)
    actual = sha256_payload(canonical)
    if not actual.eq_ignore_ascii_case(expected):
        raise ComparisonError(f"{label} receipt checksum does not match its content.")

    if receipt.get("physical_write_attempted") is not False:
        raise ComparisonError(f"{label} receipt reports a physical write attempt.")
    if receipt.get("bytes_written") != 0:
        raise ComparisonError(f"{label} receipt reports nonzero bytes written.")

    disk = receipt.get("disk")
    if not isinstance(disk, dict):
        raise ComparisonError(f"{label} receipt is missing its disk record.")

    snapshot = str(disk.get("identity_sha256") or "")
    stable = str(disk.get("stable_identity_sha256") or "")
    if not SHA256_RE.fullmatch(snapshot):
        raise ComparisonError(f"{label} receipt is missing a valid snapshot identity.")
    if not SHA256_RE.fullmatch(stable):
        raise ComparisonError(f"{label} receipt is missing a valid stable hardware identity.")

    return disk


def compare_receipts(
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    before_disk = verify_receipt(before, "before")
    after_disk = verify_receipt(after, "after")

    before_snapshot = before_disk["identity_sha256"].lower()
    after_snapshot = after_disk["identity_sha256"].lower()
    before_stable = before_disk["stable_identity_sha256"].lower()
    after_stable = after_disk["stable_identity_sha256"].lower()

    stable_identity_matches = before_stable == after_stable
    snapshot_identity_matches = before_snapshot == after_snapshot
    same_hardware = stable_identity_matches

    if not stable_identity_matches:
        classification = "hardware-substitution-or-mismatch"
        required_action = "block-and-select-original-hardware"
    elif snapshot_identity_matches:
        classification = "same-hardware-same-snapshot"
        required_action = "fresh-readonly-validation-complete"
    else:
        classification = "same-hardware-reenumerated"
        required_action = "discard-stale-authorization-and-revalidate-fresh-snapshot"

    real_hardware_evidence = (
        before.get("hardware_observed") is True
        and after.get("hardware_observed") is True
        and before.get("evidence_source") == "live"
        and after.get("evidence_source") == "live"
    )

    result = {
        "schema": COMPARISON_SCHEMA,
        "classification": classification,
        "same_hardware": same_hardware,
        "snapshot_identity_matches": snapshot_identity_matches,
        "stable_identity_matches": stable_identity_matches,
        "before_target": before_disk.get("target"),
        "after_target": after_disk.get("target"),
        "before_snapshot_identity_sha256": before_snapshot,
        "after_snapshot_identity_sha256": after_snapshot,
        "stable_identity_sha256": before_stable if same_hardware else None,
        "reenumerated": same_hardware and not snapshot_identity_matches,
        "stale_authorization_reusable": same_hardware and snapshot_identity_matches,
        "fresh_snapshot_authorization_required": not snapshot_identity_matches,
        "real_hardware_evidence": real_hardware_evidence,
        "hardware_validation_complete": (
            real_hardware_evidence
            and same_hardware
            and before.get("hardware_validated") is True
            and after.get("hardware_validated") is True
        ),
        "required_action": required_action,
        "physical_write_attempted": False,
        "bytes_written": 0,
        "system_mutations_performed": False,
    }
    result["comparison_sha256"] = sha256_payload(result)
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ComparisonError(f"cannot read evidence receipt {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ComparisonError(f"evidence receipt {path} is not a JSON object.")
    return value


def write_json_atomic(payload: dict[str, Any], destination: Path) -> None:
    destination = destination.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=destination.parent,
        delete=False,
    ) as temporary:
        temporary.write(text)
        temporary.flush()
        os.fsync(temporary.fileno())
        temporary_path = Path(temporary.name)
    os.replace(temporary_path, destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = compare_receipts(load_json(args.before), load_json(args.after))
    write_json_atomic(result, args.output)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ComparisonError, OSError, ValueError) as exc:
        print(f"DRIVE_REENUMERATION_COMPARE_FAILED: {exc}", file=__import__("sys").stderr)
        raise SystemExit(2) from exc
