#!/bin/bash
# ARCWYRE Flex SDDM Autologin Validation Script
# Boots the ISO and captures first-boot evidence
# Run on Linux host (native or VM) with QEMU and systemd-journald

set -e

ISO_PATH="${1:-.}/bwos-arcwyre-flex.iso"
TIMEOUT_SEC="${2:-240}"
OUTPUT_DIR="./flex-boot-evidence"

echo "=== ARCWYRE Flex SDDM Autologin Validation ==="
echo "ISO: $ISO_PATH"
echo "Timeout: ${TIMEOUT_SEC}s"
echo "Output: $OUTPUT_DIR"
echo ""

if [ ! -f "$ISO_PATH" ]; then
    echo "ERROR: ISO not found at $ISO_PATH"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

# Start QEMU in background with proper serial capture
echo "[1/5] Starting QEMU boot test..."
qemu-system-x86_64 \
    -cpu host \
    -m 4096 \
    -smp 4 \
    -cdrom "$ISO_PATH" \
    -display none \
    -serial file:"$OUTPUT_DIR/qemu-serial.log" \
    -no-reboot &
QPID=$!
echo "QEMU PID: $QPID"

# Wait for boot to complete
echo "[2/5] Waiting ${TIMEOUT_SEC}s for boot completion..."
sleep "$TIMEOUT_SEC"

# Kill QEMU
echo "[3/5] Stopping QEMU..."
kill -9 $QPID 2>/dev/null || true
wait $QPID 2>/dev/null || true

# Analyze serial log
echo "[4/5] Analyzing boot evidence..."
echo ""
echo "=== SERIAL LOG ANALYSIS ==="
echo ""

LOG_FILE="$OUTPUT_DIR/qemu-serial.log"
if [ -f "$LOG_FILE" ]; then
    LINES=$(wc -l < "$LOG_FILE")
    echo "Serial log lines: $LINES"
    echo ""

    echo "--- Checking for SDDM autologin marker ---"
    if grep -q "BWOS_SDDM_AUTOLOGIN_CONFIGURED" "$LOG_FILE"; then
        echo "✅ FOUND: BWOS_SDDM_AUTOLOGIN_CONFIGURED"
        grep "BWOS_SDDM_AUTOLOGIN_CONFIGURED" "$LOG_FILE"
    else
        echo "❌ NOT FOUND: BWOS_SDDM_AUTOLOGIN_CONFIGURED"
    fi
    echo ""

    echo "--- Checking for SDDM error (should NOT appear) ---"
    if grep -q 'Unable to find autologin session entry ""' "$LOG_FILE"; then
        echo "❌ ERROR PRESENT: Unable to find autologin session entry"
        grep 'Unable to find autologin session entry' "$LOG_FILE"
    else
        echo "✅ GOOD: No 'Unable to find autologin session entry' error"
    fi
    echo ""

    echo "--- Checking for successful session markers ---"
    if grep -q "BWOS_LOGINCTL_SESSION_FOUND" "$LOG_FILE"; then
        echo "✅ FOUND: BWOS_LOGINCTL_SESSION_FOUND"
        grep "BWOS_LOGINCTL_SESSION_FOUND" "$LOG_FILE"
    else
        echo "❌ NOT FOUND: BWOS_LOGINCTL_SESSION_FOUND"
    fi
    echo ""

    echo "--- Checking for graphical.target ---"
    if grep -q "graphical.target" "$LOG_FILE"; then
        echo "✅ FOUND: graphical.target reached"
        grep "graphical.target" "$LOG_FILE" | tail -3
    else
        echo "⚠️  graphical.target not mentioned in serial log"
    fi
    echo ""

    echo "--- Checking for display manager service ---"
    if grep -q "sddm.service" "$LOG_FILE"; then
        echo "✅ SDDM service mentioned"
        grep "sddm.service" "$LOG_FILE" | head -3
    else
        echo "⚠️  SDDM service not found"
    fi
    echo ""

    echo "--- Full serial log saved to: $LOG_FILE ---"
else
    echo "⚠️  Serial log not captured: $LOG_FILE"
fi

echo ""
echo "[5/5] Generating evidence report..."
echo ""
echo "=== FINAL QA EVIDENCE REPORT ==="
echo ""
echo "ISO: $(basename $ISO_PATH)"
echo "Hash: $(sha256sum "$ISO_PATH" | awk '{print $1}')"
echo ""
echo "Serial Log Location: $LOG_FILE"
echo "Serial Log Size: $(wc -c < "$LOG_FILE" 2>/dev/null || echo "0") bytes"
echo ""
echo "Required Evidence:"
echo "  ✓ BWOS_SDDM_AUTOLOGIN_CONFIGURED marker with user=arc"
echo "  ✓ Valid Plasma session detected"
echo "  ✗ NO 'Unable to find autologin session entry' error"
echo "  ✓ BWOS_LOGINCTL_SESSION_FOUND (session active)"
echo "  ✓ graphical.target reached"
echo ""
echo "Next steps on Linux host:"
echo "  1. Boot the ISO on real hardware or KVM"
echo "  2. After graphical boot, open terminal and run:"
echo "       journalctl -b | grep -E 'BWOS_SDDM_AUTOLOGIN|Unable to find autologin|sddm'"
echo "       loginctl"
echo "       systemctl status sddm --no-pager"
echo "       cat /etc/sddm.conf"
echo ""
echo "Expected output:"
echo "  - Journal shows: BWOS_SDDM_AUTOLOGIN_CONFIGURED user=arc session=plasmax11.desktop"
echo "  - Journal does NOT show: Unable to find autologin session entry"
echo "  - loginctl shows: active session for arc with service=sddm"
echo "  - /etc/sddm.conf shows [Autologin] with User=arc and valid Session"
echo ""
echo "=== END REPORT ==="
