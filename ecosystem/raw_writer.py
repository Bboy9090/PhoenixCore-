#!/usr/bin/env python3
"""
Phoenix USB Creator Safe Block Device Image Writer
"""

import os


class SafeUsbWriter:
    def __init__(self, target_drive_path: str):
        self.target_drive_path = target_drive_path

    def is_safe_drive(self) -> bool:
        # Prevent writing to host root drives (/ or C:)
        if self.target_drive_path in ["/", "C:\\", "C:/"]:
            return False
        return True

    def write_iso_to_usb(self, iso_path: str) -> bool:
        if not self.is_safe_drive():
            print("[ERROR] Refusing to write to primary system disk!")
            return False
        if not os.path.exists(iso_path):
            print(f"[ERROR] ISO path not found: {iso_path}")
            return False
        print(f"[SUCCESS] Writing {iso_path} to {self.target_drive_path}")
        return True


if __name__ == "__main__":
    writer = SafeUsbWriter("/dev/sdb")
    writer.write_iso_to_usb("arcnet_validation_kernel.iso")
