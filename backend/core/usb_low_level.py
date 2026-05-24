"""
BootForge-style low-level USB detection.

This module enumerates raw USB devices and classifies them using the same
vendor/platform/mode concepts that appear in the Bootforge-usb repository.
It is intentionally read-only and separate from storage-media detection.
"""

from __future__ import annotations

import json
import logging
import platform
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

VENDOR_NAME_MAP = {
    0x05AC: "Apple",
    0x18D1: "Google",
    0x04E8: "Samsung",
    0x0FCE: "Sony",
    0x2A70: "OnePlus",
    0x12D1: "Huawei",
    0x22D9: "OPPO",
    0x2717: "Xiaomi",
    0x0BDA: "Realtek",
    0x0781: "SanDisk",
    0x046D: "Logitech",
}


def _timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _run_command(command: List[str], timeout: int = 15) -> Tuple[int, str, str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as exc:
        logger.debug("USB command failed %s: %s", command, exc)
        return -1, "", str(exc)


def _parse_hexish(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value

    text = str(value).strip()
    match = re.search(r"0x([0-9a-fA-F]{1,8})", text)
    if match:
        return int(match.group(1), 16)

    text = text.lower().replace("0x", "")
    if re.fullmatch(r"[0-9a-f]{1,8}", text):
        return int(text, 16)
    return None


def _parse_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else None


def _parse_current_ma(value: Any) -> Optional[int]:
    if value is None:
        return None
    match = re.search(r"(\d+)", str(value))
    return int(match.group(1)) if match else None


def _classify_vendor_name(vendor_id: Optional[int]) -> Optional[str]:
    if vendor_id is None:
        return None
    return VENDOR_NAME_MAP.get(vendor_id)


def _classify_platform(vendor_id: Optional[int]) -> str:
    if vendor_id == 0x05AC:
        return "apple"
    if vendor_id in {0x18D1, 0x04E8, 0x0FCE, 0x2A70, 0x12D1, 0x22D9, 0x2717}:
        return "android"
    if vendor_id in {0x0781, 0x0BDA, 0x046D}:
        return "generic-usb"
    return "unknown"


def _classify_transport(
    usb_version: Optional[str] = None,
    speed: Optional[str] = None,
) -> str:
    normalized_speed = (speed or "").lower()
    if "20 gb" in normalized_speed or "10 gb" in normalized_speed or "5 gb" in normalized_speed:
        return "usb3"
    if "480 mb" in normalized_speed:
        return "usb2"
    if "12 mb" in normalized_speed or "1.5 mb" in normalized_speed:
        return "usb1"
    speed_match = re.search(r"(\d+(?:\.\d+)?)", normalized_speed)
    if speed_match:
        try:
            speed_value = float(speed_match.group(1))
        except ValueError:
            speed_value = 0.0
        if speed_value >= 5000:
            return "usb3"
        if speed_value >= 480:
            return "usb2"
        if speed_value > 0:
            return "usb1"

    normalized_version = (usb_version or "").strip().lower()
    version_match = re.search(r"(\d+(?:\.\d+)?)", normalized_version)
    if version_match:
        try:
            version = float(version_match.group(1))
        except ValueError:
            version = 0.0
        if version >= 3.0:
            return "usb3"
        if version >= 2.0:
            return "usb2"
        if version > 0:
            return "usb1"

    return "unknown"


def _classify_mode(vendor_id: Optional[int], product_id: Optional[int]) -> str:
    if vendor_id is None or product_id is None:
        return "unknown"

    if (vendor_id, product_id) == (0x05AC, 0x12A8):
        return "normal"
    if (vendor_id, product_id) == (0x05AC, 0x1281):
        return "recovery"
    if (vendor_id, product_id) == (0x05AC, 0x1227):
        return "dfu"
    if (vendor_id, product_id) == (0x18D1, 0x4EE7):
        return "fastboot"
    if (vendor_id, product_id) == (0x18D1, 0x4EE1):
        return "adb"
    if (vendor_id, product_id) == (0x04E8, 0x6860):
        return "adb"
    if (vendor_id, product_id) == (0x04E8, 0x685D):
        return "bootloader"
    if vendor_id == 0x0781:
        return "mass_storage"
    return "unknown"


def _recommended_workflow(platform_name: str, mode: str) -> str:
    if platform_name == "apple" and mode == "dfu":
        return "apple_restore"
    if platform_name == "apple" and mode == "recovery":
        return "apple_recovery"
    if platform_name == "android" and mode in {"fastboot", "bootloader"}:
        return "android_boot_chain"
    if platform_name == "android" and mode == "adb":
        return "android_debug"
    if mode == "mass_storage":
        return "usb_media_analysis"
    return "descriptor_inspection"


def _make_device_record(
    *,
    name: str,
    vendor_id: Optional[int],
    product_id: Optional[int],
    manufacturer: Optional[str],
    product_name: Optional[str],
    serial_number: Optional[str],
    usb_version: Optional[str],
    speed: Optional[str],
    platform_path: Optional[str],
    raw_source: str,
    bus_number: Optional[int] = None,
    device_address: Optional[int] = None,
    location_id: Optional[str] = None,
    current_required_ma: Optional[int] = None,
    current_available_ma: Optional[int] = None,
    class_code: Optional[int] = None,
    subclass_code: Optional[int] = None,
    protocol_code: Optional[int] = None,
) -> Dict[str, Any]:
    vendor_name = manufacturer or _classify_vendor_name(vendor_id)
    platform_name = _classify_platform(vendor_id)
    transport = _classify_transport(usb_version=usb_version, speed=speed)
    mode = _classify_mode(vendor_id, product_id)

    stable_id_parts = [
        serial_number,
        location_id,
        platform_path,
        f"{bus_number}:{device_address}:{vendor_id}:{product_id}",
    ]
    stable_id = next((value for value in stable_id_parts if value), name)

    return {
        "id": stable_id,
        "name": name,
        "vendor_id": vendor_id,
        "product_id": product_id,
        "vendor_name": vendor_name,
        "manufacturer": manufacturer,
        "product_name": product_name or name,
        "serial_number": serial_number,
        "platform": platform_name,
        "transport": transport,
        "mode": mode,
        "recommended_workflow": _recommended_workflow(platform_name, mode),
        "usb_version": usb_version,
        "speed": speed,
        "platform_path": platform_path,
        "bus_number": bus_number,
        "device_address": device_address,
        "location_id": location_id,
        "current_required_ma": current_required_ma,
        "current_available_ma": current_available_ma,
        "class_code": class_code,
        "subclass_code": subclass_code,
        "protocol_code": protocol_code,
        "raw_source": raw_source,
    }


def _extract_macos_usb_devices(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    devices: List[Dict[str, Any]] = []

    def visit(node: Dict[str, Any]) -> None:
        vendor_id = _parse_hexish(node.get("vendor_id"))
        product_id = _parse_hexish(node.get("product_id"))
        if vendor_id is not None or product_id is not None:
            name = node.get("_name") or node.get("product_name") or "USB Device"
            devices.append(
                _make_device_record(
                    name=name,
                    vendor_id=vendor_id,
                    product_id=product_id,
                    manufacturer=node.get("manufacturer"),
                    product_name=node.get("_name"),
                    serial_number=node.get("serial_num"),
                    usb_version=node.get("version"),
                    speed=node.get("speed"),
                    platform_path=node.get("bsd_name"),
                    location_id=node.get("location_id"),
                    current_required_ma=_parse_current_ma(node.get("extra_operating_current")),
                    current_available_ma=_parse_current_ma(node.get("current_available")),
                    raw_source="system_profiler",
                )
            )

        for child in node.get("_items", []) or []:
            if isinstance(child, dict):
                visit(child)

    for root in payload.get("SPUSBDataType", []) or []:
        if isinstance(root, dict):
            visit(root)

    return devices


def _scan_macos_low_level() -> Tuple[List[Dict[str, Any]], str]:
    returncode, stdout, _stderr = _run_command(["system_profiler", "SPUSBDataType", "-json"], timeout=25)
    if returncode != 0 or not stdout.strip():
        return [], "system_profiler"

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse system_profiler USB output: %s", exc)
        return [], "system_profiler"

    return _extract_macos_usb_devices(payload), "system_profiler"


def _read_sysfs_text(path: Path) -> Optional[str]:
    try:
        if path.exists():
            return path.read_text().strip() or None
    except Exception:
        return None
    return None


def _build_linux_sysfs_index() -> Dict[Tuple[int, int, int, int], Dict[str, Any]]:
    index: Dict[Tuple[int, int, int, int], Dict[str, Any]] = {}
    root = Path("/sys/bus/usb/devices")
    if not root.exists():
        return index

    for entry in root.iterdir():
        if ":" in entry.name:
            continue

        vendor_id = _parse_hexish(_read_sysfs_text(entry / "idVendor"))
        product_id = _parse_hexish(_read_sysfs_text(entry / "idProduct"))
        bus_number = _parse_int(_read_sysfs_text(entry / "busnum"))
        device_address = _parse_int(_read_sysfs_text(entry / "devnum"))
        if None in {vendor_id, product_id, bus_number, device_address}:
            continue

        key = (bus_number, device_address, vendor_id, product_id)
        index[key] = {
            "manufacturer": _read_sysfs_text(entry / "manufacturer"),
            "product_name": _read_sysfs_text(entry / "product"),
            "serial_number": _read_sysfs_text(entry / "serial"),
            "usb_version": _read_sysfs_text(entry / "version"),
            "speed": _read_sysfs_text(entry / "speed"),
            "class_code": _parse_hexish(_read_sysfs_text(entry / "bDeviceClass")),
            "subclass_code": _parse_hexish(_read_sysfs_text(entry / "bDeviceSubClass")),
            "protocol_code": _parse_hexish(_read_sysfs_text(entry / "bDeviceProtocol")),
            "platform_path": f"/dev/bus/usb/{bus_number:03d}/{device_address:03d}",
        }

    return index


def _parse_linux_lsusb_line(line: str) -> Optional[Dict[str, Any]]:
    match = re.match(
        r"^Bus\s+(\d+)\s+Device\s+(\d+):\s+ID\s+([0-9a-fA-F]{4}):([0-9a-fA-F]{4})\s*(.*)$",
        line.strip(),
    )
    if not match:
        return None

    return {
        "bus_number": int(match.group(1)),
        "device_address": int(match.group(2)),
        "vendor_id": int(match.group(3), 16),
        "product_id": int(match.group(4), 16),
        "description": match.group(5).strip() or None,
    }


def _scan_linux_low_level() -> Tuple[List[Dict[str, Any]], str]:
    sysfs_index = _build_linux_sysfs_index()
    returncode, stdout, _stderr = _run_command(["lsusb"], timeout=10)
    devices: List[Dict[str, Any]] = []

    if returncode == 0 and stdout.strip():
        for line in stdout.splitlines():
            parsed = _parse_linux_lsusb_line(line)
            if not parsed:
                continue

            key = (
                parsed["bus_number"],
                parsed["device_address"],
                parsed["vendor_id"],
                parsed["product_id"],
            )
            meta = sysfs_index.get(key, {})
            name = meta.get("product_name") or parsed.get("description") or "USB Device"
            devices.append(
                _make_device_record(
                    name=name,
                    vendor_id=parsed["vendor_id"],
                    product_id=parsed["product_id"],
                    manufacturer=meta.get("manufacturer"),
                    product_name=meta.get("product_name") or parsed.get("description"),
                    serial_number=meta.get("serial_number"),
                    usb_version=meta.get("usb_version"),
                    speed=meta.get("speed"),
                    platform_path=meta.get("platform_path"),
                    raw_source="lsusb",
                    bus_number=parsed["bus_number"],
                    device_address=parsed["device_address"],
                    class_code=meta.get("class_code"),
                    subclass_code=meta.get("subclass_code"),
                    protocol_code=meta.get("protocol_code"),
                )
            )
        return devices, "lsusb"

    for (bus_number, device_address, vendor_id, product_id), meta in sorted(sysfs_index.items()):
        name = meta.get("product_name") or meta.get("manufacturer") or "USB Device"
        devices.append(
            _make_device_record(
                name=name,
                vendor_id=vendor_id,
                product_id=product_id,
                manufacturer=meta.get("manufacturer"),
                product_name=meta.get("product_name"),
                serial_number=meta.get("serial_number"),
                usb_version=meta.get("usb_version"),
                speed=meta.get("speed"),
                platform_path=meta.get("platform_path"),
                raw_source="sysfs",
                bus_number=bus_number,
                device_address=device_address,
                class_code=meta.get("class_code"),
                subclass_code=meta.get("subclass_code"),
                protocol_code=meta.get("protocol_code"),
            )
        )
    return devices, "sysfs"


def _scan_windows_low_level() -> Tuple[List[Dict[str, Any]], str]:
    ps_script = r"""
    Get-PnpDevice -PresentOnly |
    Where-Object { $_.InstanceId -match '^USB' -or $_.InstanceId -match 'VID_[0-9A-Fa-f]{4}' } |
    ForEach-Object {
        $instance = $_.InstanceId
        $vid = if ($instance -match 'VID_([0-9A-Fa-f]{4})') { $matches[1] } else { $null }
        $pid = if ($instance -match 'PID_([0-9A-Fa-f]{4})') { $matches[1] } else { $null }
        [PSCustomObject]@{
            InstanceId = $instance
            FriendlyName = $_.FriendlyName
            Manufacturer = $_.Manufacturer
            Class = $_.Class
            Status = $_.Status
            VendorId = $vid
            ProductId = $pid
        }
    } | ConvertTo-Json -Depth 4
    """
    returncode, stdout, _stderr = _run_command(["powershell", "-Command", ps_script], timeout=20)
    if returncode != 0 or not stdout.strip():
        return [], "powershell"

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse PowerShell USB output: %s", exc)
        return [], "powershell"

    if isinstance(payload, dict):
        payload = [payload]

    devices: List[Dict[str, Any]] = []
    for item in payload:
        vendor_id = _parse_hexish(item.get("VendorId"))
        product_id = _parse_hexish(item.get("ProductId"))
        name = item.get("FriendlyName") or item.get("Manufacturer") or "USB Device"
        devices.append(
            _make_device_record(
                name=name,
                vendor_id=vendor_id,
                product_id=product_id,
                manufacturer=item.get("Manufacturer"),
                product_name=item.get("FriendlyName"),
                serial_number=None,
                usb_version=None,
                speed=None,
                platform_path=item.get("InstanceId"),
                raw_source="powershell",
            )
        )
    return devices, "powershell"


def scan_low_level_usb_devices() -> Dict[str, Any]:
    start_time = time.time()
    host_os = platform.system().lower()

    if host_os == "darwin":
        devices, source = _scan_macos_low_level()
    elif host_os == "linux":
        devices, source = _scan_linux_low_level()
    elif host_os == "windows":
        devices, source = _scan_windows_low_level()
    else:
        devices, source = [], "unsupported"

    elapsed_ms = (time.time() - start_time) * 1000

    return {
        "devices": devices,
        "total": len(devices),
        "scan_time_ms": round(elapsed_ms, 2),
        "host_os": host_os,
        "timestamp": _timestamp(),
        "detection_mode": "low_level_usb",
        "source": source,
    }
