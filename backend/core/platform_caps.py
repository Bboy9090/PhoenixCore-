"""
Host capability flags for honest API responses (no silent cross-OS parity).
"""
from __future__ import annotations

import os
import platform
import shutil
from typing import Dict, Any


def _executable_available(name: str) -> bool:
    if shutil.which(name):
        return True
    for d in ("/usr/bin", "/bin", "/sbin", "/usr/sbin"):
        p = os.path.join(d, name)
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return True
    return False


def destructive_usb_write_native() -> bool:
    """
    True when this backend can run the Linux-native format/write path
    (parted, dd, mkfs.*) used by usb_builder for real jobs.
    """
    if platform.system().lower() != "linux":
        return False
    return _executable_available("dd") and _executable_available("parted")


def platform_caps() -> Dict[str, Any]:
    sys = platform.system().lower()
    native = destructive_usb_write_native()
    return {
        "host_os": sys,
        "destructive_usb_write_native": native,
        "notes": (
            "When destructive_usb_write_native is false, USB build jobs may log or "
            "simulate steps; use BootForge on the desktop path or extend platform support."
        ),
    }
