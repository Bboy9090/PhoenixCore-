"""
Device Manager - Handle USB device detection and management
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DeviceManager:
    """Manages USB device detection and information"""
    
    def __init__(self):
        """Initialize device manager"""
        self.detected_devices = []
    
    def detect_devices(self) -> List[Dict]:
        """
        Detect USB devices on the system
        
        Returns:
            List of device dictionaries with info
        """
        try:
            import psutil
            
            devices = []
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                # Filter for removable devices
                if self._is_removable_device(partition):
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        device = {
                            'path': partition.device,
                            'name': partition.device.split('/')[-1],
                            'mountpoint': partition.mountpoint,
                            'fstype': partition.fstype,
                            'total_bytes': usage.total,
                            'total_gb': usage.total / (1024**3),
                            'used_bytes': usage.used,
                            'used_gb': usage.used / (1024**3),
                            'free_bytes': usage.free,
                            'free_gb': usage.free / (1024**3),
                            'percent_used': usage.percent,
                            'is_removable': True
                        }
                        devices.append(device)
                    except Exception as e:
                        logger.warning(f"Could not get usage for {partition.device}: {e}")
                        continue
            
            self.detected_devices = devices
            logger.info(f"Detected {len(devices)} USB device(s)")
            return devices
        
        except Exception as e:
            logger.error(f"Device detection error: {e}")
            return []
    
    def get_device_info(self, device_path: str) -> Optional[Dict]:
        """Get information about a specific device"""
        for device in self.detected_devices:
            if device['path'] == device_path:
                return device
        return None
    
    def validate_device(self, device_path: str) -> tuple[bool, List[str]]:
        """
        Validate device for USB building
        
        Returns:
            (is_valid, list of warnings/errors)
        """
        warnings = []
        
        device = self.get_device_info(device_path)
        if not device:
            return False, ["Device not found"]
        
        # Check if device is removable
        if not device.get('is_removable', False):
            return False, ["Device is not removable (may be system drive)"]
        
        # Check minimum size (4GB)
        if device['total_gb'] < 4:
            return False, [f"Device is too small ({device['total_gb']:.1f}GB, minimum 4GB required)"]
        
        # Check if device is mounted
        if device.get('mountpoint'):
            warnings.append(f"Device is currently mounted at {device['mountpoint']}. It will be unmounted during build.")
        
        # Check free space
        if device['free_gb'] < 1:
            warnings.append("Device has very little free space")
        
        # Check filesystem
        if device['fstype'] not in ['FAT32', 'exFAT', 'NTFS', 'ext4']:
            warnings.append(f"Unusual filesystem: {device['fstype']}")
        
        return True, warnings
    
    def unmount_device(self, device_path: str) -> tuple[bool, str]:
        """
        Unmount device before building
        
        Returns:
            (success, message)
        """
        try:
            import subprocess
            import platform
            
            system = platform.system().lower()
            
            if system == 'linux':
                # Use umount on Linux
                result = subprocess.run(['umount', device_path], capture_output=True, text=True)
                if result.returncode == 0:
                    return True, f"Device {device_path} unmounted successfully"
                else:
                    return False, f"Failed to unmount: {result.stderr}"
            
            elif system == 'darwin':
                # Use diskutil on macOS
                result = subprocess.run(['diskutil', 'unmount', device_path], capture_output=True, text=True)
                if result.returncode == 0:
                    return True, f"Device {device_path} unmounted successfully"
                else:
                    return False, f"Failed to unmount: {result.stderr}"
            
            elif system == 'windows':
                # Use wmic on Windows
                result = subprocess.run(
                    ['wmic', 'logicaldisk', 'where', f'name="{device_path}"', 'call', 'eject'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    return True, f"Device {device_path} ejected successfully"
                else:
                    return False, f"Failed to eject: {result.stderr}"
            
            else:
                return False, f"Unsupported platform: {system}"
        
        except Exception as e:
            return False, f"Error unmounting device: {str(e)}"
    
    def eject_device(self, device_path: str) -> tuple[bool, str]:
        """
        Eject device after build
        
        Returns:
            (success, message)
        """
        try:
            import subprocess
            import platform
            
            system = platform.system().lower()
            
            if system == 'linux':
                # Use eject on Linux
                result = subprocess.run(['eject', device_path], capture_output=True, text=True)
                if result.returncode == 0:
                    return True, f"Device {device_path} ejected successfully"
                else:
                    return False, f"Failed to eject: {result.stderr}"
            
            elif system == 'darwin':
                # Use diskutil on macOS
                result = subprocess.run(['diskutil', 'eject', device_path], capture_output=True, text=True)
                if result.returncode == 0:
                    return True, f"Device {device_path} ejected successfully"
                else:
                    return False, f"Failed to eject: {result.stderr}"
            
            elif system == 'windows':
                # Use wmic on Windows
                result = subprocess.run(
                    ['wmic', 'logicaldisk', 'where', f'name="{device_path}"', 'call', 'eject'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    return True, f"Device {device_path} ejected successfully"
                else:
                    return False, f"Failed to eject: {result.stderr}"
            
            else:
                return False, f"Unsupported platform: {system}"
        
        except Exception as e:
            return False, f"Error ejecting device: {str(e)}"
    
    def get_device_health(self, device_path: str) -> Dict:
        """Get device health status"""
        device = self.get_device_info(device_path)
        if not device:
            return {'status': 'unknown', 'health': 'Unknown'}
        
        # Simple health check based on usage
        percent_used = device.get('percent_used', 0)
        
        if percent_used > 90:
            health = 'Poor'
        elif percent_used > 70:
            health = 'Fair'
        elif percent_used > 50:
            health = 'Good'
        else:
            health = 'Excellent'
        
        return {
            'status': 'healthy',
            'health': health,
            'percent_used': percent_used
        }
    
    @staticmethod
    def _is_removable_device(partition) -> bool:
        """Check if partition is a removable device"""
        # Check for USB or removable in device path
        device_lower = partition.device.lower()
        
        if 'usb' in device_lower or 'removable' in partition.opts.lower():
            return True
        
        # Additional checks for specific patterns
        if device_lower.startswith('/dev/sd') and device_lower[-1].isalpha():
            # Linux USB devices typically end with a letter
            return True
        
        if device_lower.startswith('/dev/disk') and 'external' in partition.opts.lower():
            # macOS external drives
            return True
        
        return False
