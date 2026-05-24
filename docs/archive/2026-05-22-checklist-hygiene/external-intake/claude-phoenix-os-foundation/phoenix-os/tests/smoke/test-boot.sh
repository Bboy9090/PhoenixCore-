#!/bin/bash
# =============================================================================
# Phoenix OS — Smoke Test: Boot Validation
# File: tests/smoke/test-boot.sh
#
# Boots the Phoenix OS ISO in QEMU and validates that the live session
# starts correctly. Requires QEMU and KVM.
#
# Usage:
#   ./tests/smoke/test-boot.sh <path-to-iso>
#   ./tests/smoke/test-boot.sh output/phoenix-os-0.1.0-alpha-amd64.iso
#
# Exit codes:
#   0 = all checks passed
#   1 = boot failed or checks failed
#   2 = prerequisites not met
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

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $*"; }
log_fail()    { echo -e "${RED}[FAIL]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }

PASS=0
FAIL=0

check_pass() { log_success "$*"; (( PASS++ )) || true; }
check_fail() { log_fail "$*"; (( FAIL++ )) || true; }

echo ""
echo -e "${BOLD}Phoenix OS Smoke Test — Boot Validation${NC}"
echo "────────────────────────────────────────"

# ---- Validate ISO argument ----
if [[ -z "${ISO_PATH}" ]]; then
    echo "Usage: $0 <path-to-iso>"
    echo "Example: $0 output/phoenix-os-0.1.0-alpha-amd64.iso"
    exit 2
fi

if [[ ! -f "${ISO_PATH}" ]]; then
    log_fail "ISO not found: ${ISO_PATH}"
    exit 2
fi

ISO_SIZE=$(du -sh "${ISO_PATH}" | cut -f1)
log_info "ISO: ${ISO_PATH} (${ISO_SIZE})"

# ---- Check prerequisites ----
echo ""
echo -e "${BOLD}Prerequisites${NC}"

for tool in qemu-system-x86_64 timeout; do
    if command -v "${tool}" >/dev/null 2>&1; then
        check_pass "${tool} available"
    else
        check_fail "${tool} not found"
        if [[ "${tool}" == "qemu-system-x86_64" ]]; then
            echo "  Install with: sudo apt install qemu-system-x86"
            exit 2
        fi
    fi
done

# ---- ISO structure validation ----
echo ""
echo -e "${BOLD}ISO Structure${NC}"

# Check ISO is a valid ISO 9660 image
if file "${ISO_PATH}" | grep -q "ISO 9660\|bootable"; then
    check_pass "ISO format: valid ISO 9660"
else
    check_fail "ISO format: not a valid ISO image ($(file "${ISO_PATH}"))"
fi

# Check ISO contains expected files using isoinfo or xorriso
if command -v xorriso >/dev/null 2>&1; then
    if xorriso -indev "${ISO_PATH}" -find / -name "vmlinuz" -ls 2>/dev/null | grep -q vmlinuz; then
        check_pass "Kernel (vmlinuz) found in ISO"
    else
        check_fail "Kernel (vmlinuz) NOT found in ISO"
    fi

    if xorriso -indev "${ISO_PATH}" -find / -name "initrd*" -ls 2>/dev/null | grep -q initrd; then
        check_pass "Initrd found in ISO"
    else
        check_fail "Initrd NOT found in ISO"
    fi

    if xorriso -indev "${ISO_PATH}" -find / -name "filesystem.squashfs" -ls 2>/dev/null | grep -q squashfs; then
        check_pass "Squashfs root filesystem found in ISO"
    else
        check_fail "Squashfs root filesystem NOT found in ISO"
    fi
else
    log_warn "xorriso not available — skipping ISO content checks"
fi

# ---- QEMU boot test ----
echo ""
echo -e "${BOLD}QEMU Boot Test${NC}"
log_info "Booting ISO in QEMU (headless, 30 second timeout)..."
log_info "Looking for 'login:' or 'Started' systemd messages in serial output"

# Create a temporary serial log file
SERIAL_LOG=$(mktemp /tmp/phoenix-qemu-XXXXXX.log)
trap "rm -f ${SERIAL_LOG}" EXIT

# QEMU arguments:
#   -nographic          : headless mode
#   -serial stdio       : serial output to stdout/file
#   -m 2G               : 2GB RAM minimum
#   -smp 2              : 2 CPU cores
#   -enable-kvm         : KVM acceleration (if available)
#   -cdrom              : boot from ISO
#   -boot d             : boot from CD/DVD
#   -no-reboot          : don't reboot on shutdown

QEMU_KVM=""
if [[ -c /dev/kvm ]] && [[ -r /dev/kvm ]]; then
    QEMU_KVM="-enable-kvm"
    log_info "KVM acceleration enabled"
else
    log_warn "KVM not available — emulation will be slow"
fi

# Run QEMU with a 90-second timeout
# We capture serial output and look for boot success indicators
BOOT_SUCCESS=false

timeout 90 qemu-system-x86_64 \
    ${QEMU_KVM} \
    -m 2G \
    -smp 2 \
    -cdrom "${ISO_PATH}" \
    -boot d \
    -no-reboot \
    -nographic \
    -serial file:"${SERIAL_LOG}" \
    -display none \
    2>/dev/null &

QEMU_PID=$!

# Poll the serial log for boot indicators
POLL_INTERVAL=2
POLL_MAX=45  # 45 * 2s = 90s
POLL_COUNT=0

while [[ ${POLL_COUNT} -lt ${POLL_MAX} ]]; do
    sleep ${POLL_INTERVAL}
    (( POLL_COUNT++ )) || true

    if [[ -f "${SERIAL_LOG}" ]]; then
        # Check for successful boot indicators
        if grep -q "Started.*SDDM\|gdm\|lightdm\|phoenix login\|ubuntu login" "${SERIAL_LOG}" 2>/dev/null; then
            BOOT_SUCCESS=true
            break
        fi

        # Check for kernel panic
        if grep -q "Kernel panic\|kernel panic" "${SERIAL_LOG}" 2>/dev/null; then
            check_fail "Kernel panic detected during boot"
            break
        fi

        # Show progress
        if [[ $(( POLL_COUNT % 5 )) -eq 0 ]]; then
            log_info "Still booting... (${POLL_COUNT}/${POLL_MAX} polls)"
        fi
    fi
done

# Kill QEMU
kill "${QEMU_PID}" 2>/dev/null || true
wait "${QEMU_PID}" 2>/dev/null || true

if "${BOOT_SUCCESS}"; then
    check_pass "Live session started successfully (display manager started)"
else
    check_fail "Live session did not reach display manager within timeout"
    log_info "Serial log tail (last 20 lines):"
    tail -20 "${SERIAL_LOG}" 2>/dev/null | sed 's/^/  /' || true
fi

# ---- Summary ----
echo ""
echo "────────────────────────────────────────"
echo -e "${BOLD}Results:${NC} ${GREEN}${PASS} passed${NC}  ${RED}${FAIL} failed${NC}"
echo ""

if [[ "${FAIL}" -gt 0 ]]; then
    echo -e "${RED}Smoke test FAILED.${NC}"
    exit 1
else
    echo -e "${GREEN}Smoke test PASSED.${NC}"
    exit 0
fi
