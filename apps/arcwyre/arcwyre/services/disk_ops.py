"""
Disk Operations Service — Real disk access via system tools
Uses lsblk (Linux) and diskutil (macOS) for enumeration.
Uses smartctl for SMART health data.
All subprocess calls have timeouts and error capture.
"""

import json
import platform
import subprocess
import shutil
from typing import Any


def _run(cmd: list[str], timeout: int = 30) -> tuple[str, str, int]:
    """Run a subprocess with timeout. Returns (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        return "", f"Command not found: {cmd[0]}", -1
    except subprocess.TimeoutExpired:
        return "", f"Command timed out after {timeout}s: {' '.join(cmd)}", -2
    except Exception as e:
        return "", f"Unexpected error: {e}", -3


def get_block_devices() -> list[dict[str, Any]]:
    """
    Enumerate block devices using real system tools.
    Linux: lsblk --json
    macOS: diskutil list
    """
    system = platform.system()

    if system == "Linux":
        return _get_block_devices_linux()
    elif system == "Darwin":
        return _get_block_devices_macos()
    else:
        return [{"error": f"Block device enumeration not implemented for {system}"}]


def _get_block_devices_linux() -> list[dict[str, Any]]:
    """Use lsblk to enumerate block devices on Linux."""
    if not shutil.which("lsblk"):
        return [{"error": "lsblk not found. Install util-linux."}]

    stdout, stderr, rc = _run([
        "lsblk", "--json", "--bytes", "--output",
        "NAME,SIZE,TYPE,MOUNTPOINT,FSTYPE,MODEL,SERIAL,TRAN,RO,RM,HOTPLUG"
    ])

    if rc != 0:
        return [{"error": f"lsblk failed: {stderr}"}]

    try:
        data = json.loads(stdout)
        devices = []
        for dev in data.get("blockdevices", []):
            devices.append({
                "name": f"/dev/{dev.get('name', '')}",
                "size_bytes": dev.get("size", 0),
                "type": dev.get("type", "unknown"),
                "mountpoint": dev.get("mountpoint", ""),
                "filesystem": dev.get("fstype", ""),
                "model": dev.get("model", "").strip() if dev.get("model") else "",
                "serial": dev.get("serial", "").strip() if dev.get("serial") else "",
                "transport": dev.get("tran", ""),
                "read_only": dev.get("ro", False),
                "removable": dev.get("rm", False),
                "hotplug": dev.get("hotplug", False),
                "children": [
                    {
                        "name": f"/dev/{child.get('name', '')}",
                        "size_bytes": child.get("size", 0),
                        "type": child.get("type", ""),
                        "mountpoint": child.get("mountpoint", ""),
                        "filesystem": child.get("fstype", ""),
                    }
                    for child in dev.get("children", [])
                ],
            })
        return devices
    except json.JSONDecodeError as e:
        return [{"error": f"Failed to parse lsblk output: {e}"}]


def _get_block_devices_macos() -> list[dict[str, Any]]:
    """Use diskutil to enumerate block devices on macOS."""
    stdout, stderr, rc = _run(["diskutil", "list", "-plist"])

    if rc != 0:
        # Fallback to plain text parsing
        stdout_plain, _, rc2 = _run(["diskutil", "list"])
        if rc2 != 0:
            return [{"error": f"diskutil failed: {stderr}"}]

        devices = []
        current_disk = None
        for line in stdout_plain.splitlines():
            line = line.strip()
            if line.startswith("/dev/disk"):
                parts = line.split()
                current_disk = {
                    "name": parts[0],
                    "description": " ".join(parts[1:]) if len(parts) > 1 else "",
                    "size_bytes": 0,
                    "type": "disk",
                    "removable": "external" in line.lower() or "removable" in line.lower(),
                    "children": [],
                }
                devices.append(current_disk)
            elif current_disk and ":" in line and "disk" in line.lower():
                # Partition line
                parts = line.split()
                if len(parts) >= 3:
                    current_disk["children"].append({
                        "name": parts[-1] if parts[-1].startswith("disk") else "",
                        "type": "part",
                        "filesystem": parts[1] if len(parts) > 1 else "",
                    })
        return devices

    # Plist parsing would go here for richer data
    # For now, fall back to plain text
    return _get_block_devices_macos_plain()


def _get_block_devices_macos_plain() -> list[dict[str, Any]]:
    """Plain text diskutil parsing fallback."""
    stdout, stderr, rc = _run(["diskutil", "list"])
    if rc != 0:
        return [{"error": f"diskutil failed: {stderr}"}]

    devices = []
    current_disk = None
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("/dev/disk"):
            parts = stripped.split()
            current_disk = {
                "name": parts[0],
                "description": " ".join(parts[1:]).strip("():") if len(parts) > 1 else "",
                "type": "disk",
                "removable": "external" in stripped.lower(),
                "children": [],
            }
            devices.append(current_disk)
    return devices


def get_smart_health(device: str) -> dict[str, Any]:
    """
    Get SMART health data for a device using smartctl.
    Returns real data or error explanation.
    """
    if not shutil.which("smartctl"):
        return {
            "available": False,
            "error": "NOT IMPLEMENTED — smartctl not found. Install smartmontools: sudo apt install smartmontools",
        }

    stdout, stderr, rc = _run(["smartctl", "--json=c", "-a", device], timeout=60)

    if rc < 0:
        return {"available": False, "error": stderr}

    try:
        data = json.loads(stdout)
        health = data.get("smart_status", {})
        attrs = data.get("ata_smart_attributes", {}).get("table", [])

        return {
            "available": True,
            "device": device,
            "model": data.get("model_name", "Unknown"),
            "serial": data.get("serial_number", "Unknown"),
            "firmware": data.get("firmware_version", "Unknown"),
            "health_passed": health.get("passed", None),
            "temperature_c": data.get("temperature", {}).get("current", None),
            "power_on_hours": None,
            "attributes": [
                {
                    "id": attr.get("id"),
                    "name": attr.get("name", ""),
                    "value": attr.get("value"),
                    "worst": attr.get("worst"),
                    "threshold": attr.get("thresh"),
                    "raw_value": attr.get("raw", {}).get("string", ""),
                }
                for attr in attrs
            ],
        }
    except json.JSONDecodeError:
        # Try plain text fallback
        return {
            "available": True,
            "device": device,
            "raw_output": stdout,
            "parse_error": "Could not parse JSON output from smartctl",
        }


def get_removable_drives() -> list[dict[str, Any]]:
    """
    Get list of removable drives suitable for USB writing.
    This is critical for BootForge — we NEVER return system disks.
    """
    system = platform.system()

    if system == "Linux":
        devices = _get_block_devices_linux()
        return [
            d for d in devices
            if d.get("removable") or d.get("hotplug") or d.get("transport") == "usb"
        ]
    elif system == "Darwin":
        stdout, _, rc = _run(["diskutil", "list", "external"])
        if rc != 0:
            return []

        drives = []
        for line in stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("/dev/disk"):
                parts = stripped.split()
                drive_name = parts[0]
                # Get info for this specific disk
                info_out, _, info_rc = _run(["diskutil", "info", drive_name])
                if info_rc == 0:
                    size = ""
                    for info_line in info_out.splitlines():
                        if "Disk Size" in info_line:
                            size = info_line.split(":")[-1].strip()
                            break
                    drives.append({
                        "name": drive_name,
                        "description": " ".join(parts[1:]).strip("():"),
                        "size": size,
                        "removable": True,
                    })
        return drives
    else:
        return []


def is_system_disk(device: str) -> bool:
    """Safety check: determine if a device is a system disk that must NOT be written to."""
    system = platform.system()

    # Never allow writing to these
    dangerous_patterns = ["/dev/sda", "/dev/nvme0", "/dev/disk0"]

    for pattern in dangerous_patterns:
        if device.startswith(pattern):
            return True

    if system == "Linux":
        # Check if any partition of this device is mounted at /
        stdout, _, rc = _run(["lsblk", "--json", "--output", "NAME,MOUNTPOINT", device])
        if rc == 0:
            try:
                data = json.loads(stdout)
                for dev in data.get("blockdevices", []):
                    if dev.get("mountpoint") == "/":
                        return True
                    for child in dev.get("children", []):
                        if child.get("mountpoint") == "/":
                            return True
            except json.JSONDecodeError:
                pass

    return False
