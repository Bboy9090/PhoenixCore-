#!/bin/bash

# Bobby's PhoenixDrive - Heroku Deployment Script
# Automates the deployment process to Heroku

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="${1:-phoenix-drive-api}"
REGION="${2:-us}"
ENVIRONMENT="${3:-production}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Bobby's PhoenixDrive - Heroku Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v heroku &> /dev/null; then
    echo -e "${RED}Error: Heroku CLI is not installed${NC}"
    echo "Install from: https://devcenter.heroku.com/articles/heroku-cli"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: Git is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Check Heroku login
echo -e "${YELLOW}Checking Heroku authentication...${NC}"

if ! heroku auth:whoami &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Heroku. Please log in:${NC}"
    heroku login
fi

echo -e "${GREEN}✓ Heroku authentication verified${NC}"
echo ""

# Check if app exists
echo -e "${YELLOW}Checking if Heroku app exists...${NC}"

if heroku apps:info -a "$APP_NAME" &> /dev/null; then
    echo -e "${GREEN}✓ App '$APP_NAME' already exists${NC}"
    APP_EXISTS=true
else
    echo -e "${YELLOW}App '$APP_NAME' does not exist. Creating...${NC}"
    heroku create "$APP_NAME" --region "$REGION"
    APP_EXISTS=false
    echo -e "${GREEN}✓ App created successfully${NC}"
fi

echo ""

# Get app URL
APP_URL=$(heroku apps:info -a "$APP_NAME" --json | grep -o '"web_url":"[^"]*' | cut -d'"' -f4)
echo -e "${BLUE}App URL: $APP_URL${NC}"
echo ""

# Set environment variables
echo -e "${YELLOW}Setting environment variables...${NC}"

# Generate secret keys
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Set required environment variables
heroku config:set \
    -a "$APP_NAME" \
    FLASK_ENV="$ENVIRONMENT" \
    SECRET_KEY="$SECRET_KEY" \
    JWT_SECRET="$JWT_SECRET" \
    CORS_ORIGINS="$APP_URL" \
    LOG_LEVEL="INFO" \
    PYTHON_RUNTIME="python-3.11"

echo -e "${GREEN}✓ Environment variables set${NC}"
echo ""

# Prompt for optional monitoring setup
echo -e "${YELLOW}Do you want to set up monitoring? (y/n)${NC}"
read -r SETUP_MONITORING

if [[ "$SETUP_MONITORING" == "y" || "$SETUP_MONITORING" == "Y" ]]; then
    echo ""
    echo -e "${YELLOW}Sentry Setup${NC}"
    echo -n "Enter Sentry DSN (or press Enter to skip): "
    read -r SENTRY_DSN
    
    if [ -n "$SENTRY_DSN" ]; then
        heroku config:set -a "$APP_NAME" SENTRY_DSN="$SENTRY_DSN"
        echo -e "${GREEN}✓ Sentry configured${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}Datadog Setup${NC}"
    echo -n "Enter Datadog API Key (or press Enter to skip): "
    read -r DATADOG_API_KEY
    
    if [ -n "$DATADOG_API_KEY" ]; then
        heroku config:set -a "$APP_NAME" DATADOG_API_KEY="$DATADOG_API_KEY"
        echo -e "${GREEN}✓ Datadog configured${NC}"
    fi
fi

echo ""

# Add PostgreSQL addon
echo -e "${YELLOW}Setting up PostgreSQL database...${NC}"

if heroku addons:info heroku-postgresql -a "$APP_NAME" &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL already provisioned${NC}"
else
    echo -e "${YELLOW}Provisioning PostgreSQL...${NC}"
    heroku addons:create heroku-postgresql:hobby-dev -a "$APP_NAME"
    echo -e "${GREEN}✓ PostgreSQL provisioned${NC}"
fi

echo ""

# Add Redis addon (optional)
echo -e "${YELLOW}Do you want to add Redis for caching? (y/n)${NC}"
read -r SETUP_REDIS

if [[ "$SETUP_REDIS" == "y" || "$SETUP_REDIS" == "Y" ]]; then
    if heroku addons:info heroku-redis -a "$APP_NAME" &> /dev/null; then
        echo -e "${GREEN}✓ Redis already provisioned${NC}"
    else
        echo -e "${YELLOW}Provisioning Redis...${NC}"
        heroku addons:create heroku-redis:premium-0 -a "$APP_NAME"
        echo -e "${GREEN}✓ Redis provisioned${NC}"
    fi
fi

echo ""

# Create requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    echo -e "${YELLOW}Creating requirements.txt...${NC}"
    pip freeze > requirements.txt
    echo -e "${GREEN}✓ requirements.txt created${NC}"
else
    echo -e "${GREEN}✓ requirements.txt already exists${NC}"
fi

echo ""

# Check for Procfile
if [ ! -f Procfile ]; then
    echo -e "${YELLOW}Creating Procfile...${NC}"
    cat > Procfile << 'EOF'
web: gunicorn -w 4 -b 0.0.0.0:$PORT server.api:app
worker: python -m server.background_tasks
EOF
    echo -e "${GREEN}✓ Procfile created${NC}"
else
    echo -e "${GREEN}✓ Procfile already exists${NC}"
fi

echo ""

# Initialize git if needed
if [ ! -d .git ]; then
    echo -e "${YELLOW}Initializing git repository...${NC}"
    git init
    git add .
    git commit -m "Initial commit for Heroku deployment"
    echo -e "${GREEN}✓ Git repository initialized${NC}"
fi

echo ""

# Add Heroku remote
echo -e "${YELLOW}Configuring git remote...${NC}"

if git remote | grep -q heroku; then
    echo -e "${GREEN}✓ Heroku remote already configured${NC}"
else
    heroku git:remote -a "$APP_NAME"
    echo -e "${GREEN}✓ Heroku remote configured${NC}"
fi

echo ""

# Deploy to Heroku
echo -e "${YELLOW}Deploying to Heroku...${NC}"
echo -e "${BLUE}This may take a few minutes...${NC}"

git push heroku main 2>&1 | tail -20

echo ""
echo -e "${GREEN}✓ Deployment completed${NC}"
echo ""

# Run migrations
echo -e "${YELLOW}Running database migrations...${NC}"

heroku run flask db upgrade -a "$APP_NAME"

echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

# Check app status
echo -e "${YELLOW}Checking app status...${NC}"

if heroku ps -a "$APP_NAME" | grep -q "web.*up"; then
    echo -e "${GREEN}✓ App is running${NC}"
else
    echo -e "${RED}✗ App is not running${NC}"
    echo "Check logs with: heroku logs --tail -a $APP_NAME"
fi

echo ""

# Display useful information
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Deployment Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "App Name:     ${GREEN}$APP_NAME${NC}"
echo -e "App URL:      ${GREEN}$APP_URL${NC}"
echo -e "Environment:  ${GREEN}$ENVIRONMENT${NC}"
echo -e "Region:       ${GREEN}$REGION${NC}"
echo ""

echo -e "${YELLOW}Useful Commands:${NC}"
echo "  View logs:        heroku logs --tail -a $APP_NAME"
echo "  Run command:      heroku run <command> -a $APP_NAME"
echo "  Open app:         heroku open -a $APP_NAME"
echo "  View config:      heroku config -a $APP_NAME"
echo "  Restart app:      heroku restart -a $APP_NAME"
echo "  Scale dynos:      heroku ps:scale web=2 -a $APP_NAME"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Update mobile app with production API URL: $APP_URL"
echo "2. Set up custom domain (optional)"
echo "3. Configure monitoring dashboards"
echo "4. Test API endpoints"
echo "5. Monitor logs and performance"
echo ""

echo -e "${GREEN}Deployment complete! 🎉${NC}"
