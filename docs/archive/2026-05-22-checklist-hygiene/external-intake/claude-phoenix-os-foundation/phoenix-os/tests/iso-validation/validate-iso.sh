#!/bin/bash
# =============================================================================
# Phoenix OS — ISO Validation Script
# File: tests/iso-validation/validate-iso.sh
#
# Comprehensive validation of a built Phoenix OS ISO.
# Checks ISO structure, required files, metadata, checksum, and size bounds.
#
# Usage:
#   ./tests/iso-validation/validate-iso.sh <path-to-iso>
#
# Run this before publishing any ISO release.
# =============================================================================

set -euo pipefail

ISO_PATH="${1:-}"

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
echo -e "${BOLD}Phoenix OS — ISO Validation${NC}"
echo "────────────────────────────"

# ---- Validate argument ----
if [[ -z "${ISO_PATH}" ]]; then
    echo "Usage: $0 <path-to-iso>"
    exit 2
fi

if [[ ! -f "${ISO_PATH}" ]]; then
    echo -e "${RED}ERROR:${NC} ISO not found: ${ISO_PATH}"
    exit 2
fi

# ---- File format ----
echo ""
echo -e "${BOLD}File Format${NC}"

FILE_TYPE=$(file "${ISO_PATH}")
if echo "${FILE_TYPE}" | grep -q "ISO 9660"; then
    check_pass "ISO 9660 format confirmed"
else
    check_fail "Not a valid ISO 9660 image: ${FILE_TYPE}"
fi

if echo "${FILE_TYPE}" | grep -q "bootable"; then
    check_pass "ISO is bootable"
else
    check_warn "ISO may not be bootable (no boot flag in file type)"
fi

# ---- Size checks ----
echo ""
echo -e "${BOLD}Size${NC}"

ISO_SIZE_BYTES=$(stat -c%s "${ISO_PATH}")
ISO_SIZE_MB=$(( ISO_SIZE_BYTES / 1024 / 1024 ))
ISO_SIZE_HUMAN=$(du -sh "${ISO_PATH}" | cut -f1)

# Minimum: 800 MB (bare minimum for KDE + tools)
# Maximum: 6 GB (larger than this is not practical for USB boot)
MIN_SIZE_MB=800
MAX_SIZE_MB=6144

echo -e "  ${BLUE}i${NC} ISO size: ${ISO_SIZE_HUMAN} (${ISO_SIZE_MB} MB)"

if [[ "${ISO_SIZE_MB}" -ge "${MIN_SIZE_MB}" ]]; then
    check_pass "Size above minimum (${MIN_SIZE_MB} MB)"
else
    check_fail "ISO too small: ${ISO_SIZE_MB} MB < ${MIN_SIZE_MB} MB minimum"
fi

if [[ "${ISO_SIZE_MB}" -le "${MAX_SIZE_MB}" ]]; then
    check_pass "Size below maximum (${MAX_SIZE_MB} MB)"
else
    check_warn "ISO is large: ${ISO_SIZE_MB} MB (consider trimming package lists)"
fi

# ---- Checksum ----
echo ""
echo -e "${BOLD}Checksum${NC}"

ISO_DIR=$(dirname "${ISO_PATH}")
ISO_BASENAME=$(basename "${ISO_PATH}")

COMPUTED_SHA256=$(sha256sum "${ISO_PATH}" | cut -d' ' -f1)
echo -e "  ${BLUE}i${NC} SHA256: ${COMPUTED_SHA256}"

if [[ -f "${ISO_DIR}/SHA256SUMS" ]]; then
    if grep -q "${ISO_BASENAME}" "${ISO_DIR}/SHA256SUMS"; then
        EXPECTED_SHA256=$(grep "${ISO_BASENAME}" "${ISO_DIR}/SHA256SUMS" | cut -d' ' -f1)
        if [[ "${COMPUTED_SHA256}" == "${EXPECTED_SHA256}" ]]; then
            check_pass "SHA256 checksum matches SHA256SUMS file"
        else
            check_fail "SHA256 mismatch: computed ${COMPUTED_SHA256}, expected ${EXPECTED_SHA256}"
        fi
    else
        check_warn "SHA256SUMS file exists but does not contain this ISO filename"
    fi
else
    check_warn "No SHA256SUMS file found alongside ISO — generate with: sha256sum ${ISO_BASENAME} > SHA256SUMS"
fi

# ---- ISO content validation ----
echo ""
echo -e "${BOLD}ISO Content${NC}"

if ! command -v xorriso >/dev/null 2>&1; then
    check_warn "xorriso not available — skipping content validation"
else
    # List ISO contents to a temp file
    ISO_LISTING=$(mktemp)
    trap "rm -f ${ISO_LISTING}" EXIT

    xorriso -indev "${ISO_PATH}" -find / -ls 2>/dev/null > "${ISO_LISTING}" || true

    # Required files
    declare -A REQUIRED_FILES
    REQUIRED_FILES["vmlinuz"]="Linux kernel"
    REQUIRED_FILES["initrd"]="Initial ramdisk"
    REQUIRED_FILES["filesystem.squashfs"]="Root filesystem (squashfs)"

    for file_pattern in "${!REQUIRED_FILES[@]}"; do
        description="${REQUIRED_FILES[$file_pattern]}"
        if grep -q "${file_pattern}" "${ISO_LISTING}" 2>/dev/null; then
            check_pass "${description} (${file_pattern}) present"
        else
            check_fail "${description} (${file_pattern}) NOT found in ISO"
        fi
    done

    # Check for GRUB EFI support
    if grep -q "grubx64.efi\|bootx64.efi" "${ISO_LISTING}" 2>/dev/null; then
        check_pass "UEFI boot files present (grubx64.efi)"
    else
        check_warn "UEFI boot files not found — UEFI boot may not work"
    fi

    # Check for isolinux (BIOS boot)
    if grep -q "isolinux\|grub.cfg" "${ISO_LISTING}" 2>/dev/null; then
        check_pass "BIOS boot configuration present"
    else
        check_warn "BIOS boot configuration not found"
    fi

    # Check for Phoenix branding
    if grep -q "phoenix" "${ISO_LISTING}" 2>/dev/null; then
        check_pass "Phoenix branding files found in ISO"
    else
        check_warn "No Phoenix-branded files found — check branding hooks"
    fi

    rm -f "${ISO_LISTING}"
    trap - EXIT
fi

# ---- ISO metadata ----
echo ""
echo -e "${BOLD}ISO Metadata${NC}"

if command -v isoinfo >/dev/null 2>&1; then
    ISO_INFO=$(isoinfo -d -i "${ISO_PATH}" 2>/dev/null)

    VOL_ID=$(echo "${ISO_INFO}" | grep "Volume id:" | sed 's/Volume id: //')
    if echo "${VOL_ID}" | grep -qi "phoenix"; then
        check_pass "Volume ID contains 'phoenix': ${VOL_ID}"
    else
        check_warn "Volume ID does not contain 'phoenix': ${VOL_ID}"
    fi
elif command -v xorriso >/dev/null 2>&1; then
    VOL_ID=$(xorriso -indev "${ISO_PATH}" -report_system_area plain 2>/dev/null | grep -i "volume\|label" || true)
    echo -e "  ${BLUE}i${NC} Volume info: ${VOL_ID:-unknown}"
fi

# ---- Summary ----
echo ""
echo "────────────────────────────"
echo -e "${BOLD}Results:${NC} ${GREEN}${PASS} passed${NC}  ${RED}${FAIL} failed${NC}  ${YELLOW}${WARN} warnings${NC}"
echo ""

if [[ "${FAIL}" -gt 0 ]]; then
    echo -e "${RED}${BOLD}ISO validation FAILED.${NC} Do not publish this ISO."
    exit 1
elif [[ "${WARN}" -gt 0 ]]; then
    echo -e "${YELLOW}ISO validation passed with warnings.${NC} Review warnings before publishing."
    exit 0
else
    echo -e "${GREEN}${BOLD}ISO validation PASSED.${NC}"
    exit 0
fi
