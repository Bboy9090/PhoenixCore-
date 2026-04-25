"""
Admin module for Bobby's PhoenixDrive
Dashboard, authentication, and monitoring
"""

from .auth import AdminAuthManager, AdminRole, AdminUser, get_auth_manager, require_admin_auth, create_auth_routes
from .dashboard import admin_bp

__all__ = [
    'AdminAuthManager',
    'AdminRole',
    'AdminUser',
    'get_auth_manager',
    'require_admin_auth',
    'create_auth_routes',
    'admin_bp'
]
