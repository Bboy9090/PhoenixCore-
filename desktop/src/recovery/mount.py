"""Cross-platform mount helpers."""
from __future__ import annotations
from contextlib import contextmanager
from typing import Iterator, Optional
from pathlib import Path
import ctypes
import os
import string
import sys

from ..core.config import MOUNT_BASE
from ..core.logger import get_logger
from .validators import run_capture

log = get_logger(__name__)


def _ensure_base() -> Path:
    MOUNT_BASE.mkdir(parents=True, exist_ok=True)
    return MOUNT_BASE


def _free_drive_letter(prefer: str = "W") -> Optional[str]:
    if not sys.platform.startswith("win"):
        return None
    used: set[str] = set()
    try:
        drives = ctypes.windll.kernel32.GetLogicalDrives()
        for idx, letter in enumerate(string.ascii_uppercase):
            if drives & (1 << idx):
                used.add(f"{letter}:")
    except Exception:
        used = {f"{c}:" for c in string.ascii_uppercase if os.path.exists(f"{c}:\\")}
    for c in [prefer] + [x for x in string.ascii_uppercase if x not in (prefer, "A", "B", "C")]:
        if f"{c}:" not in used:
            return c
    return None


@contextmanager
def mounted(part_dev: str, desired: str | None = None, rw: bool = True) -> Iterator[str]:
    _ensure_base()
    system = sys.platform
    mount_target = None
    win_temp_letter = None
    try:
        if system.startswith("win"):
            if part_dev == "EFI":
                rc, _, _ = run_capture(["mountvol", "S:", "/S"])
                if rc != 0:
                    raise RuntimeError("Failed to mount EFI to S:")
                mount_target = "S:\\"
            elif len(part_dev) == 2 and part_dev[1] == ":":
                mount_target = f"{part_dev}\\"
            elif part_dev.startswith("\\\\?\\Volume"):
                letter = desired or _free_drive_letter("W") or "W"
                rc, _, _ = run_capture(["mountvol", f"{letter}:", part_dev])
                if rc != 0:
                    raise RuntimeError(f"Failed to mount {part_dev} to {letter}:")
                win_temp_letter = letter
                mount_target = f"{letter}:\\"
            else:
                mount_target = f"{part_dev}\\"
            yield mount_target
        elif system.startswith("darwin"):
            devname = Path(part_dev).name
            mp = Path(desired) if desired else Path(f"/Volumes/bootforge_{devname}")
            mp.mkdir(parents=True, exist_ok=True)
            rc, _, err = run_capture(["/usr/sbin/diskutil", "mount", "-mountPoint", str(mp), part_dev])
            if rc != 0:
                raise RuntimeError(f"diskutil mount failed: {err.strip()}")
            mount_target = str(mp)
            yield mount_target
        else:
            mp = Path(desired) if desired else _ensure_base() / Path(part_dev).name
            mp.mkdir(parents=True, exist_ok=True)
            opts = "rw" if rw else "ro,norecover"
            rc, _, err = run_capture(["mount", "-o", opts, "-t", "auto", part_dev, str(mp)])
            if rc != 0:
                raise RuntimeError(f"mount failed: {err.strip()}")
            mount_target = str(mp)
            yield mount_target
    finally:
        try:
            if system.startswith("win"):
                if part_dev == "EFI":
                    run_capture(["mountvol", "S:", "/D"])
                elif win_temp_letter:
                    run_capture(["mountvol", f"{win_temp_letter}:", "/D"])
            elif system.startswith("darwin"):
                if mount_target:
                    run_capture(["/usr/sbin/diskutil", "unmount", mount_target])
                    try:
                        Path(mount_target).rmdir()
                    except Exception:
                        pass
            else:
                if mount_target:
                    run_capture(["umount", "-l", mount_target])
                    try:
                        Path(mount_target).rmdir()
                    except Exception:
                        pass
        except Exception as exc:
            log.warning("Unmount cleanup issue: %s", exc)
