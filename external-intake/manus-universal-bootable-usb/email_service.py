"""
Email Notification Service for Admin Alerts
Sends email notifications for installation completion, failures, and system health warnings
"""

import logging
import os
import smtplib
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Notification types"""
    INSTALLATION_COMPLETED = "installation_completed"
    INSTALLATION_FAILED = "installation_failed"
    SYSTEM_HEALTH_WARNING = "system_health_warning"
    SYSTEM_HEALTH_CRITICAL = "system_health_critical"
    BACKUP_CREATED = "backup_created"
    DRIVER_UPDATE_AVAILABLE = "driver_update_available"
    HIGH_ERROR_RATE = "high_error_rate"
    API_DOWNTIME = "api_downtime"


@dataclass
class EmailNotification:
    """Email notification"""
    recipient: str
    notification_type: NotificationType
    subject: str
    body: str
    html_body: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class EmailService:
    """Send email notifications"""
    
    def __init__(
        self,
        smtp_server: str = None,
        smtp_port: int = 587,
        sender_email: str = None,
        sender_password: str = None,
        use_tls: bool = True
    ):
        """Initialize email service"""
        
        # Get configuration from environment or parameters
        self.smtp_server = smtp_server or os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = smtp_port or int(os.getenv('SMTP_PORT', '587'))
        self.sender_email = sender_email or os.getenv('SENDER_EMAIL', 'noreply@phoenixdrive.local')
        self.sender_password = sender_password or os.getenv('SENDER_PASSWORD', '')
        self.use_tls = use_tls
        
        self.enabled = bool(self.sender_password)
        
        if not self.enabled:
            logger.warning("Email service disabled: SENDER_PASSWORD not configured")
        else:
            logger.info(f"Email service configured: {self.smtp_server}:{self.smtp_port}")
    
    def send_notification(self, notification: EmailNotification) -> bool:
        """Send email notification"""
        
        if not self.enabled:
            logger.debug(f"Email service disabled, skipping notification: {notification.subject}")
            return False
        
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = notification.subject
            message['From'] = self.sender_email
            message['To'] = notification.recipient
            message['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            # Attach text body
            text_part = MIMEText(notification.body, 'plain')
            message.attach(text_part)
            
            # Attach HTML body if provided
            if notification.html_body:
                html_part = MIMEText(notification.html_body, 'html')
                message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            logger.info(f"Email sent: {notification.subject} to {notification.recipient}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def send_installation_completed(
        self,
        recipient: str,
        installation_id: str,
        mac_model: str,
        duration_seconds: float
    ) -> bool:
        """Send installation completed notification"""
        
        duration_minutes = int(duration_seconds / 60)
        
        subject = f"Installation Completed: {mac_model}"
        
        body = f"""Installation Completed

Installation ID: {installation_id}
Mac Model: {mac_model}
Duration: {duration_minutes} minutes
Status: SUCCESS

The Boot Camp driver installation has completed successfully.

---
Bobby's PhoenixDrive Admin System
"""
        
        html_body = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #2ecc71;">Installation Completed</h2>
    
    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Installation ID</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">{installation_id}</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Mac Model</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">{mac_model}</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Duration</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">{duration_minutes} minutes</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Status</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;"><span style="color: #2ecc71; font-weight: bold;">SUCCESS</span></td>
      </tr>
    </table>
    
    <p>The Boot Camp driver installation has completed successfully.</p>
    
    <hr style="margin: 20px 0;">
    <p style="font-size: 12px; color: #999;">Bobby's PhoenixDrive Admin System</p>
  </body>
</html>
"""
        
        notification = EmailNotification(
            recipient=recipient,
            notification_type=NotificationType.INSTALLATION_COMPLETED,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        return self.send_notification(notification)
    
    def send_installation_failed(
        self,
        recipient: str,
        installation_id: str,
        mac_model: str,
        error_message: str
    ) -> bool:
        """Send installation failed notification"""
        
        subject = f"Installation Failed: {mac_model}"
        
        body = f"""Installation Failed

Installation ID: {installation_id}
Mac Model: {mac_model}
Status: FAILED
Error: {error_message}

The Boot Camp driver installation has failed. Please check the admin dashboard for details.

---
Bobby's PhoenixDrive Admin System
"""
        
        html_body = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #e74c3c;">Installation Failed</h2>
    
    <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Installation ID</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">{installation_id}</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Mac Model</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">{mac_model}</td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Status</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;"><span style="color: #e74c3c; font-weight: bold;">FAILED</span></td>
      </tr>
      <tr>
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Error</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">{error_message}</td>
      </tr>
    </table>
    
    <p>The Boot Camp driver installation has failed. Please check the admin dashboard for details and recovery options.</p>
    
    <hr style="margin: 20px 0;">
    <p style="font-size: 12px; color: #999;">Bobby's PhoenixDrive Admin System</p>
  </body>
</html>
"""
        
        notification = EmailNotification(
            recipient=recipient,
            notification_type=NotificationType.INSTALLATION_FAILED,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        return self.send_notification(notification)
    
    def send_system_health_warning(
        self,
        recipient: str,
        warning_type: str,
        message: str,
        details: Dict[str, Any]
    ) -> bool:
        """Send system health warning notification"""
        
        subject = f"System Health Warning: {warning_type}"
        
        details_str = "\n".join([f"  {k}: {v}" for k, v in details.items()])
        
        body = f"""System Health Warning

Type: {warning_type}
Message: {message}

Details:
{details_str}

Please check the admin dashboard for more information.

---
Bobby's PhoenixDrive Admin System
"""
        
        html_body = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #f39c12;">System Health Warning</h2>
    
    <p><strong>Type:</strong> {warning_type}</p>
    <p><strong>Message:</strong> {message}</p>
    
    <h3>Details:</h3>
    <ul>
      {"".join([f"<li><strong>{k}:</strong> {v}</li>" for k, v in details.items()])}
    </ul>
    
    <p>Please check the admin dashboard for more information and recommended actions.</p>
    
    <hr style="margin: 20px 0;">
    <p style="font-size: 12px; color: #999;">Bobby's PhoenixDrive Admin System</p>
  </body>
</html>
"""
        
        notification = EmailNotification(
            recipient=recipient,
            notification_type=NotificationType.SYSTEM_HEALTH_WARNING,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        return self.send_notification(notification)
    
    def send_system_health_critical(
        self,
        recipient: str,
        critical_type: str,
        message: str,
        action_required: str
    ) -> bool:
        """Send critical system health notification"""
        
        subject = f"CRITICAL: System Health Alert - {critical_type}"
        
        body = f"""CRITICAL SYSTEM HEALTH ALERT

Type: {critical_type}
Message: {message}

Action Required:
{action_required}

This is a critical alert. Immediate action is required.

---
Bobby's PhoenixDrive Admin System
"""
        
        html_body = f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #fff; background-color: #e74c3c; padding: 20px;">
    <h2 style="color: #fff;">CRITICAL SYSTEM HEALTH ALERT</h2>
    
    <div style="background-color: rgba(0,0,0,0.2); padding: 15px; border-radius: 5px;">
      <p><strong>Type:</strong> {critical_type}</p>
      <p><strong>Message:</strong> {message}</p>
      
      <h3>Action Required:</h3>
      <p>{action_required}</p>
      
      <p style="margin-top: 20px; font-weight: bold;">This is a critical alert. Immediate action is required.</p>
    </div>
    
    <hr style="margin: 20px 0; border-color: rgba(255,255,255,0.3);">
    <p style="font-size: 12px; color: rgba(255,255,255,0.7);">Bobby's PhoenixDrive Admin System</p>
  </body>
</html>
"""
        
        notification = EmailNotification(
            recipient=recipient,
            notification_type=NotificationType.SYSTEM_HEALTH_CRITICAL,
            subject=subject,
            body=body,
            html_body=html_body
        )
        
        return self.send_notification(notification)


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


def init_email_service(
    smtp_server: str = None,
    smtp_port: int = 587,
    sender_email: str = None,
    sender_password: str = None
) -> EmailService:
    """Initialize email service"""
    global _email_service
    _email_service = EmailService(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        sender_email=sender_email,
        sender_password=sender_password
    )
    return _email_service
