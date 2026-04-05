"""
Enforce platform capability before destructive USB operations.
"""
from __future__ import annotations

from typing import NoReturn

from core.platform_caps import destructive_usb_write_native


class DestructiveOperationNotSupported(RuntimeError):
    """Raised when native destructive USB path is unavailable on this host."""


def require_destructive_usb_native(*, dry_run: bool) -> None:
    if dry_run:
        return
    if not destructive_usb_write_native():
        raise DestructiveOperationNotSupported(
            "Native destructive USB write is not supported on this host OS or required tools (dd, parted) "
            "are missing. Use BootForge on the desktop path, run on Linux with parted+dd, or use dry_run=true."
        )


def explain_block() -> str:
    return (
        "destructive_usb_write_native is false for this server: non-dry-run USB imaging is blocked. "
        "See GET /api/health capabilities."
    )
