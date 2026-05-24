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


# ── macOS / Ventoy helpers ────────────────────────────────────────────────────

def is_macos() -> bool:
    """Returns True if running on macOS (darwin)."""
    return sys.platform.startswith("darwin")


def is_linux() -> bool:
    """Returns True if running on Linux."""
    return sys.platform.startswith("linux")


def is_windows() -> bool:
    """Returns True if running on Windows."""
    return sys.platform.startswith("win")


def is_apple_silicon() -> bool:
    """Returns True if running on Apple Silicon (arm64)."""
    return is_macos() and platform.machine().lower() in ("arm64", "aarch64")


def get_ventoy_install_method(device_path: str = "/dev/disk2") -> dict:
    """
    Returns the correct Ventoy install method for the current platform.

    Returns a dict with:
        method: 'shell' | 'exe'
        platform: 'macos' | 'linux' | 'windows'
        command: the exact command to run
        description: human-readable description
        requires_sudo: bool
        script_name: the script/exe filename to use
    """
    if is_macos():
        return {
            "method": "shell",
            "platform": "macos",
            "command": f"sudo sh Ventoy2Disk.sh -i {device_path}",
            "update_command": f"sudo sh Ventoy2Disk.sh -u {device_path}",
            "description": "macOS native — Ventoy2Disk.sh (no Windows needed)",
            "requires_sudo": True,
            "script_name": "Ventoy2Disk.sh",
            "download_url": "https://github.com/ventoy/Ventoy/releases/latest/download/ventoy-1.0.99-mac.tar.gz",
        }
    if is_linux():
        return {
            "method": "shell",
            "platform": "linux",
            "command": f"sudo sh Ventoy2Disk.sh -i {device_path}",
            "update_command": f"sudo sh Ventoy2Disk.sh -u {device_path}",
            "description": "Linux native — Ventoy2Disk.sh",
            "requires_sudo": True,
            "script_name": "Ventoy2Disk.sh",
            "download_url": "https://github.com/ventoy/Ventoy/releases/latest/download/ventoy-1.0.99-linux.tar.gz",
        }
    # Windows default
    win_device = device_path.replace("/dev/disk", "\\\\.\\PhysicalDrive")
    return {
        "method": "exe",
        "platform": "windows",
        "command": f"Ventoy2Disk.exe /I {win_device}",
        "update_command": f"Ventoy2Disk.exe /U {win_device}",
        "description": "Windows — Ventoy2Disk.exe",
        "requires_sudo": False,
        "script_name": "Ventoy2Disk.exe",
        "download_url": "https://github.com/ventoy/Ventoy/releases/latest/download/ventoy-1.0.99-windows.zip",
    }


def run_ventoy_install(device_path: str, ventoy_dir: Path, update: bool = False) -> tuple[bool, str]:
    """
    Runs Ventoy2Disk.sh (macOS/Linux) or Ventoy2Disk.exe (Windows) to install/update Ventoy.

    Args:
        device_path: The disk path e.g. '/dev/disk2' or '\\\\.\\PhysicalDrive1'
        ventoy_dir:  Path to the extracted Ventoy directory containing the script/exe
        update:      If True, runs update (-u) instead of install (-i)

    Returns:
        (success: bool, output: str)
    """
    import subprocess

    info = get_ventoy_install_method(device_path)
    script = ventoy_dir / info["script_name"]

    if not script.exists():
        return False, f"Ventoy script not found at {script}"

    if info["method"] == "shell":
        flag = "-u" if update else "-i"
        cmd = ["sudo", "sh", str(script), flag, device_path]
    else:
        flag = "/U" if update else "/I"
        cmd = [str(script), flag, device_path]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Ventoy install timed out after 120 seconds"
    except Exception as e:
        return False, f"Ventoy install error: {e}"
