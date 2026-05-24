#!/bin/bash
# =============================================================================
# Phoenix OS — ISO Signing Script
# File: scripts/sign-iso.sh
#
# Signs a built ISO for public release using GPG.
# Produces:
#   output/SHA256SUMS         - SHA256 checksums
#   output/SHA256SUMS.gpg     - Detached GPG signature
#
# Requirements:
#   - A GPG key configured for signing (set PHOENIX_SIGNING_KEY env var)
#   - The ISO must have already been built and validated
#
# Usage:
#   PHOENIX_SIGNING_KEY="releases@phoenix-os.io" ./scripts/sign-iso.sh
#   ./scripts/sign-iso.sh output/phoenix-os-1.0.0-amd64.iso
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/../output"
SIGNING_KEY="${PHOENIX_SIGNING_KEY:-}"
ISO_PATH="${1:-}"

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[OK]${NC} $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

echo ""
echo -e "${BOLD}Phoenix OS — ISO Signing${NC}"
echo "────────────────────────"

# Locate ISO
if [[ -z "${ISO_PATH}" ]]; then
    ISO_PATH=$(ls -t "${OUTPUT_DIR}"/*.iso 2>/dev/null | head -1 || true)
fi

if [[ -z "${ISO_PATH}" || ! -f "${ISO_PATH}" ]]; then
    log_error "No ISO found. Build one first with: sudo ./scripts/build-iso.sh"
    exit 1
fi

log_info "ISO: ${ISO_PATH}"
log_info "Size: $(du -sh "${ISO_PATH}" | cut -f1)"

# Check GPG
if ! command -v gpg >/dev/null 2>&1; then
    log_error "GPG not found. Install with: sudo apt install gnupg"
    exit 1
fi

# Determine signing key
if [[ -z "${SIGNING_KEY}" ]]; then
    log_info "No PHOENIX_SIGNING_KEY set. Using default GPG key."
    log_info "Available keys:"
    gpg --list-secret-keys --keyid-format LONG 2>/dev/null | grep -E "^(sec|uid)" || true
    echo ""
    read -rp "Enter key ID or email to sign with: " SIGNING_KEY
fi

if [[ -z "${SIGNING_KEY}" ]]; then
    log_error "No signing key specified. Aborting."
    exit 1
fi

# Generate SHA256SUMS
log_info "Generating SHA256SUMS..."
cd "${OUTPUT_DIR}"
ISO_BASENAME=$(basename "${ISO_PATH}")
sha256sum "${ISO_BASENAME}" > SHA256SUMS
log_success "SHA256SUMS written"

# Sign SHA256SUMS
log_info "Signing with key: ${SIGNING_KEY}"
gpg --batch \
    --yes \
    --local-user "${SIGNING_KEY}" \
    --detach-sign \
    --armor \
    --output SHA256SUMS.gpg \
    SHA256SUMS

log_success "SHA256SUMS.gpg written"

# Verify signature
log_info "Verifying signature..."
gpg --verify SHA256SUMS.gpg SHA256SUMS && log_success "Signature verified" || {
    log_error "Signature verification failed"
    exit 1
}

echo ""
echo -e "${BOLD}Release artifacts:${NC}"
echo "  ${OUTPUT_DIR}/${ISO_BASENAME}"
echo "  ${OUTPUT_DIR}/SHA256SUMS"
echo "  ${OUTPUT_DIR}/SHA256SUMS.gpg"
echo ""
echo "Publish the ISO, SHA256SUMS, and SHA256SUMS.gpg together."
echo "Users verify with: gpg --verify SHA256SUMS.gpg && sha256sum -c SHA256SUMS"
