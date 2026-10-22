"""Resolve Windows system tools using the native API, not PATH or environment."""

from __future__ import annotations

import ctypes
from pathlib import Path
import subprocess
import time


class SystemToolCancelled(RuntimeError):
    """Raised after a cancelled native child has been terminated and reaped."""


class SystemToolTimeout(RuntimeError):
    """Raised after a timed-out native child has been killed and reaped."""


def run_cancellable(
    command: list[str],
    *,
    timeout_seconds: float,
    cancelled=lambda: False,
) -> subprocess.CompletedProcess[str]:
    """Capture a native command while enforcing cancellation and a deadline."""
    if not command or timeout_seconds <= 0:
        raise ValueError("A command and positive timeout are required")
    if cancelled():
        raise SystemToolCancelled("Native system-tool query cancelled before launch")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + timeout_seconds
    try:
        while True:
            if cancelled():
                process.terminate()
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                raise SystemToolCancelled("Native system-tool query cancelled")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                process.kill()
                process.communicate()
                raise SystemToolTimeout(
                    f"Native system-tool query exceeded {timeout_seconds:g} seconds"
                )
            try:
                stdout, stderr = process.communicate(timeout=min(0.1, remaining))
            except subprocess.TimeoutExpired:
                continue
            if cancelled():
                raise SystemToolCancelled(
                    "Native system-tool query cancelled before result acceptance"
                )
            return subprocess.CompletedProcess(
                command, process.returncode, stdout, stderr
            )
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()


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
