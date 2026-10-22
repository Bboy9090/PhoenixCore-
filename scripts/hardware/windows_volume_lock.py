"""Native Windows volume lock primitive for guarded provisioning phases.

This module does not select a disk, format a volume, or authorize a write. The
caller must first prove target identity and eligibility. A locked volume cannot
also be verified through its mounted drive-letter path, so readback requires a
later unlock, remount, and fresh identity binding.

Microsoft contracts:
https://learn.microsoft.com/windows/win32/api/winioctl/ni-winioctl-fsctl_lock_volume
https://learn.microsoft.com/windows/win32/api/winioctl/ni-winioctl-fsctl_dismount_volume
"""

from __future__ import annotations

import ctypes
import re
import sys


FSCTL_LOCK_VOLUME = 0x00090018
FSCTL_UNLOCK_VOLUME = 0x0009001C
FSCTL_DISMOUNT_VOLUME = 0x00090020


class VolumeLockError(RuntimeError):
    """Raised when exclusive native volume ownership cannot be established."""


def canonical_volume(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z]:", value):
        raise VolumeLockError("Volume must be an exact local drive designator like G:")
    return value.upper()


def _open_volume_handle(volume: str) -> int:
    if sys.platform != "win32":
        raise VolumeLockError("Native volume locking requires Windows")
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE
    handle = create_file(
        rf"\\.\{volume}",
        0x80000000 | 0x40000000,  # GENERIC_READ | GENERIC_WRITE
        0x00000001 | 0x00000002,  # FILE_SHARE_READ | FILE_SHARE_WRITE
        None,
        3,  # OPEN_EXISTING
        0,
        None,
    )
    if handle == wintypes.HANDLE(-1).value:
        raise VolumeLockError(
            f"Opening {volume} for direct volume access failed with Win32 error "
            f"{ctypes.get_last_error()}"
        )
    return handle


def _device_control(handle: int, control_code: int) -> None:
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    device_io = kernel32.DeviceIoControl
    device_io.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    device_io.restype = wintypes.BOOL
    returned = wintypes.DWORD()
    if not device_io(
        handle, control_code, None, 0, None, 0, ctypes.byref(returned), None
    ):
        raise VolumeLockError(
            f"Volume control 0x{control_code:08X} failed with Win32 error "
            f"{ctypes.get_last_error()}"
        )


def _close_handle(handle: int) -> None:
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    close = kernel32.CloseHandle
    close.argtypes = [wintypes.HANDLE]
    close.restype = wintypes.BOOL
    if not close(handle):
        raise VolumeLockError(
            f"Closing volume handle failed with Win32 error {ctypes.get_last_error()}"
        )


class LockedWindowsVolume:
    """Own one volume lock until explicitly released or context exit."""

    def __init__(self, volume: str, cancelled=lambda: False):
        self.volume = canonical_volume(volume)
        self.cancelled = cancelled
        self.handle: int | None = None
        self.locked = False
        self.dismounted = False

    def __enter__(self) -> "LockedWindowsVolume":
        if self.cancelled():
            raise VolumeLockError("Cancelled before opening volume lock")
        self.handle = _open_volume_handle(self.volume)
        try:
            _device_control(self.handle, FSCTL_LOCK_VOLUME)
            self.locked = True
            if self.cancelled():
                raise VolumeLockError("Cancelled after locking volume")
            return self
        except Exception:
            self.close()
            raise

    def dismount(self) -> None:
        if not self.locked or self.handle is None:
            raise VolumeLockError("Volume must be locked before dismount")
        if self.cancelled():
            raise VolumeLockError("Cancelled before volume dismount")
        _device_control(self.handle, FSCTL_DISMOUNT_VOLUME)
        self.dismounted = True

    def close(self) -> None:
        handle, locked = self.handle, self.locked
        self.handle = None
        self.locked = False
        self.dismounted = False
        if handle is None:
            return
        error = None
        try:
            if locked:
                _device_control(handle, FSCTL_UNLOCK_VOLUME)
        except Exception as exc:
            error = exc
        try:
            _close_handle(handle)
        except Exception as exc:
            error = error or exc
        if error is not None:
            raise error

    def __exit__(self, exception_type, _exception, _traceback) -> bool:
        try:
            self.close()
        except Exception:
            if exception_type is None:
                raise
        return False

