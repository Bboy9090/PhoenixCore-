#!/bin/bash
# build-edition.sh - Synthesize a BWOS edition ISO

set -euo pipefail

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

function manifest_value() {
    local key="$1"
    local file="$2"
    sed -n "s/^[[:space:]]*${key}:[[:space:]]*//p" "$file" | sed 's/^"//;s/"$//' | head -n 1
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
display_name=$(manifest_value display_name "$manifest")
tagline=$(manifest_value tagline "$manifest")
iso_name=$(manifest_value iso_name "$manifest")
wallpaper_name=$(manifest_value wallpaper "$manifest")
logo_name=$(manifest_value logo "$manifest")

if [ -n "$wallpaper_name" ] && [ ! -f "$EDITION_DIR/$wallpaper_name" ]; then
    echo "❌ Error: Wallpaper path in manifest does not exist: $wallpaper_name"
    exit 1
fi

if [ -n "$logo_name" ] && [ ! -f "$EDITION_DIR/$logo_name" ]; then
    echo "❌ Error: Logo path in manifest does not exist: $logo_name"
    exit 1
fi

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

# Stage custom wallpaper if defined
if [ -n "$wallpaper_name" ]; then
    echo "🖼️  Staging custom wallpaper: $wallpaper_name"
    mkdir -p "$LB_CONFIG_DIR/includes.chroot/usr/share/images/desktop-base"
    cp "$EDITION_DIR/$wallpaper_name" "$LB_CONFIG_DIR/includes.chroot/usr/share/images/desktop-base/desktop-background.png"
else
    echo "⚠️  WARNING: No wallpaper entry found in manifest."
fi

# Stage custom logo if defined (overrides Plymouth boot splash and SDDM login screen assets)
if [ -n "$logo_name" ]; then
    echo "🎨 Staging custom logo and full branding templates: $logo_name"
    plymouth_theme_root="$LB_CONFIG_DIR/includes.chroot/usr/share/plymouth/themes"
    sddm_theme_root="$LB_CONFIG_DIR/includes.chroot/usr/share/sddm/themes"
    plymouth_theme_dir="$plymouth_theme_root/phoenix"
    sddm_theme_dir="$sddm_theme_root/phoenix"

    mkdir -p "$plymouth_theme_root" "$sddm_theme_root"
    rm -rf "$plymouth_theme_dir" "$sddm_theme_dir"

    cp -R "$REPO_ROOT/os/phoenix-os/branding/plymouth/phoenix" "$plymouth_theme_root/"
    cp -R "$REPO_ROOT/os/phoenix-os/branding/sddm/phoenix" "$sddm_theme_root/"

    logo_path="$EDITION_DIR/$logo_name"
    logo_mime="$(file -b --mime-type "$logo_path" 2>/dev/null || true)"

    case "$logo_mime" in
        image/svg+xml)
            cp "$logo_path" "$plymouth_theme_dir/phoenix-logo-boot.svg"
            cp "$logo_path" "$sddm_theme_dir/logo.svg"
            rm -f "$plymouth_theme_dir/phoenix-logo-boot.png" "$sddm_theme_dir/logo.png"
            ;;
        image/*)
            cp "$logo_path" "$plymouth_theme_dir/phoenix-logo-boot.png"
            cp "$logo_path" "$sddm_theme_dir/logo.png"
            rm -f "$plymouth_theme_dir/phoenix-logo-boot.svg" "$sddm_theme_dir/logo.svg"
            ;;
        *)
            echo "❌ Error: Unsupported logo MIME type '$logo_mime' for $logo_name"
            exit 1
            ;;
    esac
else
    echo "⚠️  WARNING: No logo entry found in manifest."
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
