"""
device_scanner.py
PhoenixCore / BootForge USB Creator
Cross-Platform Device Scanner

Read-only, non-destructive removable device detection for Windows, macOS, and Linux.
This module only reads device metadata. It never writes to, alters, or accesses any drive.
No destructive operations or raw-device APIs exist in this module.

Detection sources:
  Windows  — PowerShell Get-CimInstance Win32_DiskDrive
  macOS    — diskutil list -plist / diskutil info -plist
  Linux    — /sys/block sysfs + udevadm info
  Fallback — lsblk -J (Linux) or degraded result
"""

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCANNER_SCHEMA = "bootforge.device_scan.v2"
MIN_ELIGIBLE_TARGET_BYTES = 2 * 1024**3


def _utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _human_size(size_bytes):
    if size_bytes is None or size_bytes <= 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def _build_device_record(**kwargs):
    warnings = kwargs.get("warnings") or []
    block_reasons = kwargs.get("block_reasons") or []

    is_fixed = kwargs.get("is_fixed", False)
    is_system = kwargs.get("is_system", False)
    is_removable = kwargs.get("is_removable", False)
    serial = kwargs.get("serial")
    stable_id = kwargs.get("stable_id")
    size_bytes = kwargs.get("size_bytes", 0)

    confidence = "high"
    if not serial and not stable_id:
        confidence = "low"
        warnings.append(
            "No serial number or stable ID available; identity lock will be unreliable."
        )
    elif not serial:
        confidence = "medium"
        warnings.append("No serial number available; using stable ID only.")

    if is_system:
        block_reasons.append("Drive is a system/boot drive.")
    if is_fixed and not is_removable:
        block_reasons.append("Drive is fixed/internal, not removable.")
    if size_bytes <= 0:
        block_reasons.append("Drive reports zero or unknown size.")
    elif (is_removable or kwargs.get("is_external", False)) and (
        size_bytes < MIN_ELIGIBLE_TARGET_BYTES
    ):
        block_reasons.append("Drive capacity is below the minimum required 2.0 GB.")
    elif (is_removable or kwargs.get("is_external", False)) and size_bytes > (
        256 * 1024**3
    ):
        warnings.append(
            "Large-capacity external target detected; physical writing remains locked."
        )

    is_eligible = (
        is_removable and not is_system and not is_fixed and len(block_reasons) == 0
    )

    return {
        "drive_path": kwargs.get("drive_path"),
        "display_name": kwargs.get("display_name")
        or kwargs.get("drive_path")
        or "Unknown",
        "stable_id": stable_id,
        "serial": serial,
        "size_bytes": size_bytes,
        "size_gb": round(size_bytes / (1024**3), 2) if size_bytes > 0 else 0.0,
        "size_human": _human_size(size_bytes),
        "filesystem": kwargs.get("filesystem"),
        "volume_label": kwargs.get("volume_label"),
        "is_removable": is_removable,
        "is_external": kwargs.get("is_external", False),
        "is_fixed": is_fixed,
        "is_system": is_system,
        "bus_protocol": kwargs.get("bus_protocol"),
        "platform": kwargs.get("platform") or sys.platform,
        "detection_source": kwargs.get("detection_source") or "unknown",
        "confidence": confidence,
        "is_eligible": is_eligible,
        "warnings": warnings,
        "block_reasons": block_reasons,
    }


def _run_command(cmd, timeout=10):
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -2, "", f"Command timed out after {timeout}s: {' '.join(cmd)}"
    except Exception as e:
        return -3, "", str(e)


def _run_command_bytes(cmd, timeout=10):
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=False,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, b"", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -2, b"", f"Command timed out after {timeout}s: {' '.join(cmd)}"
    except Exception as e:
        return -3, b"", str(e)


# ---------------------------------------------------------------------------
# Windows scanner — PowerShell Get-CimInstance Win32_DiskDrive
# ---------------------------------------------------------------------------

WINDOWS_PS_SCRIPT = (
    "Get-CimInstance Win32_DiskDrive | "
    "Select-Object DeviceID, Model, SerialNumber, Size, MediaType, "
    "InterfaceType, Partitions, Status, Caption | ConvertTo-Json"
)


def parse_windows_scan_output(raw_json):
    devices = []
    if not raw_json or not raw_json.strip():
        return devices

    try:
        data = json.loads(raw_json)
    except (json.JSONDecodeError, ValueError):
        return devices

    if isinstance(data, dict):
        data = [data]

    for item in data:
        device_id = item.get("DeviceID") or ""
        size_bytes = int(item.get("Size") or 0)
        serial = (item.get("SerialNumber") or "").strip() or None
        model = (item.get("Model") or "").strip() or None
        interface = (item.get("InterfaceType") or "").strip()
        media_type = (item.get("MediaType") or "").strip().lower()

        is_removable = (
            interface in ("USB", "SD", "1394")
            or "removable" in media_type
            or "external" in media_type
        )
        is_fixed = not is_removable and (
            "fixed" in media_type or interface not in ("USB", "SD", "1394")
        )

        disk_number = device_id.replace("\\\\.\\PHYSICALDRIVE", "").replace(
            "\\\\.\\PhysicalDrive", ""
        )
        stable_id = f"win32_disk{disk_number}_{serial}" if serial else None

        devices.append(
            _build_device_record(
                drive_path=device_id,
                display_name=model or f"Disk {disk_number}",
                stable_id=stable_id,
                serial=serial,
                size_bytes=size_bytes,
                is_removable=is_removable,
                is_external=is_removable,
                is_fixed=is_fixed,
                is_system=False,
                bus_protocol=interface or None,
                platform="win32",
                detection_source="powershell_win32_diskdrive",
            )
        )

    return devices


def scan_windows():
    code, stdout, stderr = _run_command(
        ["powershell", "-NoProfile", "-Command", WINDOWS_PS_SCRIPT],
        timeout=15,
    )
    if code != 0:
        return [], [f"PowerShell scan failed (code {code}): {stderr}"]

    devices = parse_windows_scan_output(stdout)
    return devices, []


# ---------------------------------------------------------------------------
# macOS scanner — diskutil list/info -plist
# ---------------------------------------------------------------------------


def parse_macos_disk_list(plist_bytes):
    import plistlib

    try:
        data = plistlib.loads(plist_bytes)
    except Exception:
        return []
    return data.get("WholeDisks", [])


def parse_macos_disk_info(plist_bytes):
    import plistlib

    try:
        return plistlib.loads(plist_bytes)
    except Exception:
        return {}


def build_macos_device_from_info(disk_id, info):
    is_removable = info.get("Removable", False) or info.get("RemovableMedia", False)
    is_external = info.get("External", False)
    is_internal = info.get("Internal", False)
    is_system = info.get("SystemImage", False)
    size_bytes = info.get("TotalSize", 0) or info.get("Size", 0)
    media_name = info.get("MediaName") or ""
    volume_name = info.get("VolumeName") or ""
    filesystem = info.get("FilesystemType") or info.get("Content") or None
    bus_protocol = info.get("BusProtocol") or info.get("Protocol") or None
    serial = info.get("IORegistryEntryName") or None
    device_node = info.get("DeviceNode") or f"/dev/{disk_id}"

    display_name = media_name or volume_name or disk_id
    stable_id = f"darwin_{disk_id}_{serial}" if serial else None

    return _build_device_record(
        drive_path=device_node,
        display_name=display_name,
        stable_id=stable_id,
        serial=serial,
        size_bytes=size_bytes,
        filesystem=filesystem,
        volume_label=volume_name or None,
        is_removable=is_removable or is_external,
        is_external=is_external,
        is_fixed=is_internal and not is_removable and not is_external,
        is_system=is_system,
        bus_protocol=bus_protocol,
        platform="darwin",
        detection_source="diskutil_plist",
    )


def scan_macos():
    code, stdout_bytes, stderr = _run_command_bytes(
        ["diskutil", "list", "-plist", "external", "physical"],
        timeout=10,
    )
    if code != 0:
        code2, stdout_bytes2, stderr2 = _run_command_bytes(
            ["diskutil", "list", "-plist"],
            timeout=10,
        )
        if code2 != 0:
            return [], [f"diskutil list failed (code {code2}): {stderr2}"]
        stdout_bytes = stdout_bytes2

    disk_ids = parse_macos_disk_list(stdout_bytes)
    if not disk_ids:
        return [], []

    devices = []
    scan_warnings = []
    for disk_id in disk_ids:
        code, info_bytes, stderr = _run_command_bytes(
            ["diskutil", "info", "-plist", disk_id],
            timeout=5,
        )
        if code != 0:
            scan_warnings.append(f"diskutil info failed for {disk_id}: {stderr}")
            continue

        info = parse_macos_disk_info(info_bytes)
        if not info:
            scan_warnings.append(f"Failed to parse plist for {disk_id}")
            continue

        device = build_macos_device_from_info(disk_id, info)
        devices.append(device)

    return devices, scan_warnings


# ---------------------------------------------------------------------------
# Linux scanner — /sys/block + udevadm
# ---------------------------------------------------------------------------


def read_sysfs_file(path):
    try:
        p = Path(path)
        if p.exists():
            return p.read_text().strip()
    except Exception:
        pass
    return None


def parse_udevadm_output(raw_output):
    props = {}
    if not raw_output:
        return props
    for line in raw_output.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            props[key.strip()] = value.strip()
    return props


def scan_linux_sysblock():
    block_path = Path("/sys/block")
    if not block_path.exists():
        return [], ["No /sys/block found; using fallback."]

    devices = []
    scan_warnings = []

    try:
        entries = sorted(block_path.iterdir())
    except Exception as e:
        return [], [f"Failed to read /sys/block: {e}"]

    for entry in entries:
        name = entry.name
        if name.startswith(("loop", "ram", "zram", "dm-", "md", "sr")):
            continue

        removable_val = read_sysfs_file(f"/sys/block/{name}/removable")
        is_removable = removable_val == "1"

        size_str = read_sysfs_file(f"/sys/block/{name}/size")
        size_bytes = 0
        if size_str:
            try:
                size_bytes = int(size_str) * 512
            except ValueError:
                pass
        if size_bytes <= 0:
            continue

        vendor = read_sysfs_file(f"/sys/block/{name}/device/vendor") or ""
        model = read_sysfs_file(f"/sys/block/{name}/device/model") or ""

        serial = read_sysfs_file(f"/sys/block/{name}/device/serial")
        if not serial:
            code, stdout, _ = _run_command(
                ["udevadm", "info", "--query=property", f"--name=/dev/{name}"],
                timeout=3,
            )
            if code == 0:
                props = parse_udevadm_output(stdout)
                serial = props.get("ID_SERIAL") or props.get("ID_SERIAL_SHORT")

        is_system = False
        try:
            with open("/proc/mounts", "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == "/" and name in parts[0]:
                        is_system = True
                        break
        except Exception:
            pass

        display_name = f"{vendor} {model}".strip() or name
        stable_id = f"linux_{name}_{serial}" if serial else None

        devices.append(
            _build_device_record(
                drive_path=f"/dev/{name}",
                display_name=display_name,
                stable_id=stable_id,
                serial=serial,
                size_bytes=size_bytes,
                is_removable=is_removable,
                is_external=is_removable,
                is_fixed=not is_removable,
                is_system=is_system,
                bus_protocol=None,
                platform="linux",
                detection_source="sysblock_udevadm",
            )
        )

    return devices, scan_warnings


def scan_linux_lsblk_fallback():
    code, stdout, stderr = _run_command(
        ["lsblk", "-J", "-o", "NAME,SIZE,RM,LABEL,FSTYPE,MOUNTPOINT"], timeout=10
    )
    if code != 0:
        return [], [f"lsblk fallback failed (code {code}): {stderr}"]

    devices = []
    try:
        data = json.loads(stdout)
    except (json.JSONDecodeError, ValueError):
        return [], ["lsblk output is not valid JSON."]

    for blk in data.get("blockdevices", []):
        name = blk.get("name", "")
        if name.startswith(("loop", "ram", "zram")):
            continue

        rm = blk.get("rm")
        is_removable = rm in ("1", 1, True, "true")

        devices.append(
            _build_device_record(
                drive_path=f"/dev/{name}",
                display_name=name,
                stable_id=None,
                serial=None,
                size_bytes=0,
                filesystem=blk.get("fstype"),
                volume_label=blk.get("label"),
                is_removable=is_removable,
                is_external=is_removable,
                is_fixed=not is_removable,
                is_system=blk.get("mountpoint") == "/",
                platform="linux",
                detection_source="lsblk_fallback",
            )
        )

    return devices, []


def scan_linux():
    devices, warnings = scan_linux_sysblock()
    if not devices and not warnings:
        devices, warnings = scan_linux_lsblk_fallback()
    return devices, warnings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scan_devices(platform_override=None):
    plat = platform_override or sys.platform
    scan_id = f"scan_{str(uuid.uuid4())[:12]}"
    created_at = _utc_now()

    devices = []
    scan_warnings = []
    detection_source = "unknown"

    if plat == "win32":
        devices, scan_warnings = scan_windows()
        detection_source = "powershell_win32_diskdrive"
    elif plat == "darwin":
        devices, scan_warnings = scan_macos()
        detection_source = "diskutil_plist"
    elif plat.startswith("linux"):
        devices, scan_warnings = scan_linux()
        detection_source = "sysblock_udevadm"
    else:
        scan_warnings.append(f"Unsupported platform '{plat}'; no devices detected.")

    return {
        "schema": SCANNER_SCHEMA,
        "scan_id": scan_id,
        "created_at": created_at,
        "platform": plat,
        "detection_source": detection_source,
        "safe_mode": True,
        "destructive": False,
        "operation": "read_only_device_scan",
        "device_count": len(devices),
        "devices": devices,
        "scan_warnings": scan_warnings,
    }


def get_device_by_path(scan_result, drive_path):
    for device in scan_result.get("devices", []):
        if device.get("drive_path") == drive_path:
            return device
    return None


def get_eligible_devices(scan_result):
    return [d for d in scan_result.get("devices", []) if d.get("is_eligible")]
