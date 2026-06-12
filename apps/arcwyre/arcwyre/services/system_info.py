"""
System Information Service — Real metrics via psutil
NO MOCK DATA. Every value comes from the actual OS.
"""

import platform
import socket
import time
from typing import Any

import psutil


def get_hostname() -> str:
    """Return the real system hostname."""
    return socket.gethostname()


def get_os_info() -> dict[str, str]:
    """Return real OS identification."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor() or "Unknown",
        "python_version": platform.python_version(),
    }


def get_cpu_info() -> dict[str, Any]:
    """Return real CPU information and current usage."""
    freq = psutil.cpu_freq()
    per_core = psutil.cpu_percent(interval=0.5, percpu=True)
    return {
        "model": platform.processor() or "Unknown",
        "physical_cores": psutil.cpu_count(logical=False) or 0,
        "logical_cores": psutil.cpu_count(logical=True) or 0,
        "max_freq_mhz": freq.max if freq else 0.0,
        "current_freq_mhz": freq.current if freq else 0.0,
        "total_usage_percent": sum(per_core) / len(per_core) if per_core else 0.0,
        "per_core_percent": per_core,
    }


def get_memory_info() -> dict[str, Any]:
    """Return real memory (RAM) information."""
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total_bytes": vm.total,
        "available_bytes": vm.available,
        "used_bytes": vm.used,
        "usage_percent": vm.percent,
        "swap_total_bytes": swap.total,
        "swap_used_bytes": swap.used,
        "swap_percent": swap.percent,
    }


def get_disk_info() -> list[dict[str, Any]]:
    """Return real disk partition information."""
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "filesystem": part.fstype,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "usage_percent": usage.percent,
                "opts": part.opts,
            })
        except PermissionError:
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "filesystem": part.fstype,
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "usage_percent": 0.0,
                "opts": part.opts,
                "error": "Permission denied",
            })
    return disks


def get_network_interfaces() -> list[dict[str, Any]]:
    """Return real network interface information."""
    interfaces = []
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    io = psutil.net_io_counters(pernic=True)

    for name, addr_list in addrs.items():
        iface: dict[str, Any] = {
            "name": name,
            "ipv4": "",
            "ipv6": "",
            "mac": "",
            "is_up": False,
            "speed_mbps": 0,
            "bytes_sent": 0,
            "bytes_recv": 0,
        }

        for addr in addr_list:
            if addr.family == socket.AF_INET:
                iface["ipv4"] = addr.address
            elif addr.family == socket.AF_INET6:
                iface["ipv6"] = addr.address
            elif addr.family == psutil.AF_LINK:
                iface["mac"] = addr.address

        if name in stats:
            iface["is_up"] = stats[name].isup
            iface["speed_mbps"] = stats[name].speed

        if name in io:
            iface["bytes_sent"] = io[name].bytes_sent
            iface["bytes_recv"] = io[name].bytes_recv

        interfaces.append(iface)

    return interfaces


def get_uptime_seconds() -> int:
    """Return real system uptime in seconds."""
    return int(time.time() - psutil.boot_time())


def get_battery_info() -> dict[str, Any] | None:
    """Return real battery info, or None if no battery."""
    batt = psutil.sensors_battery()
    if batt is None:
        return None
    return {
        "percent": batt.percent,
        "power_plugged": batt.power_plugged,
        "seconds_left": batt.secsleft if batt.secsleft != psutil.POWER_TIME_UNLIMITED else -1,
    }


def get_temperature_info() -> dict[str, list[dict[str, Any]]]:
    """
    Return real temperature sensor data.
    On macOS this typically returns empty — that is real behavior, not mock.
    """
    try:
        temps = psutil.sensors_temperatures()
    except AttributeError:
        # macOS does not support sensors_temperatures
        return {}

    result: dict[str, list[dict[str, Any]]] = {}
    for sensor_name, entries in temps.items():
        result[sensor_name] = [
            {
                "label": e.label or "unnamed",
                "current_c": e.current,
                "high_c": e.high,
                "critical_c": e.critical,
            }
            for e in entries
        ]
    return result


def get_process_list(limit: int = 50) -> list[dict[str, Any]]:
    """Return top processes by CPU usage. Real data only."""
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
        try:
            info = p.info
            procs.append({
                "pid": info['pid'],
                "name": info['name'] or "unknown",
                "user": info['username'] or "unknown",
                "cpu_percent": info['cpu_percent'] or 0.0,
                "memory_percent": round(info['memory_percent'] or 0.0, 1),
                "status": info['status'] or "unknown",
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sort by CPU usage descending
    procs.sort(key=lambda x: x['cpu_percent'], reverse=True)
    return procs[:limit]


def format_bytes(n: int | float) -> str:
    """Format byte count to human-readable string."""
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if abs(n) < 1024.0:
            return f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} PB"


def format_uptime(seconds: int) -> str:
    """Format seconds to human-readable uptime."""
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}m")
    return " ".join(parts)
