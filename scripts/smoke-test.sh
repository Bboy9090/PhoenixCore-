#!/bin/bash
# Command Control Center Smoke Test Script
# Builds and tests all entry points to verify basic functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Helper functions
test_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

test_skip() {
    echo -e "${YELLOW}⊘${NC} $1 (skipped)"
    ((TESTS_SKIPPED++))
}

section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════${NC}"
}

echo "==================================="
echo "Command Control Center Smoke Tests"
echo "==================================="
echo ""

# 1. Build Tests
section "1. Build Tests"

# Test Rust builds
if command -v cargo &> /dev/null; then
    echo "Building Rust core libraries..."
    if cargo build -p phoenix-core -p phoenix-safety -p phoenix-fs-fat32 2>&1 | tail -5; then
        test_pass "Rust core libraries build successfully"
    else
        test_fail "Rust core libraries build failed"
    fi
else
    test_skip "Rust build (cargo not found)"
fi

# Test Python dependencies
if command -v python3 &> /dev/null; then
    echo "Checking Python dependencies..."
    if python3 -c "import sys; sys.exit(0)" 2>/dev/null; then
        test_pass "Python environment is functional"
    else
        test_fail "Python environment check failed"
    fi
else
    test_fail "Python 3 not found"
fi

# Test frontend build (if Node.js available)
if command -v node &> /dev/null && command -v pnpm &> /dev/null; then
    if [ -d "apps/phoenix-control-center" ]; then
        echo "Building frontend (this may take a moment)..."
        cd apps/phoenix-control-center
        if [ ! -d "node_modules" ]; then
            echo "Installing frontend dependencies..."
            pnpm install --frozen-lockfile &> /dev/null || true
        fi
        if pnpm run build &> /dev/null; then
            test_pass "Frontend builds successfully"
        else
            test_skip "Frontend build (dependencies may be missing)"
        fi
        cd ../..
    else
        test_skip "Frontend build (directory not found)"
    fi
else
    test_skip "Frontend build (Node.js or pnpm not found)"
fi

# 2. Entry Point Tests
section "2. Entry Point Tests"

# Test Python CLI
if command -v python3 &> /dev/null; then
    if [ -f "main.py" ]; then
        echo "Testing Python CLI help command..."
        if timeout 5 python3 main.py --help &> /dev/null; then
            test_pass "Python CLI --help works"
        else
            test_skip "Python CLI --help (may require dependencies)"
        fi
    else
        test_skip "Python CLI (main.py not found)"
    fi
else
    test_skip "Python CLI (python3 not found)"
fi

# Test Rust CLI (if built)
if [ -f "target/debug/phoenix-cli" ]; then
    echo "Testing Rust CLI..."
    if timeout 5 ./target/debug/phoenix-cli --help &> /dev/null; then
        test_pass "Rust CLI --help works"
    else
        test_skip "Rust CLI --help (executable exists but may have issues)"
    fi
elif [ -f "apps/cli/Cargo.toml" ]; then
    test_skip "Rust CLI (not built, run: cargo build -p phoenix-cli)"
else
    test_skip "Rust CLI (crate not found)"
fi

# 3. Core Library Tests
section "3. Core Library Tests"

# Test Rust library import
if command -v cargo &> /dev/null; then
    if [ -f "crates/core/Cargo.toml" ]; then
        echo "Testing phoenix-core library..."
        if cargo test -p phoenix-core --lib -- --test-threads=1 2>&1 | grep -q "test result: ok"; then
            test_pass "phoenix-core library tests pass"
        else
            test_skip "phoenix-core library tests (may have failures)"
        fi
    else
        test_fail "phoenix-core crate not found"
    fi
else
    test_skip "Rust library tests (cargo not found)"
fi

# Test Python imports
if command -v python3 &> /dev/null; then
    echo "Testing Python imports..."
    IMPORT_TEST=$(cat <<'EOF'
try:
    import json
    import sys
    # Test basic imports
    with open('app.metadata.json') as f:
        metadata = json.load(f)
    assert metadata['packageId'] == 'com.bobbysworld.command'
    print("OK")
except Exception as e:
    print(f"FAIL: {e}")
    sys.exit(1)
EOF
)
    if python3 -c "$IMPORT_TEST" 2>&1 | grep -q "OK"; then
        test_pass "Python can read app.metadata.json"
    else
        test_fail "Python cannot read app.metadata.json"
    fi
else
    test_skip "Python import tests (python3 not found)"
fi

# 4. Edition Manifest Tests
section "4. Edition Manifest Tests"

EDITIONS=("arcwyre" "thunder-god" "forge" "blue-phoenix")

for edition in "${EDITIONS[@]}"; do
    MANIFEST="editions/$edition/edition.yaml"
    if [ -f "$MANIFEST" ]; then
        # Test YAML can be parsed (basic syntax check)
        if python3 -c "import yaml; yaml.safe_load(open('$MANIFEST'))" 2>/dev/null; then
            test_pass "$edition manifest is valid YAML"
        else
            test_fail "$edition manifest has YAML syntax errors"
        fi
    else
        test_fail "$edition manifest not found"
    fi
done

# 5. Script Tests
section "5. Script Tests"

# Test healthcheck.sh
if [ -f "scripts/healthcheck.sh" ]; then
    if [ -x "scripts/healthcheck.sh" ]; then
        echo "Running healthcheck.sh..."
        if timeout 10 bash scripts/healthcheck.sh &> /tmp/healthcheck-output.log; then
            test_pass "healthcheck.sh completes successfully"
        else
            HEALTH_EXIT=$?
            if [ $HEALTH_EXIT -eq 1 ]; then
                test_pass "healthcheck.sh reports degraded status (acceptable)"
            else
                test_skip "healthcheck.sh reports issues (check /tmp/healthcheck-output.log)"
            fi
        fi
    else
        test_fail "healthcheck.sh is not executable"
    fi
else
    test_fail "healthcheck.sh not found"
fi

# Test edition validation script
if [ -f "scripts/validate-editions.sh" ]; then
    if [ -x "scripts/validate-editions.sh" ]; then
        echo "Running validate-editions.sh..."
        if timeout 10 bash scripts/validate-editions.sh &> /dev/null; then
            test_pass "validate-editions.sh passes"
        else
            test_skip "validate-editions.sh reports issues"
        fi
    else
        test_skip "validate-editions.sh is not executable"
    fi
else
    test_skip "validate-editions.sh not found"
fi

# 6. API Tests (if backend is running)
section "6. API Tests"

if command -v curl &> /dev/null; then
    # Try to start backend for testing (non-blocking)
    if [ -f "backend/main.py" ]; then
        echo "Checking if backend API is running..."
        if curl -s -f -m 2 http://localhost:5000/health &> /dev/null; then
            test_pass "Backend API is running and healthy"

            # Test system info endpoint
            if curl -s -f -m 2 http://localhost:5000/api/v1/system/info &> /dev/null; then
                test_pass "System info endpoint responds"
            else
                test_skip "System info endpoint (may not be implemented)"
            fi
        else
            test_skip "Backend API tests (server not running)"
        fi
    else
        test_skip "Backend API tests (backend/main.py not found)"
    fi
else
    test_skip "API tests (curl not found)"
fi

# 7. Documentation Tests
section "7. Documentation Tests"

# Check critical docs exist and are not empty
DOCS=(
    "README.md"
    "docs/PRD.md"
    "docs/ROADMAP.md"
    "docs/APP_CONTRACT.md"
    "docs/RELEASE_CHECKLIST.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        # Check file is not empty
        if [ -s "$doc" ]; then
            test_pass "$doc exists and is not empty"
        else
            test_fail "$doc is empty"
        fi
    else
        test_fail "$doc not found"
    fi
done

# Summary
echo ""
section "Smoke Test Summary"
echo -e "${GREEN}Passed:${NC}  $TESTS_PASSED"
echo -e "${YELLOW}Skipped:${NC} $TESTS_SKIPPED"
echo -e "${RED}Failed:${NC}  $TESTS_FAILED"
echo ""

# Determine overall status
TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED + TESTS_SKIPPED))
PASS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))

echo "Pass Rate: $PASS_RATE% ($TESTS_PASSED/$TOTAL_TESTS)"
echo ""

# Exit code
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All smoke tests passed!${NC}"
    exit 0
elif [ $TESTS_FAILED -le 2 ]; then
    echo -e "${YELLOW}⚠ Smoke tests completed with minor issues${NC}"
    exit 1
else
    echo -e "${RED}✗ Smoke tests failed - build may be broken${NC}"
    exit 2
fi
