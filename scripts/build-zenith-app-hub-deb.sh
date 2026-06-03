#!/bin/bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$REPO_ROOT/apps/native-app-hub"
CHROOT_PACKAGES_DIR="$REPO_ROOT/os/phoenix-os/live-build/config/packages.chroot"

echo "==============================================="
echo "⚙️  Building Zenith App Hub Debian Package"
echo "==============================================="

if [ ! -d "$APP_DIR" ]; then
    echo "❌ Error: Native App Hub source not found at $APP_DIR"
    exit 1
fi

if ! command -v pnpm &> /dev/null; then
    echo "❌ Error: 'pnpm' is required but not installed."
    exit 1
fi

if ! command -v cargo &> /dev/null; then
    echo "❌ Error: 'cargo' (Rust toolchain) is required but not installed."
    exit 1
fi

# Tauri deb bundling on macOS requires dpkg and potentially cross-compilation tools
# We will just attempt to run the standard bundler command
echo "📦 Installing Node dependencies..."
cd "$APP_DIR"
pnpm install

echo "🦀 Building Tauri Debian package..."
# Use --bundles deb to specifically request only the debian package
pnpm tauri build --bundles deb

# Find the resulting .deb file
DEB_PATH=$(find "$APP_DIR/src-tauri/target/release/bundle/deb" -name "*.deb" -type f 2>/dev/null | head -n 1 || true)

if [ -z "$DEB_PATH" ]; then
    echo "❌ Error: Debian package was not generated. Check the Tauri build output."
    exit 1
fi

echo "✅ Package built: $DEB_PATH"

echo "🗂️  Staging to live-build packages.chroot..."
mkdir -p "$CHROOT_PACKAGES_DIR"
cp "$DEB_PATH" "$CHROOT_PACKAGES_DIR/"

FINAL_DEB="$CHROOT_PACKAGES_DIR/$(basename "$DEB_PATH")"
echo "✨ Success! Final staged package: $FINAL_DEB"
