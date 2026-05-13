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

echo "[INFO] Running live-build from $LIVE_BUILD_DIR."
(
  cd "$LIVE_BUILD_DIR"
  lb build
)

mapfile -t built_isos < <(find "$LIVE_BUILD_DIR" -maxdepth 1 -type f -name "*.iso" -print | sort)
if [[ "${#built_isos[@]}" -eq 0 ]]; then
  echo "[FAIL] live-build completed without producing an ISO in $LIVE_BUILD_DIR."
  exit 1
fi

for iso in "${built_isos[@]}"; do
  cp "$iso" "$BUILD_DIR/"
  echo "[OK] Copied ISO artifact to $BUILD_DIR/$(basename "$iso")"
done

echo "=== Phoenix OS ISO Build Entrypoint Complete ==="
