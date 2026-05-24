"""
BootForge Hardware Auto Detection System
Intelligent hardware detection for automatic profile matching and deployment optimization
"""

import os
import re
import json
import time
import logging
import platform
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from src.core.models import HardwareProfile


class DetectionConfidence(Enum):
    """Hardware detection confidence levels"""
    EXACT_MATCH = "exact"           # 100% confident (exact model match)
    HIGH_CONFIDENCE = "high"        # 80-99% confident (partial match with strong indicators)
    MEDIUM_CONFIDENCE = "medium"    # 60-79% confident (generic detection with some specifics)
    LOW_CONFIDENCE = "low"          # 40-59% confident (fallback/generic detection)
    UNKNOWN = "unknown"             # <40% confident (detection failed/insufficient data)


@dataclass
class DetectedHardware:
    """Detected hardware information"""
    # System identification
    system_name: Optional[str] = None
    system_manufacturer: Optional[str] = None
    system_model: Optional[str] = None
    system_serial: Optional[str] = None
    
    # CPU information
    cpu_name: Optional[str] = None
    cpu_manufacturer: Optional[str] = None
    cpu_architecture: Optional[str] = None
    cpu_cores: Optional[int] = None
    cpu_threads: Optional[int] = None
    
    # Memory information
    total_ram_gb: Optional[float] = None
    ram_modules: List[Dict[str, Any]] = field(default_factory=list)
    
    # GPU information
    gpus: List[Dict[str, Any]] = field(default_factory=list)
    primary_gpu: Optional[str] = None
    
    # Network information
    network_adapters: List[Dict[str, Any]] = field(default_factory=list)
    
    # Storage information
    storage_devices: List[Dict[str, Any]] = field(default_factory=list)
    
    # Platform-specific data
    platform: str = ""
    platform_version: Optional[str] = None
    bios_info: Dict[str, Any] = field(default_factory=dict)
    
    # Detection metadata
    detection_confidence: DetectionConfidence = DetectionConfidence.UNKNOWN
    detection_time: Optional[float] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of detected hardware"""
        parts = []
        
        if self.system_manufacturer and self.system_model:
            parts.append(f"{self.system_manufacturer} {self.system_model}")
        elif self.system_name:
            parts.append(self.system_name)
        
        if self.cpu_name:
            parts.append(f"CPU: {self.cpu_name}")
        
        if self.total_ram_gb:
            parts.append(f"RAM: {self.total_ram_gb:.1f}GB")
        
        if self.primary_gpu:
            parts.append(f"GPU: {self.primary_gpu}")
        
        return " | ".join(parts) if parts else "Unknown System"


@dataclass
class ProfileMatch:
    """Hardware profile match result"""
    profile: HardwareProfile
    confidence: DetectionConfidence
    match_score: float  # 0-100
    match_reasons: List[str] = field(default_factory=list)
    detection_data: Optional[DetectedHardware] = None
    
    def get_confidence_text(self) -> str:
        """Get human-readable confidence description"""
        confidence_map = {
            DetectionConfidence.EXACT_MATCH: "Exact Match",
            DetectionConfidence.HIGH_CONFIDENCE: "High Confidence",
            DetectionConfidence.MEDIUM_CONFIDENCE: "Medium Confidence", 
            DetectionConfidence.LOW_CONFIDENCE: "Low Confidence",
            DetectionConfidence.UNKNOWN: "Unknown"
        }
        return confidence_map.get(self.confidence, "Unknown")


class PlatformDetector(ABC):
    """Abstract base class for platform-specific hardware detection"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def detect_hardware(self) -> DetectedHardware:
        """Detect hardware on this platform"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if detection is available on this platform"""
        pass
    
    def _run_command(self, command: List[str], timeout: int = 30) -> Tuple[str, str, int]:
        """Safely run a system command with timeout"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Command timed out: {' '.join(command)}")
            return "", "Command timed out", -1
        except (OSError, subprocess.SubprocessError) as e:
            self.logger.error(f"Command execution failed: {e}")
            return "", str(e), -1


class WindowsDetector(PlatformDetector):
    """Windows-specific hardware detection using PowerShell and WMI/CIM"""
    
    def detect_hardware(self) -> DetectedHardware:
        """Detect hardware on Windows using PowerShell CIM queries"""
        hardware = DetectedHardware(platform="windows")
        
        try:
            # Detect system information
            self._detect_system_info(hardware)
            
            # Detect CPU information
            self._detect_cpu_info(hardware)
            
            # Detect memory information
            self._detect_memory_info(hardware)
            
            # Detect GPU information
            self._detect_gpu_info(hardware)
            
            # Detect network adapters
            self._detect_network_info(hardware)
            
            # Detect storage devices
            self._detect_storage_info(hardware)
            
            # Set confidence based on detection success
            hardware.detection_confidence = self._calculate_confidence(hardware)
            
        except Exception as e:
            self.logger.error(f"Windows hardware detection failed: {e}")
            hardware.detection_confidence = DetectionConfidence.UNKNOWN
        
        return hardware
    
    def is_available(self) -> bool:
        """Check if Windows detection is available"""
        return platform.system().lower() == "windows"
    
    def _detect_system_info(self, hardware: DetectedHardware):
        """Detect system information using Win32_ComputerSystem"""
        command = [
            "powershell", "-Command",
            "Get-CimInstance Win32_ComputerSystem | Select-Object Name,Manufacturer,Model,TotalPhysicalMemory | ConvertTo-Json"
        ]
        
        stdout, stderr, returncode = self._run_command(command)
        if returncode == 0 and stdout.strip():
            try:
                data = json.loads(stdout)
                hardware.system_name = data.get("Name")
                hardware.system_manufacturer = data.get("Manufacturer")
                hardware.system_model = data.get("Model")
                
                # Convert total physical memory to GB
                total_memory = data.get("TotalPhysicalMemory")
                if total_memory:
                    hardware.total_ram_gb = int(total_memory) / (1024 ** 3)
                
                hardware.raw_data["win32_computer_system"] = data
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse system info JSON: {e}")
    
    def _detect_cpu_info(self, hardware: DetectedHardware):
        """Detect CPU information using Win32_Processor"""
        command = [
            "powershell", "-Command",
            "Get-CimInstance Win32_Processor | Select-Object Name,Manufacturer,Architecture,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json"
        ]
        
        stdout, stderr, returncode = self._run_command(command)
        if returncode == 0 and stdout.strip():
            try:
                data = json.loads(stdout)
                # Handle both single processor and array of processors
                if isinstance(data, list):
                    data = data[0]  # Take the first processor
                
                hardware.cpu_name = data.get("Name", "").strip()
                hardware.cpu_manufacturer = data.get("Manufacturer")
                hardware.cpu_cores = data.get("NumberOfCores")
                hardware.cpu_threads = data.get("NumberOfLogicalProcessors")
                
                # Map architecture codes to standard names
                arch_map = {0: "x86", 1: "MIPS", 2: "Alpha", 3: "PowerPC", 6: "ia64", 9: "x64"}
                arch_code = data.get("Architecture")
                if arch_code in arch_map:
                    hardware.cpu_architecture = arch_map[arch_code]
                
                hardware.raw_data["win32_processor"] = data
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse CPU info JSON: {e}")
    
    def _detect_memory_info(self, hardware: DetectedHardware):
        """Detect memory modules using Win32_PhysicalMemory"""
        command = [
            "powershell", "-Command", 
            "Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity,Speed,Manufacturer,PartNumber | ConvertTo-Json"
        ]
        
        stdout, stderr, returncode = self._run_command(command)
        if returncode == 0 and stdout.strip():
            try:
                data = json.loads(stdout)
                if not isinstance(data, list):
                    data = [data]  # Ensure it's a list
                
                for module in data:
                    capacity_gb = int(module.get("Capacity", 0)) / (1024 ** 3) if module.get("Capacity") else 0
                    hardware.ram_modules.append({
                        "capacity_gb": capacity_gb,
                        "speed": module.get("Speed"),
                        "manufacturer": module.get("Manufacturer"),
                        "part_number": module.get("PartNumber")
                    })
                
                hardware.raw_data["win32_physical_memory"] = data
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse memory info JSON: {e}")
    
    def _detect_gpu_info(self, hardware: DetectedHardware):
        """Detect GPU information using Win32_VideoController"""
        command = [
            "powershell", "-Command",
            "Get-CimInstance Win32_VideoController | Where-Object {$_.Name -notlike '*Remote*'} | Select-Object Name,AdapterCompatibility,DriverVersion,AdapterRAM | ConvertTo-Json"
        ]
        
        stdout, stderr, returncode = self._run_command(command)
        if returncode == 0 and stdout.strip():
            try:
                data = json.loads(stdout)
                if not isinstance(data, list):
                    data = [data]
                
                for gpu in data:
                    gpu_name = gpu.get("Name", "").strip()
                    if gpu_name and "remote" not in gpu_name.lower():
                        gpu_info = {
                            "name": gpu_name,
                            "vendor": gpu.get("AdapterCompatibility"),
                            "driver_version": gpu.get("DriverVersion"),
                            "memory_bytes": gpu.get("AdapterRAM")
                        }
                        hardware.gpus.append(gpu_info)
                        
                        # Set primary GPU (usually the first discrete GPU or integrated if only one)
                        if not hardware.primary_gpu:
                            hardware.primary_gpu = gpu_name
                
                hardware.raw_data["win32_video_controller"] = data
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse GPU info JSON: {e}")
    
    def _detect_network_info(self, hardware: DetectedHardware):
        """Detect network adapters using Win32_NetworkAdapter"""
        command = [
            "powershell", "-Command",
            "Get-CimInstance Win32_NetworkAdapter | Where-Object {$_.PhysicalAdapter -eq $true -and $_.NetConnectionStatus -ne $null} | Select-Object Name,Manufacturer,MACAddress,Speed | ConvertTo-Json"
        ]
        
        stdout, stderr, returncode = self._run_command(command)
        if returncode == 0 and stdout.strip():
            try:
                data = json.loads(stdout)
                if not isinstance(data, list):
                    data = [data]
                
                for adapter in data:
                    if adapter.get("Name"):
                        hardware.network_adapters.append({
                            "name": adapter.get("Name"),
                            "manufacturer": adapter.get("Manufacturer"),
                            "mac_address": adapter.get("MACAddress"),
                            "speed": adapter.get("Speed")
                        })
                
                hardware.raw_data["win32_network_adapter"] = data
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse network info JSON: {e}")
    
    def _detect_storage_info(self, hardware: DetectedHardware):
        """Detect storage devices using Win32_DiskDrive"""
        command = [
            "powershell", "-Command",
            "Get-CimInstance Win32_DiskDrive | Select-Object Model,Manufacturer,Size,MediaType | ConvertTo-Json"
        ]
        
        stdout, stderr, returncode = self._run_command(command)
        if returncode == 0 and stdout.strip():
            try:
                data = json.loads(stdout)
                if not isinstance(data, list):
                    data = [data]
                
                for disk in data:
                    if disk.get("Model"):
                        size_gb = int(disk.get("Size", 0)) / (1024 ** 3) if disk.get("Size") else 0
                        hardware.storage_devices.append({
                            "model": disk.get("Model"),
                            "manufacturer": disk.get("Manufacturer"),
                            "size_gb": size_gb,
                            "media_type": disk.get("MediaType")
                        })
                
                hardware.raw_data["win32_disk_drive"] = data
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"Failed to parse storage info JSON: {e}")
    
    def _calculate_confidence(self, hardware: DetectedHardware) -> DetectionConfidence:
        """Calculate detection confidence based on available data"""
        confidence_factors = 0
        total_factors = 5
        
        if hardware.system_manufacturer and hardware.system_model:
            confidence_factors += 1
        if hardware.cpu_name:
            confidence_factors += 1
        if hardware.total_ram_gb:
            confidence_factors += 1
        if hardware.gpus:
            confidence_factors += 1
        if hardware.network_adapters:
            confidence_factors += 1
        
        confidence_ratio = confidence_factors / total_factors
        
        if confidence_ratio >= 0.8:
            return DetectionConfidence.HIGH_CONFIDENCE
        elif confidence_ratio >= 0.6:
            return DetectionConfidence.MEDIUM_CONFIDENCE
        elif confidence_ratio >= 0.4:
            return DetectionConfidence.LOW_CONFIDENCE
        else:
            return DetectionConfidence.UNKNOWN


class LinuxDetector(PlatformDetector):
    """Linux-specific hardware detection using system tools"""
    
    def detect_hardware(self) -> DetectedHardware:
        """Detect hardware on Linux using various system tools"""
        hardware = DetectedHardware(platform="linux")
        
        try:
            # Detect system information
            self._detect_system_info(hardware)
            
            # Detect CPU information  
            self._detect_cpu_info(hardware)
            
            # Detect memory information
          
(Content truncated due to size limit. Use line ranges to read remaining content)