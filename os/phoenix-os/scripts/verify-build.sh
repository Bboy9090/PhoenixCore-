#!/usr/bin/env bash
# Non-destructive in-container checks for the Phoenix OS build skeleton.
#
# Part of PR32 Incremental Build Acceleration.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_OS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="${PHOENIX_OS_ARTIFACT_DIR:-$PHOENIX_OS_DIR/build}"

# Default parameters to validate
MODE="release"
ARCH="amd64"
CLEAN_MODE="stage"
NO_CACHE=false
VERIFY_ONLY=false

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --mode) MODE="$2"; shift 2 ;;
    --arch) ARCH="$2"; shift 2 ;;
    --clean=*) CLEAN_MODE="${1#*=}"; shift ;;
    --clean) CLEAN_MODE="all"; shift ;;
    --no-cache) NO_CACHE=true; shift ;;
    --verify-only) VERIFY_ONLY=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

echo "=== Phoenix OS Build Skeleton Verification ==="
echo "[INFO] Phoenix OS directory: $PHOENIX_OS_DIR"
echo "[INFO] Artifact directory: $BUILD_DIR"
echo "[INFO] Mode to validate: $MODE"
echo "[INFO] Arch to validate: $ARCH"
echo "[INFO] Clean Mode to validate: $CLEAN_MODE"

# Validate options
if [[ "$MODE" != "dev-minimal" && "$MODE" != "desktop" && "$MODE" != "recovery" && "$MODE" != "release" && "$MODE" != "fast" && "$MODE" != "full" && "$MODE" != "release-hardened" ]]; then
  echo "[FAIL] Invalid build mode: $MODE"
  exit 1
fi

if [[ "$ARCH" != "amd64" && "$ARCH" != "arm64" && "$ARCH" != "i386" ]]; then
  echo "[FAIL] Invalid architecture: $ARCH"
  exit 1
fi

if [[ "$CLEAN_MODE" != "none" && "$CLEAN_MODE" != "stage" && "$CLEAN_MODE" != "all" ]]; then
  echo "[FAIL] Invalid clean mode: $CLEAN_MODE"
  exit 1
fi

required_paths=(
  "$PHOENIX_OS_DIR/README.md"
  "$PHOENIX_OS_DIR/live-build/README.md"
  "$PHOENIX_OS_DIR/calamares/README.md"
  "$PHOENIX_OS_DIR/branding/README.md"
  "$PHOENIX_OS_DIR/package-lists/README.md"
  "$PHOENIX_OS_DIR/scripts/build-iso.sh"
  "$PHOENIX_OS_DIR/scripts/package-cache.sh"
  "$PHOENIX_OS_DIR/scripts/refresh-overlays.sh"
  "$PHOENIX_OS_DIR/live-build/config/package-lists/profiles/fast.list.chroot"
  "$PHOENIX_OS_DIR/live-build/config/package-lists/profiles/full.list.chroot"
  "$PHOENIX_OS_DIR/live-build/config/package-lists/profiles/recovery-tools.list.chroot"
  "$PHOENIX_OS_DIR/live-build/config/package-lists/profiles/branding-tools.list.chroot"
  "$PHOENIX_OS_DIR/live-build/config/package-lists/edition.list.chroot"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "[FAIL] Missing required path: $path"
    exit 1
  fi
  echo "[OK] Found: $path"
done

if [[ "$BUILD_DIR" != "$PHOENIX_OS_DIR/build" ]]; then
  echo "[FAIL] Artifact directory must resolve to os/phoenix-os/build."
  exit 1
fi

mkdir -p "$BUILD_DIR"
probe="$BUILD_DIR/.phoenix-write-check"
printf 'ok\n' >"$probe"
rm -f "$probe"
echo "[OK] Artifact directory is writable."

# Destructive logic checks
if grep -RInE '(^|[;&|[:space:]])rm[[:space:]]+-rf[[:space:]]+/($|[[:space:]])' \
  "$PHOENIX_OS_DIR/scripts" "$PHOENIX_OS_DIR/container" >/tmp/phoenix-destructive-grep.txt 2>/dev/null; then
  cat /tmp/phoenix-destructive-grep.txt
  echo "[FAIL] Potential destructive host logic detected."
  exit 1
fi
echo "[OK] No destructive root-removal pattern found in Phoenix OS scripts/container files."

# Check if prebuilt packages dir exists
mkdir -p "$PHOENIX_OS_DIR/build/packages"
echo "[OK] Prebuilt custom packages directory is staged."

# Check if target ISO exists
TARGET_ISO="$BUILD_DIR/phoenix-os-${MODE}-${ARCH}.iso"
if [[ -f "$TARGET_ISO" ]]; then
  SIZE=$(stat -c%s "$TARGET_ISO" 2>/dev/null || stat -f%z "$TARGET_ISO")
  SHA256=$(sha256sum "$TARGET_ISO" | awk '{print $1}' 2>/dev/null || shasum -a 256 "$TARGET_ISO" | awk '{print $1}')
  echo "[OK] Staged ISO exists: $TARGET_ISO"
  echo "[OK] Size: $SIZE bytes"
  echo "[OK] SHA256: $SHA256"
else
  echo "[INFO] No pre-existing ISO found for $MODE-$ARCH (standard behavior before first build)."
fi

echo "=== Phoenix OS Build Skeleton Verification Complete ==="
