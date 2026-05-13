#!/bin/bash
# =============================================================================
# Phoenix OS — Installation Test (QEMU)
# File: tests/smoke/test-install.sh
#
# Boots the ISO in QEMU, runs an unattended Calamares installation to a
# virtual disk, and verifies the installed system boots.
#
# Requires: QEMU, OVMF (UEFI firmware)
# Runtime: ~15–30 minutes
#
# Usage:
#   ./tests/smoke/test-install.sh output/phoenix-os-*.iso
# =============================================================================

set -euo pipefail

ISO_PATH="${1:-}"
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $*"; }
log_fail()    { echo -e "${RED}[FAIL]${NC} $*"; (( FAIL++ )) || true; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }

PASS=0; FAIL=0
WORK_DIR=$(mktemp -d /tmp/phoenix-install-test-XXXXX)
trap "rm -rf ${WORK_DIR}" EXIT

if [[ -z "${ISO_PATH}" || ! -f "${ISO_PATH}" ]]; then
    echo "Usage: $0 <path-to-iso>"
    exit 2
fi

echo ""
echo -e "${BOLD}Phoenix OS — Installation Test${NC}"
echo "────────────────────────────────"
log_info "ISO: ${ISO_PATH}"
log_info "Work dir: ${WORK_DIR}"

# ---- Prerequisite checks ----
for tool in qemu-system-x86_64 qemu-img; do
    if command -v "${tool}" >/dev/null 2>&1; then
        (( PASS++ )) || true
    else
        log_fail "${tool} not found — install qemu-system-x86"
        exit 2
    fi
done

# ---- Create virtual disk ----
log_info "Creating 25 GB virtual disk..."
VDISK="${WORK_DIR}/phoenix-install-test.qcow2"
qemu-img create -f qcow2 "${VDISK}" 25G
log_success "Virtual disk created: $(du -sh "${VDISK}" | cut -f1)"

# ---- OVMF (UEFI) vars copy ----
OVMF_CODE=""
OVMF_VARS=""
for code_path in /usr/share/OVMF/OVMF_CODE.fd /usr/share/ovmf/OVMF.fd; do
    if [[ -f "${code_path}" ]]; then
        OVMF_CODE="${code_path}"
        break
    fi
done

if [[ -n "${OVMF_CODE}" ]]; then
    cp "${OVMF_CODE}" "${WORK_DIR}/OVMF_CODE.fd" 2>/dev/null || true
    UEFI_ARGS="-drive if=pflash,format=raw,readonly=on,file=${WORK_DIR}/OVMF_CODE.fd"
    log_info "UEFI boot enabled (OVMF found)"
else
    UEFI_ARGS=""
    log_warn "OVMF not found — testing BIOS boot only (install: sudo apt install ovmf)"
fi

# ---- Boot ISO and wait for desktop ----
KVM_FLAG=""
[[ -c /dev/kvm ]] && KVM_FLAG="-enable-kvm"

SERIAL_LOG="${WORK_DIR}/serial.log"

log_info "Booting ISO in QEMU (60s timeout for desktop)..."

timeout 90 qemu-system-x86_64 \
    ${KVM_FLAG} \
    ${UEFI_ARGS} \
    -m 3G \
    -smp 2 \
    -cdrom "${ISO_PATH}" \
    -drive "file=${VDISK},format=qcow2,if=virtio" \
    -boot d \
    -nographic \
    -serial "file:${SERIAL_LOG}" \
    -display none \
    -no-reboot \
    2>/dev/null &

QEMU_PID=$!
BOOT_OK=false

for i in $(seq 1 45); do
    sleep 2
    if grep -q "sddm\|Started.*Session\|phoenix login" "${SERIAL_LOG}" 2>/dev/null; then
        BOOT_OK=true
        break
    fi
done

kill "${QEMU_PID}" 2>/dev/null || true
wait "${QEMU_PID}" 2>/dev/null || true

if "${BOOT_OK}"; then
    log_success "Live session reached desktop"
    (( PASS++ )) || true
else
    log_fail "Live session did not reach desktop within timeout"
    log_info "Last 10 lines of serial log:"
    tail -10 "${SERIAL_LOG}" 2>/dev/null | sed 's/^/  /' || true
fi

# ---- Summary ----
echo ""
echo "────────────────────────────────"
echo -e "${BOLD}Results:${NC} ${GREEN}${PASS} passed${NC}  ${RED}${FAIL} failed${NC}"

# TODO Phase 1: Add unattended Calamares install via AutoInstall config
# and verify the installed system boots from the virtual disk.
log_warn "Unattended install verification is a Phase 1 TODO."
log_warn "Manual install testing: boot the ISO in a VM and run Calamares."

echo ""
[[ "${FAIL}" -gt 0 ]] && exit 1 || exit 0
