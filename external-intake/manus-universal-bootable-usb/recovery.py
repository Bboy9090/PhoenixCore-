"""
Boot Camp Driver Rollback and Recovery System
Manages driver backups and restoration
"""

import os
import json
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import subprocess

logger = logging.getLogger(__name__)


@dataclass
class DriverBackup:
    """Driver backup metadata"""
    backup_id: str
    timestamp: str
    mac_model: str
    driver_package_id: str
    windows_version: str
    components: Dict[str, str]
    backup_size_bytes: int
    status: str  # 'success', 'partial', 'failed'


class DriverBackupManager:
    """Manage driver backups before installation"""
    
    def __init__(self, backup_dir: str = "/backup/bootcamp_drivers"):
        """Initialize backup manager"""
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backup_index_file = self.backup_dir / "backup_index.json"
        self.backup_index = self._load_backup_index()
    
    def _load_backup_index(self) -> Dict:
        """Load backup index from disk"""
        if self.backup_index_file.exists():
            try:
                with open(self.backup_index_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load backup index: {e}")
        return {}
    
    def _save_backup_index(self) -> None:
        """Save backup index to disk"""
        try:
            with open(self.backup_index_file, 'w') as f:
                json.dump(self.backup_index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save backup index: {e}")
    
    def create_backup(
        self,
        backup_id: str,
        mac_model: str,
        driver_package_id: str,
        windows_version: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Optional[DriverBackup]:
        """Create backup of current drivers"""
        
        try:
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)
            
            components = {}
            total_size = 0
            
            # Backup Windows drivers directory
            drivers_dir = Path("C:\\Windows\\System32\\drivers")
            if drivers_dir.exists():
                if progress_callback:
                    progress_callback("Backing up drivers...", 25)
                
                drivers_backup = backup_path / "drivers"
                shutil.copytree(drivers_dir, drivers_backup, dirs_exist_ok=True)
                
                total_size += sum(f.stat().st_size for f in drivers_backup.rglob('*') if f.is_file())
                components['drivers'] = str(drivers_backup)
            
            # Backup INF directory
            inf_dir = Path("C:\\Windows\\INF")
            if inf_dir.exists():
                if progress_callback:
                    progress_callback("Backing up INF files...", 50)
                
                inf_backup = backup_path / "inf"
                shutil.copytree(inf_dir, inf_backup, dirs_exist_ok=True)
                
                total_size += sum(f.stat().st_size for f in inf_backup.rglob('*') if f.is_file())
                components['inf'] = str(inf_backup)
            
            # Backup device registry
            if progress_callback:
                progress_callback("Backing up device registry...", 75)
            
            registry_backup = backup_path / "registry.reg"
            self._backup_device_registry(registry_backup)
            total_size += registry_backup.stat().st_size
            components['registry'] = str(registry_backup)
            
            # Create backup metadata
            backup = DriverBackup(
                backup_id=backup_id,
                timestamp=datetime.now().isoformat(),
                mac_model=mac_model,
                driver_package_id=driver_package_id,
                windows_version=windows_version,
                components=components,
                backup_size_bytes=total_size,
                status='success'
            )
            
            # Save backup metadata
            self.backup_index[backup_id] = asdict(backup)
            self._save_backup_index()
            
            if progress_callback:
                progress_callback("Backup complete", 100)
            
            logger.info(f"Backup created: {backup_id} ({total_size / (1024*1024):.2f} MB)")
            return backup
        
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def restore_backup(
        self,
        backup_id: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> bool:
        """Restore drivers from backup"""
        
        try:
            if backup_id not in self.backup_index:
                logger.error(f"Backup not found: {backup_id}")
                return False
            
            backup_data = self.backup_index[backup_id]
            backup_path = self.backup_dir / backup_id
            
            if not backup_path.exists():
                logger.error(f"Backup directory not found: {backup_path}")
                return False
            
            # Restore drivers
            drivers_backup = backup_path / "drivers"
            if drivers_backup.exists():
                if progress_callback:
                    progress_callback("Restoring drivers...", 25)
                
                drivers_dir = Path("C:\\Windows\\System32\\drivers")
                shutil.rmtree(drivers_dir, ignore_errors=True)
                shutil.copytree(drivers_backup, drivers_dir)
            
            # Restore INF files
            inf_backup = backup_path / "inf"
            if inf_backup.exists():
                if progress_callback:
                    progress_callback("Restoring INF files...", 50)
                
                inf_dir = Path("C:\\Windows\\INF")
                shutil.rmtree(inf_dir, ignore_errors=True)
                shutil.copytree(inf_backup, inf_dir)
            
            # Restore registry
            registry_backup = backup_path / "registry.reg"
            if registry_backup.exists():
                if progress_callback:
                    progress_callback("Restoring registry...", 75)
                
                self._restore_device_registry(registry_backup)
            
            # Update device drivers
            if progress_callback:
                progress_callback("Updating device drivers...", 90)
            
            self._update_device_manager()
            
            if progress_callback:
                progress_callback("Restoration complete", 100)
            
            logger.info(f"Backup restored: {backup_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    def list_backups(self) -> List[DriverBackup]:
        """List all available backups"""
        backups = []
        for backup_id, backup_data in self.backup_index.items():
            try:
                backup = DriverBackup(**backup_data)
                backups.append(backup)
            except Exception as e:
                logger.error(f"Failed to parse backup: {e}")
        
        return sorted(backups, key=lambda b: b.timestamp, reverse=True)
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete backup"""
        
        try:
            backup_path = self.backup_dir / backup_id
            
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            if backup_id in self.backup_index:
                del self.backup_index[backup_id]
                self._save_backup_index()
            
            logger.info(f"Backup deleted: {backup_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False
    
    def get_backup_size(self, backup_id: str) -> int:
        """Get backup size in bytes"""
        
        if backup_id not in self.backup_index:
            return 0
        
        backup_path = self.backup_dir / backup_id
        
        if not backup_path.exists():
            return 0
        
        total_size = 0
        for file_path in backup_path.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        
        return total_size
    
    def _backup_device_registry(self, backup_file: Path) -> None:
        """Backup device driver registry"""
        
        try:
            # Export device registry
            result = subprocess.run(
                ['reg', 'export', 'HKLM\\SYSTEM\\CurrentControlSet\\Enum\\PCI', str(backup_file)],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to backup registry: {result.stderr}")
        
        except Exception as e:
            logger.error(f"Error backing up registry: {e}")
    
    def _restore_device_registry(self, backup_file: Path) -> None:
        """Restore device driver registry"""
        
        try:
            # Import device registry
            result = subprocess.run(
                ['reg', 'import', str(backup_file)],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.warning(f"Failed to restore registry: {result.stderr}")
        
        except Exception as e:
            logger.error(f"Error restoring registry: {e}")
    
    def _update_device_manager(self) -> None:
        """Update device drivers in Device Manager"""
        
        try:
            subprocess.run(
                ['devcon', 'rescan'],
                capture_output=True,
                timeout=30
            )
            
            logger.info("Device Manager updated")
        
        except Exception as e:
            logger.warning(f"Could not update Device Manager: {e}")


class DriverRecoveryOrchestrator:
    """Orchestrate driver backup and recovery"""
    
    def __init__(self, backup_dir: str = "/backup/bootcamp_drivers"):
        """Initialize recovery orchestrator"""
        self.backup_manager = DriverBackupManager(backup_dir)
    
    def backup_before_installation(
        self,
        backup_id: str,
        mac_model: str,
        driver_package_id: str,
        windows_version: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Optional[DriverBackup]:
        """Create backup before driver installation"""
        
        logger.info("Creating backup before installation...")
        
        backup = self.backup_manager.create_backup(
            backup_id=backup_id,
            mac_model=mac_model,
            driver_package_id=driver_package_id,
            windows_version=windows_version,
            progress_callback=progress_callback
        )
        
        return backup
    
    def recover_from_backup(
        self,
        backup_id: str,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> bool:
        """Recover drivers from backup"""
        
        logger.info(f"Recovering from backup: {backup_id}")
        
        return self.backup_manager.restore_backup(
            backup_id=backup_id,
            progress_callback=progress_callback
        )
    
    def get_recovery_options(self) -> List[DriverBackup]:
        """Get list of available recovery options"""
        
        return self.backup_manager.list_backups()
    
    def cleanup_old_backups(self, keep_count: int = 5) -> None:
        """Clean up old backups, keeping only the most recent"""
        
        backups = self.backup_manager.list_backups()
        
        if len(backups) > keep_count:
            for backup in backups[keep_count:]:
                self.backup_manager.delete_backup(backup.backup_id)
                logger.info(f"Deleted old backup: {backup.backup_id}")
