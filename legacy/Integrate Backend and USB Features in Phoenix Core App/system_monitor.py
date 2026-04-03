"""
Phoenix Core - Real System Monitor
Live system metrics using psutil
"""
import time
import platform
import logging
from typing import List, Optional, Dict, Any
import psutil

logger = logging.getLogger(__name__)

_prev_net_io = None
_prev_disk_io = None
_prev_time = None


def _human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def get_system_metrics() -> Dict[str, Any]:
    """Get real-time system metrics."""
    global _prev_net_io, _prev_disk_io, _prev_time

    now = time.time()

    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.1)
    try:
        cpu_per_core = psutil.cpu_percent(percpu=True, interval=0)
    except Exception:
        cpu_per_core = [cpu_percent]

    # Memory
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # Disk usage (root/system drive)
    try:
        disk = psutil.disk_usage("/")
        disk_percent = disk.percent
    except Exception:
        disk_percent = 0.0

    # Disk I/O
    try:
        disk_io = psutil.disk_io_counters()
        disk_io_data = {
            "read_bytes": disk_io.read_bytes if disk_io else 0,
            "write_bytes": disk_io.write_bytes if disk_io else 0,
            "read_count": disk_io.read_count if disk_io else 0,
            "write_count": disk_io.write_count if disk_io else 0,
        }
    except Exception:
        disk_io_data = {"read_bytes": 0, "write_bytes": 0, "read_count": 0, "write_count": 0}

    # Network I/O
    try:
        net_io = psutil.net_io_counters()
        net_data = {
            "bytes_sent": net_io.bytes_sent if net_io else 0,
            "bytes_recv": net_io.bytes_recv if net_io else 0,
            "packets_sent": net_io.packets_sent if net_io else 0,
            "packets_recv": net_io.packets_recv if net_io else 0,
        }
    except Exception:
        net_data = {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0}

    # Temperature
    temperature = None
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for sensor_name, readings in temps.items():
                if readings:
                    temperature = readings[0].current
                    break
    except Exception:
        pass

    # Uptime
    try:
        boot_time = psutil.boot_time()
        uptime_seconds = now - boot_time
    except Exception:
        uptime_seconds = 0.0

    # Load average
    try:
        load_avg = list(psutil.getloadavg())
    except Exception:
        load_avg = [0.0, 0.0, 0.0]

    # Process count
    try:
        process_count = len(psutil.pids())
    except Exception:
        process_count = 0

    return {
        "cpu_percent": round(cpu_percent, 1),
        "cpu_per_core": [round(c, 1) for c in cpu_per_core],
        "memory_percent": round(mem.percent, 1),
        "memory_used_bytes": mem.used,
        "memory_total_bytes": mem.total,
        "swap_percent": round(swap.percent, 1),
        "disk_usage_percent": round(disk_percent, 1),
        "disk_io": disk_io_data,
        "network": net_data,
        "temperature": round(temperature, 1) if temperature else None,
        "uptime_seconds": round(uptime_seconds, 0),
        "load_average": [round(l, 2) for l in load_avg],
        "process_count": process_count,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def get_usb_activity() -> Dict[str, Any]:
    """Monitor USB device activity and changes."""
    from core.device_scanner import scan_usb_devices
    result = scan_usb_devices()
    return {
        "device_count": result["total"],
        "devices": result["devices"],
        "timestamp": result["timestamp"],
    }
