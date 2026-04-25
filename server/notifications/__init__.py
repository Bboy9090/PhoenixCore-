"""
Notifications module for Bobby's PhoenixDrive
Email alerts for admin notifications
"""

from .email_service import (
    EmailService,
    EmailNotification,
    NotificationType,
    get_email_service,
    init_email_service
)

__all__ = [
    'EmailService',
    'EmailNotification',
    'NotificationType',
    'get_email_service',
    'init_email_service'
]
