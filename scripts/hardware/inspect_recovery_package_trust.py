#!/usr/bin/env python3
"""Verify recovery package integrity and signature evidence without modifying it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA = "phoenix_key.recovery_package_trust.v1"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
AUTHENTICODE_EXTENSIONS = {
    ".exe",
    ".msi",
    ".dll",
    ".efi",
    ".sys",
    ".cat",
    ".ps1",
}
HASH_MANIFEST_EXTENSIONS = {
    ".iso",
    ".wim",
    ".esd",
    ".vhd",
    ".vhdx",
    ".swm",
    ".ffu",
    ".zip",
    ".bin",
    ".rom",
    ".cap",
    ".fd",
}


class PackageTrustError(RuntimeError):
    """Raised when package trust evidence cannot be collected."""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def trust_route(path: Path) -> str:
    extension = path.suffix.lower()
    if extension in AUTHENTICODE_EXTENSIONS:
        return "hash_plus_authenticode"
    if extension in HASH_MANIFEST_EXTENSIONS:
        return "external_hash_manifest"
    return "unknown_package_type"


def inspect_authenticode(path: Path) -> dict[str, Any]:
    if sys.platform != "win32":
        return {
            "checked": False,
            "status": "not-supported-on-current-platform",
            "status_message": None,
            "signer_subject": None,
            "signer_thumbprint": None,
        }

    script = """
$ErrorActionPreference = 'Stop'
$signature = Get-AuthenticodeSignature -LiteralPath $env:PHOENIX_VERIFY_PATH
[pscustomobject]@{
  Status = [string]$signature.Status
  StatusMessage = [string]$signature.StatusMessage
  SignerSubject = if ($signature.SignerCertificate) {
    [string]$signature.SignerCertificate.Subject
  } else { $null }
  SignerThumbprint = if ($signature.SignerCertificate) {
    [string]$signature.SignerCertificate.Thumbprint
  } else { $null }
} | ConvertTo-Json -Compress
"""
    environment = dict(os.environ)
    environment["PHOENIX_VERIFY_PATH"] = str(path.resolve())
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
        raise PackageTrustError(f"Authenticode inspection failed: {message}")
    try:
        value = json.loads(completed.stdout.strip())
    except json.JSONDecodeError as exc:
        raise PackageTrustError(
            "Authenticode inspection returned malformed JSON."
        ) from exc

    return {
        "checked": True,
        "status": str(value.get("Status") or ""),
        "status_message": str(value.get("StatusMessage") or "") or None,
        "signer_subject": str(value.get("SignerSubject") or "") or None,
        "signer_thumbprint": str(value.get("SignerThumbprint") or "") or None,
    }


def evaluate_package_trust(
    path: Path,
    *,
    expected_sha256: str | None,
    expected_signer_contains: str | None = None,
    signature_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not path.is_file():
        raise PackageTrustError(
            "Recovery package does not exist or is not a regular file."
        )

    observed_sha256 = file_sha256(path)
    expected = (expected_sha256 or "").strip().lower()
    hash_expected = bool(expected)
    hash_valid_format = bool(SHA256_RE.fullmatch(expected)) if hash_expected else False
    hash_matches = hash_valid_format and observed_sha256 == expected
    route = trust_route(path)

    signature = signature_record
    if route == "hash_plus_authenticode" and signature is None:
        signature = inspect_authenticode(path)
    if signature is None:
        signature = {
            "checked": False,
            "status": "not-required-for-this-package-type",
            "status_message": None,
            "signer_subject": None,
            "signer_thumbprint": None,
        }

    signature_valid = route != "hash_plus_authenticode" or (
        signature.get("checked") is True
        and str(signature.get("status") or "").lower() == "valid"
    )
    signer_expected = (expected_signer_contains or "").strip()
    signer_subject = str(signature.get("signer_subject") or "")
    signer_matches = not signer_expected or (
        bool(signer_subject) and signer_expected.lower() in signer_subject.lower()
    )

    block_reasons: list[str] = []
    if not hash_expected:
        block_reasons.append("expected_sha256_missing")
    elif not hash_valid_format:
        block_reasons.append("expected_sha256_invalid")
    elif not hash_matches:
        block_reasons.append("sha256_mismatch")

    if route == "unknown_package_type":
        block_reasons.append("package_type_not_supported_for_trust_decision")
    if route == "hash_plus_authenticode" and not signature_valid:
        block_reasons.append("authenticode_signature_not_valid")
    if signer_expected and not signer_matches:
        block_reasons.append("signer_subject_mismatch")

    verified = not block_reasons
    return {
        "schema": SCHEMA,
        "path": str(path.resolve()),
        "package_name": path.name,
        "package_extension": path.suffix.lower(),
        "trust_route": route,
        "observed_sha256": observed_sha256,
        "expected_sha256": expected or None,
        "sha256_matches": hash_matches,
        "authenticode": signature,
        "expected_signer_contains": signer_expected or None,
        "signer_matches": signer_matches,
        "verified_for_use": verified,
        "block_reasons": block_reasons,
        "file_modified": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--expected-signer-contains")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = evaluate_package_trust(
        args.path,
        expected_sha256=args.expected_sha256,
        expected_signer_contains=args.expected_signer_contains,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (PackageTrustError, OSError, ValueError) as exc:
        print(f"RECOVERY_PACKAGE_TRUST_FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
