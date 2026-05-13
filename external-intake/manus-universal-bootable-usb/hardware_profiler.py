"""
Phoenix Core - Hardware Profiler
Comprehensive hardware detection and profiling for all platforms
Integrated from PhoenixCore- backend for production-grade hardware analysis
"""
import platform
import subprocess
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import psutil

logger = logging.getLogger(__name__)


@dataclass
class HardwareProfile:
    """Complete hardware profile information."""
    cpu_model: str
    cpu_cores: int
    cpu_threads: int
    cpu_frequency: float
    ram_total: int
    ram_available: int
    disk_total: int
    disk_available: int
    gpu_model: Optional[str]
    system: str
    release: str
    architecture: str
    hostname: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


def get_hardware_profile() -> HardwareProfile:
    """
    Get comprehensive hardware profile for the current system.
    Works across Linux, macOS, and Windows.
    """
    system = platform.system()
    
    # CPU information
    cpu_model = platform.processor() or "Unknown"
    cpu_count = psutil.cpu_count(logical=False) or 1
    cpu_threads = psutil.cpu_count(logical=True) or 1
    cpu_freq = psutil.cpu_freq()
    cpu_frequency = cpu_freq.current if cpu_freq else 0.0
    
    # RAM information
    ram = psutil.virtual_memory()
    ram_total = ram.total
    ram_available = ram.available
    
    # Disk information
    try:
        disk = psutil.disk_usage("/")
        disk_total = disk.total
        disk_available = disk.free
    except Exception:
        disk_total = 0
        disk_available = 0
    
    # GPU information (platform-specific)
    gpu_model = _detect_gpu(system)
    
    # System information
    release = platform.release()
    architecture = platform.machine()
    hostname = platform.node()
    
    return HardwareProfile(
        cpu_model=cpu_model,
        cpu_cores=cpu_count,
        cpu_threads=cpu_threads,
        cpu_frequency=cpu_frequency,
        ram_total=ram_total,
        ram_available=ram_available,
        disk_total=disk_total,
        disk_available=disk_available,
        gpu_model=gpu_model,
        system=system,
        release=release,
        architecture=architecture,
        hostname=hostname,
    )


def _detect_gpu(system: str) -> Optional[str]:
    """Detect GPU model for the current system."""
    try:
        if system == "Linux":
            # Try lspci for GPU detection
            try:
                result = subprocess.run(
                    ["lspci"],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    if "VGA" in line or "3D" in line:
                        # Extract GPU name
                        parts = line.split(":")
                        if len(parts) >= 3:
                            return parts[2].strip()
            except Exception:
                pass
            
            # Try nvidia-smi for NVIDIA GPUs
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                    capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip():
                    return result.stdout.strip().split("\n")[0]
            except Exception:
                pass
        
        elif system == "Darwin":  # macOS
            # Use system_profiler for GPU detection
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    if "Chipset Model:" in line:
                        return line.split(":", 1)[1].strip()
            except Exception:
                pass
        
        elif system == "Windows":
            # Use wmic for GPU detection
            try:
                result = subprocess.run(
                    ["wmic", "path", "win32_videocontroller", "get", "name"],
                    capture_output=True, text=True, timeout=5
                )
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    return lines[1].strip()
            except Exception:
                pass
    
    except Exception as e:
        logger.warning(f"GPU detection failed: {e}")
    
    return None


def get_system_capabilities() -> Dict[str, Any]:
    """Get system capabilities and features."""
    system = platform.system()
    
    capabilities = {
        "usb_detection": True,
        "usb_creation": True,
        "hardware_profiling": True,
        "system_monitoring": True,
        "bootcamp_drivers": system == "Darwin",
        "oclp_support": system == "Darwin",
        "multiboot": True,
        "recovery_mode": True,
        "dry_run": True,
    }
    
    return capabilities


def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        
        return {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_gb": memory.available / (1024 ** 3),
            "disk_usage_percent": disk.percent,
            "disk_available_gb": disk.free / (1024 ** 3),
            "process_count": len(psutil.pids()),
            "boot_time": psutil.boot_time(),
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        return {}
