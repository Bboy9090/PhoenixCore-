#!/bin/bash
# Arcwyre Flex OS — ISO Build Script
# Phase 1: Minimum Bootable Flex ISO
#
# CURRENT STATUS: STUBBED
# This script will build a minimal Arcwyre Flex ISO from a Debian/Ubuntu base.
# It is not yet functional — it documents the intended build pipeline.
#
# Prerequisites (to be installed):
#   - debootstrap
#   - squashfs-tools
#   - xorriso
#   - grub-pc-bin / grub-efi-amd64-bin
#   - calamares (for installer)
#
# Build phases:
#   Phase 0: Audit existing base (if any)
#   Phase 1: Bootstrap minimal Debian/Ubuntu base
#   Phase 2: Install desktop environment (XFCE/LXQt)
#   Phase 3: Apply Arcwyre branding
#   Phase 4: Configure modes (simple, power, repair, kiosk)
#   Phase 5: Build squashfs filesystem
#   Phase 6: Create bootable ISO
#   Phase 7: Measure performance baseline
#   Phase 8: Test in VM

set -e

SCRIPT_DIR=$(realpath $(dirname "$0"))
PROJECT_ROOT=$(realpath "$SCRIPT_DIR/..")
BUILD_DIR="$PROJECT_ROOT/build"
ISO_OUT="$BUILD_DIR/arcwyre-flex-0.1.iso"

echo "=== Arcwyre Flex OS — ISO Build ==="
echo "Status: STUBBED — Phase 0 (Audit) only"
echo ""
echo "Build target: $ISO_OUT"
echo ""
echo "Phase 0: Checking prerequisites..."

# Check for required tools
check_tool() {
    if command -v "$1" &>/dev/null; then
        echo "  [FOUND]   $1"
    else
        echo "  [MISSING] $1 — install with: $2"
    fi
}

check_tool debootstrap "sudo apt-get install debootstrap"
check_tool mksquashfs "sudo apt-get install squashfs-tools"
check_tool xorriso "sudo apt-get install xorriso"
check_tool grub-mkrescue "sudo apt-get install grub-pc-bin grub-efi-amd64-bin grub-common mtools"

echo ""
echo "Phase 1-8: NOT_STARTED"
echo ""
echo "Next step: Install prerequisites and implement Phase 1 (bootstrap base)."
echo "See docs/ARCHITECTURE.md for the full build plan."
