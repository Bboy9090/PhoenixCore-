#!/bin/bash

################################################################################
# Phoenix OS Build Environment Verification Script
# 
# This script verifies that your system meets the requirements for building
# Phoenix OS ISO images.
#
# Usage:
#   ./scripts/verify-host.sh
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
WARNED=0

# Logging functions
log_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNED++))
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Print header
echo "═══════════════════════════════════════════════════════════"
echo "Phoenix OS Build Environment Verification"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check OS
echo "Checking Operating System..."
if grep -E "Ubuntu 22.04|Debian 12" /etc/os-release > /dev/null 2>&1; then
    OS_VERSION=$(grep VERSION_ID /etc/os-release | cut -d= -f2 | tr -d '"')
    log_pass "OS: Ubuntu 22.04 LTS or Debian 12 (Version: $OS_VERSION)"
else
    log_warn "OS: Not Ubuntu 22.04 LTS or Debian 12 (build may not work)"
    if [ -f /etc/os-release ]; then
        OS_NAME=$(grep NAME /etc/os-release | head -1 | cut -d= -f2 | tr -d '"')
        log_info "Detected: $OS_NAME"
    fi
fi
echo ""

# Check CPU
echo "Checking CPU..."
CPU_CORES=$(nproc)
if [ "$CPU_CORES" -ge 2 ]; then
    log_pass "CPU: $CPU_CORES cores (minimum 2 required)"
else
    log_fail "CPU: Only $CPU_CORES core(s) found (minimum 2 required)"
fi
echo ""

# Check RAM
echo "Checking Memory..."
TOTAL_RAM=$(free -m | awk 'NR==2 {print $2}')
AVAILABLE_RAM=$(free -m | awk 'NR==2 {print $7}')
if [ "$TOTAL_RAM" -ge 4096 ]; then
    log_pass "RAM: ${TOTAL_RAM}MB total (minimum 4GB recommended)"
elif [ "$TOTAL_RAM" -ge 2048 ]; then
    log_warn "RAM: ${TOTAL_RAM}MB total (minimum 4GB recommended, but 2GB minimum will work)"
else
    log_fail "RAM: ${TOTAL_RAM}MB total (minimum 2GB required)"
fi
log_info "Available: ${AVAILABLE_RAM}MB"
echo ""

# Check Disk Space
echo "Checking Disk Space..."
AVAILABLE_SPACE=$(df /home/ubuntu | awk 'NR==2 {print $4}')
AVAILABLE_SPACE_GB=$((AVAILABLE_SPACE / 1024 / 1024))
if [ "$AVAILABLE_SPACE_GB" -ge 50 ]; then
    log_pass "Disk: ${AVAILABLE_SPACE_GB}GB available (minimum 50GB recommended)"
elif [ "$AVAILABLE_SPACE_GB" -ge 30 ]; then
    log_warn "Disk: ${AVAILABLE_SPACE_GB}GB available (minimum 50GB recommended)"
else
    log_fail "Disk: ${AVAILABLE_SPACE_GB}GB available (minimum 30GB required)"
fi
echo ""

# Check Internet Connection
echo "Checking Internet Connection..."
if ping -c 1 archive.ubuntu.com &> /dev/null; then
    log_pass "Internet: Connected to archive.ubuntu.com"
else
    log_fail "Internet: Cannot reach archive.ubuntu.com"
fi
echo ""

# Check Required Tools
echo "Checking Required Tools..."

# live-build
if command -v lb &> /dev/null; then
    LB_VERSION=$(lb --version 2>/dev/null | head -1 || echo "unknown")
    log_pass "live-build: Installed ($LB_VERSION)"
else
    log_fail "live-build: Not installed (install with: sudo apt-get install live-build)"
fi

# git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    log_pass "git: Installed (version $GIT_VERSION)"
else
    log_warn "git: Not installed (optional for version control)"
fi

# sudo
if command -v sudo &> /dev/null; then
    log_pass "sudo: Installed"
else
    log_fail "sudo: Not installed (required for build operations)"
fi

# debootstrap
if command -v debootstrap &> /dev/null; then
    log_pass "debootstrap: Installed"
else
    log_fail "debootstrap: Not installed (install with: sudo apt-get install debootstrap)"
fi

# squashfs-tools
if command -v mksquashfs &> /dev/null; then
    log_pass "squashfs-tools: Installed"
else
    log_fail "squashfs-tools: Not installed (install with: sudo apt-get install squashfs-tools)"
fi

# xorriso
if command -v xorriso &> /dev/null; then
    log_pass "xorriso: Installed"
else
    log_fail "xorriso: Not installed (install with: sudo apt-get install xorriso)"
fi

# isolinux
if [ -f /usr/lib/ISOLINUX/isolinux.bin ]; then
    log_pass "isolinux: Installed"
else
    log_warn "isolinux: Not found (install with: sudo apt-get install isolinux)"
fi

# syslinux
if command -v syslinux &> /dev/null; then
    log_pass "syslinux: Installed"
else
    log_warn "syslinux: Not found (optional for legacy boot)"
fi

echo ""

# Check Permissions
echo "Checking Permissions..."

# Sudo without password
if sudo -n true 2> /dev/null; then
    log_pass "sudo: Can run without password prompt"
else
    log_warn "sudo: May require password prompt (add to sudoers for automated builds)"
fi

# Write to /tmp
if [ -w /tmp ]; then
    log_pass "/tmp: Writable"
else
    log_fail "/tmp: Not writable"
fi

# Write to current directory
if [ -w . ]; then
    log_pass "Current directory: Writable"
else
    log_fail "Current directory: Not writable"
fi

echo ""

# Check Optional Tools
echo "Checking Optional Tools..."

# qemu
if command -v qemu-system-x86_64 &> /dev/null; then
    log_pass "qemu: Installed (for testing ISO)"
else
    log_info "qemu: Not installed (optional for testing, install with: sudo apt-get install qemu-system-x86)"
fi

# grub
if command -v grub-mkconfig &> /dev/null; then
    log_pass "grub: Installed"
else
    log_info "grub: Not installed (optional)"
fi

# efibootmgr
if command -v efibootmgr &> /dev/null; then
    log_pass "efibootmgr: Installed"
else
    log_info "efibootmgr: Not installed (optional for UEFI boot)"
fi

echo ""

# Summary
echo "═══════════════════════════════════════════════════════════"
echo "Verification Summary"
echo "═══════════════════════════════════════════════════════════"
echo -e "Passed:  ${GREEN}$PASSED${NC}"
echo -e "Failed:  ${RED}$FAILED${NC}"
echo -e "Warned:  ${YELLOW}$WARNED${NC}"
echo ""

if [ "$FAILED" -eq 0 ]; then
    echo -e "${GREEN}✓ Your system is ready to build Phoenix OS!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. cd /home/ubuntu/phoenix-os"
    echo "  2. ./scripts/build-iso.sh"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Your system needs some fixes before building Phoenix OS${NC}"
    echo ""
    echo "To fix missing tools, run:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install live-build debootstrap squashfs-tools xorriso isolinux"
    echo ""
    exit 1
fi
