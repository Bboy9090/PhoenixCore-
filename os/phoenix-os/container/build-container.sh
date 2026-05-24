#!/usr/bin/env bash
# Run the Phoenix OS ISO build inside the OCI builder.
#
# Part of PR32 Incremental Build Acceleration.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_OS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$PHOENIX_OS_DIR/build"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
PROJECT_NAME="${PHOENIX_OS_COMPOSE_PROJECT:-phoenix-os-oci}"
SERVICE_NAME="${PHOENIX_OS_BUILDER_SERVICE:-builder}"
VERIFY_CONTAINER="$SCRIPT_DIR/verify-container.sh"

# Default parameters
MODE="release"
ARCH=""
LINUX_FLAVOUR=""
BOOTLOADER="grub-efi"
CLEAN_MODE="stage" # stage, none, all
NO_CACHE=false
VERIFY_ONLY=false

# Support both --clean (legacy boolean) and --clean=mode (PR32 syntax)
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
    --linux-flavour)
      LINUX_FLAVOUR="$2"
      shift 2
      ;;
    --bootloader)
      BOOTLOADER="$2"
      shift 2
      ;;
    --clean=*)
      CLEAN_MODE="${1#*=}"
      shift
      ;;
    --clean)
      CLEAN_MODE="all"
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
  if [[ "$HOST_ARCH" == "arm64" && ( "$MODE" == "dev-minimal" || "$MODE" == "fast" ) ]]; then
    ARCH="arm64"
    echo "[INFO] Apple Silicon detected. Defaulting to native local speed build: arm64"
  else
    ARCH="amd64"
    echo "[INFO] Defaulting to target architecture: amd64"
  fi
fi

# Builder runtime platform can differ from target build architecture.
# i386 targets are built in an amd64 container.
BUILDER_PLATFORM_ARCH="$ARCH"
if [[ "$ARCH" == "i386" ]]; then
  BUILDER_PLATFORM_ARCH="amd64"
fi

# Export OCI Platform Environment for docker-compose.yml
export PHOENIX_OS_PLATFORM="linux/$BUILDER_PLATFORM_ARCH"

# Forward Host PHOENIX_APT_PROXY into local script env
export PHOENIX_APT_PROXY="${PHOENIX_APT_PROXY:-}"

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
  echo "[INFO] Target Arch: $ARCH"
  echo "[INFO] Linux Flavour: ${LINUX_FLAVOUR:-auto}"
  echo "[INFO] Bootloader: $BOOTLOADER"
  echo "[INFO] Host Arch: $HOST_ARCH"
  echo "[INFO] Builder Platform: $PHOENIX_OS_PLATFORM"
  echo "[INFO] Clean Mode: $CLEAN_MODE"
  echo "[INFO] APT Cache Proxy: ${PHOENIX_APT_PROXY:-None}"

  # 1. Clean operation
  if [[ "$CLEAN_MODE" == "all" ]]; then
    echo "[INFO] Cleaning host build artifacts and persistent cache..."
    rm -rf "$BUILD_DIR"/*
    rm -rf "$PHOENIX_OS_DIR/cache"/*
    
    # Run container clean to delete working workspace
    echo "[INFO] Verifying container builder before clean..."
    bash "$VERIFY_CONTAINER"
    run_builder bash -lc "bash /workspace/os/phoenix-os/scripts/build-iso.sh --clean=all"
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

  # Remap telemetry paths for the container namespace.
  export PHOENIX_BUILD_TELEMETRY_DIR="${PHOENIX_BUILD_TELEMETRY_DIR_CONTAINER:-${PHOENIX_BUILD_TELEMETRY_DIR:-}}"
  export PHOENIX_BUILD_STATE_JSON="${PHOENIX_BUILD_STATE_JSON_CONTAINER:-${PHOENIX_BUILD_STATE_JSON:-}}"
  export PHOENIX_BUILD_EVENT_LOG="${PHOENIX_BUILD_EVENT_LOG_CONTAINER:-${PHOENIX_BUILD_EVENT_LOG:-}}"
  export PHOENIX_BUILD_HUMAN_LOG="${PHOENIX_BUILD_HUMAN_LOG_CONTAINER:-${PHOENIX_BUILD_HUMAN_LOG:-}}"
  export PHOENIX_BUILD_PHASE_TIMINGS="${PHOENIX_BUILD_PHASE_TIMINGS_CONTAINER:-${PHOENIX_BUILD_PHASE_TIMINGS:-}}"
  export PHOENIX_BUILD_WARNINGS_LOG="${PHOENIX_BUILD_WARNINGS_LOG_CONTAINER:-${PHOENIX_BUILD_WARNINGS_LOG:-}}"
  export PHOENIX_BUILD_FAILURES_LOG="${PHOENIX_BUILD_FAILURES_LOG_CONTAINER:-${PHOENIX_BUILD_FAILURES_LOG:-}}"
  export PHOENIX_BUILD_SUMMARY_JSON="${PHOENIX_BUILD_SUMMARY_JSON_CONTAINER:-${PHOENIX_BUILD_SUMMARY_JSON:-}}"
  export PHOENIX_BUILD_SUMMARY_MD="${PHOENIX_BUILD_SUMMARY_MD_CONTAINER:-${PHOENIX_BUILD_SUMMARY_MD:-}}"

  echo "[INFO] Verifying builder before build..."
  bash "$VERIFY_CONTAINER"

  echo "[INFO] Running build-iso.sh inside the builder..."
  
  # Assemble dynamic options for build-iso.sh
  BUILD_ARGS="--mode $MODE --arch $ARCH --bootloader $BOOTLOADER --clean=$CLEAN_MODE"
  if [[ -n "$LINUX_FLAVOUR" ]]; then
    BUILD_ARGS="$BUILD_ARGS --linux-flavour $LINUX_FLAVOUR"
  fi
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
  artifact_files=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && artifact_files+=("$line")
  done < <(find "$BUILD_DIR" -maxdepth 1 -type f \( -name "*.iso" -o -name "*.img" \) -print | sort)
  
  if [[ "${#artifact_files[@]}" -eq 0 ]]; then
    echo "[FAIL] Build completed, but no artifact exists under $BUILD_DIR."
    exit 1
  fi

  if [[ "${#artifact_files[@]}" -gt 1 ]]; then
    echo "[WARN] Multiple build artifacts found; reporting all checksums."
  fi

  for artifact in "${artifact_files[@]}"; do
    echo "[OK] Artifact: $artifact"
    echo "[OK] SHA256: $(checksum_file "$artifact")"
    echo "[OK] Size: $(stat -c%s "$artifact" 2>/dev/null || stat -f%z "$artifact") bytes"
  done

  echo "=== Phoenix OS OCI Build Complete ==="
}

main "$@"
