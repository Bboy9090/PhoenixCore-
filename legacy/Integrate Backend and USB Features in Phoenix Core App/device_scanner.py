"""
Phoenix Core - Real USB Device Scanner
Cross-platform USB/removable drive detection using psutil and /sys filesystem
"""
import os
import re
import time
import platform
import subprocess
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import psutil

logger = logging.getLogger(__name__)


def _human_size(size_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def _is_removable_linux(device_name: str) -> bool:
    """Check if a block device is removable on Linux."""
    removable_path = Path(f"/sys/block/{device_name}/removable")
    if removable_path.exists():
        try:
            return removable_path.read_text().strip() == "1"
        except Exception:
            pass
    return False


def _get_device_vendor_model_linux(device_name: str) -> tuple:
    """Get vendor and model for a Linux block device."""
    vendor = ""
    model = ""
    try:
        vendor_path = Path(f"/sys/block/{device_name}/device/vendor")
        if vendor_path.exists():
            vendor = vendor_path.read_text().strip()
    except Exception:
        pass
    try:
        model_path = Path(f"/sys/block/{device_name}/device/model")
        if model_path.exists():
            model = model_path.read_text().strip()
    except Exception:
        pass
    return vendor, model


def _get_device_serial_linux(device_name: str) -> Optional[str]:
    """Get serial number for a Linux block device."""
    try:
        serial_path = Path(f"/sys/block/{device_name}/device/serial")
        if serial_path.exists():
            return serial_path.read_text().strip()
    except Exception:
        pass
    # Try udevadm
    try:
        result = subprocess.run(
            ["udevadm", "info", "--query=property", f"--name=/dev/{device_name}"],
            capture_output=True, text=True, timeout=3
        )
        for line in result.stdout.splitlines():
            if line.startswith("ID_SERIAL="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None


def _get_partitions_linux(device_name: str) -> List[Dict[str, Any]]:
    """Get partition info for a Linux block device."""
    partitions = []
    try:
        block_path = Path(f"/sys/block/{device_name}")
        for entry in sorted(block_path.iterdir()):
            if entry.name.startswith(device_name) and entry.is_dir():
                part_name = entry.name
                size_bytes = 0
                size_file = entry / "size"
                if size_file.exists():
                    sectors = int(size_file.read_text().strip())
                    size_bytes = sectors * 512

                # Get mount info
                mount_points = []
                filesystem = None
                for part in psutil.disk_partitions(all=True):
                    if part.device == f"/dev/{part_name}":
                        mount_points.append(part.mountpoint)
                        filesystem = part.fstype

                partitions.append({
                    "id": part_name,
                    "label": None,
                    "filesystem": filesystem,
                    "size_bytes": size_bytes,
                    "size_human": _human_size(size_bytes),
                    "mount_points": mount_points,
                })
    except Exception as e:
        logger.debug(f"Error reading partitions for {device_name}: {e}")
    return partitions


def _assess_risk(device: Dict[str, Any]) -> str:
    """Assess risk level for writing to a device."""
    if device.get("is_system_disk"):
        return "critical"
    if not device.get("removable"):
        return "high"
    size_gb = device.get("size_gb", 0)
    if size_gb > 2000:  # > 2TB
        return "high"
    if size_gb > 500:
        return "medium"
    return "low"


def scan_usb_devices() -> Dict[str, Any]:
    """
    Scan for all USB/removable storage devices.
    Returns real device information from the OS.
    """
    start_time = time.time()
    devices = []
    host_os = platform.system().lower()

    if host_os == "linux":
        devices = _scan_linux()
    elif host_os == "darwin":
        devices = _scan_macos()
    elif host_os == "windows":
        devices = _scan_windows()
    else:
        devices = _scan_generic()

    elapsed_ms = (time.time() - start_time) * 1000

    return {
        "devices": devices,
        "total": len(devices),
        "scan_time_ms": round(elapsed_ms, 2),
        "host_os": host_os,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def _scan_linux() -> List[Dict[str, Any]]:
    """Scan USB devices on Linux using /sys/block."""
    devices = []
    block_path = Path("/sys/block")

    if not block_path.exists():
        return _scan_generic()

    # Get disk partitions for mount info
    disk_partitions = {}
    for part in psutil.disk_partitions(all=True):
        disk_partitions[part.device] = part

    for entry in sorted(block_path.iterdir()):
        name = entry.name
        # Skip loop, ram, zram devices
        if name.startswith(("loop", "ram", "zram", "dm-", "md")):
            continue

        # Check if removable
        is_removable = _is_removable_linux(name)

        # Get size
        size_bytes = 0
        size_file = entry / "size"
        if size_file.exists():
            try:
                sectors = int(size_file.read_text().strip())
                size_bytes = sectors * 512
            except Exception:
                pass

        if size_bytes == 0:
            continue

        # Check if system disk
        is_system = False
        try:
            root_part = psutil.disk_partitions()
            for p in root_part:
                if p.mountpoint == "/" and name in p.device:
                    is_system = True
                    break
        except Exception:
            pass

        vendor, model = _get_device_vendor_model_linux(name)
        serial = _get_device_serial_linux(name)
        partitions = _get_partitions_linux(name)

        # Get filesystem and mount from partitions
        filesystem = None
        mount_point = None
        if partitions:
            filesystem = partitions[0].get("filesystem")
            mounts = partitions[0].get("mount_points", [])
            mount_point = mounts[0] if mounts else None

        # Also check direct device mount
        dev_path = f"/dev/{name}"
        if dev_path in disk_partitions:
            part = disk_partitions[dev_path]
            filesystem = filesystem or part.fstype
            mount_point = mount_point or part.mountpoint

        size_gb = size_bytes / (1024 ** 3)

        device_info = {
            "id": name,
            "path": f"/dev/{name}",
            "name": name,
            "friendly_name": f"{vendor} {model}".strip() or name,
            "size_bytes": size_bytes,
            "size_human": _human_size(size_bytes),
            "size_gb": round(size_gb, 2),
            "removable": is_removable,
            "is_system_disk": is_system,
            "vendor": vendor or None,
            "model": model or None,
            "serial": serial,
            "filesystem": filesystem,
            "mount_point": mount_point,
            "partitions": partitions,
            "health_status": "healthy",
            "write_speed_mbps": None,
        }
        device_info["risk_level"] = _assess_risk(device_info)
        devices.append(device_info)

    return devices


def _scan_macos() -> List[Dict[str, Any]]:
    """Scan USB devices on macOS using diskutil."""
    devices = []
    try:
        result = subprocess.run(
            ["diskutil", "list", "-plist"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return _scan_generic()

        import plistlib
        plist = plistlib.loads(result.stdout.encode())
        all_disks = plist.get("AllDisksAndPartitions", [])

        for disk in all_disks:
            disk_id = disk.get("DeviceIdentifier", "")
            size_bytes = disk.get("Size", 0)
            if size_bytes == 0:
                continue

            # Get detailed info
            info_result = subprocess.run(
                ["diskutil", "info", "-plist", disk_id],
                capture_output=True, text=True, timeout=5
            )
            info = {}
            if info_result.returncode == 0:
                info = plistlib.loads(info_result.stdout.encode())

            is_removable = info.get("Removable", False) or info.get("RemovableMedia", False)
            is_system = info.get("SystemImage", False)
            vendor = info.get("VendorCharacteristics", {}).get("VendorName", "")
            model = info.get("MediaName", "")
            filesystem = info.get("FilesystemType", "")
            mount_point = info.get("MountPoint", "")

            size_gb = size_bytes / (1024 ** 3)
            device_info = {
                "id": disk_id,
                "path": f"/dev/{disk_id}",
                "name": disk_id,
                "friendly_name": model or disk_id,
                "size_bytes": size_bytes,
                "size_human": _human_size(size_bytes),
                "size_gb": round(size_gb, 2),
                "removable": is_removable,
                "is_system_disk": is_system,
                "vendor": vendor or None,
                "model": model or None,
                "serial": info.get("IORegistryEntryName"),
                "filesystem": filesystem or None,
                "mount_point": mount_point or None,
                "partitions": [],
                "health_status": "healthy",
                "write_speed_mbps": None,
            }
            device_info["risk_level"] = _assess_risk(device_info)
            devices.append(device_info)

    except Exception as e:
        logger.error(f"macOS device scan error: {e}")
        return _scan_generic()

    return devices


def _scan_windows() -> List[Dict[str, Any]]:
    """Scan USB devices on Windows using PowerShell."""
    devices = []
    try:
        ps_script = """
        Get-Disk | ForEach-Object {
            $disk = $_
            $partitions = Get-Partition -DiskNumber $disk.Number -ErrorAction SilentlyContinue
            [PSCustomObject]@{
                Number = $disk.Number
                FriendlyName = $disk.FriendlyName
                SerialNumber = $disk.SerialNumber
                Size = $disk.Size
                BusType = $disk.BusType
                IsSystem = $disk.IsSystem
                IsReadOnly = $disk.IsReadOnly
                HealthStatus = $disk.HealthStatus
                PartitionStyle = $disk.PartitionStyle
            }
        } | ConvertTo-Json
        """
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0 and result.stdout.strip():
            import json
            disk_list = json.loads(result.stdout)
            if isinstance(disk_list, dict):
                disk_list = [disk_list]

            for disk in disk_list:
                size_bytes = disk.get("Size", 0)
                if size_bytes == 0:
                    continue
                is_removable = disk.get("BusType") in ["USB", "SD"]
                size_gb = size_bytes / (1024 ** 3)
                name = f"Disk{disk.get('Number', 0)}"
                device_info = {
                    "id": name,
                    "path": f"\\\\.\\PhysicalDrive{disk.get('Number', 0)}",
                    "name": name,
                    "friendly_name": disk.get("FriendlyName", name),
                    "size_bytes": size_bytes,
                    "size_human": _human_size(size_bytes),
                    "size_gb": round(size_gb, 2),
                    "removable": is_removable,
                    "is_system_disk": disk.get("IsSystem", False),
                    "vendor": None,
                    "model": disk.get("FriendlyName"),
                    "serial": disk.get("SerialNumber"),
                    "filesystem": None,
                    "mount_point": None,
                    "partitions": [],
                    "health_status": disk.get("HealthStatus", "unknown").lower(),
                    "write_speed_mbps": None,
                }
                device_info["risk_level"] = _assess_risk(device_info)
                devices.append(device_info)
    except Exception as e:
        logger.error(f"Windows device scan error: {e}")
        return _scan_generic()

    return devices


def _scan_generic() -> List[Dict[str, Any]]:
    """Generic fallback using psutil disk partitions."""
    devices = []
    seen = set()

    try:
        partitions = psutil.disk_partitions(all=False)
        for part in partitions:
            # Get base device (strip partition number)
            device = part.device
            base = re.sub(r'\d+$', '', device)
            if base in seen:
                continue
            seen.add(base)

            try:
                usage = psutil.disk_usage(part.mountpoint)
                size_bytes = usage.total
            except Exception:
                size_bytes = 0

            if size_bytes == 0:
                continue

            size_gb = size_bytes / (1024 ** 3)
            is_system = part.mountpoint in ("/", "C:\\", "/System/Volumes/Data")
            is_removable = part.opts and "removable" in part.opts.lower()

            device_info = {
                "id": Path(base).name,
                "path": base,
                "name": Path(base).name,
                "friendly_name": Path(base).name,
                "size_bytes": size_bytes,
                "size_human": _human_size(size_bytes),
                "size_gb": round(size_gb, 2),
                "removable": is_removable,
                "is_system_disk": is_system,
                "vendor": None,
                "model": None,
                "serial": None,
                "filesystem": part.fstype,
                "mount_point": part.mountpoint,
                "partitions": [{
                    "id": Path(device).name,
                    "label": None,
                    "filesystem": part.fstype,
                    "size_bytes": size_bytes,
                    "size_human": _human_size(size_bytes),
                    "mount_points": [part.mountpoint],
                }],
                "health_status": "healthy",
                "write_speed_mbps": None,
            }
            device_info["risk_level"] = _assess_risk(device_info)
            devices.append(device_info)
    except Exception as e:
        logger.error(f"Generic device scan error: {e}")

    return devices


def get_device_by_path(path: str) -> Optional[Dict[str, Any]]:
    """Get a specific device by its path."""
    result = scan_usb_devices()
    for device in result["devices"]:
        if device["path"] == path or device["id"] == path:
            return device
    return None
