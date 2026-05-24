#!/usr/bin/env bash
# validate-launch-experience.sh - Launch Experience & Clean Menu Verification Script
#
# Part of PR35A Launch Governance Framework.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_OS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
WORKSPACE_DIR="$(cd -- "$PHOENIX_OS_DIR/../.." && pwd)"
MANIFESTS_DIR="$WORKSPACE_DIR/apps/manifests"
CHROOT_APPS_DIR="$PHOENIX_OS_DIR/live-build/config/includes.chroot/usr/share/applications"

echo "=== Phoenix OS Launch Experience Governance Validator ==="
echo "[INFO] Status: VERIFYING CITADEL SHELL MENUS & MANIFESTS"
echo ""

exit_code=0

# 1. Verify Flagship Manifests Exist
echo "============================================="
echo "STEP 1: FLAGSHIP APP IDENTITY AUDIT"
echo "============================================="
flagships=(
  "command"
  "harbor"
  "compass"
  "relay"
  "safe"
  "workshop"
  "bootforge"
  "market"
)

for app in "${flagships[@]}"; do
  manifest_path="$MANIFESTS_DIR/${app}.yaml"
  if [[ -f "$manifest_path" ]]; then
    echo "[OK] Found frozen flagship manifest: ${app}.yaml"
    
    # Verify launch-critical field
    if grep -E "^launch_critical:[[:space:]]*true" "$manifest_path" >/dev/null; then
      echo "  [OK] Launch critical status verified."
    else
      echo "  [FAIL] Manifest ${app}.yaml must be marked launch_critical: true!"
      exit_code=1
    fi
  else
    echo "[FAIL] Missing flagship manifest at $manifest_path!"
    exit_code=1
  fi
done

# 2. Check for Duplicate Launchers
echo ""
echo "============================================="
echo "STEP 2: SCANNING FOR LAUNCHER DUPLICATES"
echo "============================================="
if [[ -d "$CHROOT_APPS_DIR" ]]; then
  echo "[INFO] Scanning desktop entry duplicates in $CHROOT_APPS_DIR..."
  
  # Search for duplicate executables launched by multiple desktop files
  duplicates=$(grep -rhE "^Exec=" "$CHROOT_APPS_DIR/" 2>/dev/null | sort | uniq -d || true)
  if [[ -n "$duplicates" ]]; then
    echo "[WARN] Potential launcher duplication detected for command targets:"
    echo "$duplicates"
  else
    echo "[OK] Zero launcher command duplicates detected."
  fi
else
  echo "[OK] No custom desktop launchers exist (relying entirely on clean upstream system settings)."
fi

# 3. Check for Hidden/Experimental Launcher Sprawl
echo ""
echo "============================================="
echo "STEP 3: MOCK & EXPERIMENTAL SPRAWL AUDIT"
echo "============================================="
reserved_apps=(
  "sonic-codex"
  "ghost-writer"
  "devicescope"
  "pulsecheck"
  "truthlog"
)

sprawl_found=false
if [[ -d "$CHROOT_APPS_DIR" ]]; then
  for res in "${reserved_apps[@]}"; do
    if grep -RInE "$res" "$CHROOT_APPS_DIR/" >/dev/null 2>&1; then
      echo "[FAIL] Incomplete experimental app launcher discovered in active menus: $res"
      sprawl_found=true
      exit_code=1
    fi
  done
fi

if [[ "$sprawl_found" == "false" ]]; then
  echo "[OK] Experimental apps successfully filtered. Public menus remain pristine."
fi

echo ""
if [[ "$exit_code" -eq 0 ]]; then
  echo "=== Validation Successful: Launch Experience Governance is fully LOCKED! ==="
else
  echo "=== Validation FAILED: Rectify menu sprawl and app manifests before release! ==="
fi

exit "$exit_code"
