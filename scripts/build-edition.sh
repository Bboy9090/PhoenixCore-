#!/bin/bash
# build-edition.sh - Synthesize a BWOS edition ISO

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EDITION_ID=""
STAGE_ONLY=false
CLEAN_STAGING=false

# Transient staging roots (kept out of tracked live-build config/)
STAGING_ROOT="$REPO_ROOT/os/phoenix-os/cache/edition-staging"
STAGING_LB_CONFIG_DIR="$STAGING_ROOT/live-build-config"
STAGING_CHROOT="$STAGING_LB_CONFIG_DIR/includes.chroot/etc/bwos/edition"
PACKAGE_LIST_DIR="$STAGING_LB_CONFIG_DIR/package-lists"
STAGED_PKG_LIST="$PACKAGE_LIST_DIR/edition.list.chroot"
STAGING_WALLPAPER_PATH="$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/images/desktop-base/desktop-background.png"

function clean_staging() {
    echo "🧹 Cleaning transient edition staging cache..."
    rm -rf "$STAGING_ROOT"
    echo "✅ Transient staging cache clean."
}

function sanitize_package_profile() {
    local source_file="$1"
    local target_file="$2"
    echo "🧹 Sanitizing package profile: $(basename "$source_file")"
    local temp_file="${target_file}.tmp"
    # Blocked packages that cause build failures (Mono/GTK# chain)
    local blocked_pkgs=("bless" "libglib2.0-cil" "libglade2.0-cil" "libgtk2.0-cil" "mono-runtime" "mono-common")
    
    # Filter out comments, empty lines, AND blocked packages
    # 1. Strip comments and whitespace
    # 2. Filter out exact matches for blocked packages
    grep -v '^[[:space:]]*#' "$source_file" | sed 's/[[:space:]]*#.*//' | sed 's/[[:space:]]*$//' | grep -v '^[[:space:]]*$' > "$temp_file"

    for pkg in "${blocked_pkgs[@]}"; do
        if grep -qx "$pkg" "$temp_file"; then
            echo "⚠️  WARNING: Blocked package '$pkg' found in $(basename "$source_file"). Removing to prevent build failure."
            grep -vx "$pkg" "$temp_file" > "${temp_file}.new"
            mv "${temp_file}.new" "$temp_file"
        fi
    done
    
    mkdir -p "$(dirname "$target_file")"
    mv "$temp_file" "$target_file"
}

function manifest_value() {
    local key="$1"
    local file="$2"
    sed -n "s/^[[:space:]]*${key}:[[:space:]]*//p" "$file" | sed 's/^"//;s/"$//' | head -n 1
}

function manifest_color() {
    local key="$1"
    local file="$2"
    awk -v k="$key" '
        $1 ~ ("^" k ":") {
            if (match($0, /#[0-9A-Fa-f]{6}/)) {
                print substr($0, RSTART, RLENGTH)
                exit
            }
        }
    ' "$file"
}

function normalize_color() {
    local raw="${1:-}"
    local fallback="${2:-#3B82F6}"
    raw="$(echo "$raw" | tr -d '[:space:]')"
    if [[ "$raw" =~ ^#[0-9A-Fa-f]{6}$ ]]; then
        echo "$raw"
    else
        echo "$fallback"
    fi
}

function hex_to_rgb_floats() {
    local hex="$1"
    python3 - "$hex" <<'PY'
import sys
h = sys.argv[1].strip().lstrip("#")
r = int(h[0:2], 16) / 255.0
g = int(h[2:4], 16) / 255.0
b = int(h[4:6], 16) / 255.0
print(f"{r:.3f} {g:.3f} {b:.3f}")
PY
}

function scale_hex_color() {
    local hex="$1"
    local factor="$2"
    python3 - "$hex" "$factor" <<'PY'
import sys
h = sys.argv[1].strip().lstrip("#")
f = float(sys.argv[2])
r = max(0, min(255, round(int(h[0:2], 16) * f)))
g = max(0, min(255, round(int(h[2:4], 16) * f)))
b = max(0, min(255, round(int(h[4:6], 16) * f)))
print(f"#{r:02X}{g:02X}{b:02X}")
PY
}

function make_solid_png() {
    local out_path="$1"
    local hex="$2"
    local alpha="${3:-255}"
    python3 - "$out_path" "$hex" "$alpha" <<'PY'
import binascii
import struct
import sys
import zlib

out_path, color_hex, alpha = sys.argv[1], sys.argv[2].lstrip("#"), int(sys.argv[3])
r = int(color_hex[0:2], 16)
g = int(color_hex[2:4], 16)
b = int(color_hex[4:6], 16)

def chunk(chunk_type, data):
    return (
        struct.pack("!I", len(data))
        + chunk_type
        + data
        + struct.pack("!I", binascii.crc32(chunk_type + data) & 0xFFFFFFFF)
    )

# RGBA pixel with filter byte 0
raw = bytes([0, r, g, b, alpha])
ihdr = struct.pack("!IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
png = (
    b"\x89PNG\r\n\x1a\n"
    + chunk(b"IHDR", ihdr)
    + chunk(b"IDAT", zlib.compress(raw, 9))
    + chunk(b"IEND", b"")
)

with open(out_path, "wb") as f:
    f.write(png)
PY
}

function escape_qml_string() {
    local value="$1"
    python3 - "$value" <<'PY'
import json
import sys
print(json.dumps(sys.argv[1])[1:-1])
PY
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
primary_color=$(normalize_color "$(manifest_color primary "$manifest")" "#3B82F6")
secondary_color=$(normalize_color "$(manifest_color secondary "$manifest")" "#64748B")
background_color=$(normalize_color "$(manifest_color background "$manifest")" "#070B16")
surface_color=$(normalize_color "$(manifest_color surface "$manifest")" "#111827")
text_color=$(normalize_color "$(manifest_color text "$manifest")" "#E5E7EB")

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

# 3. Stage Edition Assets in transient live-build overlay
echo "📦 Staging edition assets..."
clean_staging
mkdir -p "$STAGING_CHROOT"
mkdir -p "$PACKAGE_LIST_DIR"

sanitize_package_profile "$EDITION_DIR/package-profile.txt" "$STAGED_PKG_LIST"

cp "$EDITION_DIR/colors.css" "$STAGING_CHROOT/colors.css"

# Stage custom wallpaper if defined
if [ -n "$wallpaper_name" ]; then
    echo "🖼️  Staging custom wallpaper: $wallpaper_name"
    mkdir -p "$(dirname "$STAGING_WALLPAPER_PATH")"
    cp "$EDITION_DIR/$wallpaper_name" "$STAGING_WALLPAPER_PATH"
else
    echo "⚠️  WARNING: No wallpaper entry found in manifest."
fi

# Stage custom logo if defined (overrides Plymouth boot splash and SDDM login screen assets)
if [ -n "$logo_name" ]; then
    echo "🎨 Staging custom logo and full branding templates: $logo_name"
    plymouth_theme_root="$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/plymouth/themes"
    sddm_theme_root="$STAGING_LB_CONFIG_DIR/includes.chroot/usr/share/sddm/themes"
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

    read -r bg_top_r bg_top_g bg_top_b <<< "$(hex_to_rgb_floats "$background_color")"
    read -r bg_bot_r bg_bot_g bg_bot_b <<< "$(hex_to_rgb_floats "$surface_color")"
    progress_fill_color="$primary_color"
    progress_bg_color="$(scale_hex_color "$secondary_color" 0.45)"
    edition_name_qml="$(escape_qml_string "$display_name")"
    edition_tagline_qml="$(escape_qml_string "$tagline")"

    make_solid_png "$plymouth_theme_dir/progress-fill.png" "$progress_fill_color" 255
    make_solid_png "$plymouth_theme_dir/progress-bg.png" "$progress_bg_color" 210

    python3 - "$plymouth_theme_dir/phoenix.script" "$bg_top_r" "$bg_top_g" "$bg_top_b" "$bg_bot_r" "$bg_bot_g" "$bg_bot_b" <<'PY'
import sys

path = sys.argv[1]
bg_top_r, bg_top_g, bg_top_b = sys.argv[2], sys.argv[3], sys.argv[4]
bg_bot_r, bg_bot_g, bg_bot_b = sys.argv[5], sys.argv[6], sys.argv[7]
text = open(path, "r", encoding="utf-8").read()
replacements = {
    "__BG_TOP_R__": bg_top_r,
    "__BG_TOP_G__": bg_top_g,
    "__BG_TOP_B__": bg_top_b,
    "__BG_BOT_R__": bg_bot_r,
    "__BG_BOT_G__": bg_bot_g,
    "__BG_BOT_B__": bg_bot_b,
}
for key, value in replacements.items():
    text = text.replace(key, value)
open(path, "w", encoding="utf-8").write(text)
PY

    python3 - "$sddm_theme_dir/Main.qml" "$edition_name_qml" "$edition_tagline_qml" "$primary_color" "$secondary_color" "$background_color" "$surface_color" "$text_color" <<'PY'
import sys

path = sys.argv[1]
edition_name, edition_tagline = sys.argv[2], sys.argv[3]
primary, secondary, background, surface, text_color = sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8]
text = open(path, "r", encoding="utf-8").read()
replacements = {
    "__EDITION_NAME__": edition_name,
    "__EDITION_TAGLINE__": edition_tagline,
    "__COLOR_PRIMARY__": primary,
    "__COLOR_SECONDARY__": secondary,
    "__COLOR_BACKGROUND__": background,
    "__COLOR_SURFACE__": surface,
    "__COLOR_TEXT__": text_color,
}
for key, value in replacements.items():
    text = text.replace(key, value)
open(path, "w", encoding="utf-8").write(text)
PY
else
    echo "⚠️  WARNING: No logo entry found in manifest."
fi


cat <<EOF > "$STAGING_CHROOT/metadata.json"
{
  "id": "$EDITION_ID",
  "display_name": "$display_name",
  "tagline": "$tagline",
  "theme": {
    "primary": "$primary_color",
    "secondary": "$secondary_color",
    "background": "$background_color",
    "surface": "$surface_color",
    "text": "$text_color"
  }
}
EOF

echo "✅ Assets staged in: $STAGING_CHROOT"
echo "✅ Package list staged: $STAGED_PKG_LIST"
echo "✅ Transient overlay ready: $STAGING_LB_CONFIG_DIR"

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
