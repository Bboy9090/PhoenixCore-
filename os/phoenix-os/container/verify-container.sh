#!/usr/bin/env bash
# Verify the Phoenix OS OCI builder image and in-container build prerequisites.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_OS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$PHOENIX_OS_DIR/build"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
PROJECT_NAME="${PHOENIX_OS_COMPOSE_PROJECT:-phoenix-os-oci}"
SERVICE_NAME="${PHOENIX_OS_BUILDER_SERVICE:-builder}"

compose() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose \
      -f "$COMPOSE_FILE" \
      --project-directory "$SCRIPT_DIR" \
      --project-name "$PROJECT_NAME" \
      "$@"
  else
    docker-compose \
      -f "$COMPOSE_FILE" \
      --project-directory "$SCRIPT_DIR" \
      --project-name "$PROJECT_NAME" \
      "$@"
  fi
}

require_host_tools() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "[FAIL] docker was not found in PATH."
    exit 1
  fi

  if ! docker compose version >/dev/null 2>&1 && ! command -v docker-compose >/dev/null 2>&1; then
    echo "[FAIL] Neither 'docker compose' (v2) nor 'docker-compose' (v1/v2 standalone) is available."
    exit 1
  fi

  if ! docker info >/dev/null 2>&1; then
    echo "[FAIL] Docker daemon is not reachable or permission denied."
    exit 1
  fi
}

run_builder() {
  compose run --rm "$SERVICE_NAME" "$@"
}

main() {
  echo "=== Phoenix OS OCI Container Verification ==="
  echo "[INFO] Compose file: $COMPOSE_FILE"
  echo "[INFO] Artifact directory: $BUILD_DIR"

  require_host_tools
  mkdir -p "$BUILD_DIR"

  echo "[INFO] Building OCI builder image if needed..."
  compose build "$SERVICE_NAME"

  echo "[INFO] Verifying required tools inside the builder..."
  run_builder bash -lc '
    set -euo pipefail
    echo "[TOOL] lb: $(lb --version 2>&1 | head -n 1)"
    echo "[TOOL] debootstrap: $(debootstrap --version 2>&1 | head -n 1)"
    echo "[TOOL] xorriso: $(xorriso -version 2>&1 | head -n 1)"
    echo "[TOOL] mksquashfs: $(mksquashfs -version 2>&1 | head -n 1)"
    echo "[TOOL] cpio: $(cpio --version 2>&1 | head -n 1)"
    echo "[TOOL] grub-mkrescue: $(grub-mkrescue --version 2>&1 | head -n 1)"
  '

  echo "[INFO] Running Phoenix OS build skeleton verifier inside the builder..."
  run_builder bash -lc '
    set -euo pipefail
    verifier="/workspace/os/phoenix-os/scripts/verify-build.sh"
    if [[ ! -f "$verifier" ]]; then
      echo "[FAIL] Missing in-container verifier: $verifier"
      exit 1
    fi
    bash "$verifier"
  '

  echo "=== Phoenix OS OCI Container Verification Complete ==="
}

main "$@"
