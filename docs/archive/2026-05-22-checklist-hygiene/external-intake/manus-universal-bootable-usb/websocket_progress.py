"""
WebSocket Progress Streaming for Boot Camp Driver Installation
Real-time updates for installation progress, component status, and error handling
"""

import logging
from typing import Dict, Callable, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class InstallationStage(Enum):
    """Installation stages"""
    INITIALIZING = "initializing"
    BACKING_UP = "backing_up"
    DOWNLOADING = "downloading"
    EXTRACTING = "extracting"
    INSTALLING_CHIPSET = "installing_chipset"
    INSTALLING_GPU = "installing_gpu"
    INSTALLING_AUDIO = "installing_audio"
    INSTALLING_TRACKPAD = "installing_trackpad"
    INSTALLING_KEYBOARD = "installing_keyboard"
    INSTALLING_NETWORK = "installing_network"
    UPDATING_DEVICES = "updating_devices"
    FINALIZING = "finalizing"
    COMPLETE = "complete"
    ERROR = "error"


class ComponentStatus(Enum):
    """Component installation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ComponentProgress:
    """Progress for a single component"""
    name: str
    status: ComponentStatus
    progress: float  # 0-100
    error_message: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None


@dataclass
class InstallationProgress:
    """Overall installation progress"""
    installation_id: str
    stage: InstallationStage
    overall_progress: float  # 0-100
    stage_progress: float  # 0-100
    components: Dict[str, ComponentProgress]
    current_operation: str
    speed_mbps: Optional[float] = None
    eta_seconds: Optional[int] = None
    timestamp: str = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class ProgressTracker:
    """Track and emit installation progress"""
    
    def __init__(self, installation_id: str, emit_callback: Callable):
        """Initialize progress tracker"""
        self.installation_id = installation_id
        self.emit_callback = emit_callback
        self.current_stage = InstallationStage.INITIALIZING
        self.overall_progress = 0.0
        self.stage_progress = 0.0
        self.components: Dict[str, ComponentProgress] = {}
        self.current_operation = "Initializing..."
        self.speed_mbps = 0.0
        self.eta_seconds = 0
        self.error_message = None
        
        # Define component order and weights
        self.component_order = [
            'Chipset',
            'GPU',
            'Audio',
            'Trackpad',
            'Keyboard',
            'Network'
        ]
        
        # Initialize components
        for component in self.component_order:
            self.components[component] = ComponentProgress(
                name=component,
                status=ComponentStatus.PENDING,
                progress=0.0
            )
    
    def update_stage(self, stage: InstallationStage, operation: str) -> None:
        """Update installation stage"""
        self.current_stage = stage
        self.current_operation = operation
        self.stage_progress = 0.0
        self._emit_progress()
    
    def update_component(
        self,
        component_name: str,
        status: ComponentStatus,
        progress: float = 0.0,
        error_message: Optional[str] = None
    ) -> None:
        """Update component progress"""
        
        if component_name not in self.components:
            logger.warning(f"Unknown component: {component_name}")
            return
        
        component = self.components[component_name]
        component.status = status
        component.progress = progress
        component.error_message = error_message
        
        if status == ComponentStatus.IN_PROGRESS and component.start_time is None:
            component.start_time = datetime.utcnow().isoformat()
        
        if status in [ComponentStatus.COMPLETED, ComponentStatus.FAILED, ComponentStatus.SKIPPED]:
            component.end_time = datetime.utcnow().isoformat()
            if component.start_time:
                start = datetime.fromisoformat(component.start_time)
                end = datetime.fromisoformat(component.end_time)
                component.duration_seconds = (end - start).total_seconds()
        
        self._update_overall_progress()
        self._emit_progress()
    
    def update_stage_progress(
        self,
        progress: float,
        operation: str,
        speed_mbps: Optional[float] = None,
        eta_seconds: Optional[int] = None
    ) -> None:
        """Update stage progress"""
        self.stage_progress = min(100.0, max(0.0, progress))
        self.current_operation = operation
        
        if speed_mbps is not None:
            self.speed_mbps = speed_mbps
        
        if eta_seconds is not None:
            self.eta_seconds = eta_seconds
        
        self._update_overall_progress()
        self._emit_progress()
    
    def set_error(self, error_message: str) -> None:
        """Set error state"""
        self.current_stage = InstallationStage.ERROR
        self.error_message = error_message
        self._emit_progress()
    
    def complete(self) -> None:
        """Mark installation as complete"""
        self.current_stage = InstallationStage.COMPLETE
        self.overall_progress = 100.0
        self.stage_progress = 100.0
        self._emit_progress()
    
    def _update_overall_progress(self) -> None:
        """Calculate overall progress based on components"""
        
        if not self.components:
            return
        
        total_progress = 0.0
        completed_count = 0
        
        for component in self.components.values():
            if component.status == ComponentStatus.COMPLETED:
                total_progress += 100.0
                completed_count += 1
            elif component.status == ComponentStatus.IN_PROGRESS:
                total_progress += component.progress
            elif component.status == ComponentStatus.SKIPPED:
                total_progress += 100.0
                completed_count += 1
            elif component.status == ComponentStatus.FAILED:
                # Failed components still count towards progress
                total_progress += component.progress
        
        self.overall_progress = total_progress / len(self.components)
    
    def _emit_progress(self) -> None:
        """Emit progress update via WebSocket"""
        
        try:
            progress_data = InstallationProgress(
                installation_id=self.installation_id,
                stage=self.current_stage,
                overall_progress=self.overall_progress,
                stage_progress=self.stage_progress,
                components={
                    name: asdict(comp)
                    for name, comp in self.components.items()
                },
                current_operation=self.current_operation,
                speed_mbps=self.speed_mbps if self.speed_mbps > 0 else None,
                eta_seconds=self.eta_seconds if self.eta_seconds > 0 else None,
                error_message=self.error_message
            )
            
            self.emit_callback('bootcamp_progress', asdict(progress_data))
        
        except Exception as e:
            logger.error(f"Failed to emit progress: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get progress summary"""
        
        completed = sum(1 for c in self.components.values() if c.status == ComponentStatus.COMPLETED)
        failed = sum(1 for c in self.components.values() if c.status == ComponentStatus.FAILED)
        skipped = sum(1 for c in self.components.values() if c.status == ComponentStatus.SKIPPED)
        
        return {
            'installation_id': self.installation_id,
            'stage': self.current_stage.value,
            'overall_progress': self.overall_progress,
            'components_total': len(self.components),
            'components_completed': completed,
            'components_failed': failed,
            'components_skipped': skipped,
            'components_pending': len(self.components) - completed - failed - skipped,
            'speed_mbps': self.speed_mbps,
            'eta_seconds': self.eta_seconds,
            'error_message': self.error_message
        }


class WebSocketProgressManager:
    """Manage WebSocket connections for progress streaming"""
    
    def __init__(self):
        """Initialize progress manager"""
        self.trackers: Dict[str, ProgressTracker] = {}
        self.client_subscriptions: Dict[str, set] = {}  # client_id -> set of installation_ids
    
    def create_tracker(
        self,
        installation_id: str,
        emit_callback: Callable
    ) -> ProgressTracker:
        """Create new progress tracker"""
        
        tracker = ProgressTracker(installation_id, emit_callback)
        self.trackers[installation_id] = tracker
        
        logger.info(f"Progress tracker created: {installation_id}")
        return tracker
    
    def get_tracker(self, installation_id: str) -> Optional[ProgressTracker]:
        """Get existing tracker"""
        return self.trackers.get(installation_id)
    
    def subscribe_client(self, client_id: str, installation_id: str) -> None:
        """Subscribe client to installation progress"""
        
        if client_id not in self.client_subscriptions:
            self.client_subscriptions[client_id] = set()
        
        self.client_subscriptions[client_id].add(installation_id)
        logger.info(f"Client {client_id} subscribed to {installation_id}")
    
    def unsubscribe_client(self, client_id: str, installation_id: str) -> None:
        """Unsubscribe client from installation progress"""
        
        if client_id in self.client_subscriptions:
            self.client_subscriptions[client_id].discard(installation_id)
            logger.info(f"Client {client_id} unsubscribed from {installation_id}")
    
    def get_client_subscriptions(self, client_id: str) -> set:
        """Get all installations client is subscribed to"""
        return self.client_subscriptions.get(client_id, set())
    
    def cleanup_tracker(self, installation_id: str) -> None:
        """Clean up tracker after installation completes"""
        
        if installation_id in self.trackers:
            del self.trackers[installation_id]
            logger.info(f"Progress tracker cleaned up: {installation_id}")
    
    def get_all_trackers(self) -> Dict[str, ProgressTracker]:
        """Get all active trackers"""
        return self.trackers.copy()
