#!/bin/bash
# =============================================================================
# Phoenix OS — ISO Build Script
# File: scripts/build-iso.sh
#
# Builds the Phoenix OS live ISO using live-build (lb).
# Must be run as root (or with sudo) on Ubuntu 22.04 or 24.04 LTS.
#
# Usage:
#   sudo ./scripts/build-iso.sh
#   ARCH=arm64 sudo ./scripts/build-iso.sh
#   PHOENIX_VERSION=1.0.0-beta sudo ./scripts/build-iso.sh
#
# Environment variables:
#   ARCH             Target architecture (default: amd64)
#   PHOENIX_VERSION  Version string for the ISO filename (default: from VERSION file)
#   KEEP_BUILD       If set, do not clean the lb build directory on success
#   LB_VERBOSE       If set, pass --verbose to lb commands
# =============================================================================

set -euo pipefail

# ---- Script directory resolution ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ---- Configuration ----
ARCH="${ARCH:-amd64}"
PHOENIX_VERSION="${PHOENIX_VERSION:-$(cat "${REPO_ROOT}/VERSION" 2>/dev/null || echo "0.1.0-alpha")}"
BUILD_DIR="${REPO_ROOT}/build"
OUTPUT_DIR="${REPO_ROOT}/output"
LB_CONFIG_DIR="${REPO_ROOT}/live-build"
TIMESTAMP="$(date +%Y%m%d%H%M)"

ISO_NAME="phoenix-os-${PHOENIX_VERSION}-${ARCH}.iso"

# ---- Color output ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
log_step()    { echo -e "\n${BOLD}${BLUE}==>${NC}${BOLD} $*${NC}"; }

# ---- Root check ----
if [[ "$(id -u)" -ne 0 ]]; then
    log_error "This script must be run as root. Use: sudo ./scripts/build-iso.sh"
    exit 1
fi

# ---- Host verification ----
log_step "Verifying build host"
"${SCRIPT_DIR}/verify-host.sh" || {
    log_error "Host verification failed. Fix the issues above and retry."
    exit 1
}

# ---- Build custom .deb packages first ----
log_step "Building Phoenix custom packages"
if [[ -f "${SCRIPT_DIR}/package-debs.sh" ]]; then
    "${SCRIPT_DIR}/package-debs.sh" || {
        log_error "Custom package build failed."
        exit 1
    }
else
    log_warn "package-debs.sh not found; skipping custom package build."
    log_warn "Ensure custom .deb files are in live-build/config/packages.chroot/"
fi

# ---- Prepare build directory ----
log_step "Preparing build directory"

mkdir -p "${BUILD_DIR}"
mkdir -p "${OUTPUT_DIR}"

# Copy live-build config into build directory
# We work in a separate build dir to keep the repo clean
cp -r "${LB_CONFIG_DIR}/." "${BUILD_DIR}/"

cd "${BUILD_DIR}"

# ---- Configure live-build ----
log_step "Configuring live-build (lb config)"

LB_VERBOSE_FLAG=""
if [[ -n "${LB_VERBOSE:-}" ]]; then
    LB_VERBOSE_FLAG="--verbose"
fi

lb config \
    ${LB_VERBOSE_FLAG} \
    --distribution "noble" \
    --parent-distribution "noble" \
    --archive-areas "main restricted universe multiverse" \
    --architecture "${ARCH}" \
    --mirror-bootstrap "http://archive.ubuntu.com/ubuntu/" \
    --mirror-chroot "http://archive.ubuntu.com/ubuntu/" \
    --mirror-binary "http://archive.ubuntu.com/ubuntu/" \
    --image-type "iso-hybrid" \
    --bootloaders "grub-pc,grub-efi" \
    --bootappend-live "boot=live components quiet splash noeject hostname=phoenix username=phoenix" \
    --compression "xz" \
    --iso-application "Phoenix OS" \
    --iso-preparer "Phoenix OS Build System" \
    --iso-publisher "Phoenix OS Project" \
    --iso-volume "PHOENIX_OS_${PHOENIX_VERSION}" \
    --initramfs "casper" \
    --memtest "memtest86+" \
    2>&1 | tee "${OUTPUT_DIR}/lb-config-${TIMESTAMP}.log"

log_success "live-build configured"

# ---- Run the build ----
log_step "Running live-build (lb build) — this will take 15–60 minutes"
log_info "Build log: ${OUTPUT_DIR}/lb-build-${TIMESTAMP}.log"
log_info "Architecture: ${ARCH}"
log_info "Version: ${PHOENIX_VERSION}"

START_TIME=$(date +%s)

lb build \
    ${LB_VERBOSE_FLAG} \
    2>&1 | tee "${OUTPUT_DIR}/lb-build-${TIMESTAMP}.log"

END_TIME=$(date +%s)
BUILD_DURATION=$(( END_TIME - START_TIME ))
BUILD_MINUTES=$(( BUILD_DURATION / 60 ))
BUILD_SECONDS=$(( BUILD_DURATION % 60 ))

log_success "live-build completed in ${BUILD_MINUTES}m ${BUILD_SECONDS}s"

# ---- Locate the built ISO ----
log_step "Locating built ISO"

BUILT_ISO=""
for candidate in \
    "${BUILD_DIR}/live-image-${ARCH}.hybrid.iso" \
    "${BUILD_DIR}/live-image-${ARCH}.iso" \
    "${BUILD_DIR}"/*.iso; do
    if [[ -f "${candidate}" ]]; then
        BUILT_ISO="${candidate}"
        break
    fi
done

if [[ -z "${BUILT_ISO}" ]]; then
    log_error "Could not find built ISO in ${BUILD_DIR}. Check build log for errors."
    exit 1
fi

log_success "ISO found: ${BUILT_ISO}"

# ---- Copy ISO to output directory ----
log_step "Copying ISO to output directory"

cp "${BUILT_ISO}" "${OUTPUT_DIR}/${ISO_NAME}"
log_success "ISO: ${OUTPUT_DIR}/${ISO_NAME}"

# ---- Generate checksums ----
log_step "Generating SHA256 checksum"

cd "${OUTPUT_DIR}"
sha256sum "${ISO_NAME}" > SHA256SUMS
log_success "Checksum: ${OUTPUT_DIR}/SHA256SUMS"

# ---- ISO size report ----
ISO_SIZE=$(du -sh "${OUTPUT_DIR}/${ISO_NAME}" | cut -f1)
log_info "ISO size: ${ISO_SIZE}"

# ---- Optional: clean build directory ----
if [[ -z "${KEEP_BUILD:-}" ]]; then
    log_step "Cleaning build directory"
    cd "${REPO_ROOT}"
    lb clean --all 2>/dev/null || true
    log_success "Build directory cleaned"
else
    log_info "KEEP_BUILD is set; build directory retained at ${BUILD_DIR}"
fi

# ---- Summary ----
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${GREEN}║        Phoenix OS Build Complete             ║${NC}"
echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ISO:      ${BOLD}${OUTPUT_DIR}/${ISO_NAME}${NC}"
echo -e "  Size:     ${ISO_SIZE}"
echo -e "  Checksum: ${OUTPUT_DIR}/SHA256SUMS"
echo -e "  Duration: ${BUILD_MINUTES}m ${BUILD_SECONDS}s"
echo ""
echo -e "  Test with QEMU:"
echo -e "  ${BLUE}./tests/smoke/test-boot.sh ${OUTPUT_DIR}/${ISO_NAME}${NC}"
echo ""
