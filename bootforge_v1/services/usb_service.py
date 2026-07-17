from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import usb_creator

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class UsbDevice:
    path: str
    label: str
    total_bytes: int
    free_bytes: int


class UsbService:
    """Read-only device discovery and guarded calls into the legacy engine."""

    def list_devices(self) -> list[UsbDevice]:
        raw_devices: list[dict[str, Any]] = usb_creator.get_removable_drives()
        devices: list[UsbDevice] = []
        for raw in raw_devices:
            devices.append(
                UsbDevice(
                    path=str(raw.get("path") or raw.get("device") or raw.get("drive") or ""),
                    label=str(raw.get("label") or raw.get("name") or "Removable device"),
                    total_bytes=int(raw.get("total_bytes") or raw.get("size") or 0),
                    free_bytes=int(raw.get("free_bytes") or raw.get("free") or 0),
                )
            )
        return devices

    def verify_secure_registry(self) -> bool:
        registry = usb_creator.load_tool_registry()
        return bool(registry and registry.get("tools") is not None)

    def dry_run_status(self) -> dict[str, object]:
        devices = self.list_devices()
        return {
            "secure_registry": self.verify_secure_registry(),
            "device_count": len(devices),
            "devices": devices,
            "destructive_actions_enabled": False,
        }
