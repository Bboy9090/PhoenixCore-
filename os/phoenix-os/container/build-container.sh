#!/bin/bash
# Phoenix OS Containerized Build Wrapper

set -e

CONTAINER_DIR=$(dirname "$0")
cd "$CONTAINER_DIR"

echo "=== Phoenix OS OCI Build: Initialization ==="

# Check for docker
if ! command -v docker &> /dev/null; then
    echo "[FAIL] Docker not found. Please install Docker or Podman."
    exit 1
fi

echo "Building container image..."
docker compose build builder

echo "Checking build tool versions inside container..."
docker compose run --rm builder bash -c "
  echo -n 'live-build: ' && lb --version && \
  echo -n 'debootstrap: ' && debootstrap --version && \
  echo -n 'xorriso: ' && xorriso -version | head -n 1 && \
  echo -n 'mksquashfs: ' && mksquashfs -version | head -n 1
"

echo "Executing build-iso.sh inside container..."
docker compose run --rm builder sudo bash scripts/build-iso.sh

echo "=== OCI Build Complete ==="
