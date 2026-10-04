#!/usr/bin/env python3
"""Read-only resume assessment. Inputs are evidence, never authority to write a disk.

Fresh source and target observations must be collected by the native supervisor.
Completed-file observations must be read back independently of the journal.
Partitioning, image application and boot configuration cannot resume mid-step.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA = "arcwyre.windows_media_journal.v1"
OPERATION_VERSION = 1
HASH = re.compile(r"^[0-9a-f]{64}$")
IDENTITY_FIELDS = ("stable_id", "serial_number", "capacity_bytes", "logical_sector_bytes")


def _hash(value: Any) -> bool:
    return isinstance(value, str) and HASH.fullmatch(value) is not None


def _files(manifest: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise ValueError("invalid_manifest")
    entries = manifest["files"]
    result = {}
    folded = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("invalid_file_record")
        path = entry.get("path")
        size = entry.get("size_bytes")
        if (not isinstance(path, str) or not path or "\\" in path or ":" in path
                or any(part in ("", ".", "..") for part in path.split("/"))
                or path.casefold() in folded or type(size) is not int or size < 0
                or not _hash(entry.get("sha256"))):
            raise ValueError("invalid_file_record")
        folded.add(path.casefold())
        result[path] = {"path": path, "size_bytes": size, "sha256": entry["sha256"]}
    encoded = json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()
    if not entries or hashlib.sha256(encoded).hexdigest() != manifest.get("manifest_sha256"):
        raise ValueError("manifest_checksum_mismatch")
    return result


def assess_resume(journal: dict[str, Any], fresh_source: dict[str, Any],
                  fresh_target: dict[str, Any], readback_files: list[dict[str, Any]],
                  expected_plan_sha256: str) -> dict[str, Any]:
    """Return eligibility only; caller must revalidate and obtain new consent to resume.

    No disk paths are opened, no commands are executed, and no state is modified.
    The caller must not substitute journal fields for independently acquired inputs.
    """
    reasons = []
    completed_bytes = 0
    total_bytes = 0
    remaining = []
    if (journal.get("schema") != SCHEMA
            or type(journal.get("operation_version")) is not int
            or journal.get("operation_version") != OPERATION_VERSION):
        reasons.append("unsupported_operation_version")
    if journal.get("operation") != "windows_installer_file_copy":
        reasons.append("operation_not_resumable")
    if not _hash(expected_plan_sha256) or journal.get("plan_sha256") != expected_plan_sha256:
        reasons.append("plan_changed")
    if journal.get("state") not in ("interrupted", "cancelled", "failed"):
        reasons.append("operation_not_stopped")
    if journal.get("phase") != "file_copy" or journal.get("in_flight_mutation") is not False:
        reasons.append("unsafe_interruption_boundary")
    old_target = journal.get("target_identity", {})
    if not isinstance(old_target, dict) or any(
        not fresh_target.get(field) or fresh_target.get(field) != old_target.get(field)
        for field in IDENTITY_FIELDS
    ):
        reasons.append("target_identity_changed_or_missing")
    if (fresh_target.get("is_system") is not False
            or fresh_target.get("is_read_only") is not False
            or fresh_target.get("is_removable") is not True
            or any(type(fresh_target.get(field)) is not int or fresh_target[field] <= 0
                   for field in ("capacity_bytes", "logical_sector_bytes"))
            or any(not isinstance(fresh_target.get(field), str) or not fresh_target[field].strip()
                   for field in ("stable_id", "serial_number"))):
        reasons.append("target_ineligible")
    try:
        source = _files(fresh_source)
        original = _files(journal.get("source_manifest"))
        if source != original:
            reasons.append("source_changed")
        total_bytes = sum(item["size_bytes"] for item in source.values())
        completed = journal.get("completed_files")
        if not isinstance(completed, list) or not isinstance(readback_files, list):
            raise ValueError("invalid_completed_records")
        observed = {}
        for record in readback_files:
            if not isinstance(record, dict) or record.get("path") in observed:
                raise ValueError("duplicate_or_invalid_readback")
            observed[record.get("path")] = record
        seen = set()
        for record in completed:
            if not isinstance(record, dict):
                raise ValueError("invalid_completed_records")
            path = record.get("path")
            if path in seen or path not in source or record != source[path] or observed.get(path) != record:
                raise ValueError("completed_file_readback_mismatch")
            seen.add(path)
            completed_bytes += record["size_bytes"]
        if set(observed) != seen:
            raise ValueError("unaccounted_target_files")
        remaining = sorted(set(source) - seen)
    except (ValueError, TypeError) as exc:
        reasons.append(str(exc))
    return {
        "schema": "arcwyre.windows_media_resume_assessment.v1",
        "resume_eligible": not reasons,
        "block_reasons": reasons,
        "verified_completed_bytes": completed_bytes,
        "source_total_bytes": total_bytes,
        "remaining_files": remaining,
        "progress_scope": "verified_file_copy_bytes_only",
        "boot_verified": False,
        "automatic_resume_allowed": False,
        "requires_fresh_authorization": True,
        "cancellation_semantics": "stop_before_next_file; active_file_must_finish_or_be_marked_unverified",
        "target_disk_modified": False,
    }
