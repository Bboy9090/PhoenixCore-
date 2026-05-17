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
    # Restore original lists from backups if they exist
    for bak in "$PACKAGE_LIST_DIR"/*.list.chroot.bak; do
        [ -f "$bak" ] || continue
        echo "⏪ Restoring: $(basename "${bak%.bak}")"
        mv "$bak" "${bak%.bak}"
    done
    echo "✅ Staging area clean."
}

function sanitize_list() {
    local list_file="$1"
    echo "🧹 Sanitizing package list: $(basename "$list_file")"
    # Create a sanitized version: remove comments, trailing hashes, and empty lines
    local temp_file="${list_file}.tmp"
    local bak_file="${list_file}.bak"
    # Only backup if not already backed up
    if [ ! -f "$bak_file" ]; then
        cp "$list_file" "$bak_file"
    fi

    # Blocked packages that cause build failures (Mono/GTK# chain)
    local blocked_pkgs=("bless" "libglib2.0-cil" "libglade2.0-cil" "libgtk2.0-cil" "mono-runtime" "mono-common")
    
    # Filter out comments, empty lines, AND blocked packages
    # 1. Strip comments and whitespace
    # 2. Filter out exact matches for blocked packages
    grep -v '^[[:space:]]*#' "$bak_file" | sed 's/[[:space:]]*#.*//' | sed 's/[[:space:]]*$//' | grep -v '^[[:space:]]*$' > "$temp_file"

    for pkg in "${blocked_pkgs[@]}"; do
        if grep -qx "$pkg" "$temp_file"; then
            echo "⚠️  WARNING: Blocked package '$pkg' found in $(basename "$list_file"). Removing to prevent build failure."
            grep -vx "$pkg" "$temp_file" > "${temp_file}.new"
            mv "${temp_file}.new" "$temp_file"
        fi
    done
    
    mv "$temp_file" "$list_file"
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

# Sanitize all package lists in the staging area to prevent apt errors from comments
for list in "$PACKAGE_LIST_DIR"/*.list.chroot; do
    sanitize_list "$list"
done

cp "$EDITION_DIR/colors.css" "$STAGING_CHROOT/colors.css"

# Stage custom wallpaper if defined and present
wallpaper_name=$(sed -n 's/^[[:space:]]*wallpaper:[[:space:]]*//p' "$manifest" | sed 's/^"//;s/"$//')
if [ -n "$wallpaper_name" ] && [ -f "$EDITION_DIR/$wallpaper_name" ]; then
    echo "🖼️  Staging custom wallpaper: $wallpaper_name"
    mkdir -p "$LB_CONFIG_DIR/includes.chroot/usr/share/images/desktop-base"
    cp "$EDITION_DIR/$wallpaper_name" "$LB_CONFIG_DIR/includes.chroot/usr/share/images/desktop-base/desktop-background.png"
fi

# Stage custom logo if defined and present (overrides Plymouth boot splash and SDDM login screens)
logo_name=$(sed -n 's/^[[:space:]]*logo:[[:space:]]*//p' "$manifest" | sed 's/^"//;s/"$//')
if [ -n "$logo_name" ] && [ -f "$EDITION_DIR/$logo_name" ]; then
    echo "🎨 Staging custom logo: $logo_name"
    mkdir -p "$LB_CONFIG_DIR/includes.chroot/usr/share/plymouth/themes/phoenix"
    mkdir -p "$LB_CONFIG_DIR/includes.chroot/usr/share/sddm/themes/phoenix"
    cp "$EDITION_DIR/$logo_name" "$LB_CONFIG_DIR/includes.chroot/usr/share/plymouth/themes/phoenix/phoenix-logo-boot.svg"
    cp "$EDITION_DIR/$logo_name" "$LB_CONFIG_DIR/includes.chroot/usr/share/sddm/themes/phoenix/logo.svg"
fi

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
            # We don't auto-clean here to allow debugging, but we warn the user
            echo "💡 Staging area remains active. Run './scripts/build-edition.sh --clean-staging' to restore original lists."
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
