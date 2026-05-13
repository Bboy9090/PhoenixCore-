#!/bin/bash
# =============================================================================
# Phoenix OS — Build Host Verification Script
# File: scripts/verify-host.sh
#
# Checks that the build host meets all requirements for building Phoenix OS.
# Run this before build-iso.sh.
#
# Usage: ./scripts/verify-host.sh
# Exit codes: 0 = all checks pass, 1 = one or more checks failed
# =============================================================================

set -euo pipefail

# ---- Color output ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check_pass() { echo -e "  ${GREEN}✓${NC} $*"; (( PASS++ )) || true; }
check_fail() { echo -e "  ${RED}✗${NC} $*"; (( FAIL++ )) || true; }
check_warn() { echo -e "  ${YELLOW}⚠${NC} $*"; (( WARN++ )) || true; }

echo ""
echo -e "${BOLD}Phoenix OS Build Host Verification${NC}"
echo -e "────────────────────────────────────"

# ---- Operating system ----
echo ""
echo -e "${BOLD}Operating System${NC}"

OS_ID=$(. /etc/os-release && echo "${ID:-unknown}")
OS_VERSION=$(. /etc/os-release && echo "${VERSION_ID:-unknown}")
OS_CODENAME=$(. /etc/os-release && echo "${VERSION_CODENAME:-unknown}")

if [[ "${OS_ID}" == "ubuntu" ]]; then
    if [[ "${OS_VERSION}" == "22.04" || "${OS_VERSION}" == "24.04" ]]; then
        check_pass "Ubuntu ${OS_VERSION} (${OS_CODENAME}) — supported"
    else
        check_warn "Ubuntu ${OS_VERSION} detected — only 22.04 and 24.04 are tested"
    fi
elif [[ "${OS_ID}" == "debian" ]]; then
    check_warn "Debian detected — build may work but is not officially tested. Use Ubuntu 24.04."
else
    check_fail "Unsupported OS: ${OS_ID} ${OS_VERSION}. Use Ubuntu 22.04 or 24.04 LTS."
fi

# ---- Architecture ----
echo ""
echo -e "${BOLD}Architecture${NC}"

HOST_ARCH=$(uname -m)
if [[ "${HOST_ARCH}" == "x86_64" ]]; then
    check_pass "Host architecture: x86_64 (builds amd64 and arm64 with cross-tools)"
else
    check_warn "Host architecture: ${HOST_ARCH} — cross-compilation may be needed"
fi

# ---- Required packages ----
echo ""
echo -e "${BOLD}Required Packages${NC}"

REQUIRED_PACKAGES=(
    live-build
    debootstrap
    squashfs-tools
    xorriso
    grub-pc-bin
    grub-efi-amd64-bin
    mtools
    dosfstools
    isolinux
    git
    curl
    dpkg-dev
)

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if dpkg -l "${pkg}" 2>/dev/null | grep -q "^ii"; then
        check_pass "Package installed: ${pkg}"
    else
        check_fail "Package missing: ${pkg} — run: sudo apt install ${pkg}"
    fi
done

# Check live-build version
LB_VERSION=$(lb --version 2>/dev/null || echo "unknown")
echo -e "  ${BLUE}i${NC} live-build version: ${LB_VERSION}"

# ---- Disk space ----
echo ""
echo -e "${BOLD}Disk Space${NC}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AVAILABLE_KB=$(df -k "${REPO_ROOT}" | tail -1 | awk '{print $4}')
AVAILABLE_GB=$(( AVAILABLE_KB / 1024 / 1024 ))
REQUIRED_GB=35

if [[ "${AVAILABLE_GB}" -ge "${REQUIRED_GB}" ]]; then
    check_pass "Available disk space: ${AVAILABLE_GB} GB (minimum: ${REQUIRED_GB} GB)"
else
    check_fail "Insufficient disk space: ${AVAILABLE_GB} GB available, ${REQUIRED_GB} GB required"
fi

# ---- Memory ----
echo ""
echo -e "${BOLD}Memory${NC}"

TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_RAM_GB=$(( TOTAL_RAM_KB / 1024 / 1024 ))
REQUIRED_RAM_GB=8

if [[ "${TOTAL_RAM_GB}" -ge "${REQUIRED_RAM_GB}" ]]; then
    check_pass "RAM: ${TOTAL_RAM_GB} GB (minimum: ${REQUIRED_RAM_GB} GB)"
elif [[ "${TOTAL_RAM_GB}" -ge 4 ]]; then
    check_warn "RAM: ${TOTAL_RAM_GB} GB — build may succeed but could be slow. 8 GB recommended."
else
    check_fail "RAM: ${TOTAL_RAM_GB} GB — insufficient. 8 GB required."
fi

# ---- Network connectivity ----
echo ""
echo -e "${BOLD}Network${NC}"

if curl -s --connect-timeout 5 "http://archive.ubuntu.com/ubuntu/" >/dev/null 2>&1; then
    check_pass "Ubuntu archive reachable: http://archive.ubuntu.com/ubuntu/"
else
    check_warn "Cannot reach Ubuntu archive. Build requires internet for package downloads."
fi

# ---- Root/sudo ----
echo ""
echo -e "${BOLD}Privileges${NC}"

if [[ "$(id -u)" -eq 0 ]]; then
    check_pass "Running as root"
elif sudo -n true 2>/dev/null; then
    check_warn "Not root, but passwordless sudo available. build-iso.sh requires root."
else
    check_fail "build-iso.sh must be run as root. Use: sudo ./scripts/build-iso.sh"
fi

# ---- KVM (optional, for testing) ----
echo ""
echo -e "${BOLD}Virtualization (for testing — optional)${NC}"

if command -v qemu-system-x86_64 >/dev/null 2>&1; then
    check_pass "QEMU available: $(qemu-system-x86_64 --version | head -1)"
else
    check_warn "QEMU not found — smoke tests will not work. Install: sudo apt install qemu-system-x86"
fi

if [[ -c /dev/kvm ]]; then
    check_pass "KVM available (/dev/kvm exists) — QEMU boots will be fast"
else
    check_warn "KVM not available — QEMU will emulate (slow). Enable VT-x/AMD-V in BIOS."
fi

# ---- Summary ----
echo ""
echo -e "────────────────────────────────────"
echo -e "${BOLD}Results:${NC} ${GREEN}${PASS} passed${NC}  ${RED}${FAIL} failed${NC}  ${YELLOW}${WARN} warnings${NC}"
echo ""

if [[ "${FAIL}" -gt 0 ]]; then
    echo -e "${RED}${BOLD}Host verification failed.${NC} Fix the errors above before building."
    exit 1
elif [[ "${WARN}" -gt 0 ]]; then
    echo -e "${YELLOW}Host verification passed with warnings.${NC} Review warnings before building."
    exit 0
else
    echo -e "${GREEN}${BOLD}Host verification passed.${NC} Ready to build."
    exit 0
fi
