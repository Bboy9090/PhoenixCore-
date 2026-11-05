#!/usr/bin/env python3
"""Capture read-only Linux whole-disk evidence for Phoenix Key.

This collector never opens a raw device for writing and never mounts, unmounts,
formats, partitions, or otherwise mutates storage. It qualifies whether a Linux
whole-disk path has enough stable evidence to be considered by a future writer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "bws.linux-physical-drive-evidence/v1"
WHOLE_DISK = re.compile(r"^/dev/(sd[a-z]+|vd[a-z]+|xvd[a-z]+|nvme\d+n\d+|mmcblk\d+)$")
EXTERNAL_TRANSPORTS = {"usb", "sd", "mmc"}


class EvidenceError(RuntimeError):
    pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def parse_target(target: str) -> str:
    normalized = target.strip()
    if not WHOLE_DISK.fullmatch(normalized):
        raise EvidenceError(
            "Target must be an exact Linux whole-disk path such as /dev/sdb, /dev/nvme1n1, or /dev/mmcblk1."
        )
    return normalized


def _mounts(node: dict[str, Any]) -> list[str]:
    values: list[str] = []
    raw = node.get("mountpoints")
    if isinstance(raw, list):
        values.extend(str(v) for v in raw if v)
    elif raw:
        values.append(str(raw))
    if node.get("mountpoint"):
        values.append(str(node["mountpoint"]))
    for child in node.get("children") or []:
        if isinstance(child, dict):
            values.extend(_mounts(child))
    return sorted(set(values))


def find_node(payload: dict[str, Any], target: str) -> dict[str, Any]:
    devices = payload.get("blockdevices")
    if not isinstance(devices, list):
        raise EvidenceError("lsblk evidence is missing blockdevices.")

    target_name = Path(target).name
    for node in devices:
        if not isinstance(node, dict):
            continue
        path = str(node.get("path") or "")
        name = str(node.get("name") or node.get("kname") or "")
        if path == target or name == target_name:
            return node
    raise EvidenceError(f"lsblk did not return the requested target {target}.")


def normalize(node: dict[str, Any], target: str) -> dict[str, Any]:
    if str(node.get("type") or "").lower() != "disk":
        raise EvidenceError("Target is not reported as a whole disk.")

    size = int(node.get("size") or 0)
    if size <= 0:
        raise EvidenceError("Target size is missing or invalid.")

    removable = (
        bool(int(node.get("rm") or 0))
        if str(node.get("rm") or "").isdigit()
        else bool(node.get("rm"))
    )
    read_only = (
        bool(int(node.get("ro") or 0))
        if str(node.get("ro") or "").isdigit()
        else bool(node.get("ro"))
    )
    transport = str(node.get("tran") or "").strip().lower() or None
    serial = str(node.get("serial") or "").strip() or None
    wwn = str(node.get("wwn") or "").strip() or None
    model = str(node.get("model") or "").strip() or None
    mounts = _mounts(node)

    external = removable or (transport in EXTERNAL_TRANSPORTS)
    stable_material = {
        "serial": serial,
        "wwn": wwn,
        "transport": transport,
        "size_bytes": size,
    }
    stable_identity = sha256_payload(stable_material) if (serial or wwn) else None
    identity_material = {
        "target": target,
        "model": model,
        **stable_material,
    }

    block_reasons: list[str] = []
    if read_only:
        block_reasons.append("target-is-read-only")
    if not external:
        block_reasons.append("target-not-proven-external-removable")
    if mounts:
        block_reasons.append("target-or-child-partition-is-mounted")
    if "/" in mounts or "/boot" in mounts or "/boot/efi" in mounts:
        block_reasons.append("target-contains-system-mount")
    if not stable_identity:
        block_reasons.append("stable-device-identity-missing")

    return {
        "target": target,
        "kernel_name": str(node.get("kname") or node.get("name") or Path(target).name),
        "model": model,
        "serial_number": serial,
        "wwn": wwn,
        "transport": transport,
        "size_bytes": size,
        "is_removable": removable,
        "is_external": external,
        "is_read_only": read_only,
        "mountpoints": mounts,
        "identity_sha256": sha256_payload(identity_material),
        "stable_identity_sha256": stable_identity,
        "write_candidate": not block_reasons,
        "write_block_reasons": block_reasons,
    }


def query_lsblk(target: str) -> dict[str, Any]:
    if not sys.platform.startswith("linux"):
        raise EvidenceError("Live Linux physical-drive collection requires Linux.")
    completed = subprocess.run(
        [
            "lsblk",
            "-J",
            "-b",
            "-o",
            "NAME,KNAME,PATH,TYPE,SIZE,RM,RO,TRAN,SERIAL,WWN,MODEL,MOUNTPOINT,MOUNTPOINTS",
            target,
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if completed.returncode != 0:
        raise EvidenceError(
            completed.stderr.strip() or "lsblk evidence collection failed."
        )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise EvidenceError("lsblk returned malformed JSON.") from exc


def build_receipt(
    *,
    target: str,
    lsblk_payload: dict[str, Any],
    source_commit: str,
    evidence_source: str,
) -> dict[str, Any]:
    canonical_target = parse_target(target)
    node = find_node(lsblk_payload, canonical_target)
    disk = normalize(node, canonical_target)
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "captured_at": utc_now_iso(),
        "evidence_source": evidence_source,
        "source_commit": source_commit,
        "platform": "linux" if evidence_source == "live" else "fixture",
        "operation": "read-only-linux-physical-drive-evidence",
        "disk": disk,
        "bytes_read_from_raw_device": 0,
        "bytes_written": 0,
        "physical_write_attempted": False,
        "hardware_observed": evidence_source == "live",
        "classification": (
            "hardware-evidence-captured"
            if evidence_source == "live"
            else "fixture-validated"
        ),
        "next_required_action": (
            "linux-writer-remains-locked-pending-separate-executor-qualification"
            if disk["write_candidate"]
            else "resolve-write-block-reasons"
        ),
    }
    receipt["receipt_sha256"] = sha256_payload(receipt)
    return receipt


def write_atomic(receipt: dict[str, Any], output: Path) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=output.parent, delete=False
    ) as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
        temporary = Path(tmp.name)
    os.replace(temporary, output)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--source-commit", default=os.environ.get("GITHUB_SHA", "unknown")
    )
    parser.add_argument("--fixture-json", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    target = parse_target(args.target)
    if args.fixture_json:
        payload = json.loads(args.fixture_json.read_text(encoding="utf-8"))
        source = "fixture"
    else:
        payload = query_lsblk(target)
        source = "live"
    receipt = build_receipt(
        target=target,
        lsblk_payload=payload,
        source_commit=args.source_commit,
        evidence_source=source,
    )
    write_atomic(receipt, args.output)
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        EvidenceError,
        OSError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as exc:
        print(f"LINUX_DRIVE_EVIDENCE_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
