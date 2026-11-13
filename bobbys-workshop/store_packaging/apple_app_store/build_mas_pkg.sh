#!/usr/bin/env bash
# build_mas_pkg.sh — Packages BobFWTools Studio (-DSTORE_EDITION) into a Mac App Store .pkg installer
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
STORE_APP="${ROOT_DIR}/bobbys-workshop/dist/Store-Submission/BobFWTools.app"
OUT_PKG="${ROOT_DIR}/bobbys-workshop/dist/Store-Submission/BobFWTools-MacAppStore-5.0.0.pkg"

if [ ! -d "${STORE_APP}" ]; then
    echo "Error: Store bundle not found at ${STORE_APP}. Run bobbys-workshop/build_app.sh first." >&2
    exit 1
fi

xattr -cr "${STORE_APP}" 2>/dev/null || true
productbuild --component "${STORE_APP}" /Applications "${OUT_PKG}"
echo "[✓] Mac App Store submission package created: ${OUT_PKG}"
