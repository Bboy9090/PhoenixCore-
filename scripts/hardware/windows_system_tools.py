"""Resolve Windows system tools using the native API, not PATH or environment."""

from __future__ import annotations

import ctypes
from pathlib import Path


def system_tool_path(name: str) -> str:
    allowed = {
        "powershell": ("WindowsPowerShell", "v1.0", "powershell.exe"),
        "diskpart": ("diskpart.exe",),
    }
    if name not in allowed:
        raise ValueError("Unsupported Windows system tool")
    try:
        api = ctypes.windll.kernel32.GetSystemDirectoryW
    except AttributeError as exc:
        raise RuntimeError("Native Windows system directory API unavailable") from exc
    api.argtypes = [ctypes.c_wchar_p, ctypes.c_uint]
    api.restype = ctypes.c_uint
    buffer = ctypes.create_unicode_buffer(32768)
    size = api(buffer, len(buffer))
    if not size or size >= len(buffer):
        raise RuntimeError("Native Windows system directory lookup failed")
    binary = Path(buffer.value).joinpath(*allowed[name])
    if not binary.is_absolute() or not binary.is_file():
        raise RuntimeError("Windows system tool missing at native system path")
    return str(binary)
