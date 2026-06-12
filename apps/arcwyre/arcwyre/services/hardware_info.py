"""
Hardware Information Service — Real hardware detection
Uses lspci, lsusb (Linux) and system_profiler (macOS).
Uses dmidecode for BIOS/motherboard info (requires root on Linux).
"""

import platform
import subprocess
import shutil
from typing import Any


def _run(cmd: list[str], timeout: int = 30) -> tuple[str, str, int]:
    """Run a subprocess with timeout."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        return "", f"Command not found: {cmd[0]}", -1
    except subprocess.TimeoutExpired:
        return "", f"Command timed out after {timeout}s", -2
    except Exception as e:
        return "", str(e), -3


def get_pci_devices() -> list[dict[str, str]]:
    """Get PCI devices from the real system."""
    system = platform.system()

    if system == "Linux":
        if not shutil.which("lspci"):
            return [{"error": "NOT IMPLEMENTED — lspci not found. Install pciutils: sudo apt install pciutils"}]

        stdout, stderr, rc = _run(["lspci", "-vmm"])
        if rc != 0:
            return [{"error": f"lspci failed: {stderr}"}]

        devices = []
        current: dict[str, str] = {}
        for line in stdout.splitlines():
            if not line.strip():
                if current:
                    devices.append(current)
                    current = {}
                continue
            if ":" in line:
                key, _, value = line.partition(":")
                current[key.strip().lower()] = value.strip()
        if current:
            devices.append(current)
        return devices

    elif system == "Darwin":
        stdout, stderr, rc = _run(["system_profiler", "SPPCIDataType", "-detailLevel", "mini"])
        if rc != 0:
            return [{"error": f"system_profiler failed: {stderr}"}]

        devices = []
        current: dict[str, str] = {}
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip().lower()
                value = value.strip()
                if value:
                    current[key] = value
                elif current:
                    devices.append(current)
                    current = {"name": key}
            elif current:
                current.setdefault("name", line)
        if current:
            devices.append(current)
        return devices if devices else [{"info": "No PCI device data available from system_profiler"}]

    return [{"error": f"PCI enumeration not implemented for {system}"}]


def get_usb_devices() -> list[dict[str, str]]:
    """Get USB devices from the real system."""
    system = platform.system()

    if system == "Linux":
        if not shutil.which("lsusb"):
            return [{"error": "NOT IMPLEMENTED — lsusb not found. Install usbutils: sudo apt install usbutils"}]

        stdout, stderr, rc = _run(["lsusb"])
        if rc != 0:
            return [{"error": f"lsusb failed: {stderr}"}]

        devices = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            # Format: Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
            parts = line.split(":", 1)
            if len(parts) == 2:
                bus_info = parts[0].strip()
                desc = parts[1].strip()
                # Extract ID
                id_part = ""
                name_part = desc
                if desc.startswith("ID "):
                    id_rest = desc[3:]
                    id_end = id_rest.find(" ")
                    if id_end > 0:
                        id_part = id_rest[:id_end]
                        name_part = id_rest[id_end + 1:]
                    else:
                        id_part = id_rest

                devices.append({
                    "bus": bus_info,
                    "id": id_part,
                    "name": name_part,
                })
        return devices

    elif system == "Darwin":
        stdout, stderr, rc = _run(["system_profiler", "SPUSBDataType", "-detailLevel", "mini"])
        if rc != 0:
            return [{"error": f"system_profiler failed: {stderr}"}]

        devices = []
        current: dict[str, str] = {}
        for line in stdout.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip().lower()
                value = value.strip()
                if value:
                    current[key] = value
                else:
                    if current and any(k != "name" for k in current):
                        devices.append(current)
                    current = {"name": key}
        if current and any(k != "name" for k in current):
            devices.append(current)
        return devices if devices else [{"info": "No USB device data returned by system_profiler"}]

    return [{"error": f"USB enumeration not implemented for {system}"}]


def get_bios_info() -> dict[str, str]:
    """Get BIOS/firmware information. Requires root on Linux."""
    system = platform.system()

    if system == "Linux":
        if not shutil.which("dmidecode"):
            return {"error": "NOT IMPLEMENTED — dmidecode not found. Install dmidecode: sudo apt install dmidecode"}

        stdout, stderr, rc = _run(["dmidecode", "-t", "bios"])
        if rc != 0:
            if "Permission denied" in stderr or "Operation not permitted" in stderr:
                return {"error": "Requires elevated privileges. Run with sudo or pkexec."}
            return {"error": f"dmidecode failed: {stderr}"}

        info: dict[str, str] = {}
        for line in stdout.splitlines():
            line = line.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                value = value.strip()
                if value:
                    info[key.strip().lower()] = value
        return info if info else {"info": "No BIOS data parsed from dmidecode output"}

    elif system == "Darwin":
        stdout, stderr, rc = _run(["system_profiler", "SPHardwareDataType", "-detailLevel", "mini"])
        if rc != 0:
            return {"error": f"system_profiler failed: {stderr}"}

        info = {}
        for line in stdout.splitlines():
            line = line.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                value = value.strip()
                if value:
                    info[key.strip().lower()] = value
        return info if info else {"info": "No hardware data from system_profiler"}

    return {"error": f"BIOS info not implemented for {system}"}


def get_gpu_info() -> list[dict[str, str]]:
    """Get GPU information from the real system."""
    system = platform.system()

    if system == "Linux":
        if shutil.which("lspci"):
            stdout, _, rc = _run(["lspci", "-v"])
            if rc == 0:
                gpus = []
                current_gpu: dict[str, str] | None = None
                for line in stdout.splitlines():
                    if "VGA" in line or "3D" in line or "Display" in line:
                        current_gpu = {"name": line.strip()}
                    elif current_gpu and line.startswith("\t") and ":" in line:
                        key, _, value = line.strip().partition(":")
                        current_gpu[key.strip().lower()] = value.strip()
                    elif current_gpu and not line.startswith("\t"):
                        gpus.append(current_gpu)
                        current_gpu = None
                if current_gpu:
                    gpus.append(current_gpu)
                return gpus if gpus else [{"info": "No GPU devices detected in lspci output"}]

        return [{"error": "NOT IMPLEMENTED — lspci not found"}]

    elif system == "Darwin":
        stdout, _, rc = _run(["system_profiler", "SPDisplaysDataType", "-detailLevel", "mini"])
        if rc == 0:
            gpus = []
            current: dict[str, str] = {}
            for line in stdout.splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                if ":" in stripped:
                    key, _, value = stripped.partition(":")
                    key = key.strip().lower()
                    value = value.strip()
                    if value:
                        current[key] = value
                    else:
                        if current and len(current) > 1:
                            gpus.append(current)
                        current = {"name": key}
            if current and len(current) > 1:
                gpus.append(current)
            return gpus if gpus else [{"info": "No GPU data from system_profiler"}]

        return [{"error": "system_profiler failed"}]

    return [{"error": f"GPU info not implemented for {system}"}]
