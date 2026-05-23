#!/bin/bash
# Command Control Center Health Check Script
# Verifies system, edition, registry, and service status

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNED=0

# Helper functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((CHECKS_WARNED++))
}

echo "==================================="
echo "Command Control Center Health Check"
echo "==================================="
echo ""

# 1. System Checks
echo "1. System Requirements"
echo "-----------------------------------"

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        check_pass "Python $PYTHON_VERSION (>= 3.10)"
    else
        check_fail "Python $PYTHON_VERSION (requires >= 3.10)"
    fi
else
    check_fail "Python 3 not found"
fi

# Check Rust version (optional for users, required for dev)
if command -v cargo &> /dev/null; then
    RUST_VERSION=$(cargo --version 2>&1 | awk '{print $2}')
    check_pass "Rust $RUST_VERSION"
else
    check_warn "Rust not found (optional for end users)"
fi

# Check Node.js version (optional)
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version 2>&1 | sed 's/v//')
    NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
    if [ "$NODE_MAJOR" -ge 18 ]; then
        check_pass "Node.js $NODE_VERSION (>= 18)"
    else
        check_warn "Node.js $NODE_VERSION (recommends >= 18)"
    fi
else
    check_warn "Node.js not found (optional for web UI)"
fi

echo ""

# 2. File Structure Checks
echo "2. File Structure"
echo "-----------------------------------"

# Check critical files
FILES_TO_CHECK=(
    "app.metadata.json"
    "README.md"
    "requirements.txt"
    "Cargo.toml"
    "docs/PRD.md"
    "docs/ROADMAP.md"
    "docs/APP_CONTRACT.md"
    "docs/RELEASE_CHECKLIST.md"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file exists"
    else
        check_fail "$file missing"
    fi
done

# Check critical directories
DIRS_TO_CHECK=(
    "crates/core"
    "apps/phoenix-control-center"
    "editions"
    "scripts"
    "docs"
)

for dir in "${DIRS_TO_CHECK[@]}"; do
    if [ -d "$dir" ]; then
        check_pass "$dir/ exists"
    else
        check_fail "$dir/ missing"
    fi
done

echo ""

# 3. Edition Manifest Checks
echo "3. Edition Manifests"
echo "-----------------------------------"

EDITIONS=("arcwyre" "thunder-god" "forge" "blue-phoenix")

for edition in "${EDITIONS[@]}"; do
    MANIFEST="editions/$edition/edition.yaml"
    if [ -f "$MANIFEST" ]; then
        # Validate YAML syntax (basic check)
        if grep -q "^id: $edition" "$MANIFEST" && grep -q "^display_name:" "$MANIFEST"; then
            check_pass "$edition edition manifest valid"
        else
            check_fail "$edition edition manifest invalid format"
        fi
    else
        check_fail "$edition edition manifest missing"
    fi
done

# Check for BWOS_EDITION environment variable
if [ -n "$BWOS_EDITION" ]; then
    check_pass "BWOS_EDITION set to: $BWOS_EDITION"
else
    check_warn "BWOS_EDITION not set (will use default)"
fi

echo ""

# 4. App Registry Checks
echo "4. App Registry"
echo "-----------------------------------"

# Check app.metadata.json validity
if [ -f "app.metadata.json" ]; then
    if python3 -c "import json; json.load(open('app.metadata.json'))" 2>/dev/null; then
        check_pass "app.metadata.json is valid JSON"

        # Check required fields
        PACKAGE_ID=$(python3 -c "import json; print(json.load(open('app.metadata.json')).get('packageId', ''))" 2>/dev/null)
        if [ "$PACKAGE_ID" = "com.bobbysworld.command" ]; then
            check_pass "Package ID is correct: $PACKAGE_ID"
        else
            check_fail "Package ID incorrect: $PACKAGE_ID"
        fi
    else
        check_fail "app.metadata.json is invalid JSON"
    fi
else
    check_fail "app.metadata.json not found"
fi

echo ""

# 5. Service Health Checks
echo "5. Service Health"
echo "-----------------------------------"

# Check if backend is running
if command -v curl &> /dev/null; then
    if curl -s -f -m 2 http://localhost:5000/health &> /dev/null; then
        check_pass "Backend service healthy (localhost:5000)"
    else
        check_warn "Backend service not running (optional)"
    fi
else
    check_warn "curl not found, skipping service checks"
fi

# Check Rust core library
if [ -f "crates/core/Cargo.toml" ]; then
    check_pass "phoenix-core crate present"
else
    check_fail "phoenix-core crate missing"
fi

echo ""

# 6. Build Artifact Checks
echo "6. Build Artifacts"
echo "-----------------------------------"

# Check Rust build artifacts (optional)
if [ -d "target/debug" ] || [ -d "target/release" ]; then
    check_pass "Rust build artifacts present"
else
    check_warn "Rust build artifacts not found (run cargo build)"
fi

# Check Python dependencies
if python3 -c "import pytest, fastapi, pydantic, sysinfo" 2>/dev/null; then
    check_warn "Some Python dependencies missing (run pip install -r requirements.txt)"
fi

# Check frontend build (optional)
if [ -d "apps/phoenix-control-center/dist" ]; then
    check_pass "Frontend build artifacts present"
else
    check_warn "Frontend build artifacts not found (run pnpm run build)"
fi

echo ""

# 7. Permissions Checks
echo "7. Permissions"
echo "-----------------------------------"

# Check script permissions
if [ -x "scripts/healthcheck.sh" ]; then
    check_pass "healthcheck.sh is executable"
else
    check_warn "healthcheck.sh is not executable (run chmod +x scripts/healthcheck.sh)"
fi

if [ -f "scripts/smoke-test.sh" ]; then
    if [ -x "scripts/smoke-test.sh" ]; then
        check_pass "smoke-test.sh is executable"
    else
        check_warn "smoke-test.sh is not executable"
    fi
else
    check_warn "smoke-test.sh not found"
fi

echo ""

# Summary
echo "==================================="
echo "Health Check Summary"
echo "==================================="
echo -e "${GREEN}Passed:${NC}  $CHECKS_PASSED"
echo -e "${YELLOW}Warnings:${NC} $CHECKS_WARNED"
echo -e "${RED}Failed:${NC}  $CHECKS_FAILED"
echo ""

# Exit code
if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}Overall Status: HEALTHY${NC}"
    exit 0
elif [ $CHECKS_FAILED -le 3 ]; then
    echo -e "${YELLOW}Overall Status: DEGRADED${NC}"
    exit 1
else
    echo -e "${RED}Overall Status: UNHEALTHY${NC}"
    exit 2
fi
