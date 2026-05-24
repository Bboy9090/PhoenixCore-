# Bobby's PhoenixDrive — Heroku Production Deployment Guide

## Overview

This guide walks you through deploying Bobby's PhoenixDrive backend to Heroku with complete production configuration including database, monitoring, and environment variables.

## Prerequisites

Before starting, ensure you have:

- **Heroku Account** — Sign up at [heroku.com](https://www.heroku.com)
- **Heroku CLI** — Install from [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
- **Git** — Version control installed
- **Python 3.9+** — For local testing
- **Environment Variables** — Sentry DSN, Datadog API key (optional but recommended)

## Step 1: Prepare Your Local Environment

### 1.1 Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Linux
curl https://cli-assets.heroku.com/install.sh | sh

# Windows
# Download installer from https://cli-assets.heroku.com/heroku-x64.exe
```

### 1.2 Login to Heroku

```bash
heroku login
# Opens browser for authentication
```

### 1.3 Verify Installation

```bash
heroku --version
```

## Step 2: Create Heroku Application

### 2.1 Create App

```bash
cd /home/ubuntu/phoenix-core-mobile
heroku create phoenixdrive-api
# Or use a custom name: heroku create your-app-name
```

### 2.2 Verify App Creation

```bash
heroku apps
# Should list: phoenixdrive-api
```

## Step 3: Configure Environment Variables

### 3.1 Set Required Variables

```bash
# Database (Heroku Postgres)
heroku addons:create heroku-postgresql:hobby-dev --app phoenixdrive-api

# Environment
heroku config:set FLASK_ENV=production --app phoenixdrive-api
heroku config:set SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))') --app phoenixdrive-api

# Monitoring (Optional but recommended)
heroku config:set SENTRY_DSN=your-sentry-dsn-here --app phoenixdrive-api
heroku config:set DATADOG_API_KEY=your-datadog-key-here --app phoenixdrive-api
heroku config:set DATADOG_APP_KEY=your-datadog-app-key-here --app phoenixdrive-api

# Email Notifications
heroku config:set SMTP_SERVER=smtp.gmail.com --app phoenixdrive-api
heroku config:set SMTP_PORT=587 --app phoenixdrive-api
heroku config:set SMTP_USERNAME=your-email@gmail.com --app phoenixdrive-api
heroku config:set SMTP_PASSWORD=your-app-password --app phoenixdrive-api
heroku config:set ADMIN_EMAIL=admin@phoenixdrive.com --app phoenixdrive-api
```

### 3.2 Verify Configuration

```bash
heroku config --app phoenixdrive-api
# Should display all set variables
```

## Step 4: Deploy Application

### 4.1 Add Heroku Remote

```bash
git remote add heroku https://git.heroku.com/phoenixdrive-api.git
# Or if already exists:
git remote set-url heroku https://git.heroku.com/phoenixdrive-api.git
```

### 4.2 Deploy Code

```bash
git push heroku main
# Or current branch: git push heroku $(git rev-parse --abbrev-ref HEAD):main
```

### 4.3 Monitor Deployment

```bash
heroku logs --tail --app phoenixdrive-api
# Watch logs in real-time during deployment
```

### 4.4 Verify Deployment

```bash
heroku open --app phoenixdrive-api
# Opens app in browser (should show API status)
```

## Step 5: Initialize Database

### 5.1 Run Migrations

```bash
heroku run python3 -c "from server.api import db; db.create_all()" --app phoenixdrive-api
```

### 5.2 Seed Initial Data

```bash
heroku run python3 << 'EOF' --app phoenixdrive-api
from server.bootcamp.driver_database import DRIVER_DATABASE
import json

# Load driver database
print("Seeding driver database...")
print(f"Loaded {len(DRIVER_DATABASE['mac_models'])} Mac models")
print(f"Loaded {len(DRIVER_DATABASE['driver_packages'])} driver packages")
EOF
```

## Step 6: Configure Monitoring

### 6.1 Set Up Sentry (Error Tracking)

1. Create account at [sentry.io](https://sentry.io)
2. Create new project for Flask
3. Copy DSN and set environment variable:

```bash
heroku config:set SENTRY_DSN=https://your-key@your-org.ingest.sentry.io/your-project-id --app phoenixdrive-api
```

### 6.2 Set Up Datadog (Performance Monitoring)

1. Create account at [datadoghq.com](https://www.datadoghq.com)
2. Get API key from Settings → API Keys
3. Set environment variables:

```bash
heroku config:set DATADOG_API_KEY=your-api-key --app phoenixdrive-api
heroku config:set DATADOG_APP_KEY=your-app-key --app phoenixdrive-api
```

## Step 7: Test Production API

### 7.1 Get App URL

```bash
heroku info --app phoenixdrive-api
# Note the "Web URL" (e.g., https://phoenixdrive-api.herokuapp.com)
```

### 7.2 Test Health Endpoint

```bash
curl https://phoenixdrive-api.herokuapp.com/api/v1/health
# Should return: {"status": "healthy", "timestamp": "..."}
```

### 7.3 Test Mac Detection

```bash
curl -X POST https://phoenixdrive-api.herokuapp.com/api/v1/bootcamp/detect-mac \
  -H "Content-Type: application/json" \
  -d '{"model_id": "MacBookPro16,1"}'
# Should return Mac model details
```

### 7.4 Test Driver List

```bash
curl https://phoenixdrive-api.herokuapp.com/api/v1/bootcamp/drivers
# Should return list of available driver packages
```

## Step 8: Update Mobile App Configuration

### 8.1 Update API URL

Edit `app.config.ts`:

```typescript
const env = {
  appName: "Bobby's PhoenixDrive",
  appSlug: "phoenix-core-mobile",
  logoUrl: "",
  scheme: schemeFromBundleId,
  iosBundleId: bundleId,
  androidPackage: bundleId,
  // Add production API URL
  apiUrl: "https://phoenixdrive-api.herokuapp.com",
};
```

### 8.2 Update API Client

Edit `lib/trpc.ts`:

```typescript
const apiUrl = process.env.EXPO_PUBLIC_API_URL || "https://phoenixdrive-api.herokuapp.com";
```

## Step 9: Enable Auto-Scaling (Optional)

### 9.1 Add Performance Dyno

```bash
heroku ps:scale web=1 --app phoenixdrive-api
```

### 9.2 Monitor Dyno Usage

```bash
heroku ps --app phoenixdrive-api
# Shows current dyno status
```

## Step 10: Set Up Continuous Deployment (Optional)

### 10.1 Connect GitHub

```bash
heroku apps:info --app phoenixdrive-api
# Note the Git URL
```

### 10.2 Enable GitHub Deploys

1. Go to Heroku Dashboard
2. Select your app
3. Deploy → GitHub → Connect to GitHub
4. Search for your repository
5. Enable automatic deploys from main branch

## Troubleshooting

### Application Won't Start

```bash
# Check logs
heroku logs --tail --app phoenixdrive-api

# Check for errors
heroku logs --app phoenixdrive-api | grep ERROR
```

### Database Connection Issues

```bash
# Check database status
heroku pg:info --app phoenixdrive-api

# Reset database
heroku pg:reset DATABASE --app phoenixdrive-api
```

### Memory Issues

```bash
# Upgrade dyno
heroku ps:type Standard-1X --app phoenixdrive-api

# Check memory usage
heroku ps --app phoenixdrive-api
```

### Monitoring Not Working

```bash
# Verify Sentry DSN
heroku config:get SENTRY_DSN --app phoenixdrive-api

# Test Sentry
curl -X POST https://phoenixdrive-api.herokuapp.com/api/v1/test/sentry
```

## Production Checklist

- [ ] Heroku account created
- [ ] Heroku CLI installed and authenticated
- [ ] Environment variables configured
- [ ] Database initialized with migrations
- [ ] Sentry monitoring configured
- [ ] Datadog monitoring configured
- [ ] Email notifications tested
- [ ] API endpoints tested
- [ ] Mobile app updated with production URL
- [ ] Desktop app updated with production URL
- [ ] SSL certificate enabled (automatic on Heroku)
- [ ] Backup schedule configured
- [ ] Monitoring alerts set up
- [ ] Team members added to Heroku app

## Maintenance

### Regular Tasks

```bash
# Check app health daily
heroku ps --app phoenixdrive-api

# Review logs weekly
heroku logs --app phoenixdrive-api -n 1000

# Backup database monthly
heroku pg:backups:capture --app phoenixdrive-api
```

### Updates

```bash
# Deploy new version
git push heroku main

# Monitor deployment
heroku logs --tail --app phoenixdrive-api
```

## Support

For issues or questions:
- **Heroku Docs**: [devcenter.heroku.com](https://devcenter.heroku.com)
- **Sentry Docs**: [docs.sentry.io](https://docs.sentry.io)
- **Datadog Docs**: [docs.datadoghq.com](https://docs.datadoghq.com)

---

**Last Updated**: April 2026  
**Version**: 1.0  
**Author**: Manus AI
