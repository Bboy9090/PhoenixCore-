#!/bin/bash
# build-edition.sh - Synthesize a BWOS edition ISO

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EDITION_ID=""
STAGE_ONLY=false
CLEAN_STAGING=false

# Paths for staging
LB_CONFIG_DIR="$REPO_ROOT/os/phoenix-os/live-build/config"
STAGING_CHROOT="$LB_CONFIG_DIR/includes.chroot/etc/bwos/edition"
PACKAGE_LIST_DIR="$LB_CONFIG_DIR/package-lists"
STAGED_PKG_LIST="$PACKAGE_LIST_DIR/edition.list.chroot"

function clean_staging() {
    echo "🧹 Cleaning edition staging area..."
    rm -f "$STAGED_PKG_LIST"
    rm -rf "$STAGING_CHROOT"
    echo "✅ Staging area clean."
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --stage-only) STAGE_ONLY=true ;;
        --clean-staging) CLEAN_STAGING=true ;;
        -*) echo "Unknown option: $1"; exit 1 ;;
        *) EDITION_ID="$1" ;;
    esac
    shift
done

if [ "$CLEAN_STAGING" = true ]; then
    clean_staging
    exit 0
fi

if [ -z "$EDITION_ID" ]; then
    echo "Usage: ./build-edition.sh <edition-id> [--stage-only] [--clean-staging]"
    exit 1
fi

EDITION_DIR="$REPO_ROOT/editions/$EDITION_ID"

if [ ! -d "$EDITION_DIR" ]; then
    echo "❌ Error: Edition '$EDITION_ID' not found in $REPO_ROOT/editions/"
    exit 1
fi

# 1. Validate
"$REPO_ROOT/scripts/validate-editions.sh" | grep "Checking $EDITION_ID"

# 2. Extract Metadata
manifest="$EDITION_DIR/edition.yaml"
display_name=$(sed -n 's/^[[:space:]]*display_name:[[:space:]]*//p' "$manifest" | sed 's/^"//;s/"$//')
tagline=$(sed -n 's/^[[:space:]]*tagline:[[:space:]]*//p' "$manifest" | sed 's/^"//;s/"$//')
iso_name=$(sed -n 's/^[[:space:]]*iso_name:[[:space:]]*//p' "$manifest" | sed 's/^"//;s/"$//')

echo "🔨 Selected Edition: $display_name"
echo "   Tagline: \"$tagline\""
echo "   Target ISO: $iso_name"
echo ""

# 3. Stage Edition Assets for live-build
echo "📦 Staging edition assets..."
mkdir -p "$STAGING_CHROOT"
mkdir -p "$PACKAGE_LIST_DIR"

cp "$EDITION_DIR/package-profile.txt" "$STAGED_PKG_LIST"
cp "$EDITION_DIR/colors.css" "$STAGING_CHROOT/colors.css"

cat <<EOF > "$STAGING_CHROOT/metadata.json"
{
  "id": "$EDITION_ID",
  "display_name": "$display_name",
  "tagline": "$tagline"
}
EOF

echo "✅ Assets staged in: $STAGING_CHROOT"
echo "✅ Package list staged: $STAGED_PKG_LIST"

if [ "$STAGE_ONLY" = true ]; then
    echo "⏹️ Stage-only mode complete. Exiting."
    exit 0
fi

# 4. Check Docker Availability
echo "🔍 Checking Docker Synthesis Engine..."
DOCKER_AVAILABLE=false
if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
        DOCKER_AVAILABLE=true
        echo "✅ Docker daemon is reachable."
    else
        echo "⚠️ Docker daemon is not reachable. (Ensure Docker Desktop is running)"
    fi
else
    echo "⚠️ Docker command not found."
fi

# 5. Trigger Synthesis Engine
if [ "$DOCKER_AVAILABLE" = true ]; then
    BUILDER_SCRIPT="$REPO_ROOT/os/phoenix-os/container/build-container.sh"
    echo "🚀 Launching Synthesis Engine (OCI Builder)..."
    if [ -f "$BUILDER_SCRIPT" ]; then
        if bash "$BUILDER_SCRIPT"; then
            echo "✅ Synthesis Complete."
            BUILD_OUT_DIR="$REPO_ROOT/os/phoenix-os/build"
            GENERIC_ISO="$BUILD_OUT_DIR/live-image-amd64.hybrid.iso"
            FINAL_ISO="$BUILD_OUT_DIR/$iso_name"
            if [ -f "$GENERIC_ISO" ]; then
                mv "$GENERIC_ISO" "$FINAL_ISO"
                echo "✨ Produced Edition ISO: $FINAL_ISO"
            fi
        else
            echo "❌ Synthesis Engine failed."
            exit 1
        fi
    else
        echo "❌ Error: build-container.sh not found."
        exit 1
    fi
else
    echo "❌ Error: Cannot proceed with ISO build (Docker unavailable)."
    echo "💡 You can use --stage-only to verify the staging files manually."
    exit 1
fi
