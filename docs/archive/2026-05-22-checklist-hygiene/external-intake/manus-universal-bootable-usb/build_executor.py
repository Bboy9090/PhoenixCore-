"""
Build Executor - Execute USB build operations
"""

import logging
import time
from typing import Dict, Callable, Optional
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class BuildExecutor(QThread):
    """Executes USB build operations in background thread"""
    
    # Signals
    progress_updated = pyqtSignal(dict)  # Progress data
    build_completed = pyqtSignal(str)  # Success message
    build_error = pyqtSignal(str)  # Error message
    
    def __init__(self, recipe: Dict, device_path: str):
        super().__init__()
        self.recipe = recipe
        self.device_path = device_path
        self.is_cancelled = False
        self.is_paused = False
    
    def run(self):
        """Execute build process"""
        try:
            self._emit_progress({
                'type': 'progress',
                'stage': 'initializing',
                'stage_progress': 0,
                'overall_progress': 0,
                'message': 'Initializing build...'
            })
            
            # Stage 1: Validation (10%)
            self._emit_progress({
                'type': 'progress',
                'stage': 'validating',
                'stage_progress': 0,
                'overall_progress': 10,
                'message': 'Validating recipe and device...'
            })
            
            if not self._validate_build():
                return
            
            time.sleep(1)  # Simulate validation
            
            # Stage 2: Preparation (20%)
            self._emit_progress({
                'type': 'progress',
                'stage': 'preparing',
                'stage_progress': 50,
                'overall_progress': 20,
                'message': 'Preparing device...'
            })
            
            if not self._prepare_device():
                return
            
            time.sleep(1)  # Simulate preparation
            
            # Stage 3: Downloading (40%)
            self._emit_progress({
                'type': 'progress',
                'stage': 'downloading',
                'stage_progress': 0,
                'overall_progress': 30,
                'message': 'Downloading OS image...'
            })
            
            if not self._download_images():
                return
            
            # Stage 4: Writing (70%)
            self._emit_progress({
                'type': 'progress',
                'stage': 'writing',
                'stage_progress': 0,
                'overall_progress': 40,
                'message': 'Writing to USB device...'
            })
            
            if not self._write_images():
                return
            
            # Stage 5: Verifying (90%)
            self._emit_progress({
                'type': 'progress',
                'stage': 'verifying',
                'stage_progress': 0,
                'overall_progress': 80,
                'message': 'Verifying written data...'
            })
            
            if not self._verify_build():
                return
            
            # Stage 6: Finalizing (100%)
            self._emit_progress({
                'type': 'progress',
                'stage': 'finalizing',
                'stage_progress': 100,
                'overall_progress': 100,
                'message': 'Finalizing build...'
            })
            
            time.sleep(1)  # Simulate finalization
            
            # Build completed
            self._emit_progress({
                'type': 'completed',
                'message': 'Build completed successfully!'
            })
            
            self.build_completed.emit("USB build completed successfully! The device is ready to use.")
        
        except Exception as e:
            logger.error(f"Build error: {e}")
            self.build_error.emit(str(e))
    
    def _validate_build(self) -> bool:
        """Validate build configuration"""
        try:
            # Check recipe
            if not self.recipe:
                self.build_error.emit("Recipe is invalid")
                return False
            
            # Check device
            if not self.device_path:
                self.build_error.emit("Device path is invalid")
                return False
            
            # Simulate validation checks
            for i in range(5):
                if self.is_cancelled:
                    return False
                
                self._emit_progress({
                    'type': 'progress',
                    'stage': 'validating',
                    'stage_progress': (i + 1) * 20,
                    'overall_progress': 10,
                    'message': f'Validation check {i + 1}/5...'
                })
                
                time.sleep(0.5)
            
            return True
        
        except Exception as e:
            self.build_error.emit(f"Validation error: {str(e)}")
            return False
    
    def _prepare_device(self) -> bool:
        """Prepare device for writing"""
        try:
            self._emit_progress({
                'type': 'progress',
                'stage': 'preparing',
                'stage_progress': 50,
                'overall_progress': 20,
                'message': 'Unmounting device...'
            })
            
            time.sleep(1)  # Simulate unmounting
            
            if self.is_cancelled:
                return False
            
            self._emit_progress({
                'type': 'progress',
                'stage': 'preparing',
                'stage_progress': 100,
                'overall_progress': 25,
                'message': 'Device prepared'
            })
            
            return True
        
        except Exception as e:
            self.build_error.emit(f"Device preparation error: {str(e)}")
            return False
    
    def _download_images(self) -> bool:
        """Download OS images"""
        try:
            # Simulate downloading multiple images
            total_size = 5.0  # GB
            
            for progress in range(0, 101, 10):
                if self.is_cancelled:
                    return False
                
                downloaded = (progress / 100) * total_size
                
                self._emit_progress({
                    'type': 'progress',
                    'stage': 'downloading',
                    'stage_progress': progress,
                    'overall_progress': 30 + (progress / 100) * 10,
                    'message': f'Downloading: {downloaded:.1f}GB / {total_size:.1f}GB',
                    'speed_mbps': 50.0,
                    'data_written': f'{downloaded:.1f}GB / {total_size:.1f}GB'
                })
                
                time.sleep(0.5)
            
            return True
        
        except Exception as e:
            self.build_error.emit(f"Download error: {str(e)}")
            return False
    
    def _write_images(self) -> bool:
        """Write images to USB device"""
        try:
            # Simulate writing
            total_size = 15.0  # GB
            
            for progress in range(0, 101, 5):
                if self.is_cancelled:
                    return False
                
                while self.is_paused:
                    time.sleep(0.1)
                
                written = (progress / 100) * total_size
                speed = 100.0 + (progress * 0.5)  # Varying speed
                
                self._emit_progress({
                    'type': 'progress',
                    'stage': 'writing',
                    'stage_progress': progress,
                    'overall_progress': 40 + (progress / 100) * 30,
                    'message': f'Writing: {written:.1f}GB / {total_size:.1f}GB',
                    'speed_mbps': speed,
                    'data_written': f'{written:.1f}GB / {total_size:.1f}GB',
                    'eta_time': self._calculate_eta(total_size - written, speed)
                })
                
                time.sleep(0.3)
            
            return True
        
        except Exception as e:
            self.build_error.emit(f"Write error: {str(e)}")
            return False
    
    def _verify_build(self) -> bool:
        """Verify written data"""
        try:
            # Simulate verification
            for progress in range(0, 101, 10):
                if self.is_cancelled:
                    return False
                
                self._emit_progress({
                    'type': 'progress',
                    'stage': 'verifying',
                    'stage_progress': progress,
                    'overall_progress': 70 + (progress / 100) * 20,
                    'message': f'Verifying: {progress}% complete'
                })
                
                time.sleep(0.5)
            
            return True
        
        except Exception as e:
            self.build_error.emit(f"Verification error: {str(e)}")
            return False
    
    def _emit_progress(self, data: Dict):
        """Emit progress signal"""
        self.progress_updated.emit(data)
    
    def cancel_operation(self):
        """Cancel build operation"""
        self.is_cancelled = True
        logger.info("Build operation cancelled")
    
    def pause_operation(self):
        """Pause build operation"""
        self.is_paused = True
        logger.info("Build operation paused")
    
    def resume_operation(self):
        """Resume build operation"""
        self.is_paused = False
        logger.info("Build operation resumed")
    
    @staticmethod
    def _calculate_eta(remaining_gb: float, speed_mbps: float) -> str:
        """Calculate estimated time remaining"""
        if speed_mbps <= 0:
            return "--:--:--"
        
        remaining_mb = remaining_gb * 1024
        seconds = remaining_mb / speed_mbps
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
