#!/usr/bin/env bash
# Phoenix OS ISO build entrypoint for the OCI builder.
#
# PR22 restores orchestration only. This script refuses to claim success until
# real live-build configuration exists and live-build produces an ISO.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_OS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="${PHOENIX_OS_ARTIFACT_DIR:-$PHOENIX_OS_DIR/build}"
LIVE_BUILD_DIR="$PHOENIX_OS_DIR/live-build"

echo "=== Phoenix OS ISO Build Entrypoint ==="
echo "[INFO] Phoenix OS directory: $PHOENIX_OS_DIR"
echo "[INFO] Artifact directory: $BUILD_DIR"

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
  echo "[INFO] PR22 restored OCI orchestration only; add real live-build config before ISO generation."
  exit 1
fi

echo "[INFO] Preparing writable build environment..."
BUILD_WORK_DIR="/home/phoenix-builder/build-workspace"
rm -rf "$BUILD_WORK_DIR"
mkdir -p "$BUILD_WORK_DIR"

# Copy the configuration and package lists to the writable area
# Using rsync to preserve the structure
rsync -a "$LIVE_BUILD_DIR/" "$BUILD_WORK_DIR/"

echo "[INFO] Running live-build from $BUILD_WORK_DIR."
START_TIME=$(date +%s)
(
  cd "$BUILD_WORK_DIR"
  # Run lb config to ensure everything is initialized in the new location
  lb config
  sudo lb build
)
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

mapfile -t built_isos < <(find "$BUILD_WORK_DIR" -maxdepth 1 -type f -name "*.iso" -print | sort)
if [[ "${#built_isos[@]}" -eq 0 ]]; then
  echo "[FAIL] live-build completed without producing an ISO in $LIVE_BUILD_DIR."
  exit 1
fi

for iso in "${built_isos[@]}"; do
  ISO_NAME=$(basename "$iso")
  DEST="$BUILD_DIR/$ISO_NAME"
  cp "$iso" "$DEST"
  
  if [[ -f "$DEST" ]]; then
    SIZE=$(stat -c%s "$DEST" 2>/dev/null || stat -f%z "$DEST")
    SHA256=$(sha256sum "$DEST" | awk '{print $1}' 2>/dev/null || shasum -a 256 "$DEST" | awk '{print $1}')
    
    echo "[OK] Artifact: $ISO_NAME"
    echo "[OK] Path: $DEST"
    echo "[OK] Size: $SIZE bytes"
    echo "[OK] SHA256: $SHA256"
    echo "[OK] Build Duration: ${DURATION}s"
    
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
