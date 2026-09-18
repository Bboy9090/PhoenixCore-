#!/usr/bin/env python3
"""Inventory and verify a Boot Camp Windows support-software package read-only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

SCHEMA = "phoenix_key.bootcamp_driver_manifest.v1"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
SIGNED_EXTENSIONS = {".exe", ".msi", ".dll", ".sys", ".cat"}
MODEL_EVIDENCE_EXTENSIONS = {".dist", ".xml", ".plist", ".txt"}
MAX_MODEL_EVIDENCE_BYTES = 2 * 1024 * 1024


class BootCampDriverError(RuntimeError):
    """Raised when a Boot Camp support package cannot be verified safely."""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def file_contains_model_identifier(path: Path, model: str) -> bool:
    if path.suffix.lower() not in MODEL_EVIDENCE_EXTENSIONS:
        return False
    try:
        if path.stat().st_size > MAX_MODEL_EVIDENCE_BYTES:
            return False
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    pattern = re.compile(
        rf"(?<![A-Za-z0-9_,.-]){re.escape(model)}(?![A-Za-z0-9_,.-])",
        re.IGNORECASE,
    )
    return bool(pattern.search(text))


def canonical_manifest_digest(files: list[dict[str, Any]]) -> str:
    body = json.dumps(
        files,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def inspect_authenticode(path: Path) -> dict[str, Any]:
    if sys.platform != "win32":
        return {
            "checked": False,
            "status": "pending-windows-signature-check",
            "signer_subject": None,
        }

    script = """
$ErrorActionPreference = 'Stop'
$sig = Get-AuthenticodeSignature -LiteralPath $env:PHOENIX_DRIVER_PATH
[pscustomobject]@{
  Status = [string]$sig.Status
  SignerSubject = if ($sig.SignerCertificate) {
    [string]$sig.SignerCertificate.Subject
  } else { $null }
} | ConvertTo-Json -Compress
"""
    environment = dict(os.environ)
    environment["PHOENIX_DRIVER_PATH"] = str(path.resolve())
    completed = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise BootCampDriverError(
            f"Authenticode driver inspection failed: {message}"
        )
    try:
        value = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise BootCampDriverError(
            "Authenticode driver inspection returned malformed JSON."
        ) from exc
    return {
        "checked": True,
        "status": str(value.get("Status") or ""),
        "signer_subject": str(value.get("SignerSubject") or "") or None,
    }


def build_driver_manifest(
    root: Path,
    *,
    mac_model: str,
    expected_manifest_sha256: str | None = None,
    signature_inspector: Callable[[Path], dict[str, Any]] = inspect_authenticode,
) -> dict[str, Any]:
    if not root.is_dir():
        raise BootCampDriverError(
            "Boot Camp support-software path is not a directory."
        )
    model = mac_model.strip()
    if not model:
        raise BootCampDriverError("Exact Mac model identifier is required.")

    files: list[dict[str, Any]] = []
    signature_failures: list[str] = []
    signature_pending: list[str] = []
    model_evidence_files: list[str] = []

    for current_root, directories, filenames in os.walk(root):
        current = Path(current_root)
        kept_directories = []
        for name in directories:
            candidate = current / name
            if candidate.is_symlink():
                raise BootCampDriverError(
                    f"Symbolic-link directory is not accepted: {candidate}"
                )
            kept_directories.append(name)
        directories[:] = kept_directories

        for name in filenames:
            path = current / name
            if path.is_symlink():
                raise BootCampDriverError(
                    f"Symbolic-link file is not accepted: {path}"
                )
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            entry: dict[str, Any] = {
                "relative_path": relative,
                "size_bytes": path.stat().st_size,
                "sha256": file_sha256(path),
                "extension": path.suffix.lower(),
            }
            if file_contains_model_identifier(path, model):
                model_evidence_files.append(relative)
            if path.suffix.lower() in SIGNED_EXTENSIONS:
                signature = signature_inspector(path)
                entry["authenticode"] = signature
                if signature.get("checked") is not True:
                    signature_pending.append(relative)
                elif str(signature.get("status") or "").lower() != "valid":
                    signature_failures.append(relative)
            files.append(entry)

    files.sort(key=lambda item: item["relative_path"])
    manifest_sha256 = canonical_manifest_digest(files)
    expected = (expected_manifest_sha256 or "").strip().lower()
    expected_present = bool(expected)
    expected_valid = bool(SHA256_RE.fullmatch(expected)) if expected_present else False
    manifest_matches = expected_valid and expected == manifest_sha256

    block_reasons: list[str] = []
    if not files:
        block_reasons.append("driver_package_empty")
    if not expected_present:
        block_reasons.append("expected_manifest_sha256_missing")
    elif not expected_valid:
        block_reasons.append("expected_manifest_sha256_invalid")
    elif not manifest_matches:
        block_reasons.append("driver_manifest_sha256_mismatch")
    if signature_failures:
        block_reasons.append("invalid_driver_signatures_present")
    if signature_pending:
        block_reasons.append("driver_signature_verification_pending_on_windows")
    if not model_evidence_files:
        block_reasons.append("exact_model_support_evidence_missing")

    return {
        "schema": SCHEMA,
        "root": str(root.resolve()),
        "mac_model_identifier": model,
        "file_count": len(files),
        "files": files,
        "manifest_sha256": manifest_sha256,
        "expected_manifest_sha256": expected or None,
        "manifest_sha256_matches": manifest_matches,
        "signature_failures": signature_failures,
        "signature_pending": signature_pending,
        "model_evidence_files": sorted(model_evidence_files),
        "exact_model_support_evidence": bool(model_evidence_files),
        "verified_for_model": not block_reasons,
        "block_reasons": block_reasons,
        "package_modified": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--mac-model", required=True)
    parser.add_argument("--expected-manifest-sha256")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_driver_manifest(
        args.root,
        mac_model=args.mac_model,
        expected_manifest_sha256=args.expected_manifest_sha256,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BootCampDriverError, OSError, ValueError) as exc:
        print(f"BOOTCAMP_DRIVER_MANIFEST_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
