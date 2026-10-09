#!/usr/bin/env python3
"""
PhoenixCore Bare-Metal USB Flash Verification & Integrity Checker
"""

import os
import hashlib


class BareMetalFlashValidator:
    def __init__(self, usb_block_device: str):
        self.usb_block_device = usb_block_device

    def verify_sector_integrity(self, expected_sha256: str) -> bool:
        if not os.path.exists(self.usb_block_device):
            return False
        if len(expected_sha256) != 64:
            return False
        try:
            int(expected_sha256, 16)
        except ValueError:
            return False

        digest = hashlib.sha256()
        try:
            with open(self.usb_block_device, "rb", buffering=0) as stream:
                for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
                    digest.update(chunk)
        except (OSError, PermissionError):
            return False
        return digest.hexdigest() == expected_sha256.lower()


if __name__ == "__main__":
    raise SystemExit("Invoke with an explicit target and expected SHA-256.")
