"""
Admin Authentication and Authorization
JWT token generation, validation, and role-based access control
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

import jwt
from functools import wraps
from flask import request, jsonify, current_app

logger = logging.getLogger(__name__)


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


class AdminAuthManager:
    """Manage admin authentication and authorization"""
    
    def __init__(self, secret_key: Optional[str] = None):
        """Initialize auth manager"""
        self.secret_key = secret_key or os.getenv('ADMIN_SECRET_KEY', 'dev-secret-key-change-in-production')
        self.algorithm = 'HS256'
        self.token_expiry_hours = 24
        
        # Mock user database (in production, use real database)
        self.users: Dict[str, AdminUser] = {
            'admin_001': AdminUser(
                user_id='admin_001',
                username='admin',
                email='admin@phoenixdrive.local',
                role=AdminRole.ADMIN,
                created_at=datetime.utcnow().isoformat(),
                is_active=True
            ),
            'operator_001': AdminUser(
                user_id='operator_001',
                username='operator',
                email='operator@phoenixdrive.local',
                role=AdminRole.OPERATOR,
                created_at=datetime.utcnow().isoformat(),
                is_active=True
            ),
            'viewer_001': AdminUser(
                user_id='viewer_001',
                username='viewer',
                email='viewer@phoenixdrive.local',
                role=AdminRole.VIEWER,
                created_at=datetime.utcnow().isoformat(),
                is_active=True
            )
        }
    
    def generate_token(self, user_id: str, password: str) -> Optional[str]:
        """Generate JWT token for user"""
        
        # Validate credentials (mock implementation)
        user = self.users.get(user_id)
        if not user or not user.is_active:
            logger.warning(f"Login failed: invalid user {user_id}")
            return None
        
        # In production, verify password hash
        if password != 'admin':  # Mock password check
            logger.warning(f"Login failed: invalid password for {user_id}")
            return None
        
        # Create token payload
        payload = {
            'user_id': user.user_id,
            'username': user.username,
            'email': user.email,
            'role': user.role.value,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.token_expiry_hours)
        }
        
        try:
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"Token generated for user: {user_id}")
            return token
        
        except Exception as e:
            logger.error(f"Failed to generate token: {e}")
            return None
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def get_user(self, user_id: str) -> Optional[AdminUser]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    def has_role(self, user_role: AdminRole, required_role: AdminRole) -> bool:
        """Check if user has required role"""
        role_hierarchy = {
            AdminRole.VIEWER: 0,
            AdminRole.OPERATOR: 1,
            AdminRole.ADMIN: 2
        }
        return role_hierarchy[user_role] >= role_hierarchy[required_role]
    
    def update_last_login(self, user_id: str) -> None:
        """Update user's last login time"""
        if user_id in self.users:
            self.users[user_id].last_login = datetime.utcnow().isoformat()


# Global auth manager instance
_auth_manager: Optional[AdminAuthManager] = None


def get_auth_manager() -> AdminAuthManager:
    """Get or create auth manager instance"""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AdminAuthManager()
    return _auth_manager


def require_admin_auth(required_role: AdminRole = AdminRole.VIEWER):
    """Decorator to require admin authentication"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            auth_manager = get_auth_manager()
            
            # Extract token from Authorization header
            auth_header = request.headers.get('Authorization', '')
            
            if not auth_header.startswith('Bearer '):
                return jsonify({
                    'status': 'error',
                    'error_code': 'UNAUTHORIZED',
                    'message': 'Missing or invalid authorization token'
                }), 401
            
            token = auth_header[7:]
            
            # Verify token
            payload = auth_manager.verify_token(token)
            if not payload:
                return jsonify({
                    'status': 'error',
                    'error_code': 'INVALID_TOKEN',
                    'message': 'Invalid or expired token'
                }), 401
            
            # Check role
            user_role = AdminRole(payload['role'])
            if not auth_manager.has_role(user_role, required_role):
                return jsonify({
                    'status': 'error',
                    'error_code': 'INSUFFICIENT_PERMISSIONS',
                    'message': f'Required role: {required_role.value}'
                }), 403
            
            # Update last login
            auth_manager.update_last_login(payload['user_id'])
            
            # Pass user info to route
            kwargs['admin_user'] = payload
            return f(*args, **kwargs)
        
        return wrapper
    
    return decorator


# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

def create_auth_routes(app):
    """Create authentication routes"""
    
    @app.route('/api/admin/auth/login', methods=['POST'])
    def admin_login():
        """Admin login endpoint"""
        
        data = request.get_json() or {}
        
        # Validate request
        if 'username' not in data or 'password' not in data:
            return jsonify({
                'status': 'error',
                'error_code': 'MISSING_CREDENTIALS',
                'message': 'username and password are required'
            }), 400
        
        auth_manager = get_auth_manager()
        
        # Generate token
        token = auth_manager.generate_token(data['username'], data['password'])
        
        if not token:
            return jsonify({
                'status': 'error',
                'error_code': 'INVALID_CREDENTIALS',
                'message': 'Invalid username or password'
            }), 401
        
        # Get user info
        user = auth_manager.get_user(data['username'])
        
        return jsonify({
            'status': 'ok',
            'token': token,
            'user': {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'role': user.role.value
            },
            'expires_in': auth_manager.token_expiry_hours * 3600
        })
    
    @app.route('/api/admin/auth/verify', methods=['GET'])
    @require_admin_auth()
    def verify_token(admin_user: Dict[str, Any]):
        """Verify token endpoint"""
        
        return jsonify({
            'status': 'ok',
            'user': admin_user,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @app.route('/api/admin/auth/refresh', methods=['POST'])
    @require_admin_auth()
    def refresh_token(admin_user: Dict[str, Any]):
        """Refresh token endpoint"""
        
        auth_manager = get_auth_manager()
        
        # Generate new token
        token = auth_manager.generate_token(
            admin_user['user_id'],
            'admin'  # Mock password
        )
        
        if not token:
            return jsonify({
                'status': 'error',
                'error_code': 'TOKEN_GENERATION_FAILED',
                'message': 'Failed to generate new token'
            }), 500
        
        return jsonify({
            'status': 'ok',
            'token': token,
            'expires_in': auth_manager.token_expiry_hours * 3600
        })
    
    @app.route('/api/admin/auth/logout', methods=['POST'])
    @require_admin_auth()
    def logout(admin_user: Dict[str, Any]):
        """Logout endpoint"""
        
        logger.info(f"User logged out: {admin_user['username']}")
        
        return jsonify({
            'status': 'ok',
            'message': 'Logged out successfully'
        })
