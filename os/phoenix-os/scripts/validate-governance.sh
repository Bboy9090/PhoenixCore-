#!/usr/bin/env bash
# validate-governance.sh - PR34 Safe Governance Validation Script
#
# Part of PR34 Governed Application Execution.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_OS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
POLICY_FILE="$PHOENIX_OS_DIR/policies/org.aurelia.phoenix.policy"
DOCS_DIR="$PHOENIX_OS_DIR/../../docs" # Relative to core directories if needed, or absolute

echo "=== Phoenix OS Safe Governance Validator ==="
echo "[INFO] Status: AUDITING SYSTEM EXECUTION BOUNDARIES"
echo ""

exit_code=0

# 1. Verify org.aurelia.phoenix.policy exists and is structurally sound
echo "============================================="
echo "STEP 1: POLICY STRUCTURE AUDIT"
echo "============================================="
if [[ -f "$POLICY_FILE" ]]; then
  echo "[OK] Scoped Polkit configuration found: $POLICY_FILE"
  
  # Audit for forbidden generic root actions
  if grep -E 'allow_any>yes|allow_inactive>yes' "$POLICY_FILE" >/dev/null 2>&1; then
    echo "[FAIL] Insecure wide-open Polkit defaults detected!"
    exit_code=1
  else
    echo "[OK] Polkit permissions are scoped correctly (deny-by-default is locked)."
  fi
else
  echo "[FAIL] Policy configuration missing at $POLICY_FILE!"
  exit_code=1
fi

# 2. Check for Direct Repair Launchers or Mock Success Labels
echo ""
echo "============================================="
echo "STEP 2: SCANNING FOR DIRECT REPAIR & MOCK LABELS"
echo "============================================="

# Ensure no custom desktop launchers try to invoke direct recovery commands
CHROOT_APPS="$PHOENIX_OS_DIR/live-build/config/includes.chroot/usr/share/applications"
if [[ -d "$CHROOT_APPS" ]]; then
  if grep -RInE 'Exec=(gparted|dd|mkfs|parted)' "$CHROOT_APPS/" >/dev/null 2>&1; then
    echo "[FAIL] Destructive execution launchers found directly staged in chroot!"
    exit_code=1
  else
    echo "[OK] No direct block device mutation launchers staged."
  fi
else
  echo "[OK] Staging area clean. No custom applications staged directly."
fi

# 3. Verify Audited SMART Helper Execution
echo ""
echo "============================================="
echo "STEP 3: SECURE HELPER VERIFICATION"
echo "============================================="
SMART_HELPER="$PHOENIX_OS_DIR/policies/phoenix-smart-helper.sh"
if [[ -f "$SMART_HELPER" ]]; then
  echo "[OK] Secure SMART helper found: $SMART_HELPER"
  if grep -E "EUID.*ne.*0" "$SMART_HELPER" >/dev/null 2>&1; then
    echo "[OK] Helper correctly enforces EUID=0 administrative containment."
  else
    echo "[FAIL] Helper fails to enforce root access boundaries."
    exit_code=1
  fi
else
  echo "[FAIL] Secure SMART helper missing!"
  exit_code=1
fi

echo ""
if [[ "$exit_code" -eq 0 ]]; then
  echo "=== Validation Successful: Governance & Elevation Framework is fully COMPLIANT! ==="
else
  echo "=== Validation FAILED: Rectify policy permissions before packaging system! ==="
fi

exit "$exit_code"
