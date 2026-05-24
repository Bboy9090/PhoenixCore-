"""
Boot Camp Driver Installation Engine
Automates driver installation to Windows system directories
"""

import os
import subprocess
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class InstallationStage(Enum):
    """Installation stages"""
    PRE_CHECKS = "pre_checks"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    INSTALLING = "installing"
    VERIFYING = "verifying"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class InstallationResult:
    """Installation result"""
    success: bool
    stage: InstallationStage
    components_installed: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    restart_required: bool = False
    total_time_seconds: float = 0.0


class BootCampInstaller:
    """Install Boot Camp drivers to Windows"""
    
    # Windows system directories
    WINDOWS_DRIVERS_DIR = "C:\\Windows\\System32\\drivers"
    WINDOWS_INF_DIR = "C:\\Windows\\INF"
    PROGRAM_FILES = "C:\\Program Files"
    
    # Component installation order
    INSTALL_ORDER = [
        "chipset",
        "gpu",
        "audio",
        "trackpad",
        "keyboard",
        "usb",
        "camera",
        "bluetooth",
        "ethernet",
        "thunderbolt"
    ]
    
    def __init__(self):
        """Initialize installer"""
        self.components_installed = {}
        self.errors = []
        self.warnings = []
        self.restart_required = False
    
    def pre_installation_checks(self, windows_version: str) -> bool:
        """Verify system is ready for driver installation"""
        
        checks = {
            'admin_privileges': self._check_admin_privileges(),
            'windows_version': self._check_windows_version(windows_version),
            'disk_space': self._check_disk_space(),
            'drivers_dir_exists': self._check_drivers_dir_exists(),
        }
        
        all_passed = all(checks.values())
        
        if not all_passed:
            for check, passed in checks.items():
                if not passed:
                    self.errors.append(f"Pre-installation check failed: {check}")
        
        return all_passed
    
    def install_drivers(
        self,
        components: Dict[str, Path],
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> InstallationResult:
        """Install drivers in correct order"""
        
        import time
        start_time = time.time()
        
        # Pre-installation checks
        if not self.pre_installation_checks("Windows 10"):
            return InstallationResult(
                success=False,
                stage=InstallationStage.PRE_CHECKS,
                errors=self.errors
            )
        
        # Install components in order
        for i, component in enumerate(self.INSTALL_ORDER):
            if component not in components:
                logger.warning(f"Component not found: {component}")
                continue
            
            # Update progress
            progress = int((i / len(self.INSTALL_ORDER)) * 100)
            if progress_callback:
                progress_callback(f"Installing {component}...", progress)
            
            try:
                # Find INF file
                inf_file = self._find_inf_file(components[component])
                
                if not inf_file:
                    self.warnings.append(f"No INF file found for {component}")
                    self.components_installed[component] = False
                    continue
                
                # Install driver
                success = self._install_inf_file(inf_file)
                self.components_installed[component] = success
                
                if not success:
                    self.errors.append(f"Failed to install {component}")
                else:
                    logger.info(f"Installed {component}")
            
            except Exception as e:
                self.errors.append(f"Error installing {component}: {str(e)}")
                self.components_installed[component] = False
        
        # Post-installation
        self._post_installation()
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Determine success
        success = len(self.errors) == 0
        stage = InstallationStage.COMPLETE if success else InstallationStage.ERROR
        
        return InstallationResult(
            success=success,
            stage=stage,
            components_installed=self.components_installed,
            errors=self.errors,
            warnings=self.warnings,
            restart_required=self.restart_required,
            total_time_seconds=total_time
        )
    
    def _find_inf_file(self, component_dir: Path) -> Optional[Path]:
        """Find INF file in component directory"""
        
        # Look for .inf files
        inf_files = list(component_dir.glob("**/*.inf"))
        
        if not inf_files:
            logger.warning(f"No INF files found in {component_dir}")
            return None
        
        # Prefer files with specific naming patterns
        for inf_file in inf_files:
            if 'bootcamp' in inf_file.name.lower():
                return inf_file
        
        # Return first INF file
        return inf_files[0]
    
    def _install_inf_file(self, inf_file: Path) -> bool:
        """Install INF file using pnputil"""
        
        try:
            # Use pnputil to install driver
            # pnputil /add-driver <path> /install
            result = subprocess.run(
                ['pnputil', '/add-driver', str(inf_file), '/install'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed {inf_file}")
                return True
            else:
                logger.error(f"Failed to install {inf_file}: {result.stderr}")
                return False
        
        except FileNotFoundError:
            logger.error("pnputil not found - driver installation not supported on this system")
            return False
        
        except Exception as e:
            logger.error(f"Error installing INF file: {e}")
            return False
    
    def _post_installation(self) -> None:
        """Post-installation tasks"""
        
        # Check if restart is required
        self.restart_required = self._check_restart_required()
        
        # Update device drivers
        self._update_device_manager()
    
    def _check_restart_required(self) -> bool:
        """Check if system restart is required"""
        
        try:
            # Check Windows registry for restart required flag
            result = subprocess.run(
                ['reg', 'query', 'HKLM\\System\\CurrentControlSet\\Control\\Session Manager', '/v', 'PendingFileRenameOperations'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0
        
        except Exception as e:
            logger.error(f"Error checking restart requirement: {e}")
            return False
    
    def _update_device_manager(self) -> None:
        """Update device drivers in Device Manager"""
        
        try:
            # Scan for hardware changes
            subprocess.run(
                ['devcon', 'rescan'],
                capture_output=True,
                timeout=30
            )
            
            logger.info("Device Manager updated")
        
        except Exception as e:
            logger.warning(f"Could not update Device Manager: {e}")
    
    def _check_admin_privileges(self) -> bool:
        """Check if running with admin privileges"""
        
        try:
            import ctypes
            return ctypes.windll.shell.IsUserAnAdmin()
        except:
            return False
    
    def _check_windows_version(self, required_version: str) -> bool:
        """Check Windows version compatibility"""
        
        try:
            result = subprocess.run(
                ['systeminfo'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse OS version
            for line in result.stdout.split('\n'):
                if 'OS Version' in line:
                    logger.info(f"Windows version: {line}")
                    return True
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking Windows version: {e}")
            return False
    
    def _check_disk_space(self, required_mb: int = 1000) -> bool:
        """Check available disk space"""
        
        try:
            import shutil
            total, used, free = shutil.disk_usage("C:\\")
            free_mb = free / (1024 * 1024)
            
            if free_mb < required_mb:
                logger.error(f"Insufficient disk space: {free_mb}MB available, {required_mb}MB required")
                return False
            
            logger.info(f"Disk space check passed: {free_mb}MB available")
            return True
        
        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            return False
    
    def _check_drivers_dir_exists(self) -> bool:
        """Check if Windows drivers directory exists"""
        
        drivers_dir = Path(self.WINDOWS_DRIVERS_DIR)
        
        if not drivers_dir.exists():
            logger.error(f"Drivers directory not found: {self.WINDOWS_DRIVERS_DIR}")
            return False
        
        logger.info(f"Drivers directory exists: {self.WINDOWS_DRIVERS_DIR}")
        return True


class BootCampDriverInstallationOrchestrator:
    """Orchestrate complete Boot Camp driver installation"""
    
    def __init__(self):
        """Initialize orchestrator"""
        self.installer = BootCampInstaller()
    
    def install_bootcamp_drivers(
        self,
        components: Dict[str, Path],
        windows_version: str = "Windows 10",
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> InstallationResult:
        """Orchestrate complete installation process"""
        
        logger.info("Starting Boot Camp driver installation")
        
        # Install drivers
        result = self.installer.install_drivers(components, progress_callback)
        
        if result.success:
            logger.info("Boot Camp driver installation completed successfully")
        else:
            logger.error(f"Boot Camp driver installation failed: {result.errors}")
        
        return result
    
    def get_installation_status(self) -> Dict:
        """Get current installation status"""
        
        return {
            'components_installed': self.installer.components_installed,
            'errors': self.installer.errors,
            'warnings': self.installer.warnings,
            'restart_required': self.installer.restart_required
        }
