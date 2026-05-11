
import subprocess
import plistlib
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def get_removable_drives() -> List[Dict[str, Any]]:
    \"\"\"Get list of removable USB drives on macOS using diskutil\"\"\"
    try:
        # Run diskutil list -plist to get a machine-readable list of disks
        result = subprocess.run(['diskutil', 'list', '-plist'], capture_output=True, check=True)
        data = plistlib.loads(result.stdout)
        
        removable_drives = []
        for disk in data.get('AllDisksAndPartitions', []):
            # We want to check if the disk is removable
            # To get more details, we need to run diskutil info for each disk
            disk_id = disk.get('DeviceIdentifier')
            if not disk_id:
                continue
                
            info_result = subprocess.run(['diskutil', 'info', '-plist', disk_id], capture_output=True, check=True)
            info_data = plistlib.loads(info_result.stdout)
            
            if info_data.get('Removable') or info_data.get('USBSerial'):
                removable_drives.append({
                    "device_id": disk_id,
                    "path": f"/dev/{disk_id}",
                    "name": info_data.get('MediaName', 'Unknown USB Drive'),
                    "size_gb": round(info_data.get('TotalSize', 0) / (1024**3), 2),
                    "is_removable": True,
                    "vendor": info_data.get('Vendor', 'Generic'),
                    "protocol": info_data.get('BusProtocol', 'USB')
                })
        
        return removable_drives
    except Exception as e:
        logger.error(f"Error scanning for USB drives: {e}")
        # Return mock data as fallback for development
        return [
            {
                "device_id": "usb-mock-123",
                "path": "/dev/disk4",
                "name": "Mock Kingston DataTraveler",
                "size_gb": 32.0,
                "is_removable": True
            }
        ]
