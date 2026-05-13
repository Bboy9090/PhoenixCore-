#!/bin/bash
# Phoenix OS Containerized Verification Wrapper

set -e

CONTAINER_DIR=$(dirname "$0")
cd "$CONTAINER_DIR"

echo "=== Phoenix OS OCI Verification ==="

# Check for docker
if ! command -v docker &> /dev/null; then
    echo "[FAIL] Docker not found."
    exit 1
fi

echo "Building container image..."
docker compose build builder

echo "Checking build tool versions inside container..."
docker compose run --rm builder bash -c "
  lb --version && \
  debootstrap --version && \
  xorriso -version | head -n 1
"

echo "Verifying build skeleton inside container..."
docker compose run --rm builder bash scripts/verify-build.sh

echo "=== OCI Verification Complete ==="
