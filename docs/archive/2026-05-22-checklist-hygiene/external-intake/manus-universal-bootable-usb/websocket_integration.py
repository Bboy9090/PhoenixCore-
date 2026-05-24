"""
WebSocket Integration for Real-Time Progress Streaming
Connects Flask-SocketIO with progress tracking for installations and builds
"""

import logging
import uuid
from typing import Dict, Callable, Optional, Any
from datetime import datetime

from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manage WebSocket connections and progress streaming"""
    
    def __init__(self, socketio: SocketIO):
        """Initialize WebSocket manager"""
        self.socketio = socketio
        self.active_installations: Dict[str, Dict[str, Any]] = {}
        self.client_subscriptions: Dict[str, set] = {}  # client_id -> set of installation_ids
        self.progress_trackers: Dict[str, Any] = {}  # installation_id -> ProgressTracker
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            client_id = request.sid
            logger.info(f"Client connected: {client_id}")
            emit('connection_response', {
                'status': 'connected',
                'client_id': client_id,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            client_id = request.sid
            logger.info(f"Client disconnected: {client_id}")
            
            # Clean up subscriptions
            if client_id in self.client_subscriptions:
                del self.client_subscriptions[client_id]
        
        @self.socketio.on('subscribe_installation')
        def handle_subscribe(data):
            """Handle subscription to installation progress"""
            client_id = request.sid
            installation_id = data.get('installation_id')
            
            if not installation_id:
                emit('error', {
                    'error_code': 'MISSING_INSTALLATION_ID',
                    'message': 'installation_id is required'
                })
                return
            
            # Add subscription
            if client_id not in self.client_subscriptions:
                self.client_subscriptions[client_id] = set()
            
            self.client_subscriptions[client_id].add(installation_id)
            
            # Join room for this installation
            join_room(f'installation_{installation_id}')
            
            logger.info(f"Client {client_id} subscribed to installation {installation_id}")
            
            emit('subscription_confirmed', {
                'status': 'subscribed',
                'installation_id': installation_id,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            # Send current progress if available
            if installation_id in self.active_installations:
                emit('progress_update', self.active_installations[installation_id])
        
        @self.socketio.on('unsubscribe_installation')
        def handle_unsubscribe(data):
            """Handle unsubscription from installation progress"""
            client_id = request.sid
            installation_id = data.get('installation_id')
            
            if not installation_id:
                return
            
            # Remove subscription
            if client_id in self.client_subscriptions:
                self.client_subscriptions[client_id].discard(installation_id)
            
            # Leave room
            leave_room(f'installation_{installation_id}')
            
            logger.info(f"Client {client_id} unsubscribed from installation {installation_id}")
            
            emit('unsubscription_confirmed', {
                'status': 'unsubscribed',
                'installation_id': installation_id,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        @self.socketio.on('get_progress')
        def handle_get_progress(data):
            """Get current progress for an installation"""
            installation_id = data.get('installation_id')
            
            if not installation_id:
                emit('error', {
                    'error_code': 'MISSING_INSTALLATION_ID',
                    'message': 'installation_id is required'
                })
                return
            
            if installation_id in self.active_installations:
                emit('progress_update', self.active_installations[installation_id])
            else:
                emit('error', {
                    'error_code': 'INSTALLATION_NOT_FOUND',
                    'message': f'Installation {installation_id} not found'
                })
    
    def start_installation(self, installation_id: str, mac_model: str, driver_package_id: str) -> None:
        """Start tracking a new installation"""
        
        self.active_installations[installation_id] = {
            'installation_id': installation_id,
            'mac_model': mac_model,
            'driver_package_id': driver_package_id,
            'status': 'initializing',
            'overall_progress': 0,
            'stage': 'initializing',
            'stage_progress': 0,
            'components': {
                'Chipset': {'status': 'pending', 'progress': 0},
                'GPU': {'status': 'pending', 'progress': 0},
                'Audio': {'status': 'pending', 'progress': 0},
                'Trackpad': {'status': 'pending', 'progress': 0},
                'Keyboard': {'status': 'pending', 'progress': 0},
                'Network': {'status': 'pending', 'progress': 0}
            },
            'current_operation': 'Initializing installation...',
            'speed_mbps': 0,
            'eta_seconds': 0,
            'started_at': datetime.utcnow().isoformat(),
            'error_message': None
        }
        
        logger.info(f"Installation started: {installation_id}")
        
        # Broadcast to all subscribers
        self.socketio.emit('installation_started', {
            'installation_id': installation_id,
            'mac_model': mac_model,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'installation_{installation_id}')
    
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
        
        inst = self.active_installations[installation_id]
        
        # Update overall progress
        inst['overall_progress'] = min(100, max(0, overall_progress))
        inst['stage'] = stage
        inst['stage_progress'] = min(100, max(0, stage_progress))
        
        # Update component if provided
        if component and component in inst['components']:
            inst['components'][component]['status'] = component_status or 'in_progress'
            inst['components'][component]['progress'] = component_progress or 0
        
        # Update operation details
        if current_operation:
            inst['current_operation'] = current_operation
        
        if speed_mbps is not None:
            inst['speed_mbps'] = speed_mbps
        
        if eta_seconds is not None:
            inst['eta_seconds'] = eta_seconds
        
        # Broadcast to all subscribers
        self.socketio.emit('progress_update', inst, room=f'installation_{installation_id}')
        
        logger.debug(f"Progress updated: {installation_id} - {overall_progress}%")
    
    def set_error(self, installation_id: str, error_message: str) -> None:
        """Set installation error state"""
        
        if installation_id not in self.active_installations:
            logger.warning(f"Installation not found: {installation_id}")
            return
        
        inst = self.active_installations[installation_id]
        inst['status'] = 'error'
        inst['error_message'] = error_message
        inst['overall_progress'] = inst['overall_progress']  # Keep current progress
        
        logger.error(f"Installation error: {installation_id} - {error_message}")
        
        # Broadcast to all subscribers
        self.socketio.emit('installation_error', {
            'installation_id': installation_id,
            'error_message': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'installation_{installation_id}')
    
    def complete_installation(self, installation_id: str) -> None:
        """Mark installation as complete"""
        
        if installation_id not in self.active_installations:
            logger.warning(f"Installation not found: {installation_id}")
            return
        
        inst = self.active_installations[installation_id]
        inst['status'] = 'completed'
        inst['overall_progress'] = 100
        inst['stage_progress'] = 100
        inst['completed_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"Installation completed: {installation_id}")
        
        # Broadcast to all subscribers
        self.socketio.emit('installation_completed', {
            'installation_id': installation_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'installation_{installation_id}')
        
        # Keep in history for a bit, then clean up
        # In production, save to database
    
    def get_installation_status(self, installation_id: str) -> Optional[Dict[str, Any]]:
        """Get current installation status"""
        return self.active_installations.get(installation_id)
    
    def get_active_installations(self) -> Dict[str, Dict[str, Any]]:
        """Get all active installations"""
        return self.active_installations.copy()
    
    def cleanup_installation(self, installation_id: str) -> None:
        """Clean up installation from active list"""
        if installation_id in self.active_installations:
            del self.active_installations[installation_id]
            logger.info(f"Installation cleaned up: {installation_id}")


# Global WebSocket manager instance
_ws_manager: Optional[WebSocketManager] = None


def get_websocket_manager(socketio: Optional[SocketIO] = None) -> WebSocketManager:
    """Get or create WebSocket manager instance"""
    global _ws_manager
    if _ws_manager is None:
        if socketio is None:
            raise ValueError("SocketIO instance required for initialization")
        _ws_manager = WebSocketManager(socketio)
    return _ws_manager


def init_websocket_manager(app, socketio: SocketIO) -> WebSocketManager:
    """Initialize WebSocket manager with Flask app"""
    global _ws_manager
    _ws_manager = WebSocketManager(socketio)
    logger.info("WebSocket manager initialized")
    return _ws_manager
