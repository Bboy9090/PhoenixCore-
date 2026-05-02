# Bobby's PhoenixDrive Backend - Production Deployment Guide

This guide covers deploying the PhoenixDrive backend API to production cloud platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Deployment Options](#deployment-options)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Deployment Steps](#deployment-steps)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts

- **Cloud Platform Account** (choose one):
  - Heroku (free tier available, credit card required)
  - AWS (free tier available for 12 months)
  - DigitalOcean (paid, starting at $5/month)
  - Railway.app (simple deployment, starting at $5/month)
  - Render (free tier available)

### Required Tools

```bash
# Install cloud CLI tools
pip install heroku  # For Heroku
pip install awscli   # For AWS
# For DigitalOcean, use their web console or doctl CLI

# Install Docker (required for most platforms)
docker --version
```

---

## Deployment Options

### Option 1: Heroku (Recommended for Beginners)

**Pros:** Simple, free tier available, automatic HTTPS, easy scaling
**Cons:** Slower performance, limited free tier

**Cost:** Free tier (limited), $7/month+ for production

### Option 2: AWS (Recommended for Scale)

**Pros:** Highly scalable, extensive features, free tier (12 months)
**Cons:** Complex setup, cost management required

**Cost:** Free tier (12 months), then $10-50+/month depending on usage

### Option 3: DigitalOcean (Recommended for Balance)

**Pros:** Simple setup, predictable pricing, good performance
**Cons:** No free tier

**Cost:** $5-20+/month depending on droplet size

### Option 4: Railway.app (Recommended for Speed)

**Pros:** Super simple, GitHub integration, automatic deployments
**Cons:** Limited free tier, pricing can add up

**Cost:** Free tier (limited), $5/month+ for production

---

## Environment Configuration

### 1. Create `.env.production` file

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here-generate-with-secrets.token_hex(32)

# Database
DATABASE_URL=postgresql://user:password@host:port/dbname
# or for SQLite (not recommended for production)
# DATABASE_URL=sqlite:///phoenix_drive.db

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
API_WORKERS=4

# CORS Configuration
CORS_ORIGINS=https://phoenixapp-ckayyn9s.manus.space,https://yourdomain.com
CORS_ALLOW_CREDENTIALS=true

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/phoenix-drive/api.log

# PhoenixCore Configuration
PHOENIX_CORE_PATH=/app/PhoenixCore-
PHOENIX_CORE_ENABLED=true

# Build Configuration
BUILD_TEMP_DIR=/tmp/phoenix-builds
BUILD_TIMEOUT_MINUTES=60
MAX_CONCURRENT_BUILDS=4

# Security
REQUIRE_AUTH=true
JWT_SECRET=your-jwt-secret-key
JWT_EXPIRY_HOURS=24

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
DATADOG_API_KEY=your-datadog-api-key
```

### 2. Generate Secure Secret Keys

```python
import secrets
print(secrets.token_hex(32))  # For SECRET_KEY and JWT_SECRET
```

---

## Database Setup

### Option A: PostgreSQL (Recommended)

**Heroku:**
```bash
heroku addons:create heroku-postgresql:hobby-dev -a your-app-name
```

**DigitalOcean:**
```bash
# Create managed database via console
# Connection string format:
postgresql://user:password@host:port/dbname
```

**AWS RDS:**
```bash
# Create RDS instance via AWS Console
# Connection string format:
postgresql://user:password@rds-instance.region.rds.amazonaws.com:5432/dbname
```

### Option B: SQLite (Development Only)

```bash
# Not recommended for production
# But can be used for testing
DATABASE_URL=sqlite:///phoenix_drive.db
```

### Initialize Database

```bash
# Run migrations
cd /home/ubuntu/phoenix-core-mobile
flask db upgrade

# Or create tables manually
python -c "from server.api import app, db; app.app_context().push(); db.create_all()"
```

---

## Deployment Steps

### Method 1: Heroku Deployment

#### 1. Install Heroku CLI

```bash
curl https://cli-assets.heroku.com/install.sh | sh
heroku login
```

#### 2. Create Heroku App

```bash
heroku create phoenix-drive-api
# Or use existing app
heroku apps
```

#### 3. Create Procfile

```bash
cat > Procfile << 'EOF'
web: gunicorn -w 4 -b 0.0.0.0:$PORT server.api:app
worker: python -m server.background_tasks
EOF
```

#### 4. Create requirements.txt

```bash
pip freeze > requirements.txt
# Add these if missing:
# gunicorn==21.2.0
# python-dotenv==1.0.0
# psycopg2-binary==2.9.9
```

#### 5. Set Environment Variables

```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set DATABASE_URL=postgresql://...
heroku config:set CORS_ORIGINS=https://phoenixapp-ckayyn9s.manus.space
```

#### 6. Deploy

```bash
git push heroku main
# Or if using different branch
git push heroku your-branch:main
```

#### 7. Check Logs

```bash
heroku logs --tail
```

---

### Method 2: AWS Elastic Beanstalk Deployment

#### 1. Install EB CLI

```bash
pip install awsebcli
eb init -p python-3.11 phoenix-drive-api
```

#### 2. Create `.ebextensions/python.config`

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: server.api:app
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: /var/app/current:$PYTHONPATH
```

#### 3. Create Environment

```bash
eb create phoenix-drive-api-prod --instance-type t3.micro
```

#### 4. Set Environment Variables

```bash
eb setenv FLASK_ENV=production
eb setenv SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
eb setenv DATABASE_URL=postgresql://...
```

#### 5. Deploy

```bash
eb deploy
```

#### 6. Monitor

```bash
eb logs
eb status
```

---

### Method 3: DigitalOcean App Platform

#### 1. Create App Specification

```yaml
name: phoenix-drive-api
services:
- name: api
  github:
    repo: Bboy9090/PhoenixCore-
    branch: main
  build_command: pip install -r requirements.txt
  run_command: gunicorn -w 4 -b 0.0.0.0:8080 server.api:app
  envs:
  - key: FLASK_ENV
    value: production
  - key: DATABASE_URL
    value: ${db.connection_string}
  http_port: 8080
  health_check:
    http_path: /api/v1/health
databases:
- name: db
  engine: PG
  version: "14"
```

#### 2. Deploy via DigitalOcean Console

- Go to DigitalOcean Apps
- Click "Create App"
- Connect GitHub repository
- Upload app specification
- Click "Deploy"

---

### Method 4: Railway.app Deployment

#### 1. Connect GitHub

- Go to railway.app
- Click "New Project"
- Select "Deploy from GitHub"
- Select your repository

#### 2. Add Environment Variables

```
FLASK_ENV=production
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://...
CORS_ORIGINS=https://phoenixapp-ckayyn9s.manus.space
```

#### 3. Configure Start Command

```
gunicorn -w 4 -b 0.0.0.0:$PORT server.api:app
```

#### 4. Deploy

- Railway automatically deploys on push to main branch

---

## Domain Configuration

### 1. Get Your API Domain

After deployment, you'll receive a domain:
- **Heroku:** `phoenix-drive-api.herokuapp.com`
- **AWS:** `phoenix-drive-api-prod.elasticbeanstalk.com`
- **DigitalOcean:** `phoenix-drive-api-xxx.ondigitalocean.app`
- **Railway:** `phoenix-drive-api.up.railway.app`

### 2. Configure Custom Domain (Optional)

```bash
# Add your custom domain
# Update DNS records to point to your app
# Configure SSL certificate (usually automatic)
```

### 3. Update Mobile App Configuration

Update `app.config.ts`:

```typescript
const env = {
  apiUrl: 'https://phoenix-drive-api.herokuapp.com',
  // ... other config
};
```

Update `lib/hooks/use-phoenix-api.ts`:

```typescript
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'https://phoenix-drive-api.herokuapp.com';
```

---

## Monitoring & Maintenance

### 1. Health Check Endpoint

```bash
curl https://your-api-domain.com/api/v1/health
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "phoenix_core_available": true,
  "timestamp": "2026-04-02T17:00:00Z"
}
```

### 2. Set Up Monitoring

#### Sentry (Error Tracking)

```bash
pip install sentry-sdk
```

Add to `server/api.py`:

```python
import sentry_sdk
sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    traces_sample_rate=0.1,
    environment=os.getenv('FLASK_ENV')
)
```

#### Datadog (Performance Monitoring)

```bash
pip install datadog
```

#### Uptime Monitoring

Use services like:
- UptimeRobot (free)
- Pingdom
- Statuspage.io

### 3. Backup Strategy

#### Database Backups

```bash
# Heroku
heroku pg:backups:capture

# AWS RDS
# Automatic backups enabled by default

# DigitalOcean
# Automated backups available
```

#### Application Backups

```bash
# Back up build artifacts and logs
aws s3 sync /var/log/phoenix-drive s3://your-backup-bucket/logs/
```

### 4. Scaling

#### Horizontal Scaling (More Instances)

```bash
# Heroku
heroku ps:scale web=2 worker=1

# AWS
# Increase Auto Scaling group size

# DigitalOcean
# Increase instance count
```

#### Vertical Scaling (Larger Instances)

```bash
# Upgrade to larger instance type
# Usually requires downtime
```

---

## Troubleshooting

### Issue: API Returns 502 Bad Gateway

**Solution:**
```bash
# Check logs
heroku logs --tail

# Restart app
heroku restart

# Check for syntax errors
python -m py_compile server/api.py
```

### Issue: Database Connection Failed

**Solution:**
```bash
# Verify connection string
heroku config:get DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Check firewall rules
# Ensure IP whitelist includes your deployment platform
```

### Issue: PhoenixCore Modules Not Found

**Solution:**
```bash
# Ensure PhoenixCore- repository is included
# Add to .gitignore if needed
git add PhoenixCore-
git commit -m "Add PhoenixCore modules"

# Or clone during deployment
# Add to Procfile or build script:
# git clone https://github.com/Bboy9090/PhoenixCore-.git
```

### Issue: High Memory Usage

**Solution:**
```bash
# Reduce worker count
# Increase instance size
# Enable caching
# Optimize database queries
```

### Issue: Slow API Responses

**Solution:**
```bash
# Add caching headers
# Optimize database indexes
# Use CDN for static files
# Monitor slow queries
```

---

## Performance Optimization

### 1. Enable Caching

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@app.route('/api/v1/hardware/detect')
@cache.cached(timeout=300)
def detect_hardware():
    # ...
```

### 2. Use Connection Pooling

```python
from sqlalchemy.pool import QueuePool

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'poolclass': QueuePool,
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
```

### 3. Enable Compression

```python
from flask_compress import Compress

Compress(app)
```

### 4. Use CDN for Static Files

```bash
# Upload assets to S3 or CloudFront
# Update app to serve from CDN
```

---

## Security Checklist

- [ ] Enable HTTPS/SSL
- [ ] Set secure SECRET_KEY
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Set up authentication
- [ ] Use environment variables for secrets
- [ ] Enable database encryption
- [ ] Set up firewall rules
- [ ] Enable logging and monitoring
- [ ] Regular security updates
- [ ] Backup strategy in place
- [ ] Disaster recovery plan

---

## Rollback Procedure

### Heroku

```bash
heroku releases
heroku rollback v10
```

### AWS

```bash
eb appversion
eb deploy --version v10
```

### DigitalOcean

```bash
# Redeploy previous commit
git revert HEAD
git push
```

---

## Support & Resources

- **Heroku Docs:** https://devcenter.heroku.com/
- **AWS Docs:** https://docs.aws.amazon.com/
- **DigitalOcean Docs:** https://docs.digitalocean.com/
- **Railway Docs:** https://docs.railway.app/
- **Flask Deployment:** https://flask.palletsprojects.com/deployment/

---

## Next Steps

1. Choose your deployment platform
2. Follow the deployment steps for your platform
3. Configure environment variables
4. Set up monitoring and backups
5. Test the API endpoints
6. Update mobile app configuration
7. Monitor logs and performance

---

**Last Updated:** April 2, 2026
**Version:** 1.0.0
