#!/bin/bash

# Bobby's PhoenixDrive — Automated Heroku Deployment Script
# This script automates the entire Heroku deployment process

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="${1:-phoenixdrive-api}"
HEROKU_REGION="${2:-us}"
DYNO_TYPE="${3:-standard-1x}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Bobby's PhoenixDrive - Heroku Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check Prerequisites
echo -e "${YELLOW}Step 1: Checking prerequisites...${NC}"

if ! command -v heroku &> /dev/null; then
    echo -e "${RED}✗ Heroku CLI not found. Install from https://cli.heroku.com${NC}"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo -e "${RED}✗ Git not found. Please install Git.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Heroku CLI found${NC}"
echo -e "${GREEN}✓ Git found${NC}"

# Step 2: Authenticate with Heroku
echo ""
echo -e "${YELLOW}Step 2: Authenticating with Heroku...${NC}"

if heroku auth:whoami &> /dev/null; then
    HEROKU_USER=$(heroku auth:whoami)
    echo -e "${GREEN}✓ Authenticated as: $HEROKU_USER${NC}"
else
    echo -e "${YELLOW}! Not authenticated. Opening browser for login...${NC}"
    heroku login
fi

# Step 3: Create Heroku App
echo ""
echo -e "${YELLOW}Step 3: Creating Heroku application...${NC}"

if heroku apps:info "$APP_NAME" &> /dev/null; then
    echo -e "${YELLOW}! App '$APP_NAME' already exists${NC}"
else
    echo -e "Creating app '$APP_NAME'..."
    heroku create "$APP_NAME" --region "$HEROKU_REGION"
    echo -e "${GREEN}✓ App created: $APP_NAME${NC}"
fi

# Step 4: Add PostgreSQL Database
echo ""
echo -e "${YELLOW}Step 4: Adding PostgreSQL database...${NC}"

if heroku addons:info heroku-postgresql:hobby-dev --app "$APP_NAME" &> /dev/null; then
    echo -e "${YELLOW}! Database already provisioned${NC}"
else
    echo -e "Provisioning database..."
    heroku addons:create heroku-postgresql:hobby-dev --app "$APP_NAME"
    echo -e "${GREEN}✓ Database provisioned${NC}"
fi

# Step 5: Configure Environment Variables
echo ""
echo -e "${YELLOW}Step 5: Configuring environment variables...${NC}"

# Generate SECRET_KEY
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Set environment variables
heroku config:set FLASK_ENV=production --app "$APP_NAME"
heroku config:set SECRET_KEY="$SECRET_KEY" --app "$APP_NAME"
heroku config:set PYTHONUNBUFFERED=1 --app "$APP_NAME"

echo -e "${GREEN}✓ Environment variables configured${NC}"

# Step 6: Configure Optional Monitoring
echo ""
echo -e "${YELLOW}Step 6: Configuring monitoring (optional)...${NC}"

read -p "Do you want to configure Sentry error tracking? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter Sentry DSN: " SENTRY_DSN
    heroku config:set SENTRY_DSN="$SENTRY_DSN" --app "$APP_NAME"
    echo -e "${GREEN}✓ Sentry configured${NC}"
fi

read -p "Do you want to configure Datadog monitoring? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter Datadog API Key: " DATADOG_API_KEY
    read -p "Enter Datadog App Key: " DATADOG_APP_KEY
    heroku config:set DATADOG_API_KEY="$DATADOG_API_KEY" --app "$APP_NAME"
    heroku config:set DATADOG_APP_KEY="$DATADOG_APP_KEY" --app "$APP_NAME"
    echo -e "${GREEN}✓ Datadog configured${NC}"
fi

# Step 7: Configure Email (Optional)
echo ""
echo -e "${YELLOW}Step 7: Configuring email notifications (optional)...${NC}"

read -p "Do you want to configure email notifications? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter SMTP server (default: smtp.gmail.com): " SMTP_SERVER
    SMTP_SERVER=${SMTP_SERVER:-smtp.gmail.com}
    read -p "Enter SMTP port (default: 587): " SMTP_PORT
    SMTP_PORT=${SMTP_PORT:-587}
    read -p "Enter SMTP username: " SMTP_USERNAME
    read -sp "Enter SMTP password: " SMTP_PASSWORD
    echo
    read -p "Enter admin email: " ADMIN_EMAIL
    
    heroku config:set SMTP_SERVER="$SMTP_SERVER" --app "$APP_NAME"
    heroku config:set SMTP_PORT="$SMTP_PORT" --app "$APP_NAME"
    heroku config:set SMTP_USERNAME="$SMTP_USERNAME" --app "$APP_NAME"
    heroku config:set SMTP_PASSWORD="$SMTP_PASSWORD" --app "$APP_NAME"
    heroku config:set ADMIN_EMAIL="$ADMIN_EMAIL" --app "$APP_NAME"
    echo -e "${GREEN}✓ Email notifications configured${NC}"
fi

# Step 8: Add Heroku Remote
echo ""
echo -e "${YELLOW}Step 8: Adding Heroku Git remote...${NC}"

if git remote get-url heroku &> /dev/null; then
    echo -e "${YELLOW}! Heroku remote already exists${NC}"
else
    git remote add heroku "https://git.heroku.com/$APP_NAME.git"
    echo -e "${GREEN}✓ Heroku remote added${NC}"
fi

# Step 9: Deploy Code
echo ""
echo -e "${YELLOW}Step 9: Deploying code to Heroku...${NC}"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "Pushing branch '$CURRENT_BRANCH' to Heroku..."

git push heroku "$CURRENT_BRANCH:main" --force

echo -e "${GREEN}✓ Code deployed${NC}"

# Step 10: Run Migrations
echo ""
echo -e "${YELLOW}Step 10: Running database migrations...${NC}"

heroku run python3 -c "from server.api import db; db.create_all()" --app "$APP_NAME"

echo -e "${GREEN}✓ Database migrations completed${NC}"

# Step 11: Get App URL
echo ""
echo -e "${YELLOW}Step 11: Retrieving app information...${NC}"

APP_URL=$(heroku apps:info "$APP_NAME" --json | python3 -c "import sys, json; print(json.load(sys.stdin)['app']['web_url'])")

echo -e "${GREEN}✓ App URL: $APP_URL${NC}"

# Step 12: Test API
echo ""
echo -e "${YELLOW}Step 12: Testing API endpoints...${NC}"

echo -n "Testing health endpoint... "
if curl -s "$APP_URL/api/v1/health" | grep -q "healthy"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo -n "Testing Boot Camp endpoints... "
if curl -s "$APP_URL/api/v1/bootcamp/drivers" | grep -q "driver_packages"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Step 13: Display Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deployment Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Application: $APP_NAME${NC}"
echo -e "${GREEN}✓ URL: $APP_URL${NC}"
echo -e "${GREEN}✓ Region: $HEROKU_REGION${NC}"
echo -e "${GREEN}✓ Database: PostgreSQL (hobby-dev)${NC}"
echo -e "${GREEN}✓ Environment: production${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Update mobile app with production API URL: $APP_URL"
echo -e "2. Update desktop app with production API URL: $APP_URL"
echo -e "3. Run E2E tests against production"
echo -e "4. Monitor logs: heroku logs --tail --app $APP_NAME"
echo -e "5. View dashboard: heroku open --app $APP_NAME"
echo ""
echo -e "${GREEN}Deployment completed successfully!${NC}"
