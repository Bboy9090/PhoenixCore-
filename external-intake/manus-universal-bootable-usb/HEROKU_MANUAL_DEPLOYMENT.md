# Bobby's PhoenixDrive — Manual Heroku Deployment Guide

This guide walks you through deploying the PhoenixDrive backend API to Heroku without Sentry/Datadog monitoring.

## Prerequisites

- Heroku CLI installed ([https://devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli))
- Git installed and configured
- Heroku account ([https://signup.heroku.com](https://signup.heroku.com))
- PhoenixDrive repository cloned locally

## Step 1: Install Heroku CLI

### macOS
```bash
brew tap heroku/brew && brew install heroku
```

### Linux
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

### Windows
Download installer from: https://cli-assets.heroku.com/heroku-x64.exe

Verify installation:
```bash
heroku --version
```

## Step 2: Login to Heroku

```bash
heroku login
```

This opens a browser window to authenticate. Follow the prompts.

Verify login:
```bash
heroku auth:whoami
```

## Step 3: Create Heroku App

Navigate to the project directory:
```bash
cd /home/ubuntu/phoenix-core-mobile
```

Create a new Heroku app:
```bash
heroku create phoenix-drive-api
```

Output will show:
```
Creating ⬢ phoenix-drive-api... done
https://phoenix-drive-api.herokuapp.com/ | https://git.heroku.com/phoenix-drive-api.git
```

## Step 4: Add PostgreSQL Database

Add the free PostgreSQL add-on:
```bash
heroku addons:create heroku-postgresql:hobby-dev --app phoenix-drive-api
```

Verify database is created:
```bash
heroku config --app phoenix-drive-api | grep DATABASE_URL
```

## Step 5: Configure Environment Variables

Set required environment variables:

```bash
# Flask configuration
heroku config:set FLASK_ENV=production --app phoenix-drive-api
heroku config:set FLASK_APP=server/_core/index.ts --app phoenix-drive-api

# API configuration
heroku config:set API_PORT=5000 --app phoenix-drive-api
heroku config:set API_HOST=0.0.0.0 --app phoenix-drive-api

# Database (auto-set by Heroku, verify with)
heroku config --app phoenix-drive-api
```

Verify all variables are set:
```bash
heroku config --app phoenix-drive-api
```

## Step 6: Deploy Code to Heroku

Add Heroku remote (if not already added):
```bash
heroku git:remote --app phoenix-drive-api
```

Deploy the application:
```bash
git push heroku main
```

Watch the deployment logs:
```bash
heroku logs --tail --app phoenix-drive-api
```

Wait for deployment to complete. You should see:
```
-----> Build succeeded!
-----> Discovering process types
       Procfile declares types -> web
-----> Compressing...
-----> Launching...
       Released v1
       https://phoenix-drive-api.herokuapp.com/ deployed to Heroku
```

## Step 7: Run Database Migrations

Initialize the database:
```bash
heroku run python3 -c "from server._core.db import init_db; init_db()" --app phoenix-drive-api
```

Or if using Drizzle ORM:
```bash
heroku run npm run db:push --app phoenix-drive-api
```

## Step 8: Verify Deployment

Check app status:
```bash
heroku ps --app phoenix-drive-api
```

Should show:
```
=== web (Free): gunicorn server._core.index:app (1)
web.1: up 2023/01/15 10:30:00 +0000 (~ 1m ago)
```

Test the health endpoint:
```bash
curl https://phoenix-drive-api.herokuapp.com/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2023-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

## Step 9: Test API Endpoints

### Test Hardware Detection
```bash
curl -X POST https://phoenix-drive-api.herokuapp.com/api/v1/hardware/detect \
  -H "Content-Type: application/json" \
  -d '{"device_id": "test-device"}'
```

### Test Boot Camp Detection
```bash
curl -X POST https://phoenix-drive-api.herokuapp.com/api/v1/bootcamp/detect-mac \
  -H "Content-Type: application/json" \
  -d '{"serial_number": "C02ABC123DEF"}'
```

### Test Recipe Building
```bash
curl -X POST https://phoenix-drive-api.herokuapp.com/api/v1/recipes/build \
  -H "Content-Type: application/json" \
  -d '{
    "os": "Windows 11",
    "tool": "Ventoy",
    "device_id": "test-device"
  }'
```

## Step 10: Configure Custom Domain (Optional)

If you have a custom domain:

```bash
heroku domains:add api.phoenixdrive.com --app phoenix-drive-api
```

Then update your DNS provider to point to Heroku:
```
CNAME: api.phoenixdrive.com -> phoenix-drive-api.herokuapp.com
```

## Step 11: View Logs

View real-time logs:
```bash
heroku logs --tail --app phoenix-drive-api
```

View last 100 lines:
```bash
heroku logs -n 100 --app phoenix-drive-api
```

View specific dyno logs:
```bash
heroku logs --dyno web --app phoenix-drive-api
```

## Step 12: Scale Application (Optional)

Increase web dyno capacity:
```bash
heroku dyno:scale web=2 --app phoenix-drive-api
```

## Step 13: Monitor Application

Check app metrics:
```bash
heroku apps:info --app phoenix-drive-api
```

View recent releases:
```bash
heroku releases --app phoenix-drive-api
```

Rollback to previous version if needed:
```bash
heroku releases:rollback --app phoenix-drive-api
```

## Troubleshooting

### App Crashes on Startup
```bash
heroku logs --tail --app phoenix-drive-api
```

Check for missing environment variables or database connection issues.

### Database Connection Failed
```bash
heroku config --app phoenix-drive-api | grep DATABASE_URL
heroku pg:info --app phoenix-drive-api
```

### Port Already in Use
The Heroku Procfile should use `$PORT` environment variable. Verify Procfile:
```bash
cat Procfile
```

Should contain:
```
web: gunicorn server._core.index:app --bind 0.0.0.0:$PORT
```

### Memory Issues
```bash
heroku ps --app phoenix-drive-api
```

If dyno is restarting, upgrade to a larger dyno:
```bash
heroku dyno:type standard-1x --app phoenix-drive-api
```

## Updating Application

After making code changes:

```bash
git add .
git commit -m "Update: description of changes"
git push heroku main
```

Heroku automatically redeploys on push.

## Useful Commands Reference

| Command | Purpose |
|---------|---------|
| `heroku create APP_NAME` | Create new app |
| `heroku config` | View environment variables |
| `heroku config:set KEY=VALUE` | Set environment variable |
| `heroku logs --tail` | View real-time logs |
| `heroku ps` | View running dynos |
| `heroku releases` | View deployment history |
| `heroku releases:rollback` | Revert to previous version |
| `heroku addons` | View add-ons |
| `heroku domains` | View custom domains |
| `git push heroku main` | Deploy application |

## Production Checklist

- [ ] Heroku app created
- [ ] PostgreSQL database added
- [ ] Environment variables configured
- [ ] Code deployed successfully
- [ ] Database migrations run
- [ ] Health endpoint responds
- [ ] API endpoints tested
- [ ] Logs monitored for errors
- [ ] Custom domain configured (optional)
- [ ] Mobile app updated with production URL

## Next Steps

1. **Update Mobile App** — Change API URL in app.config.ts to `https://phoenix-drive-api.herokuapp.com`
2. **Build Desktop App** — Run `bash build-all-platforms.sh` to create installers
3. **Run E2E Tests** — Execute `bash run-e2e-tests.sh https://phoenix-drive-api.herokuapp.com`
4. **Configure Monitoring** — Set up error tracking and performance monitoring
5. **Publish Releases** — Create GitHub releases with desktop app installers

## Support

For Heroku documentation: https://devcenter.heroku.com/
For PhoenixDrive issues: Check logs with `heroku logs --tail --app phoenix-drive-api`

---
**Created:** $(date)
**Version:** 1.0.0
