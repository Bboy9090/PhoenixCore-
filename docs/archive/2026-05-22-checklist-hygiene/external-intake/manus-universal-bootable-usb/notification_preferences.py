"""
Admin Notification Preferences
Manage admin notification settings and preferences
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    DASHBOARD = "dashboard"
    SMS = "sms"


class NotificationSeverity(Enum):
    """Notification severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class NotificationPreference:
    """Individual notification preference"""
    notification_type: str
    enabled: bool = True
    channels: List[NotificationChannel] = field(default_factory=lambda: [NotificationChannel.EMAIL])
    min_severity: NotificationSeverity = NotificationSeverity.INFO


@dataclass
class AdminNotificationPreferences:
    """Admin notification preferences"""
    admin_id: str
    email: str
    phone: Optional[str] = None
    
    # Notification type preferences
    installation_completed: NotificationPreference = field(default_factory=lambda: NotificationPreference(
        "installation_completed",
        enabled=True,
        channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD]
    ))
    installation_failed: NotificationPreference = field(default_factory=lambda: NotificationPreference(
        "installation_failed",
        enabled=True,
        channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD]
    ))
    system_health_warning: NotificationPreference = field(default_factory=lambda: NotificationPreference(
        "system_health_warning",
        enabled=True,
        channels=[NotificationChannel.EMAIL],
        min_severity=NotificationSeverity.WARNING
    ))
    system_health_critical: NotificationPreference = field(default_factory=lambda: NotificationPreference(
        "system_health_critical",
        enabled=True,
        channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
        min_severity=NotificationSeverity.CRITICAL
    ))
    high_error_rate: NotificationPreference = field(default_factory=lambda: NotificationPreference(
        "high_error_rate",
        enabled=True,
        channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD]
    ))
    driver_update_available: NotificationPreference = field(default_factory=lambda: NotificationPreference(
        "driver_update_available",
        enabled=True,
        channels=[NotificationChannel.DASHBOARD]
    ))
    
    # Alert thresholds
    error_rate_threshold: float = 5.0  # Percentage
    api_response_time_threshold: int = 5000  # Milliseconds
    failed_installation_threshold: int = 3  # Number of failures
    disk_space_warning_threshold: int = 10  # Percentage remaining
    
    # Quiet hours
    quiet_hours_enabled: bool = False
    quiet_hours_start: str = "22:00"  # HH:MM format
    quiet_hours_end: str = "08:00"  # HH:MM format
    quiet_hours_timezone: str = "UTC"
    
    # Digest settings
    daily_digest_enabled: bool = False
    daily_digest_time: str = "09:00"  # HH:MM format
    weekly_digest_enabled: bool = False
    weekly_digest_day: str = "Monday"  # Day of week
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class NotificationPreferencesManager:
    """Manage notification preferences"""
    
    def __init__(self):
        """Initialize preferences manager"""
        # In production, this would be a database
        self.preferences: Dict[str, AdminNotificationPreferences] = {}
    
    def create_preferences(
        self,
        admin_id: str,
        email: str,
        phone: Optional[str] = None
    ) -> AdminNotificationPreferences:
        """Create notification preferences for admin"""
        
        prefs = AdminNotificationPreferences(
            admin_id=admin_id,
            email=email,
            phone=phone
        )
        
        self.preferences[admin_id] = prefs
        logger.info(f"Notification preferences created for admin {admin_id}")
        
        return prefs
    
    def get_preferences(self, admin_id: str) -> Optional[AdminNotificationPreferences]:
        """Get notification preferences for admin"""
        return self.preferences.get(admin_id)
    
    def update_preferences(
        self,
        admin_id: str,
        updates: Dict[str, Any]
    ) -> Optional[AdminNotificationPreferences]:
        """Update notification preferences"""
        
        prefs = self.preferences.get(admin_id)
        if not prefs:
            logger.warning(f"Preferences not found for admin {admin_id}")
            return None
        
        # Update simple fields
        for key, value in updates.items():
            if key in ['email', 'phone', 'error_rate_threshold', 'api_response_time_threshold',
                      'failed_installation_threshold', 'disk_space_warning_threshold',
                      'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end',
                      'quiet_hours_timezone', 'daily_digest_enabled', 'daily_digest_time',
                      'weekly_digest_enabled', 'weekly_digest_day']:
                setattr(prefs, key, value)
        
        # Update notification type preferences
        for notif_type in ['installation_completed', 'installation_failed', 'system_health_warning',
                          'system_health_critical', 'high_error_rate', 'driver_update_available']:
            if notif_type in updates:
                notif_updates = updates[notif_type]
                notif_pref = getattr(prefs, notif_type)
                
                if 'enabled' in notif_updates:
                    notif_pref.enabled = notif_updates['enabled']
                
                if 'channels' in notif_updates:
                    notif_pref.channels = [
                        NotificationChannel(ch) if isinstance(ch, str) else ch
                        for ch in notif_updates['channels']
                    ]
                
                if 'min_severity' in notif_updates:
                    notif_pref.min_severity = NotificationSeverity(notif_updates['min_severity'])
        
        prefs.updated_at = datetime.utcnow().isoformat()
        logger.info(f"Notification preferences updated for admin {admin_id}")
        
        return prefs
    
    def should_notify(
        self,
        admin_id: str,
        notification_type: str,
        severity: NotificationSeverity = NotificationSeverity.INFO,
        channel: NotificationChannel = NotificationChannel.EMAIL
    ) -> bool:
        """Check if admin should be notified"""
        
        prefs = self.preferences.get(admin_id)
        if not prefs:
            return False
        
        # Get notification preference
        notif_pref = getattr(prefs, notification_type, None)
        if not notif_pref:
            return False
        
        # Check if enabled
        if not notif_pref.enabled:
            return False
        
        # Check severity
        severity_order = {
            NotificationSeverity.INFO: 0,
            NotificationSeverity.WARNING: 1,
            NotificationSeverity.ERROR: 2,
            NotificationSeverity.CRITICAL: 3
        }
        
        if severity_order.get(severity, 0) < severity_order.get(notif_pref.min_severity, 0):
            return False
        
        # Check channel
        if channel not in notif_pref.channels:
            return False
        
        return True
    
    def get_notification_channels(
        self,
        admin_id: str,
        notification_type: str
    ) -> List[NotificationChannel]:
        """Get notification channels for a notification type"""
        
        prefs = self.preferences.get(admin_id)
        if not prefs:
            return []
        
        notif_pref = getattr(prefs, notification_type, None)
        if not notif_pref or not notif_pref.enabled:
            return []
        
        return notif_pref.channels
    
    def to_dict(self, admin_id: str) -> Optional[Dict[str, Any]]:
        """Convert preferences to dictionary"""
        
        prefs = self.preferences.get(admin_id)
        if not prefs:
            return None
        
        return {
            'admin_id': prefs.admin_id,
            'email': prefs.email,
            'phone': prefs.phone,
            'installation_completed': {
                'enabled': prefs.installation_completed.enabled,
                'channels': [ch.value for ch in prefs.installation_completed.channels],
                'min_severity': prefs.installation_completed.min_severity.value
            },
            'installation_failed': {
                'enabled': prefs.installation_failed.enabled,
                'channels': [ch.value for ch in prefs.installation_failed.channels],
                'min_severity': prefs.installation_failed.min_severity.value
            },
            'system_health_warning': {
                'enabled': prefs.system_health_warning.enabled,
                'channels': [ch.value for ch in prefs.system_health_warning.channels],
                'min_severity': prefs.system_health_warning.min_severity.value
            },
            'system_health_critical': {
                'enabled': prefs.system_health_critical.enabled,
                'channels': [ch.value for ch in prefs.system_health_critical.channels],
                'min_severity': prefs.system_health_critical.min_severity.value
            },
            'high_error_rate': {
                'enabled': prefs.high_error_rate.enabled,
                'channels': [ch.value for ch in prefs.high_error_rate.channels],
                'min_severity': prefs.high_error_rate.min_severity.value
            },
            'driver_update_available': {
                'enabled': prefs.driver_update_available.enabled,
                'channels': [ch.value for ch in prefs.driver_update_available.channels],
                'min_severity': prefs.driver_update_available.min_severity.value
            },
            'error_rate_threshold': prefs.error_rate_threshold,
            'api_response_time_threshold': prefs.api_response_time_threshold,
            'failed_installation_threshold': prefs.failed_installation_threshold,
            'disk_space_warning_threshold': prefs.disk_space_warning_threshold,
            'quiet_hours_enabled': prefs.quiet_hours_enabled,
            'quiet_hours_start': prefs.quiet_hours_start,
            'quiet_hours_end': prefs.quiet_hours_end,
            'quiet_hours_timezone': prefs.quiet_hours_timezone,
            'daily_digest_enabled': prefs.daily_digest_enabled,
            'daily_digest_time': prefs.daily_digest_time,
            'weekly_digest_enabled': prefs.weekly_digest_enabled,
            'weekly_digest_day': prefs.weekly_digest_day,
            'created_at': prefs.created_at,
            'updated_at': prefs.updated_at
        }


# Global preferences manager instance
_preferences_manager: Optional[NotificationPreferencesManager] = None


def get_preferences_manager() -> NotificationPreferencesManager:
    """Get or create preferences manager instance"""
    global _preferences_manager
    if _preferences_manager is None:
        _preferences_manager = NotificationPreferencesManager()
    return _preferences_manager


def init_preferences_manager() -> NotificationPreferencesManager:
    """Initialize preferences manager"""
    global _preferences_manager
    _preferences_manager = NotificationPreferencesManager()
    return _preferences_manager
