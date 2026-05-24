"""
WebSocket Client for Real-Time Progress Monitoring
Connects to backend API for live build progress updates
"""

import json
import logging
import threading
import time
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from enum import Enum

try:
    import websocket
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False

logger = logging.getLogger(__name__)


class BuildStatus(Enum):
    """Build status enumeration."""
    IDLE = "idle"
    PREPARING = "preparing"
    VALIDATING = "validating"
    DOWNLOADING = "downloading"
    BUILDING = "building"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BuildProgress:
    """Build progress data."""
    
    build_id: str
    status: BuildStatus
    overall_progress: float  # 0-100
    current_stage: str
    stage_progress: float  # 0-100
    current_component: str
    components_completed: int
    total_components: int
    speed_mbps: float
    eta_seconds: int
    data_written_mb: float
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "build_id": self.build_id,
            "status": self.status.value,
            "overall_progress": self.overall_progress,
            "current_stage": self.current_stage,
            "stage_progress": self.stage_progress,
            "current_component": self.current_component,
            "components_completed": self.components_completed,
            "total_components": self.total_components,
            "speed_mbps": self.speed_mbps,
            "eta_seconds": self.eta_seconds,
            "data_written_mb": self.data_written_mb,
            "error_message": self.error_message,
        }


class WebSocketClient:
    """WebSocket client for real-time progress monitoring."""
    
    def __init__(self, api_url: str = "ws://localhost:3000"):
        """Initialize WebSocket client."""
        if not HAS_WEBSOCKET:
            raise ImportError("websocket-client not installed. Install with: pip install websocket-client")
        
        self.api_url = api_url.replace("http://", "ws://").replace("https://", "wss://")
        self.ws = None
        self.connected = False
        self.thread = None
        self.running = False
        
        # Callbacks
        self.on_progress: Optional[Callable[[BuildProgress], None]] = None
        self.on_status_change: Optional[Callable[[BuildStatus], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_connected: Optional[Callable[[], None]] = None
        self.on_disconnected: Optional[Callable[[], None]] = None
    
    def connect(self, build_id: str, timeout: int = 10) -> bool:
        """Connect to WebSocket server."""
        try:
            ws_url = f"{self.api_url}/api/v1/builds/{build_id}/progress"
            logger.info(f"Connecting to {ws_url}")
            
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_ws_error,
                on_close=self._on_close,
            )
            
            # Run in background thread
            self.running = True
            self.thread = threading.Thread(target=self.ws.run_forever, daemon=True)
            self.thread.start()
            
            # Wait for connection
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            if self.connected:
                logger.info("WebSocket connected successfully")
                if self.on_connected:
                    self.on_connected()
                return True
            else:
                logger.error("WebSocket connection timeout")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            if self.on_error:
                self.on_error(str(e))
            return False
    
    def disconnect(self):
        """Disconnect from WebSocket server."""
        try:
            self.running = False
            if self.ws:
                self.ws.close()
            if self.thread:
                self.thread.join(timeout=5)
            self.connected = False
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")
    
    def send_message(self, message: Dict[str, Any]):
        """Send message to server."""
        try:
            if self.ws and self.connected:
                self.ws.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
    
    def pause_build(self, build_id: str):
        """Pause build."""
        self.send_message({
            "action": "pause",
            "build_id": build_id,
        })
    
    def resume_build(self, build_id: str):
        """Resume build."""
        self.send_message({
            "action": "resume",
            "build_id": build_id,
        })
    
    def cancel_build(self, build_id: str):
        """Cancel build."""
        self.send_message({
            "action": "cancel",
            "build_id": build_id,
        })
    
    def _on_open(self, ws):
        """Handle WebSocket open."""
        self.connected = True
        logger.info("WebSocket opened")
    
    def _on_message(self, ws, message: str):
        """Handle WebSocket message."""
        try:
            data = json.loads(message)
            
            # Parse progress data
            progress = BuildProgress(
                build_id=data.get("build_id"),
                status=BuildStatus(data.get("status", "idle")),
                overall_progress=data.get("overall_progress", 0),
                current_stage=data.get("current_stage", ""),
                stage_progress=data.get("stage_progress", 0),
                current_component=data.get("current_component", ""),
                components_completed=data.get("components_completed", 0),
                total_components=data.get("total_components", 0),
                speed_mbps=data.get("speed_mbps", 0),
                eta_seconds=data.get("eta_seconds", 0),
                data_written_mb=data.get("data_written_mb", 0),
                error_message=data.get("error_message"),
            )
            
            # Call progress callback
            if self.on_progress:
                self.on_progress(progress)
            
            # Call status change callback
            if self.on_status_change:
                self.on_status_change(progress.status)
                
        except Exception as e:
            logger.error(f"Failed to parse message: {e}")
            if self.on_error:
                self.on_error(str(e))
    
    def _on_ws_error(self, ws, error):
        """Handle WebSocket error."""
        logger.error(f"WebSocket error: {error}")
        if self.on_error:
            self.on_error(str(error))
    
    def _on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close."""
        self.connected = False
        logger.info("WebSocket closed")
        if self.on_disconnected:
            self.on_disconnected()


class ProgressMonitor:
    """Monitor build progress from multiple builds."""
    
    def __init__(self, api_url: str = "ws://localhost:3000"):
        """Initialize progress monitor."""
        self.api_url = api_url
        self.clients: Dict[str, WebSocketClient] = {}
        self.progress_data: Dict[str, BuildProgress] = {}
    
    def monitor_build(self, build_id: str) -> bool:
        """Start monitoring a build."""
        try:
            client = WebSocketClient(self.api_url)
            
            # Set callbacks
            client.on_progress = lambda p: self._on_progress(build_id, p)
            client.on_error = lambda e: self._on_error(build_id, e)
            
            # Connect
            if client.connect(build_id):
                self.clients[build_id] = client
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to monitor build {build_id}: {e}")
            return False
    
    def stop_monitoring(self, build_id: str):
        """Stop monitoring a build."""
        if build_id in self.clients:
            self.clients[build_id].disconnect()
            del self.clients[build_id]
    
    def get_progress(self, build_id: str) -> Optional[BuildProgress]:
        """Get current progress for build."""
        return self.progress_data.get(build_id)
    
    def _on_progress(self, build_id: str, progress: BuildProgress):
        """Handle progress update."""
        self.progress_data[build_id] = progress
        logger.info(
            f"Build {build_id}: {progress.overall_progress:.1f}% - "
            f"{progress.current_stage} ({progress.current_component})"
        )
    
    def _on_error(self, build_id: str, error: str):
        """Handle error."""
        logger.error(f"Build {build_id} error: {error}")
