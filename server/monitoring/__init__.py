"""
Monitoring and observability module for PhoenixDrive API
Integrates Sentry, Datadog, and custom logging
"""

from .sentry_config import (
    init_sentry,
    capture_exception,
    capture_message,
    set_user_context,
    clear_user_context,
    set_tag,
    set_context,
    add_breadcrumb,
    create_sentry_middleware,
    SentryMetrics,
)

from .datadog_config import (
    init_datadog,
    track_metric,
    track_api_call,
    track_build_metric,
    track_hardware_metric,
    datadog_trace,
    create_datadog_middleware,
    DatadogMetrics,
    send_datadog_event,
)

__all__ = [
    # Sentry
    'init_sentry',
    'capture_exception',
    'capture_message',
    'set_user_context',
    'clear_user_context',
    'set_tag',
    'set_context',
    'add_breadcrumb',
    'create_sentry_middleware',
    'SentryMetrics',
    
    # Datadog
    'init_datadog',
    'track_metric',
    'track_api_call',
    'track_build_metric',
    'track_hardware_metric',
    'datadog_trace',
    'create_datadog_middleware',
    'DatadogMetrics',
    'send_datadog_event',
]
