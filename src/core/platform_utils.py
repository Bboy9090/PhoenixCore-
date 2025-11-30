"""Cross-platform helpers for environment detection."""
from __future__ import annotations
import ctypes
import os
import sys
from pathlib import Path
import platform


def is_admin() -> bool:
    if sys.platform.startswith("win"):
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False
    return os.geteuid() == 0 if hasattr(os, "geteuid") else True


def arch() -> str:
    return platform.machine().lower()


def is_efi_boot() -> bool:
    if sys.platform.startswith("win"):
        return True
    if sys.platform.startswith("darwin"):
        return True
    return Path("/sys/firmware/efi").exists()


def meipass_path() -> Path:
    base = getattr(sys, "_MEIPASS", None)
    return Path(base) if base else Path(__file__).resolve().parent
