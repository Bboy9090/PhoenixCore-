# Vercel Deployment Guide for Bobby's PhoenixDrive API

**Status:** Production Ready  
**Last Updated:** May 5, 2026  
**Version:** 2.0.0

---

## Overview

This guide walks you through deploying the FastAPI backend to Vercel with Supabase PostgreSQL database and real-time WebSocket support.

**Why Vercel + Supabase?**
- **Vercel:** Serverless deployment with automatic scaling, global CDN, and instant rollbacks
- **Supabase:** PostgreSQL with real-time features, built-in authentication, and REST API
- **WebSocket:** Socket.io support for real-time progress monitoring
- **Cost-effective:** Pay-as-you-go pricing with generous free tier

---

## Prerequisites

1. **Vercel Account** — Sign up at https://vercel.com
2. **Supabase Account** — Sign up at https://supabase.com
3. **GitHub Account** — For repository connection (optional but recommended)
4. **Vercel CLI** — Install with `npm install -g vercel`
5. **Git** — For version control

---

## Step 1: Set Up Supabase Database

### 1.1 Create Supabase Project

1. Go to https://supabase.com and sign in
2. Click "New Project"
3. Enter project name: `phoenix-drive`
4. Choose region closest to your users
5. Set a strong database password
6. Click "Create new project"

### 1.2 Get Database Credentials

1. Go to Project Settings → Database
2. Copy the following:
   - **Host:** `db.your-project.supabase.co`
   - **Port:** `5432`
   - **Database:** `postgres`
   - **User:** `postgres`
   - **Password:** Your database password

3. Go to Settings → API
4. Copy:
   - **Project URL:** Your Supabase URL
   - **Anon Key:** Public key for client-side access
   - **Service Role Key:** Secret key for server-side access

### 1.3 Initialize Database Schema

1. Go to SQL Editor in Supabase dashboard
2. Create new query
3. Paste the schema from `server/supabase_config.py` (SCHEMA_SQL)
4. Click "Run"
5. Verify tables are created

Alternatively, run via Python:

```bash
export DATABASE_URL="postgresql://postgres:password@db.your-project.supabase.co:5432/postgres"
python3 -c "from server.supabase_config import init_database; init_database()"
```

---

## Step 2: Prepare FastAPI Backend

### 2.1 Update Environment Variables

Create `.env.production` file:

```bash
cp .env.production.example .env.production
```

Fill in your values:

```env
# Vercel
VERCEL_URL=https://phoenix-drive-api.vercel.app
API_URL=https://phoenix-drive-api.vercel.app

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
DATABASE_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres
JWT_SECRET=your-secret-key

# CORS
CORS_ORIGINS=https://phoenixapp-ckayyn9s.manus.space,https://your-app.com

# Monitoring (optional)
SENTRY_DSN=https://your-key@sentry.io/your-project
DATADOG_API_KEY=your-datadog-key

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 2.2 Update app.config.ts

Update mobile app to use production API:

```typescript
const env = {
  appName: "Bobby's PhoenixDrive",
  appSlug: "phoenix-drive",
  scheme: "manus20240115103045",
  iosBundleId: "space.manus.phoenix.drive",
  androidPackage: "space.manus.phoenix.drive",
  // Production API URLs
  apiUrl: "https://phoenix-drive-api.vercel.app",
  wsUrl: "wss://phoenix-drive-api.vercel.app",
};
```

### 2.3 Verify Dependencies

Ensure `requirements.txt` has all dependencies:

```bash
pip install -r requirements.txt
```

---

## Step 3: Deploy to Vercel

### 3.1 Connect GitHub Repository (Recommended)

1. Push code to GitHub:

```bash
git add .
git commit -m "feat: prepare for Vercel deployment"
git push origin main
```

2. Go to https://vercel.com/new
3. Select "Import Git Repository"
4. Choose your GitHub repository
5. Click "Import"

### 3.2 Configure Vercel Project

1. **Framework:** Select "Other"
2. **Build Command:** Leave empty (Vercel auto-detects Python)
3. **Output Directory:** Leave empty
4. **Root Directory:** Leave empty

### 3.3 Add Environment Variables

In Vercel dashboard:

1. Go to Settings → Environment Variables
2. Add all variables from `.env.production`:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
DATABASE_URL=postgresql://postgres:...
JWT_SECRET=your-secret-key
CORS_ORIGINS=...
SENTRY_DSN=... (optional)
DATADOG_API_KEY=... (optional)
SMTP_HOST=... (optional)
```

### 3.4 Deploy

1. Click "Deploy"
2. Wait for build to complete (2-5 minutes)
3. Verify deployment at `https://phoenix-drive-api.vercel.app`

---

## Step 4: Verify Deployment

### 4.1 Test Health Endpoint

```bash
curl https://phoenix-drive-api.vercel.app/api/v1/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "uptime": 123.45,
  "database": "connected",
  "monitoring": {
    "sentry": "configured",
    "datadog": "configured"
  }
}
```

### 4.2 Test Hardware Detection

```bash
curl https://phoenix-drive-api.vercel.app/api/v1/hardware/detect
```

### 4.3 Test WebSocket Connection

```javascript
const socket = io('https://phoenix-drive-api.vercel.app');
socket.on('connect', () => {
  console.log('Connected to API');
});
```

### 4.4 Test Database Connection

```bash
curl https://phoenix-drive-api.vercel.app/api/v1/database/status
```

---

## Step 5: Configure Custom Domain (Optional)

1. Go to Vercel project settings
2. Click "Domains"
3. Add your custom domain (e.g., `api.phoenixdrive.app`)
4. Follow DNS configuration instructions
5. Wait for SSL certificate (5-15 minutes)

---

## Step 6: Set Up Monitoring

### 6.1 Sentry Error Tracking

1. Go to https://sentry.io and sign up
2. Create new project (Python)
3. Copy DSN
4. Add to Vercel environment: `SENTRY_DSN=your-dsn`
5. Redeploy

### 6.2 Datadog Performance Monitoring

1. Go to https://www.datadoghq.com and sign up
2. Create API key
3. Add to Vercel environment:
   - `DATADOG_API_KEY=your-key`
   - `DATADOG_APP_KEY=your-app-key`
4. Redeploy

---

## Step 7: Update Mobile App

### 7.1 Update API URLs

In `app.config.ts`:

```typescript
const env = {
  // ... other config
  apiUrl: "https://phoenix-drive-api.vercel.app",
  wsUrl: "wss://phoenix-drive-api.vercel.app",
};
```

### 7.2 Rebuild Mobile App

```bash
# For iOS
eas build --platform ios

# For Android
eas build --platform android
```

---

## Troubleshooting

### Issue: Deployment Fails

**Check logs:**
```bash
vercel logs
```

**Common causes:**
- Missing environment variables
- Python version mismatch
- Missing dependencies in `requirements.txt`

**Solution:**
```bash
vercel env pull  # Pull environment variables
vercel redeploy  # Redeploy
```

### Issue: Database Connection Fails

**Check connection string:**
```bash
echo $DATABASE_URL
```

**Test connection:**
```bash
psql $DATABASE_URL -c "SELECT 1"
```

**Verify Supabase:**
- Check IP whitelist in Supabase settings
- Ensure database is not paused

### Issue: WebSocket Not Working

**Check WebSocket URL:**
```bash
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  https://phoenix-drive-api.vercel.app/socket.io
```

**Enable WebSocket in Vercel:**
- WebSocket is automatically enabled for Python apps
- Verify in project settings

### Issue: CORS Errors

**Check CORS configuration:**
```bash
curl -H "Origin: https://your-app.com" \
  https://phoenix-drive-api.vercel.app/api/v1/health
```

**Update CORS_ORIGINS:**
```bash
vercel env add CORS_ORIGINS "https://your-app.com,https://another-domain.com"
vercel redeploy
```

---

## Performance Optimization

### 1. Enable Caching

Add to `vercel.json`:

```json
{
  "headers": [
    {
      "source": "/api/v1/catalog/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=3600"
        }
      ]
    }
  ]
}
```

### 2. Optimize Database Queries

Add indexes in Supabase:

```sql
CREATE INDEX idx_builds_status ON builds(status);
CREATE INDEX idx_recipes_recipe_id ON recipes(recipe_id);
```

### 3. Enable Compression

Already enabled by default in Vercel.

---

## Production Checklist

- [ ] Database schema initialized in Supabase
- [ ] Environment variables configured in Vercel
- [ ] Health endpoint returns 200 OK
- [ ] WebSocket connection works
- [ ] CORS configured for your domains
- [ ] Sentry DSN configured (optional)
- [ ] Datadog API key configured (optional)
- [ ] Custom domain configured (optional)
- [ ] Mobile app updated with production API URL
- [ ] Monitoring dashboards set up
- [ ] Backup strategy configured
- [ ] Rate limiting enabled
- [ ] SSL certificate verified

---

## Monitoring & Alerts

### Set Up Alerts in Vercel

1. Go to Settings → Alerts
2. Configure:
   - Build failures
   - Deployment errors
   - Performance degradation

### Set Up Alerts in Sentry

1. Go to Alerts → Create Alert Rule
2. Configure:
   - Error rate > 5%
   - New issue detected
   - Release health

### Set Up Alerts in Datadog

1. Go to Monitors → New Monitor
2. Configure:
   - API response time > 5s
   - Error rate > 5%
   - Database connection failures

---

## Rollback Procedure

If deployment has issues:

```bash
# View deployment history
vercel list

# Rollback to previous deployment
vercel rollback

# Or manually redeploy specific commit
vercel --prod
```

---

## Next Steps

1. **Desktop App Builds** — Build installers for Windows/macOS/Linux
2. **iOS App Store** — Submit to App Store
3. **Android Play Store** — Submit to Google Play
4. **Documentation** — Create user guides
5. **Marketing** — Launch and promote

---

## Support & Resources

- **Vercel Docs:** https://vercel.com/docs
- **Supabase Docs:** https://supabase.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **Socket.io Docs:** https://socket.io/docs/

---

**Deployment Status:** ✅ Ready for Production

For questions or issues, contact: support@phoenixdrive.app
