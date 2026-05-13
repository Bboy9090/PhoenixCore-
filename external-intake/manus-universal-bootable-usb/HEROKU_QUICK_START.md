# Bobby's PhoenixDrive - Heroku Quick Start Guide

Deploy the PhoenixDrive API to Heroku in 5 minutes.

## Prerequisites

1. **Heroku Account** — Sign up at [heroku.com](https://www.heroku.com)
2. **Heroku CLI** — Install from [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)
3. **Git** — Already installed on most systems

## Step 1: Login to Heroku

```bash
heroku login
```

This opens your browser for authentication.

## Step 2: Create Heroku App

```bash
heroku create phoenix-drive-api
```

Replace `phoenix-drive-api` with your desired app name. Heroku generates a unique URL.

## Step 3: Add PostgreSQL Database

```bash
heroku addons:create heroku-postgresql:hobby-dev -a phoenix-drive-api
```

This provisions a free PostgreSQL database.

## Step 4: Set Environment Variables

```bash
# Generate secret keys
python3 -c "import secrets; print(secrets.token_hex(32))"

# Set environment variables
heroku config:set \
  -a phoenix-drive-api \
  FLASK_ENV=production \
  SECRET_KEY=<your-secret-key> \
  JWT_SECRET=<your-jwt-secret> \
  LOG_LEVEL=INFO
```

## Step 5: Deploy

```bash
git push heroku main
```

If your branch is not `main`, use:

```bash
git push heroku your-branch:main
```

## Step 6: Run Migrations

```bash
heroku run flask db upgrade -a phoenix-drive-api
```

## Step 7: Verify Deployment

```bash
# Check app status
heroku ps -a phoenix-drive-api

# View logs
heroku logs --tail -a phoenix-drive-api

# Test API
curl https://phoenix-drive-api.herokuapp.com/api/v1/health
```

## Optional: Add Monitoring

### Sentry (Error Tracking)

1. Create account at [sentry.io](https://sentry.io)
2. Create new project for Python/Flask
3. Copy DSN
4. Set environment variable:

```bash
heroku config:set SENTRY_DSN=<your-sentry-dsn> -a phoenix-drive-api
```

### Datadog (Performance Monitoring)

1. Create account at [datadoghq.com](https://www.datadoghq.com)
2. Get API key from settings
3. Set environment variables:

```bash
heroku config:set \
  DATADOG_API_KEY=<your-api-key> \
  DATADOG_APP_KEY=<your-app-key> \
  -a phoenix-drive-api
```

## Update Mobile App

Update `app.config.ts` with your Heroku URL:

```typescript
const env = {
  apiUrl: 'https://phoenix-drive-api.herokuapp.com',
  // ... other config
};
```

Or set environment variable:

```bash
export EXPO_PUBLIC_API_URL=https://phoenix-drive-api.herokuapp.com
```

## Useful Commands

```bash
# View app info
heroku apps:info -a phoenix-drive-api

# View config variables
heroku config -a phoenix-drive-api

# View logs
heroku logs --tail -a phoenix-drive-api

# Run a command
heroku run python -c "print('Hello')" -a phoenix-drive-api

# Restart app
heroku restart -a phoenix-drive-api

# Scale dynos (increase performance)
heroku ps:scale web=2 -a phoenix-drive-api

# Open app in browser
heroku open -a phoenix-drive-api

# Destroy app
heroku apps:destroy -a phoenix-drive-api
```

## Troubleshooting

### App crashes on startup

Check logs:
```bash
heroku logs --tail -a phoenix-drive-api
```

Common issues:
- Missing environment variables
- Database migration failed
- Python version mismatch

### Database connection error

Verify DATABASE_URL is set:
```bash
heroku config:get DATABASE_URL -a phoenix-drive-api
```

### Slow performance

Scale up dynos:
```bash
heroku ps:scale web=2 -a phoenix-drive-api
```

Or upgrade dyno type:
```bash
heroku ps:type web=standard-1x -a phoenix-drive-api
```

## Next Steps

1. ✅ Deploy to Heroku
2. ✅ Set up monitoring
3. ✅ Update mobile app with production URL
4. ✅ Test API endpoints
5. ✅ Monitor logs and performance
6. ✅ Configure custom domain (optional)
7. ✅ Set up automatic backups

## Support

- **Heroku Docs:** https://devcenter.heroku.com/
- **Flask Deployment:** https://flask.palletsprojects.com/deployment/
- **PhoenixDrive Issues:** https://github.com/Bboy9090/PhoenixCore-/issues

---

**Deployment Time:** ~5 minutes
**Cost:** Free tier available (with limitations)
**Scaling:** Easy horizontal scaling with Heroku dynos
