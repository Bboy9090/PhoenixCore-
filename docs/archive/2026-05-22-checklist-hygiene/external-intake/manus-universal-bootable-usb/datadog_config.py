"""
Datadog performance monitoring and APM integration
Tracks API performance, build metrics, and system health
"""

import os
import logging
import time
from typing import Optional, Dict, Any, Callable
from functools import wraps
from flask import Flask, request, g
from datadog import initialize, api, statsd
from datadog.api import metrics

logger = logging.getLogger(__name__)


class DatadogConfig:
    """Configuration for Datadog monitoring"""
    
    def __init__(self):
        self.api_key = os.getenv('DATADOG_API_KEY')
        self.app_key = os.getenv('DATADOG_APP_KEY')
        self.site = os.getenv('DATADOG_SITE', 'datadoghq.com')
        self.environment = os.getenv('FLASK_ENV', 'development')
        self.service_name = os.getenv('DATADOG_SERVICE_NAME', 'phoenix-drive-api')
        self.version = os.getenv('APP_VERSION', '1.0.0')
        self.enabled = bool(self.api_key and self.environment == 'production')
    
    def is_enabled(self) -> bool:
        """Check if Datadog is enabled"""
        return self.enabled
    
    def get_options(self) -> Dict[str, Any]:
        """Get Datadog initialization options"""
        return {
            'api_key': self.api_key,
            'app_key': self.app_key,
            'api_version': 'v1',
            'statsd_host': os.getenv('DATADOG_STATSD_HOST', 'localhost'),
            'statsd_port': int(os.getenv('DATADOG_STATSD_PORT', '8125')),
        }


def init_datadog(app: Flask) -> bool:
    """
    Initialize Datadog APM and monitoring
    
    Args:
        app: Flask application instance
        
    Returns:
        True if Datadog was initialized, False otherwise
    """
    config = DatadogConfig()
    
    if not config.is_enabled():
        logger.info("Datadog monitoring is disabled (no API key or not production environment)")
        return False
    
    try:
        # Initialize Datadog
        initialize(**config.get_options())
        
        logger.info("Datadog monitoring initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Datadog: {e}")
        return False


def create_datadog_middleware(app: Flask):
    """
    Create middleware for automatic Datadog integration
    
    Args:
        app: Flask application instance
    """
    config = DatadogConfig()
    
    if not config.is_enabled():
        return
    
    @app.before_request
    def before_request_datadog():
        """Track request start time"""
        g.request_start_time = time.time()
        g.request_tags = [
            f"service:{config.service_name}",
            f"environment:{config.environment}",
            f"version:{config.version}",
        ]
    
    @app.after_request
    def after_request_datadog(response):
        """Track request metrics"""
        if not hasattr(g, 'request_start_time'):
            return response
        
        # Calculate request duration
        duration = time.time() - g.request_start_time
        
        # Get tags
        tags = g.get('request_tags', [])
        tags.extend([
            f"method:{request.method}",
            f"path:{request.path}",
            f"status:{response.status_code}",
        ])
        
        # Send metrics
        try:
            statsd.timing('phoenix.request.duration', duration * 1000, tags=tags)
            statsd.increment('phoenix.request.count', tags=tags)
            
            if response.status_code >= 400:
                statsd.increment('phoenix.request.errors', tags=tags)
        except Exception as e:
            logger.error(f"Failed to send Datadog metrics: {e}")
        
        return response


def track_metric(metric_name: str, value: float, metric_type: str = 'gauge', tags: Optional[list] = None):
    """
    Track a custom metric in Datadog
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        metric_type: Type of metric (gauge, counter, histogram, distribution)
        tags: List of tags
    """
    config = DatadogConfig()
    
    if not config.is_enabled():
        return
    
    try:
        if metric_type == 'gauge':
            statsd.gauge(metric_name, value, tags=tags)
        elif metric_type == 'counter':
            statsd.increment(metric_name, value, tags=tags)
        elif metric_type == 'histogram':
            statsd.histogram(metric_name, value, tags=tags)
        elif metric_type == 'distribution':
            statsd.distribution(metric_name, value, tags=tags)
    except Exception as e:
        logger.error(f"Failed to track metric {metric_name}: {e}")


def track_api_call(endpoint: str, method: str, status_code: int, duration_ms: float, **tags):
    """
    Track API call metrics
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        status_code: HTTP status code
        duration_ms: Duration in milliseconds
        **tags: Additional tags
    """
    tag_list = [
        f"endpoint:{endpoint}",
        f"method:{method}",
        f"status:{status_code}",
    ]
    
    for key, value in tags.items():
        tag_list.append(f"{key}:{value}")
    
    track_metric('phoenix.api.duration', duration_ms, 'histogram', tag_list)
    track_metric('phoenix.api.calls', 1, 'counter', tag_list)


def track_build_metric(build_id: str, metric_name: str, value: float, **tags):
    """
    Track build-related metrics
    
    Args:
        build_id: Build identifier
        metric_name: Metric name
        value: Metric value
        **tags: Additional tags
    """
    tag_list = [f"build_id:{build_id}"]
    
    for key, val in tags.items():
        tag_list.append(f"{key}:{val}")
    
    track_metric(f"phoenix.build.{metric_name}", value, 'gauge', tag_list)


def track_hardware_metric(device_id: str, metric_name: str, value: float, **tags):
    """
    Track hardware detection metrics
    
    Args:
        device_id: Device identifier
        metric_name: Metric name
        value: Metric value
        **tags: Additional tags
    """
    tag_list = [f"device_id:{device_id}"]
    
    for key, val in tags.items():
        tag_list.append(f"{key}:{val}")
    
    track_metric(f"phoenix.hardware.{metric_name}", value, 'gauge', tag_list)


def datadog_trace(operation_name: str, service: Optional[str] = None, resource: Optional[str] = None):
    """
    Decorator for tracing function calls in Datadog
    
    Args:
        operation_name: Name of the operation
        service: Service name
        resource: Resource name
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = DatadogConfig()
            
            if not config.is_enabled():
                return func(*args, **kwargs)
            
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                
                track_metric(
                    f"phoenix.{operation_name}.duration",
                    duration,
                    'histogram',
                    [f"status:success"]
                )
                
                return result
                
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                
                track_metric(
                    f"phoenix.{operation_name}.duration",
                    duration,
                    'histogram',
                    [f"status:error"]
                )
                
                raise
        
        return wrapper
    
    return decorator


class DatadogMetrics:
    """Helper class for tracking common metrics"""
    
    @staticmethod
    def track_build_started(build_id: str, recipe_id: str):
        """Track build start"""
        track_build_metric(build_id, 'started', 1, recipe_id=recipe_id)
    
    @staticmethod
    def track_build_progress(build_id: str, progress: float, speed_mbps: float):
        """Track build progress"""
        track_build_metric(build_id, 'progress', progress)
        track_build_metric(build_id, 'speed_mbps', speed_mbps)
    
    @staticmethod
    def track_build_completed(build_id: str, duration_seconds: float, bytes_written: int):
        """Track build completion"""
        track_build_metric(build_id, 'completed', 1)
        track_build_metric(build_id, 'duration_seconds', duration_seconds)
        track_build_metric(build_id, 'bytes_written', bytes_written)
    
    @staticmethod
    def track_build_failed(build_id: str, error_message: str):
        """Track build failure"""
        track_build_metric(build_id, 'failed', 1, error=error_message)
    
    @staticmethod
    def track_hardware_detected(device_id: str, os_count: int, cpu_cores: int):
        """Track hardware detection"""
        track_hardware_metric(device_id, 'detected', 1)
        track_hardware_metric(device_id, 'compatible_os_count', os_count)
        track_hardware_metric(device_id, 'cpu_cores', cpu_cores)
    
    @staticmethod
    def track_recipe_validation(recipe_id: str, valid: bool, error_count: int = 0):
        """Track recipe validation"""
        track_metric(
            'phoenix.recipe.validation',
            1 if valid else 0,
            'gauge',
            [f"recipe_id:{recipe_id}", f"valid:{valid}", f"errors:{error_count}"]
        )
    
    @staticmethod
    def track_usb_device_detected(device_id: str, size_gb: float, health_status: str):
        """Track USB device detection"""
        track_metric(
            'phoenix.usb.device_detected',
            1,
            'counter',
            [f"device_id:{device_id}", f"size_gb:{size_gb}", f"health:{health_status}"]
        )
    
    @staticmethod
    def track_api_error(endpoint: str, error_type: str, status_code: int):
        """Track API errors"""
        track_metric(
            'phoenix.api.errors',
            1,
            'counter',
            [f"endpoint:{endpoint}", f"error_type:{error_type}", f"status:{status_code}"]
        )
    
    @staticmethod
    def track_database_query(query_type: str, duration_ms: float):
        """Track database query performance"""
        track_metric(
            'phoenix.database.query_duration',
            duration_ms,
            'histogram',
            [f"query_type:{query_type}"]
        )
    
    @staticmethod
    def track_cache_hit(cache_key: str, hit: bool):
        """Track cache hits and misses"""
        track_metric(
            'phoenix.cache.hit',
            1 if hit else 0,
            'counter',
            [f"cache_key:{cache_key}", f"hit:{hit}"]
        )
    
    @staticmethod
    def track_websocket_connection(build_id: str, connected: bool):
        """Track WebSocket connections"""
        track_metric(
            'phoenix.websocket.connection',
            1 if connected else 0,
            'gauge',
            [f"build_id:{build_id}", f"connected:{connected}"]
        )


def send_datadog_event(title: str, text: str, alert_type: str = 'info', tags: Optional[list] = None):
    """
    Send a custom event to Datadog
    
    Args:
        title: Event title
        text: Event text
        alert_type: Alert type (info, success, warning, error)
        tags: List of tags
    """
    config = DatadogConfig()
    
    if not config.is_enabled():
        return
    
    try:
        api.Event.create(
            title=title,
            text=text,
            alert_type=alert_type,
            tags=tags or [],
        )
    except Exception as e:
        logger.error(f"Failed to send Datadog event: {e}")
