"""
Mac Hardware Detection Module for Boot Camp Driver System
Detects Mac model, CPU, GPU, and other hardware specifications
"""

import subprocess
import re
import json
import logging
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class MacType(Enum):
    """Mac computer types"""
    MACBOOK_PRO = "MacBook Pro"
    MACBOOK_AIR = "MacBook Air"
    MACBOOK = "MacBook"
    IMAC = "iMac"
    MAC_MINI = "Mac mini"
    MAC_STUDIO = "Mac Studio"
    MAC_PRO = "Mac Pro"
    UNKNOWN = "Unknown"


@dataclass
class MacSystemInfo:
    """Mac system information"""
    model_identifier: str          # e.g., "MacBookPro15,1"
    model_name: str                # e.g., "MacBook Pro (15-inch, 2018)"
    mac_type: MacType              # Computer type
    year: int                       # Model year
    board_id: str                  # Board identifier
    serial_number: str             # Serial number
    cpu_brand: str                 # e.g., "Intel Core i7-8750H"
    cpu_cores: int                 # Number of cores
    ram_gb: int                    # RAM in GB
    storage_gb: int                # Storage in GB
    gpu_model: str                 # e.g., "AMD Radeon Pro 555X"
    boot_camp_support: bool        # Supports Boot Camp
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['mac_type'] = self.mac_type.value
        return data


class MacDetector:
    """Detect Mac system information"""
    
    # Mac model identifier patterns
    MAC_MODELS = {
        # MacBook Pro
        'MacBookPro18': ('MacBook Pro', 2021, True),
        'MacBookPro17': ('MacBook Pro', 2020, True),
        'MacBookPro16': ('MacBook Pro', 2019, True),
        'MacBookPro15': ('MacBook Pro', 2018, True),
        'MacBookPro14': ('MacBook Pro', 2017, True),
        'MacBookPro13': ('MacBook Pro', 2017, True),
        'MacBookPro12': ('MacBook Pro', 2015, True),
        'MacBookPro11': ('MacBook Pro', 2013, True),
        'MacBookPro10': ('MacBook Pro', 2012, True),
        
        # MacBook Air
        'MacBookAir10': ('MacBook Air', 2022, False),  # Apple Silicon
        'MacBookAir9': ('MacBook Air', 2022, False),   # Apple Silicon
        'MacBookAir8': ('MacBook Air', 2018, True),
        'MacBookAir7': ('MacBook Air', 2015, True),
        'MacBookAir6': ('MacBook Air', 2013, True),
        'MacBookAir5': ('MacBook Air', 2012, True),
        
        # MacBook
        'MacBook10': ('MacBook', 2017, True),
        'MacBook9': ('MacBook', 2016, True),
        'MacBook8': ('MacBook', 2015, True),
        
        # iMac
        'iMac21': ('iMac', 2021, False),    # Apple Silicon
        'iMac20': ('iMac', 2020, True),
        'iMac19': ('iMac', 2019, True),
        'iMac18': ('iMac', 2017, True),
        'iMac17': ('iMac', 2015, True),
        'iMac16': ('iMac', 2014, True),
        
        # Mac mini
        'Macmini9': ('Mac mini', 2021, False),  # Apple Silicon
        'Macmini8': ('Mac mini', 2018, True),
        'Macmini7': ('Mac mini', 2014, True),
        
        # Mac Pro
        'MacPro7': ('Mac Pro', 2019, True),
        'MacPro6': ('Mac Pro', 2013, True),
        
        # Mac Studio
        'Mac14': ('Mac Studio', 2023, False),   # Apple Silicon
        'Mac13': ('Mac Studio', 2022, False),   # Apple Silicon
    }
    
    def detect(self) -> Optional[MacSystemInfo]:
        """Detect Mac system information"""
        try:
            model_id = self._get_model_identifier()
            if not model_id:
                logger.error("Could not detect Mac model identifier")
                return None
            
            model_name = self._get_model_name()
            board_id = self._get_board_id()
            serial_number = self._get_serial_number()
            cpu_brand = self._get_cpu_brand()
            cpu_cores = self._get_cpu_cores()
            ram_gb = self._get_ram_gb()
            storage_gb = self._get_storage_gb()
            gpu_model = self._get_gpu_model()
            
            # Parse model type and year
            mac_type, year, boot_camp_support = self._parse_model_identifier(model_id)
            
            return MacSystemInfo(
                model_identifier=model_id,
                model_name=model_name,
                mac_type=mac_type,
                year=year,
                board_id=board_id,
                serial_number=serial_number,
                cpu_brand=cpu_brand,
                cpu_cores=cpu_cores,
                ram_gb=ram_gb,
                storage_gb=storage_gb,
                gpu_model=gpu_model,
                boot_camp_support=boot_camp_support
            )
        
        except Exception as e:
            logger.error(f"Error detecting Mac system info: {e}")
            return None
    
    def _get_model_identifier(self) -> str:
        """Get Mac model identifier (e.g., MacBookPro15,1)"""
        try:
            result = subprocess.run(
                ['system_profiler', 'SPHardwareDataType'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if 'Model Identifier' in line:
                    return line.split(':')[1].strip()
        
        except Exception as e:
            logger.error(f"Failed to get model identifier: {e}")
        
        return ""
    
    def _get_model_name(self) -> str:
        """Get Mac model name (e.g., MacBook Pro (15-inch, 2018))"""
        try:
            result = subprocess.run(
                ['system_profiler', 'SPHardwareDataType'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if 'Model Name' in line:
                    return line.split(':')[1].strip()
        
        except Exception as e:
            logger.error(f"Failed to get model name: {e}")
        
        return ""
    
    def _get_board_id(self) -> str:
        """Get Mac board ID"""
        try:
            result = subprocess.run(
                ['ioreg', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            match = re.search(r'"board-id" = <"([^"]+)">', result.stdout)
            if match:
                return match.group(1)
        
        except Exception as e:
            logger.error(f"Failed to get board ID: {e}")
        
        return ""
    
    def _get_serial_number(self) -> str:
        """Get Mac serial number"""
        try:
            result = subprocess.run(
                ['system_profiler', 'SPHardwareDataType'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if 'Serial Number' in line:
                    return line.split(':')[1].strip()
        
        except Exception as e:
            logger.error(f"Failed to get serial number: {e}")
        
        return ""
    
    def _get_cpu_brand(self) -> str:
        """Get CPU brand and model"""
        try:
            result = subprocess.run(
                ['sysctl', '-n', 'machdep.cpu.brand_string'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        
        except Exception as e:
            logger.error(f"Failed to get CPU brand: {e}")
        
        return ""
    
    def _get_cpu_cores(self) -> int:
        """Get number of CPU cores"""
        try:
            result = subprocess.run(
                ['sysctl', '-n', 'hw.ncpu'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return int(result.stdout.strip())
        
        except Exception as e:
            logger.error(f"Failed to get CPU cores: {e}")
        
        return 0
    
    def _get_ram_gb(self) -> int:
        """Get RAM in GB"""
        try:
            result = subprocess.run(
                ['sysctl', '-n', 'hw.memsize'],
                capture_output=True,
                text=True,
                timeout=5
            )
            bytes_val = int(result.stdout.strip())
            return bytes_val // (1024 ** 3)
        
        except Exception as e:
            logger.error(f"Failed to get RAM: {e}")
        
        return 0
    
    def _get_storage_gb(self) -> int:
        """Get storage capacity in GB"""
        try:
            result = subprocess.run(
                ['df', '-g', '/'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            lines = result.stdout.split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                return int(parts[1])
        
        except Exception as e:
            logger.error(f"Failed to get storage: {e}")
        
        return 0
    
    def _get_gpu_model(self) -> str:
        """Get GPU model"""
        try:
            result = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            for line in result.stdout.split('\n'):
                if 'Chipset Model' in line:
                    return line.split(':')[1].strip()
        
        except Exception as e:
            logger.error(f"Failed to get GPU model: {e}")
        
        return ""
    
    def _parse_model_identifier(self, model_id: str) -> tuple:
        """Parse model identifier to extract type and year"""
        
        # Extract prefix (e.g., "MacBookPro" from "MacBookPro15,1")
        match = re.match(r'([A-Za-z]+)(\d+)', model_id)
        if not match:
            return MacType.UNKNOWN, 0, False
        
        prefix = match.group(1) + match.group(2)
        
        # Look up in models dictionary
        for model_prefix, (model_name, year, boot_camp) in self.MAC_MODELS.items():
            if prefix.startswith(model_prefix):
                mac_type = MacType(model_name)
                return mac_type, year, boot_camp
        
        return MacType.UNKNOWN, 0, False


class BootCampCompatibilityChecker:
    """Check Boot Camp compatibility"""
    
    MINIMUM_REQUIREMENTS = {
        'ram_gb': 8,
        'storage_gb': 64,
        'windows_version': 'Windows 10 1909',
    }
    
    def check_compatibility(self, mac_info: MacSystemInfo) -> Dict[str, Any]:
        """Check if Mac is compatible with Boot Camp"""
        
        if not mac_info.boot_camp_support:
            return {
                'compatible': False,
                'reason': f"{mac_info.mac_type.value} with Apple Silicon is not compatible with Boot Camp"
            }
        
        issues = []
        
        if mac_info.ram_gb < self.MINIMUM_REQUIREMENTS['ram_gb']:
            issues.append(f"Insufficient RAM: {mac_info.ram_gb}GB (minimum {self.MINIMUM_REQUIREMENTS['ram_gb']}GB)")
        
        if mac_info.storage_gb < self.MINIMUM_REQUIREMENTS['storage_gb']:
            issues.append(f"Insufficient storage: {mac_info.storage_gb}GB (minimum {self.MINIMUM_REQUIREMENTS['storage_gb']}GB)")
        
        if issues:
            return {
                'compatible': False,
                'reason': 'System does not meet minimum requirements',
                'issues': issues
            }
        
        return {
            'compatible': True,
            'reason': 'System meets Boot Camp requirements'
        }
