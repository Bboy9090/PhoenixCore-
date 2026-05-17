#!/usr/bin/env bash
# Phoenix OS ISO build entrypoint for the OCI builder.
#
# Part of PR31 Build Acceleration Framework.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_OS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="${PHOENIX_OS_ARTIFACT_DIR:-$PHOENIX_OS_DIR/build}"
LIVE_BUILD_DIR="$PHOENIX_OS_DIR/live-build"
BUILD_WORK_DIR="/home/phoenix-builder/build-workspace"

# Default parameters
MODE="release-hardened"
ARCH="amd64"
CLEAN=false
NO_CACHE=false

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    --arch)
      ARCH="$2"
      shift 2
      ;;
    --clean)
      CLEAN=true
      shift
      ;;
    --no-cache)
      NO_CACHE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

echo "=== Phoenix OS ISO Build Entrypoint ==="
echo "[INFO] Phoenix OS directory: $PHOENIX_OS_DIR"
echo "[INFO] Artifact directory: $BUILD_DIR"
echo "[INFO] Mode: $MODE"
echo "[INFO] Arch: $ARCH"
echo "[INFO] Clean: $CLEAN"
echo "[INFO] No-Cache: $NO_CACHE"

if [[ "$BUILD_DIR" != "$PHOENIX_OS_DIR/build" ]]; then
  echo "[FAIL] Refusing to write artifacts outside os/phoenix-os/build."
  exit 1
fi

mkdir -p "$BUILD_DIR"

if ! command -v lb >/dev/null 2>&1; then
  echo "[FAIL] live-build command 'lb' is unavailable in the container."
  exit 1
fi

if [[ ! -d "$LIVE_BUILD_DIR/config" && ! -f "$LIVE_BUILD_DIR/auto/config" ]]; then
  echo "[FAIL] No live-build configuration exists yet under $LIVE_BUILD_DIR."
  exit 1
fi

# Clean operation
if [[ "$CLEAN" == "true" ]]; then
  echo "[INFO] Performing clean rebuild path..."
  sudo rm -rf "$BUILD_WORK_DIR"
  sudo rm -rf /workspace/os/phoenix-os/cache/*
  echo "[OK] Clean complete."
  exit 0
fi

echo "[INFO] Preparing writable build environment..."
rm -rf "$BUILD_WORK_DIR"
mkdir -p "$BUILD_WORK_DIR"

# Copy the configuration and package lists to the writable area
rsync -a "$LIVE_BUILD_DIR/" "$BUILD_WORK_DIR/"

# 2. Package List Staging Mode-Driven
echo "[INFO] Staging package list profile for mode: $MODE..."
PKG_DEST_DIR="$BUILD_WORK_DIR/config/package-lists"

# Remove default package lists to prevent duplication/override
rm -f "$PKG_DEST_DIR"/phoenix-hardened.list.chroot
rm -f "$PKG_DEST_DIR"/phoenix.list.chroot

PROFILE_DIR="$BUILD_WORK_DIR/config/package-lists/profiles"

if [[ ! -d "$PROFILE_DIR" ]]; then
  echo "[FAIL] Profile directory does not exist: $PROFILE_DIR"
  exit 1
fi

if [[ "$MODE" == "fast" ]]; then
  cat "$PROFILE_DIR/fast.list.chroot" "$PROFILE_DIR/branding-tools.list.chroot" > "$PKG_DEST_DIR/phoenix.list.chroot"
elif [[ "$MODE" == "full" || "$MODE" == "release-hardened" ]]; then
  cat "$PROFILE_DIR/fast.list.chroot" "$PROFILE_DIR/full.list.chroot" "$PROFILE_DIR/recovery-tools.list.chroot" "$PROFILE_DIR/branding-tools.list.chroot" > "$PKG_DEST_DIR/phoenix.list.chroot"
else
  echo "[FAIL] Unsupported build mode: $MODE"
  exit 1
fi

echo "[INFO] Staging branding assets and safety rules..."
# Ensure directories exist
mkdir -p "$BUILD_WORK_DIR/config/includes.chroot/usr/share/plymouth/themes"
mkdir -p "$BUILD_WORK_DIR/config/includes.chroot/usr/share/sddm/themes"

# Copy harvested themes if they exist
if [ -d "$PHOENIX_OS_DIR/branding/plymouth/phoenix" ]; then
    cp -r "$PHOENIX_OS_DIR/branding/plymouth/phoenix" "$BUILD_WORK_DIR/config/includes.chroot/usr/share/plymouth/themes/"
fi

if [ -d "$PHOENIX_OS_DIR/branding/sddm/phoenix" ]; then
    cp -r "$PHOENIX_OS_DIR/branding/sddm/phoenix" "$BUILD_WORK_DIR/config/includes.chroot/usr/share/sddm/themes/"
fi

# Restore package cache if present and enabled
if [[ "$NO_CACHE" == "false" ]]; then
  echo "[INFO] Checking for persistent APT package cache..."
  mkdir -p "$BUILD_WORK_DIR/cache/packages.chroot"
  if [[ -d "/workspace/os/phoenix-os/cache/packages.chroot" ]]; then
    # Copy deb files safely
    find /workspace/os/phoenix-os/cache/packages.chroot/ -maxdepth 1 -name "*.deb" -exec cp -p {} "$BUILD_WORK_DIR/cache/packages.chroot/" \; 2>/dev/null || true
    echo "[OK] Staged persistent package cache."
  fi
fi

echo "[INFO] Running live-build from $BUILD_WORK_DIR."
START_TIME=$(date +%s)
(
  cd "$BUILD_WORK_DIR"
  # Run lb config to ensure everything is initialized for the target architecture
  lb config --architecture "$ARCH"
  sudo lb build
)
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

mapfile -t built_isos < <(find "$BUILD_WORK_DIR" -maxdepth 1 -type f -name "*.iso" -print | sort)
if [[ "${#built_isos[@]}" -eq 0 ]]; then
  echo "[FAIL] live-build completed without producing an ISO."
  exit 1
fi

for iso in "${built_isos[@]}"; do
  ISO_NAME=$(basename "$iso")
  
  # Standard name or custom architecture name
  DEST="$BUILD_DIR/$ISO_NAME"
  cp "$iso" "$DEST"
  
  # Also create a mode/arch friendly named link/file for easy user discovery
  FRIENDLY_NAME="phoenix-os-${MODE}-${ARCH}.iso"
  cp "$iso" "$BUILD_DIR/$FRIENDLY_NAME"
  
  if [[ -f "$DEST" ]]; then
    SIZE=$(stat -c%s "$DEST" 2>/dev/null || stat -f%z "$DEST")
    SHA256=$(sha256sum "$DEST" | awk '{print $1}' 2>/dev/null || shasum -a 256 "$DEST" | awk '{print $1}')
    
    echo "[OK] Artifact: $ISO_NAME"
    echo "[OK] Friendly Name: $FRIENDLY_NAME"
    echo "[OK] Path: $DEST"
    echo "[OK] Size: $SIZE bytes"
    echo "[OK] SHA256: $SHA256"
    echo "[OK] Build Duration: ${DURATION}s"
    
    # Save back new packages to persistent cache if caching is active
    if [[ "$NO_CACHE" == "false" ]]; then
      echo "[INFO] Preserving downloaded packages to persistent APT cache..."
      mkdir -p "/workspace/os/phoenix-os/cache/packages.chroot"
      find "$BUILD_WORK_DIR/cache/packages.chroot/" -maxdepth 1 -name "*.deb" -exec cp -p {} "/workspace/os/phoenix-os/cache/packages.chroot/" \; 2>/dev/null || true
    fi
    
    # Non-destructive validation
    echo "[INFO] Validating ISO structure..."
    file "$DEST"
    if command -v xorriso >/dev/null 2>&1; then
      xorriso -indev "$DEST" -report_el_torito plain -report_system_area plain
    fi
  else
    echo "[FAIL] Failed to copy ISO to $DEST"
    exit 1
  fi
done

echo "=== Phoenix OS ISO Build Entrypoint Complete ==="
