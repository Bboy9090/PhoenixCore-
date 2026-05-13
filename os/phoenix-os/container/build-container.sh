#!/usr/bin/env bash
# Run the Phoenix OS ISO build inside the OCI builder.

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PHOENIX_OS_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$PHOENIX_OS_DIR/build"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
PROJECT_NAME="${PHOENIX_OS_COMPOSE_PROJECT:-phoenix-os-oci}"
SERVICE_NAME="${PHOENIX_OS_BUILDER_SERVICE:-builder}"
VERIFY_CONTAINER="$SCRIPT_DIR/verify-container.sh"

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
  echo "[INFO] Verifying builder before build..."
  bash "$VERIFY_CONTAINER"

  mkdir -p "$BUILD_DIR"

  echo "[INFO] Running build-iso.sh inside the builder..."
  run_builder bash -lc '
    set -euo pipefail
    builder="/workspace/os/phoenix-os/scripts/build-iso.sh"
    if [[ ! -f "$builder" ]]; then
      echo "[FAIL] Missing in-container build script: $builder"
      exit 1
    fi
    bash "$builder"
  '

  mapfile -t iso_files < <(find "$BUILD_DIR" -maxdepth 1 -type f -name "*.iso" -print | sort)
  if [[ "${#iso_files[@]}" -eq 0 ]]; then
    echo "[FAIL] Build command completed, but no ISO exists under $BUILD_DIR."
    exit 1
  fi

  if [[ "${#iso_files[@]}" -gt 1 ]]; then
    echo "[WARN] Multiple ISO artifacts found; reporting all checksums."
  fi

  for iso in "${iso_files[@]}"; do
    echo "[OK] ISO: $iso"
    echo "[OK] SHA256: $(checksum_file "$iso")"
  done

  echo "=== Phoenix OS OCI Build Complete ==="
}

main "$@"
