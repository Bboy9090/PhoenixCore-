#!/usr/bin/env bash
# Run the Phoenix OS ISO build inside the OCI builder.
#
# Part of PR31 Build Acceleration Framework.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_OS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$PHOENIX_OS_DIR/build"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
PROJECT_NAME="${PHOENIX_OS_COMPOSE_PROJECT:-phoenix-os-oci}"
SERVICE_NAME="${PHOENIX_OS_BUILDER_SERVICE:-builder}"
VERIFY_CONTAINER="$SCRIPT_DIR/verify-container.sh"

# Default parameters
MODE="release-hardened"
ARCH=""
CLEAN=false
NO_CACHE=false
VERIFY_ONLY=false

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
    --verify-only)
      VERIFY_ONLY=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Apple Silicon Auto-Architecture Default Logic
HOST_ARCH="$(uname -m)"
if [[ -z "$ARCH" ]]; then
  if [[ "$HOST_ARCH" == "arm64" && "$MODE" == "fast" ]]; then
    ARCH="arm64"
    echo "[INFO] Apple Silicon detected. Defaulting to native local speed build: arm64"
  else
    ARCH="amd64"
    echo "[INFO] Defaulting to target architecture: amd64"
  fi
fi

# Export OCI Platform Environment for docker-compose.yml
export PHOENIX_OS_PLATFORM="linux/$ARCH"

compose() {
  docker compose \
    -f "$COMPOSE_FILE" \
    --project-directory "$SCRIPT_DIR" \
    --project-name "$PROJECT_NAME" \
    "$@"
}

checksum_file() {
  local path="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$path" | awk '{print $1}'
  else
    shasum -a 256 "$path" | awk '{print $1}'
  fi
}

run_builder() {
  compose run --rm "$SERVICE_NAME" "$@"
}

main() {
  echo "=== Phoenix OS OCI Build ==="
  echo "[INFO] Mode: $MODE"
  echo "[INFO] Arch: $ARCH"
  echo "[INFO] Host Arch: $HOST_ARCH"
  echo "[INFO] Platform target: $PHOENIX_OS_PLATFORM"

  # 1. Clean operation
  if [[ "$CLEAN" == "true" ]]; then
    echo "[INFO] Cleaning host build artifacts and persistent cache..."
    rm -rf "$BUILD_DIR"/*
    rm -rf "$PHOENIX_OS_DIR/cache"/*
    
    # Run container clean to delete working workspace
    echo "[INFO] Verifying container builder before clean..."
    bash "$VERIFY_CONTAINER"
    run_builder bash -lc "bash /workspace/os/phoenix-os/scripts/build-iso.sh --clean"
    echo "=== Clean Complete ==="
    exit 0
  fi

  # 2. Verify only
  if [[ "$VERIFY_ONLY" == "true" ]]; then
    echo "[INFO] Running verification checks only..."
    bash "$PHOENIX_OS_DIR/scripts/verify-build.sh" --mode "$MODE" --arch "$ARCH" --verify-only
    exit 0
  fi

  # Ensure caching folders exist on host before composing
  mkdir -p "$PHOENIX_OS_DIR/cache/packages.chroot"
  mkdir -p "$BUILD_DIR"

  echo "[INFO] Verifying builder before build..."
  bash "$VERIFY_CONTAINER"

  echo "[INFO] Running build-iso.sh inside the builder..."
  
  # Assemble dynamic options for build-iso.sh
  BUILD_ARGS="--mode $MODE --arch $ARCH"
  if [[ "$NO_CACHE" == "true" ]]; then
    BUILD_ARGS="$BUILD_ARGS --no-cache"
  fi

  run_builder bash -lc "
    set -euo pipefail
    builder=\"/workspace/os/phoenix-os/scripts/build-iso.sh\"
    if [[ ! -f \"\$builder\" ]]; then
      echo \"[FAIL] Missing in-container build script: \$builder\"
      exit 1
    fi
    bash \"\$builder\" $BUILD_ARGS
  "

  # Find built ISO files and summarize
  iso_files=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && iso_files+=("$line")
  done < <(find "$BUILD_DIR" -maxdepth 1 -type f -name "*.iso" -print | sort)
  
  if [[ "${#iso_files[@]}" -eq 0 ]]; then
    echo "[FAIL] Build completed, but no ISO exists under $BUILD_DIR."
    exit 1
  fi

  if [[ "${#iso_files[@]}" -gt 1 ]]; then
    echo "[WARN] Multiple ISO artifacts found; reporting all checksums."
  fi

  for iso in "${iso_files[@]}"; do
    echo "[OK] ISO: $iso"
    echo "[OK] SHA256: $(checksum_file "$iso")"
    echo "[OK] Size: $(stat -c%s "$iso" 2>/dev/null || stat -f%z "$iso") bytes"
  done

  echo "=== Phoenix OS OCI Build Complete ==="
}

main "$@"
