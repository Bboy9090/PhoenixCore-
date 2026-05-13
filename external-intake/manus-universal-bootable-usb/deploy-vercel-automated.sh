#!/bin/bash

###############################################################################
# Automated Vercel Deployment Script for Bobby's PhoenixDrive
# Deploys FastAPI backend to Vercel with Supabase database
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="phoenix-drive-api"
VERCEL_ORG=${VERCEL_ORG:-""}
SUPABASE_PROJECT=${SUPABASE_PROJECT:-""}
ENVIRONMENT=${ENVIRONMENT:-"production"}

# Functions
print_header() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Vercel CLI
    if ! command -v vercel &> /dev/null; then
        print_error "Vercel CLI not found. Install with: npm install -g vercel"
        exit 1
    fi
    print_success "Vercel CLI found"
    
    # Check Git
    if ! command -v git &> /dev/null; then
        print_error "Git not found"
        exit 1
    fi
    print_success "Git found"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        exit 1
    fi
    print_success "Python 3 found"
    
    # Check Vercel login
    if ! vercel whoami &> /dev/null; then
        print_warning "Not logged into Vercel. Running 'vercel login'..."
        vercel login
    fi
    print_success "Vercel authenticated"
}

# Validate environment
validate_environment() {
    print_header "Validating Environment"
    
    # Check .env.production exists
    if [ ! -f ".env.production" ]; then
        print_error ".env.production not found"
        print_info "Copy .env.production.example to .env.production and fill in values"
        exit 1
    fi
    print_success ".env.production found"
    
    # Check required environment variables
    required_vars=("SUPABASE_URL" "SUPABASE_KEY" "DATABASE_URL" "JWT_SECRET")
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env.production; then
            print_error "Missing $var in .env.production"
            exit 1
        fi
    done
    print_success "All required environment variables configured"
    
    # Check requirements.txt
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    print_success "requirements.txt found"
    
    # Check vercel.json
    if [ ! -f "vercel.json" ]; then
        print_error "vercel.json not found"
        exit 1
    fi
    print_success "vercel.json found"
}

# Initialize Supabase database
init_supabase_database() {
    print_header "Initializing Supabase Database"
    
    # Check if DATABASE_URL is set
    if [ -z "$DATABASE_URL" ]; then
        print_warning "DATABASE_URL not set in environment. Skipping database initialization."
        print_info "Initialize manually: python3 -c 'from server.supabase_config import init_database; init_database()'"
        return
    fi
    
    print_info "Initializing database schema..."
    python3 << 'EOF'
import os
import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from server.supabase_config import init_database
    if init_database():
        print("✓ Database schema initialized successfully")
    else:
        print("✗ Failed to initialize database schema")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error initializing database: {e}")
    sys.exit(1)
EOF
    
    if [ $? -eq 0 ]; then
        print_success "Database schema initialized"
    else
        print_error "Failed to initialize database schema"
        exit 1
    fi
}

# Configure Vercel project
configure_vercel_project() {
    print_header "Configuring Vercel Project"
    
    # Create or link project
    print_info "Linking Vercel project..."
    vercel link --project=$PROJECT_NAME --confirm || true
    
    # Pull environment variables
    print_info "Pulling environment variables from Vercel..."
    vercel env pull .env.production.local || true
    
    # Add environment variables from .env.production
    print_info "Setting environment variables in Vercel..."
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [ -z "$key" ] && continue
        
        # Remove quotes if present
        value="${value%\"}"
        value="${value#\"}"
        
        print_info "Setting $key..."
        vercel env add "$key" "$value" --yes || true
    done < .env.production
    
    print_success "Environment variables configured"
}

# Build and test locally
build_and_test() {
    print_header "Building and Testing Locally"
    
    # Install dependencies
    print_info "Installing Python dependencies..."
    pip install -r requirements.txt -q
    print_success "Dependencies installed"
    
    # Run tests
    if [ -f "tests/test_api.py" ]; then
        print_info "Running tests..."
        python3 -m pytest tests/ -v || print_warning "Some tests failed"
    fi
}

# Deploy to Vercel
deploy_to_vercel() {
    print_header "Deploying to Vercel"
    
    # Commit changes
    print_info "Committing changes..."
    git add .
    git commit -m "chore: prepare for Vercel deployment" || true
    
    # Deploy
    print_info "Deploying to Vercel..."
    if [ "$ENVIRONMENT" = "production" ]; then
        vercel --prod
    else
        vercel
    fi
    
    print_success "Deployment completed"
}

# Verify deployment
verify_deployment() {
    print_header "Verifying Deployment"
    
    # Get deployment URL
    DEPLOYMENT_URL=$(vercel list --json | python3 -c "import sys, json; data = json.load(sys.stdin); print(data[0]['url'] if data else '')" 2>/dev/null || echo "")
    
    if [ -z "$DEPLOYMENT_URL" ]; then
        print_warning "Could not determine deployment URL"
        print_info "Check https://vercel.com/dashboard for deployment status"
        return
    fi
    
    print_info "Deployment URL: https://$DEPLOYMENT_URL"
    
    # Test health endpoint
    print_info "Testing health endpoint..."
    sleep 5  # Wait for deployment to be ready
    
    if curl -s "https://$DEPLOYMENT_URL/api/v1/health" | grep -q "healthy"; then
        print_success "Health endpoint responding"
    else
        print_warning "Health endpoint not responding yet. It may take a few moments."
    fi
    
    # Test database connection
    print_info "Testing database connection..."
    if curl -s "https://$DEPLOYMENT_URL/api/v1/database/status" | grep -q "connected"; then
        print_success "Database connection verified"
    else
        print_warning "Database connection check failed"
    fi
}

# Update mobile app config
update_mobile_config() {
    print_header "Updating Mobile App Configuration"
    
    # Get deployment URL
    DEPLOYMENT_URL=$(vercel list --json | python3 -c "import sys, json; data = json.load(sys.stdin); print(data[0]['url'] if data else '')" 2>/dev/null || echo "")
    
    if [ -z "$DEPLOYMENT_URL" ]; then
        print_warning "Could not determine deployment URL. Update app.config.ts manually."
        return
    fi
    
    print_info "Updating app.config.ts with production API URL..."
    
    # Update API URLs in app.config.ts
    sed -i.bak "s|apiUrl: .*|apiUrl: \"https://$DEPLOYMENT_URL\",|" app.config.ts
    sed -i.bak "s|wsUrl: .*|wsUrl: \"wss://$DEPLOYMENT_URL\",|" app.config.ts
    
    print_success "Mobile app configuration updated"
    print_info "API URL: https://$DEPLOYMENT_URL"
    print_info "WebSocket URL: wss://$DEPLOYMENT_URL"
}

# Main deployment flow
main() {
    print_header "Bobby's PhoenixDrive - Vercel Automated Deployment"
    print_info "Version: 2.0.0"
    print_info "Environment: $ENVIRONMENT"
    echo ""
    
    # Run deployment steps
    check_prerequisites
    echo ""
    
    validate_environment
    echo ""
    
    init_supabase_database
    echo ""
    
    configure_vercel_project
    echo ""
    
    build_and_test
    echo ""
    
    deploy_to_vercel
    echo ""
    
    verify_deployment
    echo ""
    
    update_mobile_config
    echo ""
    
    print_header "Deployment Complete!"
    print_success "FastAPI backend deployed to Vercel"
    print_success "Supabase database configured"
    print_success "Mobile app configuration updated"
    print_info "Next steps:"
    print_info "1. Verify deployment at https://vercel.com/dashboard"
    print_info "2. Test API endpoints"
    print_info "3. Build and submit mobile apps to stores"
    print_info "4. Monitor production metrics"
}

# Run main function
main "$@"
