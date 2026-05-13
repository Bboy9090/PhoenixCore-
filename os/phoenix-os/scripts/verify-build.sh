#!/usr/bin/env bash
# Non-destructive in-container checks for the Phoenix OS build skeleton.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_OS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="${PHOENIX_OS_ARTIFACT_DIR:-$PHOENIX_OS_DIR/build}"

required_paths=(
  "$PHOENIX_OS_DIR/README.md"
  "$PHOENIX_OS_DIR/live-build/README.md"
  "$PHOENIX_OS_DIR/calamares/README.md"
  "$PHOENIX_OS_DIR/branding/README.md"
  "$PHOENIX_OS_DIR/package-lists/README.md"
  "$PHOENIX_OS_DIR/scripts/build-iso.sh"
)

echo "=== Phoenix OS Build Skeleton Verification ==="
echo "[INFO] Phoenix OS directory: $PHOENIX_OS_DIR"
echo "[INFO] Artifact directory: $BUILD_DIR"

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

if grep -RInE '(^|[;&|[:space:]])rm[[:space:]]+-rf[[:space:]]+/($|[[:space:]])' \
  "$PHOENIX_OS_DIR/scripts" "$PHOENIX_OS_DIR/container" >/tmp/phoenix-destructive-grep.txt 2>/dev/null; then
  cat /tmp/phoenix-destructive-grep.txt
  echo "[FAIL] Potential destructive host logic detected."
  exit 1
fi
echo "[OK] No destructive root-removal pattern found in Phoenix OS scripts/container files."

echo "=== Phoenix OS Build Skeleton Verification Complete ==="
