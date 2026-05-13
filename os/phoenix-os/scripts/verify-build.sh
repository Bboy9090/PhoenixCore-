#!/bin/bash
# Phoenix OS Build Verification Script

set -e

echo "=== Verifying Phoenix OS Build Skeleton ==="

# Check directories
DIRS=("config" "packages" "scripts" "branding" "overlays" "docs")
for dir in "${DIRS[@]}"; do
    if [ -d "os/phoenix-os/$dir" ]; then
        echo "[OK] Directory found: $dir"
    else
        echo "[FAIL] Missing directory: $dir"
        exit 1
    fi
done

# Check package manifests
FILES=("base.list" "kde.list" "phoenix.list")
for file in "${FILES[@]}"; do
    if [ -f "os/phoenix-os/packages/$file" ]; then
        echo "[OK] Manifest found: $file"
    else
        echo "[FAIL] Missing manifest: $file"
        exit 1
    fi
done

# Check for destructive logic (safety check)
if grep -r "rm -rf /" os/phoenix-os/scripts; then
    echo "[CRITICAL] Destructive logic detected in scripts!"
    exit 1
fi

echo "=== Verification Successful ==="
