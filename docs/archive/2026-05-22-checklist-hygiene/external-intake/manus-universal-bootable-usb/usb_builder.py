"""
BootForge Storage Builder Engine
Enhanced bootable storage device creation system for offline deployment scenarios
Supports USB drives, hard drives, SSDs, and other storage devices
"""

import os
import json
import time
import uuid
import shutil
import logging
import hashlib
import tempfile
import platform
import subprocess
from pathlib import Path
from enum import Enum
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, asdict, field
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from src.core.disk_manager import DiskManager, DiskInfo, WriteProgress
from src.core.safety_validator import SafetyValidator, SafetyLevel, ValidationResult, DeviceRisk
from src.core.patch_pipeline import PatchPlanner, PatchPlan, PatchSet, PatchAction, PatchStatus
from src.core.patch_config_loader import PatchConfigLoader
from src.core.vendor_database import PatchCompatibility
from src.core.models import (
    HardwareProfile, DeploymentType, PartitionScheme, FileSystem, 
    PartitionInfo, DeploymentRecipe
)
from src.core.hardware_profiles import create_mac_patch_sets
from src.core.grub_manager import GRUBManager, GRUBBootMode


# Imported from models.py to prevent circular imports


# All classes moved to models.py to prevent circular imports


@dataclass
class BuildProgress:
    """USB build operation progress"""
    current_step: str
    step_number: int
    total_steps: int
    step_progress: float
    overall_progress: float
    speed_mbps: float
    eta_seconds: int
    detailed_status: str
    logs: List[str] = field(default_factory=list)


class StorageBuilder(QThread):
    """Storage Builder thread for creating bootable deployment drives on any storage device"""
    
    # Signals
    progress_updated = pyqtSignal(object)  # BuildProgress
    operation_completed = pyqtSignal(bool, str)
    operation_started = pyqtSignal(str)
    log_message = pyqtSignal(str, str)  # level, message
    
    def __init__(self, safety_level: SafetyLevel = SafetyLevel.STANDARD):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.safety_validator = SafetyValidator(safety_level)
        self.recipe: Optional[DeploymentRecipe] = None
        self.target_device: str = ""
        self.hardware_profile: Optional[HardwareProfile] = None
        self.source_files: Dict[str, str] = {}
        self.is_cancelled = False
        self.build_log: List[str] = []
        self.temp_dir: Optional[Path] = None
        self.rollback_operations: List[Callable] = []  # For rollback on failure
    
    def start_build(self, recipe: DeploymentRecipe, target_device: str, 
                   hardware_profile: HardwareProfile, source_files: Dict[str, str]):
        """Start storage device build operation"""
        self.recipe = recipe
        self.target_device = target_device
        self.hardware_profile = hardware_profile
        self.source_files = source_files
        self.is_cancelled = False
        self.build_log = []
        self.rollback_operations = []
        self.grub_config = None
        self.start()
    
    def start_multiboot_build(self, recipe: DeploymentRecipe, target_device: str,
                             hardware_profile: HardwareProfile, source_files: Dict[str, str],
                             grub_config):
        """Start multi-boot storage device build operation"""
        self.recipe = recipe
        self.target_device = target_device  
        self.hardware_profile = hardware_profile
        self.source_files = source_files
        self.grub_config = grub_config
        self.is_cancelled = False
        self.build_log = []
        self.rollback_operations = []
        self.start()
    
    def cancel_build(self):
        """Cancel current build operation"""
        self.is_cancelled = True
        self._log_message("INFO", "Storage device build operation cancelled by user")
    
    def run(self):
        """Main storage device building thread"""
        try:
            # Create temporary working directory
            self.temp_dir = Path(tempfile.mkdtemp(prefix="bootforge_build_"))
            self._log_message("INFO", f"Created temporary directory: {self.temp_dir}")
            
            # Validate inputs
            if not self._validate_build_inputs():
                return
            
            # Calculate total steps
            total_steps = 7  # Basic steps, may increase based on recipe
            step = 0
            
            # Step 1: Prepare target device
            step += 1
            self._emit_progress("Preparing target device", step, total_steps, 0)
            if not self._prepare_target_device():
                return
            
            # Step 2: Create partition scheme
            step += 1
            self._emit_progress("Creating partition scheme", step, total_steps, 0)
            if not self._create_partition_scheme():
                return
            
            # Step 3: Format partitions
            step += 1
            self._emit_progress("Formatting partitions", step, total_steps, 0)
            if not self._format_partitions():
                return
            
            # Step 4: Mount partitions
            step += 1
            self._emit_progress("Mounting partitions", step, total_steps, 0)
            partition_mounts = self._mount_partitions()
            if not partition_mounts:
                return
            
            # Step 5: Deploy files based on recipe
            step += 1
            self._emit_progress("Deploying files", step, total_steps, 0)
            if not self._deploy_files(partition_mounts):
                return
            
            # Step 6: Configure bootloader
            step += 1
            self._emit_progress("Configuring bootloader", step, total_steps, 0)
            if self.recipe and self.recipe.deployment_type == DeploymentType.MULTIBOOT:
                if not self._configure_multiboot_grub(partition_mounts):
                    return
            else:
                if not self._configure_bootloader(partition_mounts):
                    return
            
            # Step 7: Finalize and verify
            step += 1
            self._emit_progress("Finalizing build", step, total_steps, 0)
            if not self._finalize_build(partition_mounts):
                return
            
            self._build_successful = True
            self._log_message("INFO", "Storage device build completed successfully")
            self.operation_completed.emit(True, "Storage device build completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in storage device building: {e}")
            self._log_message("ERROR", f"Build error: {str(e)}")
            self.operation_completed.emit(False, f"Build error: {str(e)}")
        
        finally:
            # Perform rollback if needed
            if self.is_cancelled or not hasattr(self, '_build_successful'):
                self._perform_rollback()
            # Cleanup
            self._cleanup_build()
    
    def _validate_build_inputs(self) -> bool:
        """Comprehensive safety validation of build inputs"""
        try:
            self._log_message("INFO", "Starting comprehensive safety validation...")
            
            # Check recipe
            if not self.recipe:
                self.operation_completed.emit(False, "No recipe specified")
                return False
            
            # 1. CRITICAL: Device Safety Validation
            self._log_message("INFO", "Validating target device safety...")
            device_risk = self.safety_validator.validate_device_safety(self.target_device)
            
            if device_risk.overall_risk == ValidationResult.BLOCKED:
                error_msg = (
                    f"🚫 OPERATION BLOCKED FOR SAFETY 🚫\n"
                    f"Device: {self.target_device}\n"
                    f"Risk Factors: {', '.join(device_risk.risk_factors)}\n"
                    f"This device is not safe to use for storage device creation."
                )
                self._log_message("ERROR", error_msg)
                self.operation_completed.emit(False, error_msg)
                return False
            
            # CRITICAL: Block DANGEROUS devices immediately - no exceptions!
            if device_risk.overall_risk == ValidationResult.DANGEROUS:
                error_msg = (
                    f"🚫 DANGEROUS DEVICE - OPERATION BLOCKED 🚫\n"
                    f"Device: {self.target_device} ({device_risk.size_gb:.1f}GB)\n"
                    f"Risk Factors: {', '.join(device_risk.risk_factors)}\n"
                    f"This device poses too high a risk for automated operations.\n"
                    f"Use extreme caution and manual verification if you must proceed."
                )
                self._log_message("ERROR", error_msg)
                self.operation_completed.emit(False, error_msg)
                return False
            
            # Log device validation results
            self._log_message("INFO", f"Device validation: {device_risk.overall_risk.value}")
            self._log_message("INFO", f"Device size: {device_risk.size_gb:.1f}GB")
            self._log_message("INFO", f"Removable: {device_risk.is_removable}")
            self._log_message("INFO", f"System disk: {device_risk.is_system_disk}")
            
            # 2. Prerequisites Validation
            self._log_message("INFO", "Validating system prerequisites...")
            prereq_checks = self.safety_validator.validate_prerequisites()
            
            blocked_checks = [check for check in prereq_checks if check.result == ValidationResult.BLOCKED]
            if blocked_checks:
                error_msg = "❌ MISSING PREREQUISITES:\n" + "\n".join(
                    f"• {check.name}: {check.message}" for check in blocked_checks
                )
                self._log_message("ERROR", error_msg)
                self.operation_completed.emit(False, error_msg)
                return False
            
            # 3. Source Files Validation
            self._log_message("INFO", "Validating source files...")
            source_checks = self.safety_validator.validate_source_files(self.source_files)
            
            blocked_sources = [check for check in source_checks if check.result == ValidationResult.BLOCKED]
            if blocked_sources:
                error_msg = "❌ SOURCE FILE ISSUES:\n" + "\n".join(
                    f"• {check.name}: {check.message}" for check in blocked_sources
                )
                self._log_message("ERROR", error_msg)
                self.operation_completed.emit(False, error_msg)
                return False
            
            # 4. Hardware Profile Compatibility
            if (self.hardware_profile and 
                self.hardware_profile.model not in self.recipe.hardware_profiles and 
                "generic" not in self.recipe.hardware_profiles):
                self._log_message("WARNING", f"Hardware profile {self.hardware_profile.model} not officially supported for this recipe")
            
            # 5. Final Safety Summary
            self._log_message("INFO", "✅ All safety validations passed")
            self._log_message("INFO", f"Target: {self.target_device} ({device_risk.size_gb:.1f}GB)")
            self._log_message("INFO", f"Recipe: {self.recipe.name}")
            self._log_message("INFO", f"Files: {len(self.source_files)} source files validated")
            
            return True
            
        except Exception as e:
            error_msg = f"Critical validation error: {str(e)}"
            self.logger.error(error_msg)
            self._log_message("ERROR", error_msg)
            self.operation_completed.emit(False, error_msg)
            return False
    
    def _prepare_target_device(self) -> bool:
        """Prepare target device for partitioning"""
        try:
            self._log_message("INFO", f"Preparing device {self.target_device}")
            
            # Unmount all partitions on the device
            self._unmount_device_partitions()
            
            # Clear any existing partition table
            if platform.system() == "Linux":
                result = subprocess.run(
                    ['sudo', 'wipefs', '-a', self.target_device],
                    capture_output=True, text=True, check=False
                )
                if result.returncode != 0:
                    self._log_message("WARNING", f"Could not wipe filesystem signatures: {result.stderr}")
            
            self._log_message("INFO", "Device preparation completed")
            return True
            
        except Exception as e:
            self._log_message("ERROR", f"Error preparing device: {e}")
            return False
    
    def _create_partition_scheme(self) -> bool:
        """Create partition scheme based on recipe"""
        try:
            if not self.recipe:
                self._log_message("ERROR", "No recipe available")
                return False
                
            system = platform.system()
            scheme = self.recipe.partition_scheme
            
            self._log_message("INFO", f"Creating {scheme.value.upper()} partition scheme")
            
            if system == "Linux":
                return self._create_partitions_linux()
            elif system == "Darwin":  # macOS
                return self._create_partitions_macos()
            elif system == "Windows":
                return self._create_partitions_windows()
            else:
                self._log_message("ERROR", f"Unsupported platform: {system}")
                return False
                
        except Exception as e:
            self._log_message("ERROR", f"Error creating partition scheme: {e}")
            return False
    
    def _create_partitions_linux(self) -> bool:
        """Create partitions on Linux using parted"""
        try:
            if not self.recipe:
                self._log_message("ERROR", "No recipe available")
                return False
                
            # Create partition table
            scheme_type = "gpt" if self.recipe.partition_scheme == PartitionScheme.GPT else "msdos"
            
            result = subprocess.run(
                ['sudo', 'parted', '-s', self.target_device, 'mklabel', scheme_type],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                self._log_message("ERROR", f"Failed to create partition table: {result.stderr}")
                return False
            
            # Add rollback operation for partition table creation
            self._partition_table_created = True
            self._add_rollback_operation(
                lambda: subprocess.run(
                    ['sudo', 'wipefs', '-a', self.target_device], 
                    capture_output=True, check=False
                )
            )
            self._log_message("INFO", "Added rollback operation for partition table")
            
            # Create partitions
            current_start = 1  # Start at 1MB
            
            for i, partition in enumerate(self.recipe.partitions, 1):
                if partition.size_mb == -1:  # Use remaining space
                    end = "100%"
                else:
                    end = f"{current_start + partition.size_mb}MB"
                
                # Create partition
                result = subprocess.run([
                    'sudo', 'parted', '-s', self.target_device, 'mkpart',
                    'primary', f"{current_start}MB", end
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    self._log_message("ERROR", f"Failed to create partition {i}: {result.stderr}")
                    return False
                
                # Set bootable flag if needed
                if partition.bootable:
                    subprocess.run([
                        'sudo', 'parted', '-s', self.target_device, 'set', str(i), 'boot', 'on'
                    ], capture_output=True, text=True)
                
                if partiti
(Content truncated due to size limit. Use line ranges to read remaining content)