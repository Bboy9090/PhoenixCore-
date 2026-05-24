#!/usr/bin/env bash
# Build the flagship arm64 target plus the legacy dd-image target we are
# actively prioritizing right now:
# - Thunder God ARM64 for Apple Silicon / M1-class Macs
# - home-legacy-i386 dd-image for legacy 32-bit Intel Macs

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=========================================================="
echo "Blue Phoenix OS: Flagship ARM64 + Legacy Matrix Builder"
echo "=========================================================="
echo "Targets:"
echo "  - thunder-god-arm64 (most powerful arm64 flagship)"
echo "  - home-legacy-i386 (dd image)"
echo ""
echo "These are separate boot artifacts. One artifact does not boot on every CPU architecture."
echo "The amd64 Home track and Home ARM64 foundation track are deferred for now."
echo "=========================================================="
echo ""

exec bash "$REPO_ROOT/scripts/build-all-isos.sh" \
  --editions=thunder-god-arm64,home-legacy-i386 \
  "$@"
