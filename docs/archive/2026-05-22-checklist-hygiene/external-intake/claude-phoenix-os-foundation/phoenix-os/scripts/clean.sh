#!/bin/bash
# =============================================================================
# Phoenix OS — Clean Script
# File: scripts/clean.sh
#
# Cleans the live-build workspace and output directory.
# Run this before a fresh build to ensure no stale state.
#
# Usage:
#   sudo ./scripts/clean.sh           # Clean build artifacts (keep package cache)
#   sudo ./scripts/clean.sh --all     # Clean everything including package cache
#   sudo ./scripts/clean.sh --output  # Also clean the output/ directory
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUILD_DIR="${REPO_ROOT}/build"

# ---- Color output ----
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }

CLEAN_ALL=false
CLEAN_OUTPUT=false

for arg in "$@"; do
    case "${arg}" in
        --all)    CLEAN_ALL=true ;;
        --output) CLEAN_OUTPUT=true ;;
        --help|-h)
            echo "Usage: sudo ./scripts/clean.sh [--all] [--output]"
            echo "  (no flags)  Clean lb build state, keep package cache and output/"
            echo "  --all       Clean everything including package cache"
            echo "  --output    Also clean output/ directory (ISO files)"
            exit 0
            ;;
    esac
done

echo ""
echo -e "${BOLD}Phoenix OS — Build Cleanup${NC}"
echo "────────────────────────────────────"

if [[ "$(id -u)" -ne 0 ]]; then
    echo "Warning: Some lb clean operations require root. Consider running with sudo."
fi

# ---- Change to build directory ----
if [[ -d "${BUILD_DIR}" ]]; then
    cd "${BUILD_DIR}"
    
    if "${CLEAN_ALL}"; then
        log_info "Running: lb clean --all (includes package cache)"
        lb clean --all 2>/dev/null || true
    else
        log_info "Running: lb clean --nopackages (keeps package cache)"
        lb clean --nopackages 2>/dev/null || true
    fi
    log_success "live-build state cleaned"
else
    log_info "Build directory does not exist — nothing to clean"
fi

# ---- Clean output directory ----
if "${CLEAN_OUTPUT}"; then
    if [[ -d "${REPO_ROOT}/output" ]]; then
        log_info "Cleaning output directory"
        rm -f "${REPO_ROOT}/output"/*.iso
        rm -f "${REPO_ROOT}/output"/SHA256SUMS*
        rm -f "${REPO_ROOT}/output"/lb-*.log
        log_success "Output directory cleaned"
    fi
fi

# ---- Clean locally-built .deb packages from lb config ----
if [[ -d "${BUILD_DIR}/config/packages.chroot" ]]; then
    log_info "Cleaning locally-built packages from chroot"
    rm -f "${BUILD_DIR}/config/packages.chroot"/*.deb
    log_success "Local packages cleaned"
fi

echo ""
log_success "Clean complete. Run sudo ./scripts/build-iso.sh to build."
echo ""
