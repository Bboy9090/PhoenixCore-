"""
Phoenix Core - Real Hardware Profiler
Detects actual system hardware using psutil and platform APIs
"""
import platform
import subprocess
import logging
import time
import re
from typing import List, Optional, Dict, Any
import psutil

logger = logging.getLogger(__name__)


def _human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def _get_cpu_info() -> Dict[str, Any]:
    """Get detailed CPU information."""
    cpu_name = "Unknown CPU"
    manufacturer = "Unknown"
    
    system = platform.system()
    
    if system == "Linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line.lower():
                        cpu_name = line.split(":")[1].strip()
                        break
            # Detect manufacturer
            if "intel" in cpu_name.lower():
                manufacturer = "Intel"
            elif "amd" in cpu_name.lower():
                manufacturer = "AMD"
            elif "arm" in cpu_name.lower():
                manufacturer = "ARM"
            elif "apple" in cpu_name.lower():
                manufacturer = "Apple"
        except Exception:
            pass
    elif system == "Darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                cpu_name = result.stdout.strip()
                if "Intel" in cpu_name:
                    manufacturer = "Intel"
                elif "Apple" in cpu_name:
                    manufacturer = "Apple"
        except Exception:
            pass
    elif system == "Windows":
        try:
            result = subprocess.run(
                ["wmic", "cpu", "get", "name", "/value"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if "Name=" in line:
                    cpu_name = line.split("=")[1].strip()
                    break
        except Exception:
            pass

    freq = psutil.cpu_freq()
    freq_mhz = freq.current if freq else 0.0

    return {
        "name": cpu_name,
        "manufacturer": manufacturer,
        "architecture": platform.machine(),
        "cores_physical": psutil.cpu_count(logical=False) or 1,
        "cores_logical": psutil.cpu_count(logical=True) or 1,
        "frequency_mhz": round(freq_mhz, 1),
        "usage_percent": psutil.cpu_percent(interval=0.1),
    }


def _get_memory_info() -> Dict[str, Any]:
    """Get memory information."""
    mem = psutil.virtual_memory()
    return {
        "total_bytes": mem.total,
        "total_human": _human_size(mem.total),
        "available_bytes": mem.available,
        "used_bytes": mem.used,
        "percent": mem.percent,
    }


def _get_gpu_info() -> List[Dict[str, Any]]:
    """Get GPU information."""
    gpus = []
    system = platform.system()

    if system == "Linux":
        try:
            # Try lspci
            result = subprocess.run(
                ["lspci", "-mm"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if "VGA" in line or "3D" in line or "Display" in line:
                    parts = line.split('"')
                    vendor = parts[3] if len(parts) > 3 else "Unknown"
                    model = parts[5] if len(parts) > 5 else "Unknown GPU"
                    gpus.append({
                        "name": model,
                        "vendor": vendor,
                        "vram_bytes": None,
                    })
        except Exception:
            pass
        
        if not gpus:
            try:
                # Try /sys/class/drm
                drm_path = "/sys/class/drm"
                import os
                for entry in os.listdir(drm_path):
                    if "card" in entry and "-" not in entry:
                        vendor_path = f"{drm_path}/{entry}/device/vendor"
                        if os.path.exists(vendor_path):
                            vendor_id = open(vendor_path).read().strip()
                            vendor_map = {
                                "0x10de": "NVIDIA",
                                "0x1002": "AMD",
                                "0x8086": "Intel",
                            }
                            vendor = vendor_map.get(vendor_id, vendor_id)
                            gpus.append({
                                "name": f"{vendor} GPU ({entry})",
                                "vendor": vendor,
                                "vram_bytes": None,
                            })
            except Exception:
                pass

    elif system == "Darwin":
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType", "-json"],
                capture_output=True, text=True, timeout=10
            )
            import json
            data = json.loads(result.stdout)
            displays = data.get("SPDisplaysDataType", [])
            for display in displays:
                gpus.append({
                    "name": display.get("sppci_model", "Unknown GPU"),
                    "vendor": display.get("sppci_vendor", "Unknown"),
                    "vram_bytes": None,
                })
        except Exception:
            pass

    if not gpus:
        gpus.append({"name": "Integrated Graphics", "vendor": "Unknown", "vram_bytes": None})

    return gpus


def _get_storage_devices() -> List[Dict[str, Any]]:
    """Get storage device information."""
    devices = []
    seen = set()

    try:
        for part in psutil.disk_partitions(all=False):
            base = re.sub(r'\d+$', '', part.device)
            if base in seen:
                continue
            seen.add(base)

            try:
                usage = psutil.disk_usage(part.mountpoint)
                size_bytes = usage.total
            except Exception:
                size_bytes = 0

            import os
            is_removable = False
            dev_name = os.path.basename(base)
            removable_path = f"/sys/block/{dev_name}/removable"
            if os.path.exists(removable_path):
                try:
                    is_removable = open(removable_path).read().strip() == "1"
                except Exception:
                    pass

            devices.append({
                "name": os.path.basename(base),
                "path": base,
                "size_bytes": size_bytes,
                "size_human": _human_size(size_bytes),
                "filesystem": part.fstype,
                "mount_point": part.mountpoint,
                "is_removable": is_removable,
            })
    except Exception as e:
        logger.error(f"Storage scan error: {e}")

    return devices


def _get_system_info() -> Dict[str, Any]:
    """Get system/machine information."""
    system = platform.system()
    manufacturer = "Unknown"
    model = "Unknown"
    bios_version = None
    serial = None

    if system == "Linux":
        try:
            import os
            vendor_path = "/sys/devices/virtual/dmi/id/sys_vendor"
            product_path = "/sys/devices/virtual/dmi/id/product_name"
            bios_path = "/sys/devices/virtual/dmi/id/bios_version"
            serial_path = "/sys/devices/virtual/dmi/id/product_serial"

            if os.path.exists(vendor_path):
                manufacturer = open(vendor_path).read().strip()
            if os.path.exists(product_path):
                model = open(product_path).read().strip()
            if os.path.exists(bios_path):
                bios_version = open(bios_path).read().strip()
            if os.path.exists(serial_path):
                serial = open(serial_path).read().strip()
                if serial in ("", "To be filled by O.E.M.", "Default string"):
                    serial = None
        except Exception:
            pass

    elif system == "Darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "hw.model"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                model = result.stdout.strip()
                manufacturer = "Apple"
        except Exception:
            pass

    elif system == "Windows":
        try:
            result = subprocess.run(
                ["wmic", "computersystem", "get", "manufacturer,model", "/value"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if "Manufacturer=" in line:
                    manufacturer = line.split("=")[1].strip()
                elif "Model=" in line:
                    model = line.split("=")[1].strip()
        except Exception:
            pass

    return {
        "manufacturer": manufacturer,
        "model": model,
        "bios_version": bios_version,
        "serial": serial,
    }


def _check_oclp_compatibility(model: str, manufacturer: str) -> bool:
    """Check if the system might be OCLP-compatible."""
    oclp_models = [
        "iMac", "MacBook", "MacPro", "Mac mini", "MacBook Pro", "MacBook Air",
        "iMac Pro",
    ]
    if manufacturer == "Apple":
        for m in oclp_models:
            if m in model:
                return True
    return False


def _get_recommended_os(manufacturer: str, model: str, architecture: str) -> List[str]:
    """Get recommended OS options for this hardware."""
    recommended = ["Linux (Ubuntu 22.04 LTS)"]

    if manufacturer == "Apple":
        recommended = ["macOS (Latest)", "macOS (OCLP Patched)", "Linux (Ubuntu)"]
    elif architecture in ("x86_64", "AMD64"):
        recommended = [
            "Windows 11",
            "Windows 10",
            "Linux (Ubuntu 22.04 LTS)",
            "Linux (Fedora 39)",
        ]
    elif "arm" in architecture.lower() or "aarch64" in architecture.lower():
        recommended = [
            "Linux (Ubuntu 22.04 ARM)",
            "Linux (Raspberry Pi OS)",
        ]

    return recommended


def get_hardware_profile() -> Dict[str, Any]:
    """
    Get complete hardware profile of the current system.
    Returns real hardware data.
    """
    system_info = _get_system_info()
    cpu = _get_cpu_info()
    memory = _get_memory_info()
    gpus = _get_gpu_info()
    storage = _get_storage_devices()

    arch = platform.machine()
    os_name = platform.system()
    os_version = platform.version()

    manufacturer = system_info["manufacturer"]
    model = system_info["model"]

    return {
        "system_name": f"{manufacturer} {model}".strip(),
        "manufacturer": manufacturer,
        "model": model,
        "platform": os_name.lower(),
        "platform_version": platform.release(),
        "architecture": arch,
        "cpu": cpu,
        "memory": memory,
        "gpus": gpus,
        "storage": storage,
        "bios_version": system_info.get("bios_version"),
        "serial_number": system_info.get("serial"),
        "detection_confidence": "high",
        "oclp_compatible": _check_oclp_compatibility(model, manufacturer),
        "recommended_os": _get_recommended_os(manufacturer, model, arch),
    }
