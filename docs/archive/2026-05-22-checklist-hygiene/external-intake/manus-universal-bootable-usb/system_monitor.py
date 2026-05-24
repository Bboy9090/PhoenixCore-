"""
Phoenix Core - System Monitor
Real-time system metrics and USB activity monitoring
Integrated from PhoenixCore- backend for production-grade monitoring
"""
import time
import logging
from typing import Dict, List, Any
import psutil

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitor system metrics and USB activity."""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics_history: List[Dict[str, Any]] = []
        self.usb_activity: List[Dict[str, Any]] = []
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            
            metrics = {
                "timestamp": time.time(),
                "uptime_seconds": time.time() - self.start_time,
                "cpu_usage_percent": cpu_percent,
                "cpu_count": psutil.cpu_count(),
                "memory_usage_percent": memory.percent,
                "memory_total_gb": memory.total / (1024 ** 3),
                "memory_available_gb": memory.available / (1024 ** 3),
                "memory_used_gb": memory.used / (1024 ** 3),
                "disk_usage_percent": disk.percent,
                "disk_total_gb": disk.total / (1024 ** 3),
                "disk_available_gb": disk.free / (1024 ** 3),
                "disk_used_gb": disk.used / (1024 ** 3),
                "process_count": len(psutil.pids()),
                "temperature": _get_system_temperature(),
            }
            
            # Store in history (keep last 100 samples)
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > 100:
                self.metrics_history.pop(0)
            
            return metrics
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}
    
    def get_usb_activity(self) -> Dict[str, Any]:
        """Get USB device activity and statistics."""
        try:
            # Get network I/O stats (proxy for USB activity)
            net_io = psutil.net_io_counters()
            disk_io = psutil.disk_io_counters()
            
            activity = {
                "timestamp": time.time(),
                "network_bytes_sent": net_io.bytes_sent,
                "network_bytes_recv": net_io.bytes_recv,
                "disk_read_bytes": disk_io.read_bytes,
                "disk_write_bytes": disk_io.write_bytes,
                "disk_read_count": disk_io.read_count,
                "disk_write_count": disk_io.write_count,
            }
            
            # Store in history
            self.usb_activity.append(activity)
            if len(self.usb_activity) > 100:
                self.usb_activity.pop(0)
            
            return activity
        except Exception as e:
            logger.error(f"Failed to get USB activity: {e}")
            return {}
    
    def get_metrics_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get historical metrics data."""
        return self.metrics_history[-limit:]
    
    def get_usb_activity_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get historical USB activity data."""
        return self.usb_activity[-limit:]


def _get_system_temperature() -> Dict[str, Any]:
    """Get system temperature information."""
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return {}
        
        result = {}
        for name, entries in temps.items():
            for entry in entries:
                if entry.current:
                    result[name] = {
                        "current": entry.current,
                        "high": entry.high,
                        "critical": entry.critical,
                    }
        
        return result
    except Exception:
        return {}


def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics (module-level function)."""
    monitor = SystemMonitor()
    return monitor.get_system_metrics()


def get_usb_activity() -> Dict[str, Any]:
    """Get USB activity (module-level function)."""
    monitor = SystemMonitor()
    return monitor.get_usb_activity()
