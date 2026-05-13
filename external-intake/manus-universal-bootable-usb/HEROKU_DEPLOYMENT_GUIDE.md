# Bobby's PhoenixDrive - Heroku Deployment & Verification Guide

Complete guide for deploying to Heroku, verifying production API, and testing end-to-end integration.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deploy to Heroku](#deploy-to-heroku)
3. [Verify Production API](#verify-production-api)
4. [Configure Monitoring](#configure-monitoring)
5. [Update Mobile App](#update-mobile-app)
6. [Test End-to-End](#test-end-to-end)
7. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying to Heroku, verify:

- [ ] Heroku account created
- [ ] Heroku CLI installed and authenticated
- [ ] Git repository initialized
- [ ] All changes committed
- [ ] Environment variables documented
- [ ] Database migrations tested locally
- [ ] API endpoints tested locally
- [ ] Monitoring credentials (Sentry DSN, Datadog keys) ready
- [ ] Custom domain configured (optional)
- [ ] SSL certificate ready (optional)

---

## Deploy to Heroku

### Option 1: Automated Script (Recommended)

```bash
# Make script executable
chmod +x deploy-heroku.sh

# Run deployment
./deploy-heroku.sh
```

The script will:
1. Check prerequisites
2. Create Heroku app
3. Provision PostgreSQL database
4. Set environment variables
5. Deploy code
6. Run migrations
7. Verify deployment

### Option 2: Manual Deployment

#### Step 1: Create Heroku App

```bash
heroku create phoenix-drive-api
```

#### Step 2: Add PostgreSQL

```bash
heroku addons:create heroku-postgresql:hobby-dev -a phoenix-drive-api
```

#### Step 3: Set Environment Variables

```bash
# Generate secrets
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
python3 -c "import secrets; print('JWT_SECRET=' + secrets.token_hex(32))"

# Set variables
heroku config:set \
  -a phoenix-drive-api \
  FLASK_ENV=production \
  SECRET_KEY=<your-secret-key> \
  JWT_SECRET=<your-jwt-secret> \
  LOG_LEVEL=INFO
```

#### Step 4: Deploy

```bash
git push heroku main
```

#### Step 5: Run Migrations

```bash
heroku run flask db upgrade -a phoenix-drive-api
```

---

## Verify Production API

### Health Check

```bash
# Test health endpoint
curl https://phoenix-drive-api.herokuapp.com/api/v1/health

# Expected response:
{
  "status": "ok",
  "version": "1.0.0",
  "phoenix_core_available": true,
  "monitoring_available": true,
  "timestamp": "2026-04-02T18:50:00.000000"
}
```

### Test Hardware Detection

```bash
# Test hardware detection
curl -X POST https://phoenix-drive-api.herokuapp.com/api/v1/hardware/detect \
  -H "Content-Type: application/json" \
  -d '{
    "include_storage": true,
    "include_network": true,
    "timeout_seconds": 30
  }'

# Expected response:
{
  "status": "success",
  "hardware": {
    "cpu_cores": 4,
    "cpu_model": "Intel Core i7",
    "ram_gb": 16,
    "storage_devices": [...],
    "network_interfaces": [...]
  },
  "compatible_os": ["Windows 10", "Ubuntu 20.04", "Fedora 33"],
  "timestamp": "2026-04-02T18:50:00.000000"
}
```

### Test Recipe Building

```bash
# Build recipe
curl -X POST https://phoenix-drive-api.herokuapp.com/api/v1/recipes/build \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "os_type": "windows",
    "os_version": "10",
    "tool_type": "ventoy",
    "device_id": "usb-device-123"
  }'

# Expected response:
{
  "status": "success",
  "recipe_id": "recipe-uuid",
  "recipe": {...},
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": []
  }
}
```

### Test WebSocket Connection

```bash
# Connect to WebSocket
wscat -c wss://phoenix-drive-api.herokuapp.com/api/v1/builds/stream

# Subscribe to build
{"action": "subscribe", "build_id": "build-uuid"}

# Receive progress updates
{"event": "progress", "progress": 25, "speed_mbps": 50.0, "eta_seconds": 120}
```

---

## Configure Monitoring

### Sentry Setup

1. Go to [sentry.io](https://sentry.io)
2. Create new project
3. Copy DSN
4. Set environment variable:

```bash
heroku config:set SENTRY_DSN=<your-sentry-dsn> -a phoenix-drive-api
```

5. Restart app:

```bash
heroku restart -a phoenix-drive-api
```

6. Verify in Sentry dashboard

### Datadog Setup

1. Go to [datadoghq.com](https://www.datadoghq.com)
2. Get API key and app key
3. Set environment variables:

```bash
heroku config:set \
  DATADOG_API_KEY=<your-api-key> \
  DATADOG_APP_KEY=<your-app-key> \
  -a phoenix-drive-api
```

4. Restart app:

```bash
heroku restart -a phoenix-drive-api
```

5. Verify in Datadog dashboard

---

## Update Mobile App

### Update API URL

Edit `app.config.ts`:

```typescript
const env = {
  apiUrl: 'https://phoenix-drive-api.herokuapp.com',
  apiVersion: 'v1',
  // ... other config
};
```

Or set environment variable:

```bash
export EXPO_PUBLIC_API_URL=https://phoenix-drive-api.herokuapp.com
export EXPO_PUBLIC_API_VERSION=v1
```

### Rebuild Mobile App

```bash
# Rebuild for iOS
eas build --platform ios --profile production

# Rebuild for Android
eas build --platform android --profile production
```

---

## Test End-to-End

### Test Flow: Device Detection

1. **Mobile App:**
   - Open Device Wizard
   - Tap "Detect Hardware"
   - Verify device info displays

2. **Backend:**
   - Check logs: `heroku logs --tail -a phoenix-drive-api`
   - Verify hardware detection endpoint called
   - Check response time < 5 seconds

3. **Monitoring:**
   - Check Datadog: hardware detection metrics
   - Check Sentry: no errors

### Test Flow: Recipe Building

1. **Mobile App:**
   - Open USB Builder
   - Select OS (Windows 10)
   - Select Tool (Ventoy)
   - Select Device
   - Tap "Build Recipe"

2. **Backend:**
   - Check logs: recipe building started
   - Verify validation passed
   - Check response includes recipe JSON

3. **Desktop App:**
   - Scan QR code from mobile
   - Verify recipe imported
   - Check recipe details match

4. **Monitoring:**
   - Check Datadog: build metrics
   - Check Sentry: no errors
   - Verify build duration < 30 seconds

### Test Flow: Build Execution

1. **Desktop App:**
   - Select USB device
   - Tap "Build"
   - Monitor progress

2. **Backend:**
   - Check WebSocket connection active
   - Verify progress updates streaming
   - Monitor build execution

3. **Monitoring:**
   - Check Datadog: build progress metrics
   - Check real-time speed and ETA
   - Verify build completion event

---

## Performance Optimization

### Scale Dynos

```bash
# Upgrade dyno type
heroku ps:type web=standard-1x -a phoenix-drive-api

# Scale to multiple dynos
heroku ps:scale web=2 -a phoenix-drive-api
```

### Add Redis Cache

```bash
# Provision Redis
heroku addons:create heroku-redis:premium-0 -a phoenix-drive-api

# Verify connection
heroku config:get REDIS_URL -a phoenix-drive-api
```

### Enable CDN

```bash
# Add CloudFlare
heroku certs:add --cert cert.pem --key key.pem -a phoenix-drive-api
```

---

## Monitoring & Alerts

### View Logs

```bash
# Real-time logs
heroku logs --tail -a phoenix-drive-api

# Logs from specific time
heroku logs --since 1h -a phoenix-drive-api

# Filter logs
heroku logs --grep "ERROR" -a phoenix-drive-api
```

### View Metrics

```bash
# CPU usage
heroku metrics -a phoenix-drive-api

# Dyno info
heroku ps -a phoenix-drive-api
```

### Set Up Alerts

**Heroku Alerts:**

```bash
# CPU alert
heroku alerts:add --threshold 80 --type cpu -a phoenix-drive-api

# Memory alert
heroku alerts:add --threshold 90 --type memory -a phoenix-drive-api
```

**Sentry Alerts:**

1. Go to Sentry project
2. Settings → Alerts
3. Create alert rule
4. Set threshold (e.g., 5% error rate)
5. Configure notification channel

**Datadog Alerts:**

1. Go to Datadog
2. Monitors → New Monitor
3. Set metric and threshold
4. Configure notification

---

## Troubleshooting

### App Won't Start

```bash
# Check logs
heroku logs --tail -a phoenix-drive-api

# Common issues:
# - Missing environment variables
# - Database migration failed
# - Python version mismatch
```

**Fix:**
```bash
# Set missing variables
heroku config:set VARIABLE_NAME=value -a phoenix-drive-api

# Run migrations
heroku run flask db upgrade -a phoenix-drive-api

# Restart
heroku restart -a phoenix-drive-api
```

### Slow Performance

```bash
# Check dyno usage
heroku ps -a phoenix-drive-api

# Check database connections
heroku pg:info -a phoenix-drive-api
```

**Fix:**
```bash
# Scale up
heroku ps:scale web=2 -a phoenix-drive-api

# Upgrade dyno
heroku ps:type web=standard-1x -a phoenix-drive-api
```

### Database Issues

```bash
# Check database status
heroku pg:info -a phoenix-drive-api

# View connections
heroku pg:connections -a phoenix-drive-api

# Restart database
heroku pg:restart -a phoenix-drive-api
```

### WebSocket Connection Issues

```bash
# Check SocketIO logs
heroku logs --grep "SocketIO" --tail -a phoenix-drive-api

# Verify CORS settings
heroku config:get CORS_ORIGINS -a phoenix-drive-api
```

**Fix:**
```bash
# Update CORS
heroku config:set CORS_ORIGINS="https://your-domain.com" -a phoenix-drive-api

# Restart
heroku restart -a phoenix-drive-api
```

---

## Maintenance

### Regular Backups

```bash
# Create backup
heroku pg:backups:capture -a phoenix-drive-api

# List backups
heroku pg:backups -a phoenix-drive-api

# Download backup
heroku pg:backups:download -a phoenix-drive-api
```

### Update Dependencies

```bash
# Check for updates
pip list --outdated

# Update requirements.txt
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt

# Commit and push
git add requirements.txt
git commit -m "Update dependencies"
git push heroku main
```

### Monitor Costs

```bash
# View current costs
heroku billing

# View resource usage
heroku ps -a phoenix-drive-api
```

---

## Useful Commands

```bash
# View app info
heroku apps:info -a phoenix-drive-api

# View config
heroku config -a phoenix-drive-api

# View logs
heroku logs --tail -a phoenix-drive-api

# Run command
heroku run <command> -a phoenix-drive-api

# Restart app
heroku restart -a phoenix-drive-api

# Scale dynos
heroku ps:scale web=2 -a phoenix-drive-api

# Open app
heroku open -a phoenix-drive-api

# Destroy app
heroku apps:destroy -a phoenix-drive-api
```

---

## References

- **Heroku Docs:** https://devcenter.heroku.com/
- **Flask Deployment:** https://flask.palletsprojects.com/deployment/
- **PostgreSQL on Heroku:** https://devcenter.heroku.com/articles/heroku-postgresql
- **Sentry Docs:** https://docs.sentry.io/
- **Datadog Docs:** https://docs.datadoghq.com/

---

**Last Updated:** April 2, 2026
**Version:** 1.0.0
