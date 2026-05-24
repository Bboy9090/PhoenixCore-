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