"""
BootForge Disk Management System
Handles disk operations, image writing, and USB drive management
"""

import os
import time
import logging
import hashlib
import shutil
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from PyQt6.QtCore import QThread, pyqtSignal, QObject
import psutil


@dataclass
class DiskInfo:
    """Disk information structure"""
    path: str
    name: str
    size_bytes: int
    filesystem: str
    mountpoint: Optional[str]
    is_removable: bool
    model: str
    vendor: str
    serial: Optional[str]
    health_status: str
    write_speed_mbps: float


@dataclass
class WriteProgress:
    """Write operation progress information"""
    bytes_written: int
    total_bytes: int
    percentage: float
    speed_mbps: float
    eta_seconds: int
    current_operation: str


class DiskWriter(QThread):
    """Disk writing thread with progress monitoring"""
    
    # Signals
    progress_updated = pyqtSignal(WriteProgress)
    operation_completed = pyqtSignal(bool, str)  # success, message
    operation_started = pyqtSignal(str)  # operation description
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.source_path = ""
        self.target_device = ""
        self.verify_after_write = True
        self.buffer_size = 1024 * 1024  # 1MB buffer
        self.is_cancelled = False
    
    def write_image(self, source_path: str, target_device: str, verify: bool = True):
        """Start disk writing operation"""
        self.source_path = source_path
        self.target_device = target_device
        self.verify_after_write = verify
        self.is_cancelled = False
        self.start()
    
    def cancel_operation(self):
        """Cancel current operation"""
        self.is_cancelled = True
        self.logger.info("Disk write operation cancelled by user")
    
    def run(self):
        """Main writing thread"""
        try:
            # Validate inputs
            if not os.path.exists(self.source_path):
                self.operation_completed.emit(False, f"Source file not found: {self.source_path}")
                return
            
            if not self._validate_target_device():
                self.operation_completed.emit(False, f"Invalid target device: {self.target_device}")
                return
            
            # Get file size
            source_size = os.path.getsize(self.source_path)
            self.operation_started.emit(f"Writing {Path(self.source_path).name} to {self.target_device}")
            
            # Unmount target device if mounted
            self._unmount_device()
            
            # Write image
            success = self._write_image_data(source_size)
            
            if success and self.verify_after_write and not self.is_cancelled:
                self.operation_started.emit("Verifying written data...")
                success = self._verify_written_data(source_size)
            
            if success:
                self.operation_completed.emit(True, "Disk write completed successfully")
            else:
                self.operation_completed.emit(False, "Disk write failed or was cancelled")
                
        except Exception as e:
            self.logger.error(f"Error in disk writing: {e}")
            self.operation_completed.emit(False, f"Write error: {str(e)}")
    
    def _validate_target_device(self) -> bool:
        """Validate target device"""
        try:
            # Check if device exists
            if not os.path.exists(self.target_device):
                return False
            
            # Additional platform-specific checks
            system = platform.system()
            
            if system == "Linux":
                # Check if it's a block device
                import stat
                device_stat = os.stat(self.target_device)
                return stat.S_ISBLK(device_stat.st_mode)
                
            elif system == "Windows":
                # Windows device validation
                return self.target_device.startswith(r'\\.\PhysicalDrive')
                
            elif system == "Darwin":  # macOS
                # macOS device validation
                return self.target_device.startswith('/dev/')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating target device: {e}")
            return False
    
    def _unmount_device(self):
        """Unmount target device if mounted"""
        try:
            system = platform.system()
            
            if system == "Linux":
                # Find and unmount all partitions of the device
                partitions = psutil.disk_partitions()
                for partition in partitions:
                    if partition.device.startswith(self.target_device):
                        subprocess.run(['umount', partition.device], 
                                     capture_output=True, check=False)
                        self.logger.info(f"Unmounted {partition.device}")
                        
            elif system == "Darwin":  # macOS
                # Use diskutil to unmount
                subprocess.run(['diskutil', 'unmountDisk', self.target_device], 
                             capture_output=True, check=False)
                self.logger.info(f"Unmounted {self.target_device}")
                
        except Exception as e:
            self.logger.warning(f"Could not unmount device: {e}")
    
    def _write_image_data(self, total_size: int) -> bool:
        """Write image data to target device"""
        try:
            bytes_written = 0
            start_time = time.time()
            last_progress_time = start_time
            
            with open(self.source_path, 'rb') as source:
                with open(self.target_device, 'wb') as target:
                    while bytes_written < total_size and not self.is_cancelled:
                        # Read chunk
                        chunk = source.read(self.buffer_size)
                        if not chunk:
                            break
                        
                        # Write chunk
                        target.write(chunk)
                        target.flush()
                        bytes_written += len(chunk)
                        
                        # Update progress
                        current_time = time.time()
                        if current_time - last_progress_time >= 0.5:  # Update every 0.5 seconds
                            self._emit_progress(bytes_written, total_size, current_time - start_time)
                            last_progress_time = current_time
                        
                        # Sync to disk periodically
                        if bytes_written % (self.buffer_size * 100) == 0:
                            os.fsync(target.fileno())
            
            # Final sync
            if not self.is_cancelled:
                os.sync() if hasattr(os, 'sync') else None
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error writing image data: {e}")
            return False
    
    def _verify_written_data(self, total_size: int) -> bool:
        """Verify written data matches source"""
        try:
            source_hash = hashlib.sha256()
            target_hash = hashlib.sha256()
            
            bytes_verified = 0
            start_time = time.time()
            last_progress_time = start_time
            
            with open(self.source_path, 'rb') as source:
                with open(self.target_device, 'rb') as target:
                    while bytes_verified < total_size and not self.is_cancelled:
                        source_chunk = source.read(self.buffer_size)
                        target_chunk = target.read(self.buffer_size)
                        
                        if not source_chunk or not target_chunk:
                            break
                        
                        source_hash.update(source_chunk)
                        target_hash.update(target_chunk)
                        bytes_verified += len(source_chunk)
                        
                        # Update progress
                        current_time = time.time()
                        if current_time - last_progress_time >= 0.5:
                            progress = WriteProgress(
                                bytes_written=bytes_verified,
                                total_bytes=total_size,
                                percentage=(bytes_verified / total_size) * 100,
                                speed_mbps=0,  # Verification doesn't track speed
                                eta_seconds=0,
                                current_operation="Verifying data..."
                            )
                            self.progress_updated.emit(progress)
                            last_progress_time = current_time
            
            if self.is_cancelled:
                return False
            
            # Compare hashes
            return source_hash.hexdigest() == target_hash.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error verifying written data: {e}")
            return False
    
    def _emit_progress(self, bytes_written: int, total_bytes: int, elapsed_time: float):
        """Emit progress update signal"""
        percentage = (bytes_written / total_bytes) * 100
        speed_mbps = (bytes_written / (1024 * 1024)) / elapsed_time if elapsed_time > 0 else 0
        
        remaining_bytes = total_bytes - bytes_written
        eta_seconds = (remaining_bytes / (bytes_written / elapsed_time)) if bytes_written > 0 else 0
        
        progress = WriteProgress(
            bytes_written=bytes_written,
            total_bytes=total_bytes,
            percentage=percentage,
            speed_mbps=speed_mbps,
            eta_seconds=int(eta_seconds),
            current_operation="Writing data..."
        )
        
        self.progress_updated.emit(progress)


class DiskManager:
    """Main disk management class"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.writer = DiskWriter()
    
    def get_removable_drives(self) -> List[DiskInfo]:
        """Get list of removable drives suitable for writing"""
        drives = []
        
        try:
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                if self._is_removable_drive(partition.device):
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        
                        # Get device information
                        model, vendor = self._get_device_info(partition.device)
                        serial = self._get_device_serial(partition.device)
                        health = self._check_device_health(partition.device)
                        write_speed = self._measure_write_speed(partition.device)
                        
                        drive_info = DiskInfo(
                            path=partition.device,
                            name=model or partition.device,
                            size_bytes=usage.total,
                            filesystem=partition.fstype,
                            mountpoint=partition.mountpoint,
                            is_removable=True,
                            model=model or "Unknown",
                            vendor=vendor or "Unknown",
                            serial=serial,
                            health_status=health,
                            write_speed_mbps=write_speed
                        )
                        
                        drives.append(drive_info)
                        
                    except (PermissionError, OSError) as e:
                        self.logger.debug(f"Could not access drive {partition.device}: {e}")
                        continue
                        
        except Exception as e:
            self.logger.error(f"Error getting removable drives: {e}")
        
        return drives
    
    def _is_removable_drive(self, device_path: str) -> bool:
        """Check if device is a removable drive"""
        try:
            system = platform.system()
            
            if system == "Linux":
                device_name = device_path.split('/')[-1].rstrip('0123456789')
                removable_file = f"/sys/block/{device_name}/removable"
                
                if os.path.exists(removable_file):
                    with open(removable_file, 'r') as f:
                        return f.read().strip() == '1'
                        
            elif system == "Windows":
                import ctypes
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(device_path)
                return drive_type == 2  # DRIVE_REMOVABLE
                
            elif system == "Darwin":  # macOS
                return "/Volumes/" in device_path
                
            return False
            
        except Exception:
            return False
    
    def _get_device_info(self, device_path: str) -> Tuple[Optional[str], Optional[str]]:
        """Get device model and vendor information"""
        try:
            system = platform.system()
            
            if system == "Linux":
                device_name = device_path.split('/')[-1].rstrip('0123456789')
                
                model_file = f"/sys/block/{device_name}/device/model"
                vendor_file = f"/sys/block/{device_name}/device/vendor"
                
                model = None
                vendor = None
                
                if os.path.exists(model_file):
                    with open(model_file, 'r') as f:
                        model = f.read().strip()
                
                if os.path.exists(vendor_file):
                    with open(vendor_file, 'r') as f:
                        vendor = f.read().strip()
                
                return model, vendor
                
            return None, None
            
        except Exception:
            return None, None
    
    def _get_device_serial(self, device_path: str) -> Optional[str]:
        """Get device serial number"""
        try:
            system = platform.system()
            
            if system == "Linux":
                device_name = device_path.split('/')[-1].rstrip('0123456789')
                serial_file = f"/sys/block/{device_name}/device/serial"
                
                if os.path.exists(serial_file):
                    with open(serial_file, 'r') as f:
                        return f.read().strip()
                        
            return None
            
        except Exception:
            return None
    
    def _check_device_health(self, device_path: str) -> str:
        """Check device health status"""
        try:
            # Basic health check - could be expanded with SMART data
            if os.path.exists(device_path):
                return "Good"
            else:
                return "Unknown"
                
        except Exception:
            return "Unknown"
    
    def _measure_write_speed(self, device_path: str) -> float:
        """Measure device write speed (basic estimation)"""
        try:
            # This is a simplified estimation
            # In a real implementation, you'd perform a write test
            return 25.0  # Default estimate of 25 MB/s
            
        except Exception:
            return 0.0
    
    def write_image_to_device(self, image_path: str, device_path: str, 
                            verify: bool = True, progress_callback: Optional[Callable] = None):
        """Write image to device with progress monitoring"""
        if progress_callback:
            self.writer.progress_updated.connect(progress_callback)
        
        self.writer.write_image(image_path, device_path, verify)
        return self.writer
    
    def format_device(self, device_path: str, filesystem: str = "fat32") -> bool:
        """Format device with specified filesystem"""
        try:
            system = platform.system()
            
            if system == "Linux":
                if filesystem.lower() == "fat32":
                    result = subprocess.run(
                        ['mkfs.fat', '-F', '32', device_path],
                        capture_output=True, text=True
                    )
                elif filesystem.lower() == "ntfs":
                    result = subprocess.run(
                        ['mkfs.ntfs', '-f', device_path],
                        capture_output=True, text=True
                    )
                else:
                    return False
                
                return result.returncode == 0
                
            elif system == "Windows":
                # Use Windows format command
                drive_letter = device_path.rstrip('\\')
                result = subprocess.run(
                    ['format', f'{drive_letter}:', '/fs:fat32', '/q'],
                    capture_output=True, text=True
                )
                return result.returncode == 0
                
            elif system == "Darwin":  # macOS
                # Use diskutil
                fs_type = "MS-DOS FAT32" if filesystem.lower() == "fat32" else "ExFAT"
                result = subprocess.run(
                    ['diskutil', 'eraseDisk', fs_type, 'BOOTFORGE', device_path],
                    capture_output=True, text=True
                )
                return result.returncode == 0
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error formatting device: {e}")
            return False