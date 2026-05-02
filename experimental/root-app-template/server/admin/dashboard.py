"""
Admin Dashboard Backend Routes
Monitoring active installations, backup history, and driver database management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from flask import Blueprint, request, jsonify, current_app

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ============================================================================
# DATA MODELS
# ============================================================================

class AdminRole(Enum):
    """Admin role levels"""
    VIEWER = "viewer"  # Read-only access
    OPERATOR = "operator"  # Can manage installations
    ADMIN = "admin"  # Full access


@dataclass
class AdminUser:
    """Admin user"""
    user_id: str
    username: str
    email: str
    role: AdminRole
    created_at: str
    last_login: Optional[str] = None
    is_active: bool = True


@dataclass
class InstallationMetrics:
    """Installation metrics"""
    total_installations: int
    successful: int
    failed: int
    in_progress: int
    success_rate: float
    avg_duration_seconds: float
    total_data_written_gb: float


@dataclass
class SystemMetrics:
    """System metrics"""
    api_uptime_hours: float
    total_requests: int
    avg_response_time_ms: float
    error_rate: float
    active_connections: int
    database_size_mb: float
    backup_storage_used_gb: float


@dataclass
class DriverUpdate:
    """Driver database update"""
    update_id: str
    timestamp: str
    driver_package_id: str
    mac_models_added: int
    mac_models_updated: int
    components_updated: int
    status: str  # 'pending', 'applied', 'failed'


# ============================================================================
# AUTHENTICATION & AUTHORIZATION
# ============================================================================

def require_admin_role(required_role: AdminRole):
    """Decorator to require admin role"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            # Extract auth token from request
            auth_header = request.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                return jsonify({
                    'status': 'error',
                    'error_code': 'UNAUTHORIZED',
                    'message': 'Missing or invalid authorization token'
                }), 401
            
            token = auth_header[7:]
            
            # Verify token and get user (mock implementation)
            user = verify_admin_token(token)
            if not user:
                return jsonify({
                    'status': 'error',
                    'error_code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired token'
                }), 401
            
            # Check role
            if not has_required_role(user.role, required_role):
                return jsonify({
                    'status': 'error',
                    'error_code': 'INSUFFICIENT_PERMISSIONS',
                    'message': f'Required role: {required_role.value}'
                }), 403
            
            # Pass user to route
            kwargs['admin_user'] = user
            return f(*args, **kwargs)
        
        wrapper.__name__ = f.__name__
        return wrapper
    
    return decorator


def verify_admin_token(token: str) -> Optional[AdminUser]:
    """Verify admin token and return user (mock implementation)"""
    # In production, verify JWT token and fetch from database
    # For now, return mock user if token is valid format
    
    if len(token) < 20:
        return None
    
    # Mock user for demonstration
    return AdminUser(
        user_id='admin_001',
        username='admin',
        email='admin@phoenixdrive.local',
        role=AdminRole.ADMIN,
        created_at=datetime.utcnow().isoformat(),
        last_login=datetime.utcnow().isoformat()
    )


def has_required_role(user_role: AdminRole, required_role: AdminRole) -> bool:
    """Check if user has required role"""
    role_hierarchy = {
        AdminRole.VIEWER: 0,
        AdminRole.OPERATOR: 1,
        AdminRole.ADMIN: 2
    }
    return role_hierarchy[user_role] >= role_hierarchy[required_role]


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================

@admin_bp.route('/health', methods=['GET'])
@require_admin_role(AdminRole.VIEWER)
def admin_health(admin_user: AdminUser):
    """Admin health check"""
    return jsonify({
        'status': 'ok',
        'admin_user': asdict(admin_user),
        'timestamp': datetime.utcnow().isoformat()
    })


@admin_bp.route('/metrics/installations', methods=['GET'])
@require_admin_role(AdminRole.VIEWER)
def get_installation_metrics(admin_user: AdminUser):
    """Get installation metrics"""
    
    # Mock metrics (in production, fetch from database)
    metrics = InstallationMetrics(
        total_installations=1247,
        successful=1189,
        failed=58,
        in_progress=3,
        success_rate=95.3,
        avg_duration_seconds=1245.0,
        total_data_written_gb=5847.3
    )
    
    return jsonify({
        'status': 'ok',
        'metrics': asdict(metrics)
    })


@admin_bp.route('/metrics/system', methods=['GET'])
@require_admin_role(AdminRole.VIEWER)
def get_system_metrics(admin_user: AdminUser):
    """Get system metrics"""
    
    # Mock metrics (in production, fetch from monitoring systems)
    metrics = SystemMetrics(
        api_uptime_hours=720.5,
        total_requests=45230,
        avg_response_time_ms=145.2,
        error_rate=0.8,
        active_connections=23,
        database_size_mb=2847.5,
        backup_storage_used_gb=125.3
    )
    
    return jsonify({
        'status': 'ok',
        'metrics': asdict(metrics)
    })


@admin_bp.route('/installations', methods=['GET'])
@require_admin_role(AdminRole.VIEWER)
def list_installations(admin_user: AdminUser):
    """List active installations"""
    
    # Query parameters
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    status_filter = request.args.get('status', None)
    
    # Mock installations (in production, fetch from database)
    installations = [
        {
            'installation_id': f'inst_{i:05d}',
            'mac_model': 'MacBook Pro 15" (2018)',
            'status': 'in_progress' if i % 10 == 0 else 'completed',
            'progress': 75 if i % 10 == 0 else 100,
            'started_at': (datetime.utcnow() - timedelta(hours=i)).isoformat(),
            'duration_seconds': 1245 if i % 10 != 0 else None,
            'components_completed': 5 if i % 10 == 0 else 6,
            'components_total': 6,
            'error_message': None
        }
        for i in range(1, limit + 1)
    ]
    
    return jsonify({
        'status': 'ok',
        'installations': installations,
        'total': 1247,
        'limit': limit,
        'offset': offset
    })


@admin_bp.route('/installations/<installation_id>', methods=['GET'])
@require_admin_role(AdminRole.VIEWER)
def get_installation_details(installation_id: str, admin_user: AdminUser):
    """Get installation details"""
    
    # Mock installation (in production, fetch from database)
    installation = {
        'installation_id': installation_id,
        'mac_model': 'MacBook Pro 15" (2018)',
        'mac_model_id': 'MacBookPro15,1',
        'status': 'completed',
        'progress': 100,
        'started_at': datetime.utcnow().isoformat(),
        'completed_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        'duration_seconds': 3600,
        'components': {
            'Chipset': {'status': 'completed', 'progress': 100, 'duration': 450},
            'GPU': {'status': 'completed', 'progress': 100, 'duration': 520},
            'Audio': {'status': 'completed', 'progress': 100, 'duration': 380},
            'Trackpad': {'status': 'completed', 'progress': 100, 'duration': 290},
            'Keyboard': {'status': 'completed', 'progress': 100, 'duration': 310},
            'Network': {'status': 'completed', 'progress': 100, 'duration': 250}
        },
        'backup_id': 'backup_001',
        'backup_size_mb': 2847,
        'error_message': None
    }
    
    return jsonify({
        'status': 'ok',
        'installation': installation
    })


@admin_bp.route('/backups', methods=['GET'])
@require_admin_role(AdminRole.VIEWER)
def list_backups(admin_user: AdminUser):
    """List driver backups"""
    
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Mock backups (in production, fetch from backup manager)
    backups = [
        {
            'backup_id': f'backup_{i:05d}',
            'timestamp': (datetime.utcnow() - timedelta(days=i)).isoformat(),
            'mac_model': 'MacBook Pro 15" (2018)',
            'driver_package_id': 'BootCampESD_6.1',
            'windows_version': 'Windows 11',
            'size_mb': 2847 + i * 10,
            'status': 'success',
            'components': 6
        }
        for i in range(1, limit + 1)
    ]
    
    return jsonify({
        'status': 'ok',
        'backups': backups,
        'total': 1247,
        'limit': limit,
        'offset': offset
    })


@admin_bp.route('/drivers/updates', methods=['GET'])
@require_admin_role(AdminRole.VIEWER)
def list_driver_updates(admin_user: AdminUser):
    """List driver database updates"""
    
    limit = request.args.get('limit', 20, type=int)
    
    # Mock updates (in production, fetch from database)
    updates = [
        {
            'update_id': f'update_{i:05d}',
            'timestamp': (datetime.utcnow() - timedelta(days=i)).isoformat(),
            'driver_package_id': f'BootCampESD_{6.0 + i * 0.1:.1f}',
            'mac_models_added': 5 + i,
            'mac_models_updated': 10 + i * 2,
            'components_updated': 6,
            'status': 'applied'
        }
        for i in range(1, limit + 1)
    ]
    
    return jsonify({
        'status': 'ok',
        'updates': updates
    })


@admin_bp.route('/drivers/update', methods=['POST'])
@require_admin_role(AdminRole.ADMIN)
def apply_driver_update(admin_user: AdminUser):
    """Apply driver database update"""
    
    data = request.get_json() or {}
    
    # Validate request
    if 'driver_package_id' not in data:
        return jsonify({
            'status': 'error',
            'error_code': 'MISSING_FIELD',
            'message': 'driver_package_id is required'
        }), 400
    
    # Mock update application
    update = {
        'update_id': f'update_{datetime.utcnow().timestamp()}',
        'timestamp': datetime.utcnow().isoformat(),
        'driver_package_id': data['driver_package_id'],
        'mac_models_added': 5,
        'mac_models_updated': 12,
        'components_updated': 6,
        'status': 'applied'
    }
    
    logger.info(f"Driver update applied: {update['update_id']} by {admin_user.username}")
    
    return jsonify({
        'status': 'ok',
        'update': update
    })


@admin_bp.route('/installations/<installation_id>/cancel', methods=['POST'])
@require_admin_role(AdminRole.OPERATOR)
def cancel_installation(installation_id: str, admin_user: AdminUser):
    """Cancel active installation"""
    
    # Mock cancellation
    logger.info(f"Installation cancelled: {installation_id} by {admin_user.username}")
    
    return jsonify({
        'status': 'ok',
        'message': f'Installation {installation_id} cancelled',
        'installation_id': installation_id
    })


@admin_bp.route('/backups/<backup_id>/delete', methods=['POST'])
@require_admin_role(AdminRole.ADMIN)
def delete_backup(backup_id: str, admin_user: AdminUser):
    """Delete backup"""
    
    # Mock deletion
    logger.info(f"Backup deleted: {backup_id} by {admin_user.username}")
    
    return jsonify({
        'status': 'ok',
        'message': f'Backup {backup_id} deleted',
        'backup_id': backup_id
    })


@admin_bp.route('/audit-log', methods=['GET'])
@require_admin_role(AdminRole.ADMIN)
def get_audit_log(admin_user: AdminUser):
    """Get audit log"""
    
    limit = request.args.get('limit', 50, type=int)
    
    # Mock audit log
    audit_log = [
        {
            'timestamp': (datetime.utcnow() - timedelta(minutes=i)).isoformat(),
            'action': ['installation_started', 'installation_completed', 'backup_created', 'driver_updated'][i % 4],
            'user': 'admin',
            'resource_id': f'inst_{i:05d}',
            'details': f'Action details for log entry {i}'
        }
        for i in range(1, limit + 1)
    ]
    
    return jsonify({
        'status': 'ok',
        'audit_log': audit_log,
        'total': 5000
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@admin_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'error_code': 'NOT_FOUND',
        'message': 'Resource not found'
    }), 404


@admin_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'status': 'error',
        'error_code': 'INTERNAL_ERROR',
        'message': 'Internal server error'
    }), 500
