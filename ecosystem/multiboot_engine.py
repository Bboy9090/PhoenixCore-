#!/usr/bin/env python3
"""Phoenix USB Creator multiboot payload manifest writer."""

import hashlib
import json
from pathlib import Path


class MultiBootPayloadEngine:
    def __init__(self, target_drive_path: str):
        self.target_drive_path = target_drive_path
        self.payloads = []

    def add_payload(self, name: str, iso_path: str, payload_type: str):
        self.payloads.append({"name": name, "iso_path": iso_path, "type": payload_type})

    def write_manifest(self, manifest_data: dict) -> str:
        target = Path(self.target_drive_path)
        if not target.is_dir():
            raise FileNotFoundError(f"Target root does not exist: {target}")
        if not manifest_data.get("target_identity"):
            raise ValueError("A stable target_identity is required")

        verified_payloads = []
        for payload in self.payloads:
            source = Path(payload["iso_path"])
            if not source.is_file() or source.stat().st_size == 0:
                raise FileNotFoundError(f"Payload is missing or empty: {source}")
            digest = hashlib.sha256()
            with source.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            verified_payloads.append(
                {
                    **payload,
                    "size_bytes": source.stat().st_size,
                    "sha256": digest.hexdigest(),
                }
            )

        document = {
            **manifest_data,
            "schema": "arcwyre.drive.multiboot-manifest.v1",
            "payloads": verified_payloads,
        }
        manifest_path = target / "REPAIR_MANIFEST.json"
        temporary_path = manifest_path.with_suffix(".json.partial")
        temporary_path.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        temporary_path.replace(manifest_path)
        return str(manifest_path)


if __name__ == "__main__":
    raise SystemExit("Invoke through ARCWYRE Drive with an identity-locked target root.")
