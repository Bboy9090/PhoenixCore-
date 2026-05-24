"""
Sentry error tracking and monitoring integration
Captures exceptions, performance issues, and user feedback
"""

import os
import logging
from typing import Optional, Dict, Any
from flask import Flask, request
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

logger = logging.getLogger(__name__)


class SentryConfig:
    """Configuration for Sentry error tracking"""
    
    def __init__(self):
        self.dsn = os.getenv('SENTRY_DSN')
        self.environment = os.getenv('FLASK_ENV', 'development')
        self.traces_sample_rate = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1'))
        self.profiles_sample_rate = float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '0.1'))
        self.enabled = bool(self.dsn and self.environment == 'production')
    
    def is_enabled(self) -> bool:
        """Check if Sentry is enabled"""
        return self.enabled
    
    def get_dsn(self) -> Optional[str]:
        """Get Sentry DSN"""
        return self.dsn


def init_sentry(app: Flask) -> bool:
    """
    Initialize Sentry error tracking
    
    Args:
        app: Flask application instance
        
    Returns:
        True if Sentry was initialized, False otherwise
    """
    config = SentryConfig()
    
    if not config.is_enabled():
        logger.info("Sentry is disabled (no DSN or not production environment)")
        return False
    
    try:
        # Initialize Sentry SDK
        sentry_sdk.init(
            dsn=config.get_dsn(),
            integrations=[
                FlaskIntegration(),
                SqlalchemyIntegration(),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                ),
                RedisIntegration(),
            ],
            environment=config.environment,
            traces_sample_rate=config.traces_sample_rate,
            profiles_sample_rate=config.profiles_sample_rate,
            release=os.getenv('APP_VERSION', '1.0.0'),
            
            # Performance monitoring
            enable_tracing=True,
            
            # Capture local variables in stack traces
            with_locals=True,
            
            # Maximum breadcrumbs to capture
            max_breadcrumbs=100,
            
            # Request body logging
            include_request_body='medium',
            
            # Ignore specific exceptions
            ignore_errors=[
                'KeyboardInterrupt',
                'SystemExit',
            ],
            
            # Before send hook for filtering
            before_send=before_send_sentry,
            
            # Before breadcrumb hook
            before_breadcrumb=before_breadcrumb_sentry,
        )
        
        logger.info("Sentry error tracking initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        return False


def before_send_sentry(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Hook to filter events before sending to Sentry
    
    Args:
        event: Sentry event dictionary
        hint: Additional hint information
        
    Returns:
        Modified event or None to drop the event
    """
    
    # Don't send 4xx errors to Sentry (client errors)
    if 'response' in event:
        status_code = event['response'].get('status_code')
        if 400 <= status_code < 500:
            return None
    
    # Don't send 404 errors
    if event.get('exception'):
        exc_info = event['exception']['values'][0]
        if exc_info.get('type') == 'NotFound':
            return None
    
    # Filter sensitive data
    if 'request' in event:
        request_data = event['request']
        
        # Remove sensitive headers
        if 'headers' in request_data:
            sensitive_headers = [
                'Authorization',
                'Cookie',
                'X-API-Key',
                'X-Auth-Token',
            ]
            for header in sensitive_headers:
                request_data['headers'].pop(header, None)
        
        # Remove sensitive query parameters
        if 'query_string' in request_data:
            sensitive_params = ['password', 'token', 'api_key', 'secret']
            for param in sensitive_params:
                request_data['query_string'] = request_data['query_string'].replace(
                    f'{param}=', f'{param}=***'
                )
    
    return event


def before_breadcrumb_sentry(crumb: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Hook to filter breadcrumbs before sending to Sentry
    
    Args:
        crumb: Breadcrumb dictionary
        hint: Additional hint information
        
    Returns:
        Modified breadcrumb or None to drop it
    """
    
    # Ignore noisy breadcrumbs
    if crumb.get('category') in ['http.client', 'urllib3']:
        return None
    
    # Filter sensitive data from breadcrumbs
    if 'data' in crumb:
        data = crumb['data']
        
        # Remove sensitive query parameters
        if 'url' in data:
            sensitive_params = ['password', 'token', 'api_key', 'secret']
            for param in sensitive_params:
                data['url'] = data['url'].replace(
                    f'{param}=', f'{param}=***'
                )
    
    return crumb


def capture_exception(exception: Exception, level: str = 'error', **kwargs):
    """
    Manually capture an exception in Sentry
    
    Args:
        exception: Exception to capture
        level: Severity level (fatal, error, warning, info, debug)
        **kwargs: Additional context
    """
    if not SentryConfig().is_enabled():
        return
    
    sentry_sdk.capture_exception(exception, level=level, extra=kwargs)


def capture_message(message: str, level: str = 'info', **kwargs):
    """
    Manually capture a message in Sentry
    
    Args:
        message: Message to capture
        level: Severity level (fatal, error, warning, info, debug)
        **kwargs: Additional context
    """
    if not SentryConfig().is_enabled():
        return
    
    sentry_sdk.capture_message(message, level=level, extra=kwargs)


def set_user_context(user_id: str, email: Optional[str] = None, **kwargs):
    """
    Set user context for Sentry events
    
    Args:
        user_id: User identifier
        email: User email
        **kwargs: Additional user data
    """
    if not SentryConfig().is_enabled():
        return
    
    sentry_sdk.set_user({
        'id': user_id,
        'email': email,
        **kwargs
    })


def clear_user_context():
    """Clear user context from Sentry"""
    if not SentryConfig().is_enabled():
        return
    
    sentry_sdk.set_user(None)


def set_tag(key: str, value: str):
    """
    Set a tag for Sentry events
    
    Args:
        key: Tag key
        value: Tag value
    """
    if not SentryConfig().is_enabled():
        return
    
    sentry_sdk.set_tag(key, value)


def set_context(name: str, context: Dict[str, Any]):
    """
    Set context for Sentry events
    
    Args:
        name: Context name
        context: Context dictionary
    """
    if not SentryConfig().is_enabled():
        return
    
    sentry_sdk.set_context(name, context)


def add_breadcrumb(message: str, category: str = 'info', level: str = 'info', **kwargs):
    """
    Add a breadcrumb to Sentry
    
    Args:
        message: Breadcrumb message
        category: Breadcrumb category
        level: Breadcrumb level
        **kwargs: Additional data
    """
    if not SentryConfig().is_enabled():
        return
    
    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        data=kwargs
    )


def create_sentry_middleware(app: Flask):
    """
    Create middleware for automatic Sentry integration
    
    Args:
        app: Flask application instance
    """
    
    @app.before_request
    def before_request_sentry():
        """Set context before each request"""
        if not SentryConfig().is_enabled():
            return
        
        # Set request context
        set_context('request', {
            'method': request.method,
            'path': request.path,
            'remote_addr': request.remote_addr,
            'user_agent': request.user_agent.string,
        })
        
        # Add breadcrumb for request
        add_breadcrumb(
            message=f"{request.method} {request.path}",
            category='http.request',
            level='info',
            method=request.method,
            path=request.path,
        )
    
    @app.after_request
    def after_request_sentry(response):
        """Add response status to breadcrumb"""
        if not SentryConfig().is_enabled():
            return response
        
        # Add breadcrumb for response
        add_breadcrumb(
            message=f"Response: {response.status_code}",
            category='http.response',
            level='info' if response.status_code < 400 else 'warning',
            status_code=response.status_code,
        )
        
        return response
    
    @app.errorhandler(Exception)
    def handle_exception_sentry(error):
        """Handle exceptions with Sentry"""
        if not SentryConfig().is_enabled():
            raise error
        
        # Capture exception
        capture_exception(error, level='error')
        
        # Re-raise to let Flask handle it
        raise error


class SentryMetrics:
    """Helper class for tracking custom metrics in Sentry"""
    
    @staticmethod
    def track_build_started(build_id: str, recipe_id: str):
        """Track build start event"""
        set_tag('event', 'build_started')
        set_context('build', {
            'build_id': build_id,
            'recipe_id': recipe_id,
        })
        add_breadcrumb(
            message=f"Build started: {build_id}",
            category='build',
            level='info',
        )
    
    @staticmethod
    def track_build_completed(build_id: str, duration_seconds: float):
        """Track build completion event"""
        set_tag('event', 'build_completed')
        set_context('build', {
            'build_id': build_id,
            'duration_seconds': duration_seconds,
        })
        add_breadcrumb(
            message=f"Build completed: {build_id} ({duration_seconds}s)",
            category='build',
            level='info',
        )
    
    @staticmethod
    def track_build_failed(build_id: str, error_message: str):
        """Track build failure event"""
        set_tag('event', 'build_failed')
        set_context('build', {
            'build_id': build_id,
            'error_message': error_message,
        })
        add_breadcrumb(
            message=f"Build failed: {build_id}",
            category='build',
            level='error',
        )
    
    @staticmethod
    def track_hardware_detection(device_id: str, os_count: int):
        """Track hardware detection event"""
        set_tag('event', 'hardware_detected')
        set_context('hardware', {
            'device_id': device_id,
            'compatible_os_count': os_count,
        })
        add_breadcrumb(
            message=f"Hardware detected: {device_id} ({os_count} compatible OS)",
            category='hardware',
            level='info',
        )
    
    @staticmethod
    def track_recipe_validation(recipe_id: str, valid: bool, error_count: int = 0):
        """Track recipe validation event"""
        set_tag('event', 'recipe_validated')
        set_context('recipe', {
            'recipe_id': recipe_id,
            'valid': valid,
            'error_count': error_count,
        })
        add_breadcrumb(
            message=f"Recipe validated: {recipe_id} ({'valid' if valid else 'invalid'})",
            category='recipe',
            level='info' if valid else 'warning',
        )
