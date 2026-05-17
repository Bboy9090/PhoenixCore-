#!/usr/bin/env bash
# package-cache.sh - Phoenix OS Prebuilt Package Staging Manager
#
# Part of PR32 Incremental Build Acceleration.
# This script scans the prebuilt packages directory and stages them into the
# live-build chroot environment so they are automatically installed during the build.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_OS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
PACKAGES_SRC_DIR="$PHOENIX_OS_DIR/build/packages"
PACKAGES_DEST_DIR="$PHOENIX_OS_DIR/live-build/config/packages.chroot"

echo "=== Phoenix OS Prebuilt Package Cache Manager ==="
echo "[INFO] Source packages directory: $PACKAGES_SRC_DIR"
echo "[INFO] Destination directory: $PACKAGES_DEST_DIR"

# Ensure directories exist
mkdir -p "$PACKAGES_SRC_DIR"
mkdir -p "$PACKAGES_DEST_DIR"

# Check for .deb files in source directory
mapfile -t deb_files < <(find "$PACKAGES_SRC_DIR" -maxdepth 1 -type f -name "*.deb" -print 2>/dev/null || true)

if [[ "${#deb_files[@]}" -eq 0 ]]; then
  echo "[INFO] No custom prebuilt (.deb) packages found in $PACKAGES_SRC_DIR."
  echo "[INFO] (Place your custom Phoenix Control Center or Agent debian files here for automated injection)."
  exit 0
fi

echo "[INFO] Found ${#deb_files[@]} prebuilt package(s) to cache:"
for deb in "${deb_files[@]}"; do
  echo "  -> $(basename "$deb")"
done

# Clean destination config directory to prevent stale caches
echo "[INFO] Cleaning target package staging directory..."
rm -f "$PACKAGES_DEST_DIR"/*.deb

# Staging packages
echo "[INFO] Staging prebuilt packages for live-build chroot injection..."
for deb in "${deb_files[@]}"; do
  cp -p "$deb" "$PACKAGES_DEST_DIR/"
  echo "[OK] Staged: $(basename "$deb")"
done

echo "=== Staging Complete ==="
