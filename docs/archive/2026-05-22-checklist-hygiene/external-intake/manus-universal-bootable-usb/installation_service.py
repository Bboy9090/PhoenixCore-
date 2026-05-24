"""
Boot Camp Installation Service
Handles installation workflow with WebSocket progress streaming and email notifications
"""

import logging
import uuid
import threading
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

from server.websocket_integration import get_websocket_manager
from server.notifications import get_email_service

logger = logging.getLogger(__name__)


@dataclass
class InstallationConfig:
    """Installation configuration"""
    installation_id: str
    mac_model: str
    driver_package_id: str
    admin_email: Optional[str] = None
    notify_on_completion: bool = True
    notify_on_failure: bool = True
    backup_drivers: bool = True


class BootCampInstallationService:
    """Service for managing Boot Camp driver installations"""
    
    def __init__(self):
        """Initialize installation service"""
        self.active_installations: Dict[str, Dict[str, Any]] = {}
        self.ws_manager = None
        self.email_service = None
    
    def initialize(self):
        """Initialize service with WebSocket and email managers"""
        try:
            self.ws_manager = get_websocket_manager()
            self.email_service = get_email_service()
            logger.info("Installation service initialized with WebSocket and email")
        except Exception as e:
            logger.warning(f"Failed to initialize managers: {e}")
    
    def start_installation(self, config: InstallationConfig) -> str:
        """Start a new installation"""
        
        installation_id = config.installation_id or str(uuid.uuid4())
        
        # Initialize WebSocket tracking
        if self.ws_manager:
            self.ws_manager.start_installation(
                installation_id,
                config.mac_model,
                config.driver_package_id
            )
        
        # Store installation config
        self.active_installations[installation_id] = {
            'config': config,
            'status': 'initializing',
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': None,
            'error': None
        }
        
        logger.info(f"Installation started: {installation_id} for {config.mac_model}")
        
        return installation_id
    
    def update_progress(
        self,
        installation_id: str,
        overall_progress: float,
        stage: str,
        stage_progress: float,
        component: Optional[str] = None,
        component_status: Optional[str] = None,
        component_progress: Optional[float] = None,
        current_operation: Optional[str] = None,
        speed_mbps: Optional[float] = None,
        eta_seconds: Optional[int] = None
    ) -> None:
        """Update installation progress"""
        
        if installation_id not in self.active_installations:
            logger.warning(f"Installation not found: {installation_id}")
            return
        
        # Update WebSocket
        if self.ws_manager:
            self.ws_manager.update_progress(
                installation_id=installation_id,
                overall_progress=overall_progress,
                stage=stage,
                stage_progress=stage_progress,
                component=component,
                component_status=component_status,
                component_progress=component_progress,
                current_operation=current_operation,
                speed_mbps=speed_mbps,
                eta_seconds=eta_seconds
            )
        
        logger.debug(f"Progress updated: {installation_id} - {overall_progress}%")
    
    def complete_installation(self, installation_id: str) -> None:
        """Mark installation as complete and send notifications"""
        
        if installation_id not in self.active_installations:
            logger.warning(f"Installation not found: {installation_id}")
            return
        
        inst_data = self.active_installations[installation_id]
        config = inst_data['config']
        
        # Calculate duration
        started_at = datetime.fromisoformat(inst_data['started_at'])
        completed_at = datetime.utcnow()
        duration_seconds = (completed_at - started_at).total_seconds()
        
        inst_data['status'] = 'completed'
        inst_data['completed_at'] = completed_at.isoformat()
        
        # Update WebSocket
        if self.ws_manager:
            self.ws_manager.complete_installation(installation_id)
        
        # Send email notification
        if config.notify_on_completion and config.admin_email and self.email_service:
            self.email_service.send_installation_completed(
                recipient=config.admin_email,
                installation_id=installation_id,
                mac_model=config.mac_model,
                duration_seconds=duration_seconds
            )
        
        logger.info(f"Installation completed: {installation_id} in {duration_seconds:.1f}s")
    
    def fail_installation(self, installation_id: str, error_message: str) -> None:
        """Mark installation as failed and send notifications"""
        
        if installation_id not in self.active_installations:
            logger.warning(f"Installation not found: {installation_id}")
            return
        
        inst_data = self.active_installations[installation_id]
        config = inst_data['config']
        
        inst_data['status'] = 'failed'
        inst_data['error'] = error_message
        inst_data['completed_at'] = datetime.utcnow().isoformat()
        
        # Update WebSocket
        if self.ws_manager:
            self.ws_manager.set_error(installation_id, error_message)
        
        # Send email notification
        if config.notify_on_failure and config.admin_email and self.email_service:
            self.email_service.send_installation_failed(
                recipient=config.admin_email,
                installation_id=installation_id,
                mac_model=config.mac_model,
                error_message=error_message
            )
        
        logger.error(f"Installation failed: {installation_id} - {error_message}")
    
    def send_system_health_warning(
        self,
        admin_email: str,
        warning_type: str,
        message: str,
        details: Dict[str, Any]
    ) -> None:
        """Send system health warning to admin"""
        
        if self.email_service:
            self.email_service.send_system_health_warning(
                recipient=admin_email,
                warning_type=warning_type,
                message=message,
                details=details
            )
        
        logger.warning(f"System health warning: {warning_type} - {message}")
    
    def send_system_health_critical(
        self,
        admin_email: str,
        critical_type: str,
        message: str,
        action_required: str
    ) -> None:
        """Send critical system health alert to admin"""
        
        if self.email_service:
            self.email_service.send_system_health_critical(
                recipient=admin_email,
                critical_type=critical_type,
                message=message,
                action_required=action_required
            )
        
        logger.critical(f"System health critical: {critical_type} - {message}")
    
    def get_installation_status(self, installation_id: str) -> Optional[Dict[str, Any]]:
        """Get installation status"""
        return self.active_installations.get(installation_id)
    
    def get_active_installations(self) -> Dict[str, Dict[str, Any]]:
        """Get all active installations"""
        return self.active_installations.copy()


# Global installation service instance
_installation_service: Optional[BootCampInstallationService] = None


def get_installation_service() -> BootCampInstallationService:
    """Get or create installation service instance"""
    global _installation_service
    if _installation_service is None:
        _installation_service = BootCampInstallationService()
        _installation_service.initialize()
    return _installation_service


def init_installation_service() -> BootCampInstallationService:
    """Initialize installation service"""
    global _installation_service
    _installation_service = BootCampInstallationService()
    _installation_service.initialize()
    return _installation_service
