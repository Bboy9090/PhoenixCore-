#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "========================================================"
echo "🐳 Launching Zenith App Hub Linux Container Builder"
echo "========================================================"

if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is required but not installed or not in PATH."
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Error: Docker daemon is not running."
    exit 1
fi

echo "📦 Spinning up Ubuntu container and installing toolchain..."

# We use debian:bookworm because the live-build target OS is Bookworm.
docker run --rm --platform linux/amd64 -v "$REPO_ROOT:/workspace" -w "/workspace" -e CI=true debian:bookworm /bin/bash -c "
    set -euo pipefail
    
    export DEBIAN_FRONTEND=noninteractive
    echo '=> Container Architecture Info:'
    uname -m
    dpkg --print-architecture
    
    echo '=> Updating APT repositories...'
    apt-get update -yq
    
    echo '=> Installing system dependencies...'
    apt-get install -yq curl ca-certificates build-essential pkg-config dpkg-dev patchelf \
        libwebkit2gtk-4.0-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev libsoup2.4-dev
    
    echo '=> Installing Node.js & pnpm...'
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -yq nodejs
    npm install -g pnpm
    
    echo '=> Installing Rust Toolchain...'
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    export PATH=\"\$HOME/.cargo/bin:\$PATH\"
    
    echo '=> Executing PR42A Zenith Builder Script...'
    ./scripts/build-zenith-app-hub-deb.sh
"

echo "✅ Container builder finished successfully."
