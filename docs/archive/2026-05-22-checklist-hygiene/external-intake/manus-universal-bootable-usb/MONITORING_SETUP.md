# Bobby's PhoenixDrive - Monitoring Setup Guide

Complete guide for setting up Sentry and Datadog monitoring for production API.

## Table of Contents

1. [Sentry Error Tracking](#sentry-error-tracking)
2. [Datadog Performance Monitoring](#datadog-performance-monitoring)
3. [Monitoring Dashboard](#monitoring-dashboard)
4. [Alerts & Notifications](#alerts--notifications)
5. [Troubleshooting](#troubleshooting)

---

## Sentry Error Tracking

### Setup

#### 1. Create Sentry Account

1. Go to [sentry.io](https://sentry.io)
2. Sign up for free account
3. Create new organization

#### 2. Create Project

1. Click "Create Project"
2. Select "Python" platform
3. Select "Flask" framework
4. Name it "PhoenixDrive API"
5. Click "Create Project"

#### 3. Get DSN

1. Copy the DSN (Data Source Name)
2. Format: `https://key@sentry.io/project-id`

#### 4. Configure Environment

```bash
# For Heroku
heroku config:set SENTRY_DSN=<your-sentry-dsn> -a phoenix-drive-api

# For local development
export SENTRY_DSN=<your-sentry-dsn>
```

### Features Tracked

**Exceptions:**
- API errors (500, 400, etc.)
- Hardware detection failures
- USB build failures
- Database errors

**Performance:**
- Slow API endpoints
- Database query performance
- Build execution time

**User Context:**
- User identification
- Build history
- Error patterns

### Dashboard

Access at: https://sentry.io/organizations/your-org/issues/

**Key Metrics:**
- Error rate
- Error frequency
- Affected users
- Error timeline

### Custom Events

Track specific events:

```python
from server.monitoring import capture_message, SentryMetrics

# Track build completion
SentryMetrics.track_build_completed(build_id, duration_seconds)

# Track hardware detection
SentryMetrics.track_hardware_detection(device_id, os_count)

# Capture custom message
capture_message("Build completed successfully", level='info')
```

---

## Datadog Performance Monitoring

### Setup

#### 1. Create Datadog Account

1. Go to [datadoghq.com](https://www.datadoghq.com)
2. Sign up for free trial (14 days)
3. Select "Infrastructure" as use case

#### 2. Get API Keys

1. Go to "Organization Settings" → "API Keys"
2. Copy API Key
3. Go to "Application Keys"
4. Create new application key
5. Copy Application Key

#### 3. Configure Environment

```bash
# For Heroku
heroku config:set \
  DATADOG_API_KEY=<your-api-key> \
  DATADOG_APP_KEY=<your-app-key> \
  DATADOG_SITE=datadoghq.com \
  -a phoenix-drive-api

# For local development
export DATADOG_API_KEY=<your-api-key>
export DATADOG_APP_KEY=<your-app-key>
```

### Features Tracked

**API Performance:**
- Request duration
- Request count
- Error rate
- Response time by endpoint

**Build Metrics:**
- Build duration
- Build success rate
- Write speed (MB/s)
- Bytes written

**Hardware Metrics:**
- Detection time
- Compatible OS count
- CPU cores
- Device health

**System Health:**
- Database query performance
- Cache hit rate
- WebSocket connections
- Memory usage

### Dashboard

Access at: https://app.datadoghq.com/

**Key Dashboards:**
1. **API Performance** — Request metrics and latency
2. **Build Metrics** — Build success and performance
3. **System Health** — Database, cache, and resource usage
4. **Error Tracking** — Error rates and types

### Custom Metrics

Track custom metrics:

```python
from server.monitoring import track_metric, DatadogMetrics

# Track build progress
DatadogMetrics.track_build_progress(build_id, progress=45.5, speed_mbps=50.0)

# Track hardware detection
DatadogMetrics.track_hardware_detected(device_id, os_count=5, cpu_cores=8)

# Track custom metric
track_metric('phoenix.custom.metric', value=42, metric_type='gauge', tags=['env:prod'])
```

---

## Monitoring Dashboard

### Create Unified Dashboard

#### In Datadog

1. Go to "Dashboards" → "New Dashboard"
2. Name: "PhoenixDrive API Monitoring"
3. Add widgets:

**API Performance Widget**
```
Query: avg:phoenix.api.duration{*} by {endpoint}
Type: Timeseries
```

**Build Success Rate Widget**
```
Query: sum:phoenix.build.completed{*} / sum:phoenix.build.started{*}
Type: Gauge
```

**Error Rate Widget**
```
Query: sum:phoenix.api.errors{*} / sum:phoenix.api.calls{*}
Type: Gauge
```

**Build Duration Widget**
```
Query: avg:phoenix.build.duration_seconds{*}
Type: Timeseries
```

### Create Sentry Dashboard

1. Go to Sentry organization
2. Click "Dashboards"
3. Create new dashboard
4. Add widgets:
   - Error rate
   - Error frequency
   - Affected users
   - Error timeline

---

## Alerts & Notifications

### Sentry Alerts

#### 1. Error Rate Alert

1. Go to "Alerts" → "Create Alert"
2. Condition: "Error rate > 5% in last 5 minutes"
3. Notification: Email/Slack
4. Create

#### 2. New Issue Alert

1. Go to "Alerts" → "Alert Rules"
2. Condition: "New issue"
3. Notification: Email/Slack
4. Create

### Datadog Alerts

#### 1. API Latency Alert

```
Query: avg:phoenix.api.duration{*} > 5000
Threshold: 5000ms
Duration: 5 minutes
Severity: Warning
```

#### 2. Build Failure Alert

```
Query: sum:phoenix.build.failed{*} > 0
Threshold: 0
Duration: 1 minute
Severity: Critical
```

#### 3. Error Rate Alert

```
Query: sum:phoenix.api.errors{*} / sum:phoenix.api.calls{*} > 0.05
Threshold: 0.05 (5%)
Duration: 5 minutes
Severity: Warning
```

### Slack Integration

#### Sentry

1. Go to "Integrations" → "Slack"
2. Click "Install"
3. Authorize Slack workspace
4. Select channel for notifications

#### Datadog

1. Go to "Integrations" → "Slack"
2. Click "Install"
3. Authorize Slack workspace
4. Configure notification channels

---

## Monitoring Best Practices

### 1. Set Baseline Metrics

Track normal performance:
- Average API response time: ~200ms
- Build success rate: >95%
- Error rate: <1%
- Database query time: <100ms

### 2. Regular Review

- Daily: Check error rate and critical alerts
- Weekly: Review performance trends
- Monthly: Analyze usage patterns and optimize

### 3. Incident Response

1. **Alert Triggered** → Check dashboard
2. **Identify Issue** → Review logs and traces
3. **Investigate Root Cause** → Check recent changes
4. **Fix Issue** → Deploy fix
5. **Verify Resolution** → Monitor metrics
6. **Post-Mortem** → Document lesson learned

### 4. Performance Optimization

Based on monitoring data:
- Slow endpoints → Add caching
- High error rate → Fix bugs
- High latency → Optimize queries
- Resource usage → Scale up

---

## Troubleshooting

### Sentry Not Receiving Events

**Check:**
1. DSN is correct
2. Environment variable is set
3. Flask app is initialized with Sentry
4. No errors in Flask logs

**Fix:**
```python
# Verify Sentry initialization
import sentry_sdk
print(sentry_sdk.Hub.current.client)  # Should not be None
```

### Datadog Not Receiving Metrics

**Check:**
1. API key is correct
2. StatsD is running (for local development)
3. Environment variables are set
3. No errors in Flask logs

**Fix:**
```bash
# Test Datadog connection
curl -X POST "https://api.datadoghq.com/api/v1/validate" \
  -H "DD-API-KEY: $DATADOG_API_KEY"
```

### High Latency in Monitoring

**Solutions:**
1. Reduce sample rate: `SENTRY_TRACES_SAMPLE_RATE=0.05`
2. Filter noisy events: Use `before_send` hook
3. Increase buffer size: Configure StatsD

### Missing Metrics

**Check:**
1. Metrics are being tracked in code
2. Tags are formatted correctly
3. Metric names follow convention
4. No filtering rules excluding metrics

---

## Advanced Configuration

### Custom Integrations

#### Email Notifications

```python
from server.monitoring import send_datadog_event

send_datadog_event(
    title="Build Completed",
    text="Build #123 completed successfully",
    alert_type="success",
    tags=["build", "success"]
)
```

#### Custom Dashboards

Create dashboards for specific use cases:
- Build performance
- Hardware compatibility
- User activity
- System health

#### Metrics Export

Export metrics to external systems:
- Grafana
- Prometheus
- CloudWatch
- Custom analytics

---

## Cost Optimization

### Sentry

- **Free Tier:** 5,000 events/month
- **Pro:** $29/month + usage
- **Optimization:** Filter low-priority events

### Datadog

- **Free Trial:** 14 days
- **Pro:** $15/host/month
- **Optimization:** Reduce sample rate, aggregate metrics

---

## References

- **Sentry Docs:** https://docs.sentry.io/
- **Datadog Docs:** https://docs.datadoghq.com/
- **Flask Monitoring:** https://flask.palletsprojects.com/
- **Python Monitoring:** https://docs.python.org/3/library/logging.html

---

**Last Updated:** April 2, 2026
**Version:** 1.0.0
